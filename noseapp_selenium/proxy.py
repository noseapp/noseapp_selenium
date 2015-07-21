# -*- coding: utf-8 -*-

from types import MethodType
from contextlib import contextmanager

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains as __ActionChains

from noseapp_selenium.tools import polling
from noseapp_selenium.tools import make_object
from noseapp_selenium.query.processor import QueryProcessor


def factory_method(f, config):
    """
    Factory for create WebElement instance
    """
    def wrapper(*args, **kwargs):
        result = f(*args, **kwargs)

        if isinstance(result, WebElement):
            return ProxyObject(result, config=config)

        if isinstance(result, list):
            we_list = []
            for obj in result:
                if isinstance(obj, WebElement):
                    we_list.append(ProxyObject(obj, config=config))
                else:
                    return result
            return we_list

        return result

    return wrapper


def to_proxy_object(obj, **kw):
    """
    Convert instance to ProxyObject
    """
    if isinstance(obj, (WebElement, WebDriver)):
        return ProxyObject(obj, **kw)

    return obj


def get_driver(driver):
    """
    Get instance of web driver
    """
    if isinstance(driver.orig(), WebDriver):
        d = driver
    else:
        d = ProxyObject(driver._parent)

    if isinstance(d.orig(), WebDriver):
        return d

    return get_driver(d)


class ActionChains(__ActionChains):
    """
    Action chains inside ProxyObject
    """

    def __init__(self, driver):
        super(ActionChains, self).__init__(get_driver(driver))

    def perform(self):
        """
        We are must refresh actions after perform
        """
        super(ActionChains, self).perform()
        self._actions = []

    def new(self):
        """
        Create new instance of self
        """
        return self.__class__(self._driver)


class ProxyObject(object):
    """
    Proxy for WebElement or WebDriver instance
    """

    def __init__(self, wrapped, config=None):
        self.__dict__['polling'] = True
        self.__dict__['wrapped'] = wrapped
        self.__dict__['config'] = config or wrapped.config

        wrapped.query = QueryProcessor(self)
        wrapped.action_chains = ActionChains(self)

    @property
    def config(self):
        return self.__dict__['config']

    @property
    def query(self):
        return self.__dict__['wrapped'].query

    @property
    def action_chains(self):
        return self.__dict__['wrapped'].action_chains

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

    @property
    def obj(self):
        return make_object(self.__dict__['wrapped'], allow_raise=False)

    def __getattr__(self, item):
        wrapped = self.__dict__['wrapped']
        config = self.__dict__['config']

        allow_polling = config.POLLING_TIMEOUT and self.__dict__['polling']

        attr = getattr(wrapped, item)

        if callable(attr) and type(attr) == MethodType:
            if allow_polling:
                return polling(
                    callback=factory_method(attr, config),
                    timeout=config.POLLING_TIMEOUT,
                )

            return factory_method(attr, config)

        return attr

    def __setattr__(self, key, value):
        return setattr(self.__dict__['wrapped'], key, value)

    def __repr__(self):
        return 'ProxyObject: {}'.format(
            repr(self.__dict__['wrapped']),
        )
