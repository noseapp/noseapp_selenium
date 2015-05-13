# -*- coding: utf-8 -*-

import time
from Queue import Queue

from noseapp.utils.common import waiting_for
from noseapp.utils.common import TimeoutException

from noseapp_selenium.query import QueryObject
from noseapp_selenium.proxy import to_proxy_object
from noseapp_selenium.tools import get_query_from_driver


def page_element(query_object):
    """
    Factory for creating query
    result from query object instance
    """
    def wrapper(self):
        return self.query.from_object(query_object).first()
    return property(wrapper)


class WaitConfig(object):
    """
    Configuration for wait complete method
    """

    def __init__(self,
                 objects=None,
                 one_of_many=False,
                 timeout=30,
                 ready_state_complete=True):
        self._objects = objects or tuple()
        self._one_of_many = one_of_many
        self._timeout = timeout
        self._ready_state_complete = ready_state_complete

    @property
    def objects(self):
        return self._objects

    @property
    def timeout(self):
        return self._timeout

    @property
    def one_of_many(self):
        return self._one_of_many

    @property
    def ready_state_complete(self):
        return self._ready_state_complete


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


class PageObject(object):
    """
    Base page class
    """

    __metaclass__ = PageObjectMeta

    def __init__(self, driver):
        self._driver = to_proxy_object(driver)

        meta = getattr(self, 'Meta', object())

        self._wrapper = getattr(meta, 'wrapper', None)

        if not hasattr(self, 'wait_complete'):
            wait_config = getattr(meta, 'wait_config', WaitConfig())
            self.wait_complete = WaitComplete(
                self._driver,
                self._wrapper,
                self.__class__.__name__,
                wait_config,
            )

    @property
    def query(self):
        return get_query_from_driver(
            self._driver,
            wrapper=self._wrapper,
        )


class WaitComplete(object):
    """
    Waiting for load page
    """

    def __init__(self, driver, wrapper, page_name, config):
        self.config = config

        self.__driver = driver
        self.__wrapper = wrapper
        self.__page_name = page_name

    def __call__(self):
        if self.config.ready_state_complete:
            self.__ready_state_complete()

        wait_funcs = {
            False: self.__all,
            True: self.__one_of_many,
        }
        wait_funcs[bool(self.config.one_of_many)]()

    def __repr__(self):
        return '<WaitComplete of <{}>>'.format(self.__page_name)

    def __ready_state_complete(self):
        waiting_for(
            lambda: self.__driver.execute_script(
                'return document.readyState == "complete"',
            ),
            timeout=self.config.timeout,
        )

    def __all(self):
        if not self.config.objects:
            return

        queue = Queue()
        map(queue.put_nowait, self.config.objects)
        t_start = time.time()

        query = get_query_from_driver(
            self.__driver,
            wrapper=self.__wrapper,
        )

        while (time.time() <= t_start + self.config.timeout) or (not queue.empty()):
            obj = queue.get()

            if not query.from_object(obj).exist:
                queue.put(obj)
        else:
            if not queue.empty():
                raise TimeoutException(
                    'Could not wait ready page "{}". Timeout "{}" exceeded.'.format(
                        self.__page_name, self.config.timeout,
                    ),
                )

    def __one_of_many(self):
        if not self.config.objects:
            return

        queue = Queue()
        map(queue.put_nowait, self.config.objects)
        t_start = time.time()

        query = get_query_from_driver(
            self.__driver,
            wrapper=self.__wrapper,
        )

        while time.time() <= t_start + self.config.timeout:
            obj = queue.get()

            if query.from_object(obj).exist:
                break

            queue.put(obj)
        else:
            raise TimeoutException(
                'Could not wait ready page "{}". Timeout "{}" exceeded.'.format(
                    self.__page_name, self.config.timeout,
                ),
            )
