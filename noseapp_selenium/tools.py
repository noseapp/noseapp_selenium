# -*- coding: utf8 -*-

import time
from functools import wraps

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException


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


def polling(self, callback=None, timeout=30, sleep=0.01):

    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            t_start = time.time()

            while time.time() <= t_start + timeout:
                try:
                    return f(*args, **kwargs)
                except WebDriverException:
                    time.sleep(sleep)
                    continue
            else:
                # raise condition
                return f(*args, **kwargs)

        return wrapped

    if callable(callback):
        return wrapper(callback)

    return wrapper


def re_raise_wd_exception(callback=None, exc_cls=WebDriverException, message=None):

    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except WebDriverException as e:
                raise exc_cls(
                    u"""
                    Re raise web driver exception:

                    * Message: {}
                    * Original exception class: {}
                    * Original message: {}
                    """.format(
                        message or '',
                        e.__class__.__name__,
                        e.message,
                    ),
                )

        return wrapped

    if callable(callback):
        return wrapper(callback)

    return wrapper
