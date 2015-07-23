# -*- coding: utf-8 -*-

from copy import deepcopy
from selenium.common.exceptions import NoSuchElementException

from noseapp_selenium.tools import polling
from noseapp_selenium.proxy import get_driver
from noseapp_selenium.query import QueryObject
from noseapp_selenium.proxy import to_proxy_object
from noseapp_selenium.tools import get_query_from_driver
from noseapp_selenium.page_object.wait import WaitComplete
from noseapp_selenium.page_object.wait import ContentLength
from noseapp_selenium.tools import get_meta_info_from_object
from noseapp_selenium.page_object.wait import wait_for_filling


def page_element(query_object):
    """
    Factory for creating query
    result from query object instance
    """
    def wrapper(self):
        return self.query.from_object(query_object).first()
    return property(wrapper)


class BaseInterfaceObjectOfPage(object):
    """
    Common interface for all objects of page
    """

    @property
    def query(self):
        raise NotImplementedError('Property "query"')

    @property
    def driver(self):
        raise NotImplementedError('Property "driver"')

    @property
    def wrapper(self):
        raise NotImplementedError('Property "wrapper"')

    def use_with(self, obj_or_driver):
        raise NotImplementedError('Method "use with"')


class PageApi(object):
    """
    For creating api methods of page
    """

    def __init__(self, page):
        self.__page = page

    @property
    def page(self):
        return self.__page


class PageFactory(object):
    """
    Factory for create child objects
    """

    def __init__(self, page):
        self.__page = page

    def __call__(self, *args, **kwargs):
        return self.creator(*args, **kwargs)

    def creator(self, cls, args=None, kwargs=None):
        args = args or tuple()
        kwargs = kwargs or dict()

        if issubclass(cls, PageObject):
            kwargs.setdefault('wrapper', self.__page.wrapper)

        return cls(self.__page.driver, *args, **kwargs)


class ChildObjects(dict):
    """
    Storage for child objects of page
    """

    def __init__(self, *args, **kwargs):
        super(ChildObjects, self).__init__(*args, **kwargs)

        self.__dict__['__page__'] = None
        self.__dict__['__instances__'] = {}

    def __setattr__(self, key, value):
        self.add(key, value)

    def __getattr__(self, item):
        if item in self.__dict__['__instances__']:
            return self.__dict__['__instances__'][item]

        try:
            cls = self[item]
        except KeyError:
            raise AttributeError(
                'Child object "{}" does not exist'.format(item),
            )

        self.__dict__['__instances__'][item] = self.__dict__['__page__'].factory(cls)

        return self.__dict__['__instances__'][item]

    def mount(self, page):
        self.__dict__['__page__'] = page
        return self

    def add(self, key, value):
        self.__dict__['__instances__'][key] = value

    def refresh(self):
        self.__dict__['__instances__'] = {}


class PageObjectMeta(type):
    """
    Factory for creating page object class
    """

    def __new__(cls, name, bases, dct):
        new_cls = type.__new__(cls, name, bases, dct)

        cls_items = (
            (a, getattr(new_cls, a, None))
            for a in dir(new_cls)
            if not a.startswith('_')
        )

        for atr, value in cls_items:
            if isinstance(value, QueryObject):
                setattr(new_cls, atr, page_element(value))

        return new_cls


class PageObject(BaseInterfaceObjectOfPage):
    """
    Base page class
    """

    __metaclass__ = PageObjectMeta

    def __init__(self, driver, wrapper=None):
        self.selected = None
        self.meta = get_meta_info_from_object(self)

        self.api = self.meta.get('api_class', PageApi)(self)
        self.factory = self.meta.get('factory_class', PageFactory)(self)

        self.forms = deepcopy(self.meta.get('forms', ChildObjects())).mount(self)
        self.objects = deepcopy(self.meta.get('objects', ChildObjects())).mount(self)

        if not hasattr(self, 'wait_complete'):
            self.wait_complete = WaitComplete(self)

        self.__driver = to_proxy_object(driver)
        self.__content_length = ContentLength(driver)
        self.__wrapper = self.meta.get('wrapper', wrapper)

    @property
    def query(self):
        return get_query_from_driver(
            self.__driver,
            wrapper=self.__wrapper,
        )

    @property
    def driver(self):
        return self.__driver

    @property
    def wrapper(self):
        return self.__wrapper

    @property
    def children(self):
        return []

    @property
    def content_length(self):
        self.__content_length.update()
        return int(self.__content_length)

    @polling(timeout=5)
    def select(self, **ftr):
        try:
            key = ftr.keys()[0]
        except IndexError:
            raise TypeError('Filter is not defined')
        value = ftr[key]

        try:
            self.selected = next(
                o for o in self.children
                if getattr(o, key) == value,
            )
        except StopIteration:
            raise NoSuchElementException(
                'Object of "{}" is not selected. Filter: {}={}'.format(
                    self.__class__.__name__, key, value,
                ),
            )

    def get_wrapper_element(self):
        if self.__wrapper:
            return self.__driver.query.from_object(
                self.__wrapper,
            ).first()

        return None

    def use_with(self, obj_or_driver):
        if isinstance(obj_or_driver, BaseInterfaceObjectOfPage):
            self.__driver = obj_or_driver.driver
        else:
            self.__driver = obj_or_driver

    def wait_for_filling(self, steps=None, tries_at_step=None):
        return wait_for_filling(
            steps=steps,
            tries_at_step=tries_at_step,
            content_length=self.__content_length,
        )

    def wait(self):
        self.wait_complete()

    def refresh(self, force=False):
        if force:
            get_driver(self.__driver).refresh()

        self.forms.refresh()
        self.objects.refresh()


assert issubclass(PageObject, BaseInterfaceObjectOfPage)
