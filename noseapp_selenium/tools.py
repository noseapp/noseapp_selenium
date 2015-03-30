# -*- coding: utf8 -*-

from selenium.webdriver.remote.webdriver import WebDriver


def make_object(web_element):
    """
    Example:

        input = driver.find_element...
        value = make_object(input).value
        css_value = make_object(input).css.background_image

    :type web_element: selenium.webdriver.remote.webdriver.WebElement
    """
    # TODO: __setattr__
    class WebElementToObject(object):

        def __init__(self, web_element):
            self.__web_element = web_element

        @property
        def css(self):
            return WebElementCssToObject(self.__web_element)

        def __getattr__(self, item):
            atr = self.__web_element.get_attribute(item)

            if atr:
                return atr

            raise AttributeError('{} "{}"'.format(repr(self.__web_element), item))

    class WebElementCssToObject(object):

        def __init__(self, web_element):
            self.__web_element = web_element

        def __getattr__(self, item):
            return self.__web_element.value_of_css_property(
                item.replace('_', '-'),
            )

    return WebElementToObject(web_element)


def get_driver_from_web_element(web_element):
    """
    :type web_element: selenium.webdriver.remote.webdriver.WebElement
    """
    driver = web_element._parent

    if isinstance(driver, WebDriver):
        return driver

    return get_driver_from_web_element(driver)
