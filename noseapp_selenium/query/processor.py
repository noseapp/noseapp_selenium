# -*- coding: utf-8 -*-

from selenium.webdriver.remote.webelement import WebElement

from noseapp_selenium.proxy import to_proxy_object
from noseapp_selenium.query.base import QueryObject
from noseapp_selenium.query.handler import make_result


class QueryProcessor(object):
    """
    Example:

        driver = WebDriver()
        query = QueryProcessor(driver)

        search_wrapper = query.div(id='search').first()
        search_field = query(search_wrapper).input(_class='search').first()
        search_field.send_keys(*'Hello World!')
    """

    def __init__(self, client):
        self._client = to_proxy_object(client)

    def __getattr__(self, item):
        return make_result(self._client, item)

    def __call__(self, client):
        return self.__class__(client)

    @property
    def client(self):
        return self._client

    def from_object(self, obj):
        """
        Creating result from object

        :type obj: QueryObject
        """
        if not isinstance(obj, QueryObject):
            raise TypeError('"{}" is not QueryObject instance'.format(type(obj)))

        return self.__getattr__(obj.tag)(**obj.selector)

    def get_text(self):
        """
        Get text from page or web element
        """
        if isinstance(self._client.orig(), WebElement):
            return self._client.text

        return self._client.find_element_by_tag_name('body').text
