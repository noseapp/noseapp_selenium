# -*- coding: utf-8 -*-

from selenium.webdriver.remote.webelement import WebElement

from noseapp_selenium.query.base import QueryObject
from noseapp_selenium.query.handler import make_result


class QueryProcessor(object):
    """
    Class implement dynamic interface for creation query to
    instance of WebDriver or WebElement class

    Example:

        driver = WebDriver()
        query = QueryProcessor(driver)

        search_field = query.div(id='search').input(_class='search').first()
        search_field.send_keys(*'Hello World!')

        or

        search_wrapper = query.div(id='search').first()
        search_field = query(search_wrapper).input(_class='search').first()
        search_field.send_keys(*'Hello World!')
    """

    def __init__(self, client):
        """
        :param client: instance of WebDriver or WebElement class
        """
        self.__client = client

    def __getattr__(self, item):
        return make_result(self.__client, item)

    def __call__(self, client):
        return self.__class__(client)

    @property
    def client(self):
        return self.__client

    def from_object(self, obj):
        """
        Create result from QueryObject instance

        :type obj: QueryObject
        """
        if not isinstance(obj, QueryObject):
            raise TypeError('"{}" is not QueryObject instance'.format(type(obj)))

        return self.__getattr__(obj.tag)(**obj.selector)

    def get_text(self):
        """
        Get text from driver or web element.

        if client is instance of WebDriver, then will
        be selected tag body as client.
        """
        if isinstance(self.__client.orig(), WebElement):
            return self.__client.text

        return self.__client.find_element_by_tag_name('body').text
