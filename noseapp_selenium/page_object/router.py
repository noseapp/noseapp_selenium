# -*- coding: utf-8 -*-

import re

from noseapp.utils.common import waiting_for

from noseapp_selenium.query import QueryResult
from noseapp_selenium.query import QueryObject
from noseapp_selenium.page_object.base import PageObject


class PageIsNotFound(BaseException):
    pass


class PageRouter(object):
    """
    Realization relationships of page object to regexp string.
    """

    __rules = {}

    def __init__(self, driver, base_path=None):
        self._driver = driver
        self._base_path = base_path.rstrip('/')

    @classmethod
    def add_rule(cls, rule, page_cls):
        """
        Add rule for page object class

        :param rule: regexp
        :param page_cls: page object class
        """
        if not issubclass(page_cls, PageObject):
            raise ValueError('page is not PageObject subclass')

        cls.__rules[re.compile(r'^{}$'.format(rule))] = page_cls

    @property
    def base_path(self):
        return self._base_path + '/'

    def get(self, path, wait=True, go_to=True):
        """
        Get page object instance by path.

        Create page instance, go to path,
        call wait complete method of page object.

        :type path: str
        """
        for rule in self.__rules:
            if rule.search(path) is not None:
                page_cls = self.__rules[rule]
                page = page_cls(self._driver)
                break
        else:
            raise PageIsNotFound(path)

        if self._base_path is not None and go_to:
            self.go_to(path)

            if type(wait) is bool and wait:
                page.wait_complete()
            elif isinstance(wait, QueryResult):
                wait.wait()
            elif isinstance(wait, QueryObject):
                page._query.from_object(wait).wait()
            elif callable(wait):
                waiting_for(wait)

        return page

    def get_no_wait(self, path):
        """
        Get method wrapper.

        Get page object instance by rule and
        exclude calling wait complete method of page object.
        """
        return self.get(path, wait=False)

    def get_page(self, path):
        """
        Get method wrapper.

        Get page object instance by rule. Don't go to path.
        """
        return self.get(path, go_to=False)

    def go_to(self, path):
        """
        Simple go to path.
        """
        self._driver.get('{}{}'.format(self._base_path, path))
