# -*- coding: utf-8 -*-

import logging
from functools import wraps
from urllib2 import URLError

from noseapp.utils.common import waiting_for
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from noseapp_selenium import drivers


logger = logging.getLogger(__name__)


_DRIVER_TO_CAPABILITIES = {
    drivers.OPERA: DesiredCapabilities.OPERA,
    drivers.CHROME: DesiredCapabilities.CHROME,
    drivers.FIREFOX: DesiredCapabilities.FIREFOX,
    drivers.PHANTOMJS: DesiredCapabilities.PHANTOMJS,
    drivers.IE: DesiredCapabilities.INTERNETEXPLORER,
}

DEFAULT_IMPLICITLY_WAIT = 30
DEFAULT_MAXIMIZE_WINDOW = True
DEFAULT_DRIVER = drivers.CHROME

GET_DRIVER_TIMEOUT = 10
GET_DRIVER_SLEEP = 0.5


class SeleniumExError(BaseException):
    pass


def get_capabilities(driver_name):
    try:
        return _DRIVER_TO_CAPABILITIES[driver_name]
    except KeyError:
        raise SeleniumExError(
            'capabilities for driver "{}" is not found'.find(driver_name),
        )


def apply_settings(f):

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        driver = f(self, *args, **kwargs)

        if self._implicitly_wait is not None:
            driver.IMPLICITLY_WAIT = self._implicitly_wait
            driver.implicitly_wait(self._implicitly_wait)
        else:
            driver.IMPLICITLY_WAIT = 0

        if self._maximize_window:
            driver.maximize_window()

        return driver

    return wrapper


class SeleniumEx(object):
    """
    Initialize selenium extension for noseapp
    """

    name = 'selenium'

    def __init__(
            self,
            config,
            use_remote=False,
            driver_name=DEFAULT_DRIVER,
            maximize_window=DEFAULT_MAXIMIZE_WINDOW,
            implicitly_wait=DEFAULT_IMPLICITLY_WAIT):
        self._config = config
        self._use_remote = use_remote
        self._driver_name = driver_name.lower()
        self._maximize_window = maximize_window
        self._implicitly_wait = implicitly_wait

        logger.debug(
            'Selenium-EX initialize. Config: {}, Use Remote: {}, Driver name: {}'.format(
                config,
                'Yes' if use_remote else 'No',
                driver_name,
            ),
        )

    @property
    def config(self):
        return self._config

    @property
    @apply_settings
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

    @property
    @apply_settings
    def ie(self):
        ie_config = self._config.get('IE_WEBDRIVER')

        if not ie_config:
            raise SeleniumExError('ie web driver settings not found')

        logger.debug('Ie config: {}'.format(str(ie_config)))

        return drivers.IeWebDriver(**ie_config)

    @property
    @apply_settings
    def chrome(self):
        chrome_config = self._config.get('CHROME_WEBDRIVER')

        if not chrome_config:
            raise SeleniumExError('google chrome web driver settings not found')

        logger.debug('Chrome config: {}'.format(str(chrome_config)))

        return drivers.ChromeWebDriver(**chrome_config)

    @property
    @apply_settings
    def firefox(self):
        firefox_config = self._config.get('FIREFOX_WEBDRIVER', {})

        logger.debug('Firefox config: {}'.format(str(firefox_config)))

        return drivers.FirefoxWebDriver(**firefox_config)

    @property
    @apply_settings
    def phantom(self):
        phantom_config = self._config.get('PHANTOMJS_WEBDRIVER')

        if not phantom_config:
            raise SeleniumExError('phantom js web driver settings not found')

        logger.debug('PhantomJS config: {}'.format(str(phantom_config)))

        return drivers.PhantomJSWebDriver(**phantom_config)

    @property
    @apply_settings
    def opera(self):
        opera_config = self._config.get('OPERA_WEBDRIVER')

        if not opera_config:
            raise SeleniumExError('opera web driver settings not found')

        logger.debug('Opera config: {}'.format(str(opera_config)))

        return drivers.OperaWebDriver(**opera_config)

    def _get_local_driver(self):
        driver = getattr(self, self._driver_name, None)

        if driver:
            return driver

        raise SeleniumExError(
            'incorrect driver name "{}"'.format(self._driver_name),
        )

    def _get_remote_driver(self):
        return self.remote

    def get_driver(self, timeout=GET_DRIVER_TIMEOUT, sleep=GET_DRIVER_SLEEP):
        def get_driver(func):
            try:
                return func()
            except URLError:
                return None

        if self._use_remote:
            driver = waiting_for(
                lambda: get_driver(self._get_remote_driver),
                timeout=timeout,
                sleep=sleep,
            )
        else:
            driver = waiting_for(
                lambda: get_driver(self._get_local_driver),
                timeout=timeout,
                sleep=sleep,
            )

        return driver
