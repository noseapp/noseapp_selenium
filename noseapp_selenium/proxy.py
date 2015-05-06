# -*- coding: utf-8 -*-

from types import MethodType
from contextlib import contextmanager

from selenium.webdriver.remote.webelement import WebElement

from noseapp_selenium.tools import polling
from noseapp_selenium.tools import get_config


def factory(f):
    """
    Factory for create WebElement instance
    """
    def wrapper(*args, **kwargs):
        result = f(*args, **kwargs)

        if isinstance(result, WebElement):
            return ProxyObject(result)

        if isinstance(result, list):
            we_list = []
            for obj in result:
                if isinstance(obj, WebElement):
                    we_list.append(ProxyObject(obj))
                else:
                    return result
            return we_list

        return result

    return wrapper


class ProxyObject(object):
    """
    Proxy for WebElement or WebDriver instance
    """

    def __init__(self, wrapped):
        self.__dict__['polling'] = True
        self.__dict__['wrapped'] = wrapped
        self.__dict__['config'] = get_config(wrapped)

    @contextmanager
    def disable_polling(self):
        try:
            self.__dict__['polling'] = False

            wrapped = self.__dict__['wrapped']

            if hasattr(wrapped, 'disable_polling'):
                with wrapped.disable_polling():
                    yield
                    self.__dict__['polling'] = True
            else:
                yield
                self.__dict__['polling'] = True
        except:
            self.__dict__['polling'] = True
            raise

    def orig(self):
        return self.__dict__['wrapped']

    def __getattr__(self, item):
        wrapped = self.__dict__['wrapped']
        config = self.__dict__['config']

        allow_polling = config.POLLING_TIMEOUT and self.__dict__['polling']

        attr = getattr(wrapped, item)

        if callable(attr) and type(attr) == MethodType:
            if allow_polling:
                return polling(callback=factory(attr), timeout=config.POLLING_TIMEOUT)

            return factory(attr)

        return attr

    def __setattr__(self, key, value):
        return setattr(self.__dict__['wrapped'], key, value)

    def __repr__(self):
        return 'ProxyObject: {}'.format(
            repr(self.__dict__['wrapped']),
        )
