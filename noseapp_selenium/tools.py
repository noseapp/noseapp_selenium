# -*- coding: utf8 -*-

from selenium.webdriver.remote.webdriver import WebDriver


def make_object(web_element):
    """
    Example:

        input = driver.find_element...
        value = make_object(input).value

    :type web_element: selenium.webdriver.remote.webdriver.WebElement
    """
    # TODO: __setattr__
    class WebElementToObject(object):

        def __init__(self, web_element):
            self._web_element = web_element

        def __getattr__(self, item):
            atr = self._web_element.get_attribute(item)

            if atr:
                return atr

            raise AttributeError('{} "{}"'.format(repr(self._web_element), item))

    return WebElementToObject(web_element)


class Container(object):

    def __init__(self, _class):
        self.__class = _class

    def __call__(self, *args, **kwargs):
        return self.__class(*args, **kwargs)


def get_driver_from_web_element(web_element):
    """
    :type web_element: selenium.webdriver.remote.webdriver.WebElement
    """
    driver = web_element._parent

    if isinstance(driver, WebDriver):
        return driver

    return get_driver_from_web_element(driver)
