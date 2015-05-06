# -*- coding: utf-8 -*-

import time
from Queue import Queue

from noseapp.utils.common import waiting_for
from noseapp.utils.common import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from noseapp_selenium import QueryProcessor
from noseapp_selenium.query import QueryObject
from noseapp_selenium.proxy import ProxyObject


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
        if isinstance(driver, (WebDriver, WebElement)):
            driver = ProxyObject(driver)

        self._driver = driver
        self.__query = QueryProcessor(driver)

        meta = getattr(self, 'Meta', object())

        self._wrapper = getattr(meta, 'wrapper', None)

        if not hasattr(self, 'wait_complete'):
            wait_config = getattr(meta, 'wait_config', WaitConfig())
            self.wait_complete = WaitComplete(
                self._driver,
                self.__query,
                self.__class__.__name__,
                wait_config,
            )

    @property
    def query(self):
        if isinstance(self._wrapper, QueryObject):
            return self.__query(
                self.__query.from_object(self._wrapper).first(),
            )
        return self.__query


class WaitComplete(object):
    """
    Waiting for load page
    """

    def __init__(self, driver, query, page_name, config):
        self.config = config

        self.__query = query
        self.__driver = driver
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

        while (time.time() <= t_start + self.config.timeout) or (not queue.empty()):
            obj = queue.get()

            if not self.__query.from_object(obj).exist:
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

        while time.time() <= t_start + self.config.timeout:
            obj = queue.get()

            if self.__query.from_object(obj).exist:
                break

            queue.put(obj)
        else:
            raise TimeoutException(
                'Could not wait ready page "{}". Timeout "{}" exceeded.'.format(
                    self.__page_name, self.config.timeout,
                ),
            )
