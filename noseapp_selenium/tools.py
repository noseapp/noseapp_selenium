# -*- coding: utf8 -*-

import time
from functools import wraps

from noseapp.utils.common import TimeoutException
from selenium.common.exceptions import WebDriverException


class WebElementToObject(object):  # TODO: __setattr__

    def __init__(self, web_element, allow_raise=True):
        self.__web_element = web_element
        self.__allow_raise = allow_raise

    @property
    def css(self):
        return WebElementCssToObject(self.__web_element)

    def __getattr__(self, item):
        atr = self.__web_element.get_attribute(
            item.replace('_', '-'),
        )

        if atr:
            return atr

        if self.__allow_raise:
            raise AttributeError('{} "{}"'.format(repr(self.__web_element), item))


class WebElementCssToObject(object):

    def __init__(self, web_element):
        self.__web_element = web_element

    def __getattr__(self, item):
        return self.__web_element.value_of_css_property(
            item.replace('_', '-'),
        )


def make_object(web_element, allow_raise=True):
    """
    Convert web element to object.

    Example:

        input = driver.find_element...
        value = make_object(input).value
        css_value = make_object(input).css.background_image

    :type web_element: selenium.webdriver.remote.webdriver.WebElement
    """
    return WebElementToObject(web_element, allow_raise=allow_raise)


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


def get_query_from_driver(driver, wrapper=None):
    """
    Return QueryProcessor instance from driver.
    If wrapper is not None, at wrapper will be merged.

    :param driver: ProxyObject
    :param wrapper: QueryObject
    """
    if wrapper:
        return driver.query.from_object(
            wrapper,
        ).first().query

    return driver.query


def get_meta_info_from_object(obj, **defaults):
    """
    Convert meta info class to dict
    """
    meta = getattr(obj, 'Meta', object())
    dct = dict(
        (atr_name, getattr(meta, atr_name, None))
        for atr_name in dir(meta)
        if not atr_name.startswith('_')
    )

    if defaults:
        for k, v in defaults.items():
            set_default_to_meta(meta, k, v)

    return dct


def set_default_to_meta(meta, key, default_value):
    """
    Set default value to dict of meta
    """
    if callable(default_value):
        default_value = default_value()

    meta.setdefault(key, default_value)
