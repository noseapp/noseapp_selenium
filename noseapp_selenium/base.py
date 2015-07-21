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


def setup_config(f):
    """
    Setup config to driver and apply settings.
    Wrap driver in proxy object.
    """
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        driver = f(self, *args, **kwargs)

        driver.config = DriverConfig(
            driver,
            window_size=self._window_size,
            implicitly_wait=self._implicitly_wait,
            maximize_window=self._maximize_window,
            polling_timeout=self._polling_timeout,
        )
        driver.config.apply()

        return to_proxy_object(driver)

    return wrapper


class DriverConfig(object):
    """
    Configuration for WerDriver instance
    """

    def __init__(self, driver,
                 window_size=DEFAULT_WINDOW_SIZE,
                 implicitly_wait=DEFAULT_IMPLICITLY_WAIT,
                 maximize_window=DEFAULT_MAXIMIZE_WINDOW,
                 polling_timeout=DEFAULT_POLLING_TIMEOUT):
        self.__driver = driver

        self.WINDOW_SIZE = window_size
        self.IMPLICITLY_WAIT = implicitly_wait
        self.MAXIMIZE_WINDOW = maximize_window
        self.POLLING_TIMEOUT = polling_timeout

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
        self._config = config
        self._use_remote = use_remote
        self._window_size = window_size
        self._driver_name = driver_name.lower()
        self._maximize_window = maximize_window
        self._implicitly_wait = implicitly_wait
        self._polling_timeout= polling_timeout

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
        return self._config

    @setup_config
    def remote(self):
        remote_config = self._config.get('REMOTE_WEBDRIVER')

        if not remote_config:
            raise SeleniumExError('remote web driver settings not found')

        logger.debug('Remote config: {}'.format(str(remote_config)))

        options = remote_config.get('options', {})
        capabilities = get_capabilities(self._driver_name)
        capabilities.update(
            remote_config['capabilities'][self._driver_name],
        )

        return drivers.RemoteWebDriver(
            desired_capabilities=capabilities,
            **options
        )

    @setup_config
    def ie(self):
        ie_config = self._config.get('IE_WEBDRIVER')

        if not ie_config:
            raise SeleniumExError('ie web driver settings not found')

        logger.debug('Ie config: {}'.format(str(ie_config)))

        return drivers.IeWebDriver(**ie_config)

    @setup_config
    def chrome(self):
        chrome_config = self._config.get('CHROME_WEBDRIVER')

        if not chrome_config:
            raise SeleniumExError('google chrome web driver settings not found')

        logger.debug('Chrome config: {}'.format(str(chrome_config)))

        return drivers.ChromeWebDriver(**chrome_config)

    @setup_config
    def firefox(self):
        firefox_config = self._config.get('FIREFOX_WEBDRIVER', {})

        logger.debug('Firefox config: {}'.format(str(firefox_config)))

        return drivers.FirefoxWebDriver(**firefox_config)

    @setup_config
    def phantomjs(self):
        phantom_config = self._config.get('PHANTOMJS_WEBDRIVER')

        if not phantom_config:
            raise SeleniumExError('phantom js web driver settings not found')

        logger.debug('PhantomJS config: {}'.format(str(phantom_config)))

        return drivers.PhantomJSWebDriver(**phantom_config)

    @setup_config
    def opera(self):
        opera_config = self._config.get('OPERA_WEBDRIVER')

        if not opera_config:
            raise SeleniumExError('opera web driver settings not found')

        logger.debug('Opera config: {}'.format(str(opera_config)))

        return drivers.OperaWebDriver(**opera_config)

    def _get_local_driver(self):
        driver = getattr(self, self._driver_name, None)

        if driver:
            return driver()

        raise SeleniumExError(
            'Incorrect driver name "{}"'.format(self._driver_name),
        )

    def get_driver(self,
                   driver_name=None,
                   timeout=None,
                   sleep=None):
        if driver_name is not None:
            self._driver_name = driver_name

        def get_driver(func):
            try:
                return func()
            except (URLError, WebDriverException):
                return None

        if self._use_remote:
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
