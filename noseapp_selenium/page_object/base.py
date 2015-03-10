# -*- coding: utf-8 -*-

import time
from Queue import Queue

from noseapp.utils.common import waiting_for
from noseapp.utils.common import TimeoutException

from noseapp_selenium import QueryProcessor
from noseapp_selenium.query import QueryObject


def page_element(query_object):

    def wrapper(self):
        if isinstance(self._wrapper, QueryObject):
            return self._query(
                self._query.from_object(self._wrapper).first(),
            ).from_object(query_object).first()
        return self._query.from_object(query_object).first()

    return property(wrapper)


class PageObjectMeta(type):

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

    __metaclass__ = PageObjectMeta

    def __init__(self, driver):
        self._driver = driver
        self._query = QueryProcessor(self._driver)

        meta = getattr(self, 'Meta', object())

        self._wrapper = getattr(meta, 'wrapper', None)
        self.wait_complete = WaitComplete(self)


class WaitComplete(object):

    def __init__(self, page):
        self._query = page._query
        self._driver = page._driver
        self._page_name = page.__class__.__name__

        meta = getattr(page, 'Meta', object())

        self._wait_objects = getattr(meta, 'wait_objects', tuple())
        self._timeout = getattr(meta, 'wait_complete_timeout', 30)
        self._one_of_many = bool(getattr(meta, 'wait_one_of_many', False))
        self._ready_state_complete = getattr(meta, 'wait_ready_state_complete', True)

    def __call__(self):
        if self._ready_state_complete:
            self.ready_state_complete()

        wait_funcs = {
            False: self.all,
            True: self.one,
        }
        wait_funcs[self._one_of_many]()

    def __repr__(self):
        return '<WaitComplete of <{}>>'.format(self._page_name)

    def ready_state_complete(self):
        waiting_for(
            lambda: self._driver.execute_script(
                'return document.readyState == "complete"',
            ),
            timeout=self._timeout,
        )

    def all(self):
        if not self._wait_objects:
            return

        queue = Queue()
        map(queue.put_nowait, self._wait_objects)
        t_start = time.time()

        while (time.time() <= t_start + self._timeout) or (not queue.empty()):
            obj = queue.get()

            if not self._query.from_object(obj).exist:
                queue.put(obj)
        else:
            if not queue.empty():
                raise TimeoutException(
                    'Could not wait ready page "{}". Timeout "{}" exceeded.'.format(
                        self._page_name, self._timeout,
                    ),
                )

    def one(self):
        if not self._wait_objects:
            return

        queue = Queue()
        map(queue.put_nowait, self._wait_objects)
        t_start = time.time()

        while time.time() <= t_start + self._timeout:
            obj = queue.get()

            if self._query.from_object(obj).exist:
                break

            queue.put(obj)
        else:
            raise TimeoutException(
                'Could not wait ready page "{}". Timeout "{}" exceeded.'.format(
                    self._page_name, self._timeout,
                ),
            )
