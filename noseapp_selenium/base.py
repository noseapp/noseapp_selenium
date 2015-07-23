# -*- coding: utf-8 -*-

import logging
from functools import wraps
from urllib2 import URLError

from noseapp.core import ExtensionInstaller
from noseapp.utils.common import waiting_for
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from noseapp_selenium import drivers
from noseapp_selenium.proxy import to_proxy_object
from noseapp_selenium.page_object.router import PageRouter


logger = logging.getLogger(__name__)


GET_DRIVER_SLEEP = 0.5
GET_DRIVER_TIMEOUT = 10

DEFAULT_WINDOW_SIZE = None
DEFAULT_IMPLICITLY_WAIT = 30
DEFAULT_POLLING_TIMEOUT = 30
DEFAULT_MAXIMIZE_WINDOW = True
DEFAULT_DRIVER = drivers.CHROME

DRIVER_TO_CAPABILITIES = {
    drivers.OPERA: DesiredCapabilities.OPERA,
    drivers.CHROME: DesiredCapabilities.CHROME,
    drivers.FIREFOX: DesiredCapabilities.FIREFOX,
    drivers.PHANTOMJS: DesiredCapabilities.PHANTOMJS,
    drivers.IE: DesiredCapabilities.INTERNETEXPLORER,
}


class SeleniumExError(BaseException):
    pass


def get_capabilities(driver_name):
    """
    Get capabilities of driver

    :param driver_name: driver name
    :type driver_name: str
    """
    try:
        return DRIVER_TO_CAPABILITIES[driver_name]
    except KeyError:
        raise SeleniumExError(
            'Capabilities for driver "{}" is not found'.find(driver_name),
        )


def patch(f):
    """
    Setup config to driver and apply settings.
    Wrap driver in proxy object.
    """
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        driver = f(self, *args, **kwargs)

        driver.config = DriverConfig(self, driver)
        driver.config.apply()

        return to_proxy_object(driver)

    return wrapper


class DriverConfig(object):
    """
    Configuration for WerDriver instance
    """

    def __init__(self, ex, driver):
        """
        :type ex: noseapp_selenium.base.SeleniumEx
        :type driver: selenium.webdriver.remote.webdriver.WebDriver
        """
        self.__driver = driver

        self.WINDOW_SIZE = ex.window_size
        self.IMPLICITLY_WAIT = ex.implicitly_wait
        self.MAXIMIZE_WINDOW = ex.maximize_window
        self.POLLING_TIMEOUT = ex.polling_timeout

    def apply(self):
        self.apply_implicitly_wait()
        self.apply_window_settings()

    def apply_implicitly_wait(self):
        if self.IMPLICITLY_WAIT is not None:
            self.__driver.implicitly_wait(self.IMPLICITLY_WAIT)
        else:
            self.__driver.IMPLICITLY_WAIT = 0

    def implicitly_wait(self, value):
        self.__driver.implicitly_wait(value)

    def apply_window_settings(self):
        if self.WINDOW_SIZE:
            self.__driver.set_window_size(*self.WINDOW_SIZE)
        elif self.MAXIMIZE_WINDOW:
            self.__driver.maximize_window()


class SeleniumEx(object):
    """
    Initialize selenium extension for noseapp
    """

    name = 'selenium'
    config_key = 'SELENIUM_EX'

    def __init__(
            self,
            config,
            use_remote=False,
            driver_name=DEFAULT_DRIVER,
            window_size=DEFAULT_WINDOW_SIZE,
            maximize_window=DEFAULT_MAXIMIZE_WINDOW,
            implicitly_wait=DEFAULT_IMPLICITLY_WAIT,
            polling_timeout=DEFAULT_POLLING_TIMEOUT):
        # self settings
        self.__config = config
        self.__use_remote = use_remote
        self.__driver_name = driver_name.lower()

        # will be pushed to web driver config
        self.__window_size = window_size
        self.__maximize_window = maximize_window
        self.__implicitly_wait = implicitly_wait
        self.__polling_timeout = polling_timeout

        logger.debug(
            'Selenium-EX initialize. Config: {}, Use Remote: {}, Driver name: {}'.format(
                config,
                'Yes' if use_remote else 'No',
                driver_name,
            ),
        )

    @classmethod
    def install(cls, app, url_rule_to_page=None):
        """
        Automatic installation from app instance

        :param app: instance of application
        :param url_rule_to_page: relationships of url rules to page class
        :type url_rule_to_page: dict
        """
        config = app.config.get(cls.config_key, {})
        options = config.pop('OPTIONS', {})
        installer = ExtensionInstaller(cls, (config, ), options)
        app.shared_extension(cls=installer)

        if isinstance(url_rule_to_page, dict):
            for rule, page_cls in url_rule_to_page.items():
                PageRouter.add_rule(rule, page_cls)

        return installer

    @property
    def config(self):
        return self.__config

    @property
    def use_remote(self):
        return self.__use_remote

    @property
    def driver_name(self):
        return self.__driver_name

    @property
    def window_size(self):
        return self.__window_size

    @property
    def maximize_window(self):
        return self.__maximize_window

    @property
    def implicitly_wait(self):
        return self.__implicitly_wait

    @property
    def polling_timeout(self):
        return self.__polling_timeout

    @patch
    def remote(self):
        """
        :return: selenium.webdriver.remote.webdriver.WebDriver
        """
        remote_config = self.__config.get('REMOTE_WEBDRIVER')

        if not remote_config:
            raise SeleniumExError('remote web driver settings not found')

        logger.debug('Remote config: {}'.format(str(remote_config)))

        options = remote_config.get('options', {})
        capabilities = get_capabilities(self.__driver_name)
        capabilities.update(
            remote_config['capabilities'][self.__driver_name],
        )

        return drivers.RemoteWebDriver(
            desired_capabilities=capabilities,
            **options
        )

    @patch
    def ie(self):
        """
        :return: selenium.webdriver.ie.webdriver.WebDriver
        """
        ie_config = self.__config.get('IE_WEBDRIVER')

        if not ie_config:
            raise SeleniumExError('ie web driver settings not found')

        logger.debug('Ie config: {}'.format(str(ie_config)))

        return drivers.IeWebDriver(**ie_config)

    @patch
    def chrome(self):
        """
        :return: selenium.webdriver.chrome.webdriver.WebDriver
        """
        chrome_config = self.__config.get('CHROME_WEBDRIVER')

        if not chrome_config:
            raise SeleniumExError('google chrome web driver settings not found')

        logger.debug('Chrome config: {}'.format(str(chrome_config)))

        return drivers.ChromeWebDriver(**chrome_config)

    @patch
    def firefox(self):
        """
        :return: selenium.webdriver.firefox.webdriver.WebDriver
        """
        firefox_config = self.__config.get('FIREFOX_WEBDRIVER', {})

        logger.debug('Firefox config: {}'.format(str(firefox_config)))

        return drivers.FirefoxWebDriver(**firefox_config)

    @patch
    def phantomjs(self):
        """
        :return: selenium.webdriver.phantomjs.webdriver.WebDriver
        """
        phantom_config = self.__config.get('PHANTOMJS_WEBDRIVER')

        if not phantom_config:
            raise SeleniumExError('phantom js web driver settings not found')

        logger.debug('PhantomJS config: {}'.format(str(phantom_config)))

        return drivers.PhantomJSWebDriver(**phantom_config)

    @patch
    def opera(self):
        """
        :return: selenium.webdriver.opera.webdriver.WebDriver
        """
        opera_config = self.__config.get('OPERA_WEBDRIVER')

        if not opera_config:
            raise SeleniumExError('opera web driver settings not found')

        logger.debug('Opera config: {}'.format(str(opera_config)))

        return drivers.OperaWebDriver(**opera_config)

    def _get_local_driver(self):
        driver = getattr(self, self.__driver_name, None)

        if driver:
            return driver()

        raise SeleniumExError(
            'Incorrect driver name "{}"'.format(self.__driver_name),
        )

    def get_driver(self,
                   driver_name=None,
                   timeout=None,
                   sleep=None):
        """
        :param driver_name: name of web driver
        :param timeout: timeout for getting driver
        :param sleep: sleep for polling

        :return: selenium.webdriver.remote.webdriver.WebDriver
        """
        if driver_name is not None:
            self.__driver_name = driver_name

        def get_driver(func):
            try:
                return func()
            except (URLError, WebDriverException):
                return None

        if self.__use_remote:
            driver = waiting_for(
                lambda: get_driver(self.remote),
                timeout=timeout or GET_DRIVER_TIMEOUT,
                sleep=sleep or GET_DRIVER_SLEEP,
            )
        else:
            driver = waiting_for(
                lambda: get_driver(self._get_local_driver),
                timeout=timeout or GET_DRIVER_TIMEOUT,
                sleep=sleep or GET_DRIVER_SLEEP,
            )

        return driver
