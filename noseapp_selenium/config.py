# -*- coding: utf-8 -*-

from noseapp_selenium import drivers


BASE_CONFIG = {
    'REMOTE_WEBDRIVER': {
        'options': {},
        'capabilities': {
            drivers.IE: {},
            drivers.OPERA: {},
            drivers.CHROME: {},
            drivers.FIREFOX: {},
            drivers.PHANTOMJS: {},
        },
    },

    'IE_WEBDRIVER': {},

    'CHROME_WEBDRIVER': {},

    'FIREFOX_WEBDRIVER': {},

    'PHANTOMJS_WEBDRIVER': {},

    'OPERA_WEBDRIVER': {},

    'OPTIONS': {},
}


class Config(dict):

    def configure(self, **options):
        """
        Extension settings configure
        """
        self['OPTIONS'].update(options)

    def remote_configure(self, options=None, capabilities=None):
        """
        :param options: kwargs for method of WebDriver class
        :param capabilities: update base capabilities
        """
        self['REMOTE_WEBDRIVER']['options'].update(options or {})
        self['REMOTE_WEBDRIVER']['capabilities'].update(capabilities or {})

    def ie_configure(self, **options):
        """
        :param options: kwargs for method of WebDriver class
        """
        self['IE_WEBDRIVER'].update(options)

    def chrome_configure(self, **options):
        """
        :param options: kwargs for method of WebDriver class
        """
        self['CHROME_WEBDRIVER'].update(options)

    def firefox_configure(self, **options):
        """
        :param options: kwargs for method of WebDriver class
        """
        self['FIREFOX_WEBDRIVER'].update(options)

    def phantomjs_configure(self, **options):
        """
        :param options: kwargs for method of WebDriver class
        """
        self['PHANTOMJS_WEBDRIVER'].update(options)

    def opera_configure(self, **options):
        """
        :param options: kwargs for method of WebDriver class
        """
        self['OPERA_WEBDRIVER'].update(options)


def make_config():
    """
    Create base config
    """
    return Config(BASE_CONFIG)
