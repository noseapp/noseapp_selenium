# -*- coding: utf-8 -*-

import re

from noseapp.utils.common import waiting_for

from noseapp_selenium.query import QueryResult
from noseapp_selenium.query import QueryObject
from noseapp_selenium.page_object.base import PageObject


class PageIsNotFound(BaseException):
    pass


class PageRouter(object):

    __rules = {}

    def __init__(self, driver, base_path=None):
        self._driver = driver
        self._base_path = base_path

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

    def get(self, path, wait=True):
        """
        Get page object instance by path

        :type path: str
        """
        for rule in self.__rules:
            if rule.search(path) is not None:
                page_cls = self.__rules[rule]
                page = page_cls(self._driver)
                break
        else:
            raise PageIsNotFound(path)

        if self._base_path is not None:
            self._driver.get('{}{}'.format(self._base_path, path))

            if type(wait) is bool and wait:
                page.wait_complete()
            elif isinstance(wait, QueryResult):
                wait.wait()
            elif isinstance(wait, QueryObject):
                page._query.from_object(wait).wait()
            elif callable(wait):
                waiting_for(wait)

        return page
