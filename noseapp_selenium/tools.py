# -*- coding: utf8 -*-

import time
from functools import wraps

from noseapp.utils.common import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement


def make_object(web_element):
    """
    Convert web element to object.

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
    if isinstance(web_element, (WebElement, WebElementDecorator)):
        driver = web_element._parent
    else:
        driver = web_element

    if isinstance(driver, WebDriver):
        return driver

    return get_driver_from_web_element(driver)


def get_driver_from_query(query):
    """
    :param query: instance of QueryProcessor
    """
    return get_driver_from_web_element(query._client)


def polling(callback=None, timeout=30, sleep=0.01):
    """
    Do sleep while wrapped function will be raised
    exception of WebDriverException class.

    Use timeout param for setting max seconds to waiting.
    This function will be used like decorator if callback is None.
    """
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
                raise

        return wrapped

    if callback is not None:
        return wrapper(callback)

    return wrapper


class ReRaiseWebDriverException(BaseException):
    pass


def re_raise_wd_exc(callback=None, exc_cls=ReRaiseWebDriverException, message=None):
    """
    Except WebDriverException and re raising to custom exception.
    Also, TimeoutException will be excepting for re raise polling.
    """
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (TimeoutException, WebDriverException) as e:
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


class WebElementDecorator(object):
    """
    Decorator for WebElement instance
    """

    DECORATOR_ID_TO_WEB_ELEMENT = {}  # Cached WebElement instance by decorator instance id

    def __init__(self, web_element):
        WebElementDecorator.DECORATOR_ID_TO_WEB_ELEMENT[id(self)] = web_element

    def __del__(self):
        del WebElementDecorator.DECORATOR_ID_TO_WEB_ELEMENT[id(self)]

    def __getattr__(self, item):
        web_element = WebElementDecorator.DECORATOR_ID_TO_WEB_ELEMENT[id(self)]

        driver = get_driver_from_web_element(web_element)

        atr = getattr(web_element, item)

        if callable(atr) and driver.config.POLLING_TIMEOUT:
            return polling(callback=atr, timeout=driver.config.POLLING_TIMEOUT)

        return atr

    def __setattr__(self, key, value):
        web_element = WebElementDecorator.DECORATOR_ID_TO_WEB_ELEMENT[id(self)]
        return setattr(web_element, key, value)

    def __repr__(self):
        web_element = WebElementDecorator.DECORATOR_ID_TO_WEB_ELEMENT[id(self)]
        return repr(web_element)
