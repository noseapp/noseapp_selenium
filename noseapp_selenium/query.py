# -*- coding: utf-8 -*-

import logging

from noseapp.utils.common import waiting_for
from noseapp.utils.common import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement

from noseapp_selenium.tools import get_driver_from_web_element


logger = logging.getLogger(__name__)


REPLACE_ATTRIBUTES = {
    '_id': 'id',
    '_class': 'class',
    '_type': 'type',
}

REPLACE_TAGS = {
    'link': 'a',
}

DEFAULT_SLEEP = 0.01
DEFAULT_WAIT_TIMEOUT = 30


class QueryError(BaseException):
    pass


def _error_handler(e, client, css):
    prefix = u' ' if e.message else u''

    if isinstance(client, WebElement):
        e.message += u'{}QueryProcessor(From: {}, CSS: {})\n\n--\nSEARCH AREA: {}\n--\n'.format(
            prefix,
            repr(client),
            css,
            client.get_attribute('innerHTML'),
        )
    else:
        e.message += u'{}QueryProcessor(From: {}, CSS: {})'.format(
            prefix,
            repr(client),
            css,
        )


def _execute(client, css, get_all):
    """
    Execute css query
    """
    logger.debug(u'CSS: {} Get all: {}'.format(css, 'Yes' if get_all else 'No'))

    css_executor = {
        True: client.find_elements_by_css_selector,
        False: client.find_element_by_css_selector,
    }

    try:
        return css_executor[get_all](css)
    except WebDriverException as e:
        _error_handler(e, client, css)
        raise
    except KeyError:
        raise QueryError('get_all param must be bool type only')


def _replace_attribute(atr_name):
    return REPLACE_ATTRIBUTES.get(atr_name, atr_name).replace('_', '-')


def _replace_tag(tag_name):
    return REPLACE_TAGS.get(tag_name, tag_name)


def _handler(client, tag):
    """
    :type client: selenium.webdriver.remote.webdriver.WebDriver
    :param tag: html tag name
    """
    def handle(**selector):
        query = [_replace_tag(tag)]

        def get_format(value):
            if isinstance(value, _Contains):
                return u'[{}*="{}"]'
            return u'[{}="{}"]'

        map(
            query.append,
            (
                get_format(val).format(_replace_attribute(atr), val)
                for atr, val in selector.items()
            ),
        )

        return QueryResult(client, ''.join(query))

    return handle


class QueryObject(object):

    def __init__(self, tag, **selector):
        self.tag = tag
        self.selector = selector

    def __unicode__(self):
        return u'<{} {}>'.format(
            self.tag,
            u' '.join(
                [u'{}="{}"'.format(k, v) for k, v in self.selector.items()]
            ),
        )


class _Contains(object):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value

    def __unicode__(self):
        return self.value


def contains(value):
    return _Contains(value)


class QueryResult(object):

    def __init__(self, client, css):
        self._client = client
        self._css = css

    def __getattr__(self, item):
        return getattr(QueryProcessor(self.first()), item)

    @property
    def exist(self):
        if isinstance(self._client, WebElement):
            driver = get_driver_from_web_element(self._client)
            driver.implicitly_wait(0)
        else:
            driver = self._client

        driver.implicitly_wait(0)

        try:
            el = self.first()
            if el:
                driver.config.apply_implicitly_wait()
                return True
            driver.config.apply_implicitly_wait()
            return False
        except WebDriverException:
            driver.config.apply_implicitly_wait()
            return False
        except BaseException:
            driver.config.apply_implicitly_wait()
            raise

    @property
    def with_wait(self):
        self.wait()
        return self

    def wait(self, timeout=None, sleep=None):
        try:
            return waiting_for(
                lambda: self.exist,
                sleep=sleep or DEFAULT_SLEEP,
                timeout=timeout or DEFAULT_WAIT_TIMEOUT,
            )
        except TimeoutException:
            raise TimeoutException(
                'Could not wait web element with css "{}"'.format(self._css),
            )

    def get(self, index):
        try:
            return _execute(self._client, self._css, True)[index]
        except IndexError as e:
            e.message = 'Result does not have element with index "{}". Query: "{}".'.format(
                index, self._css,
            )
            raise

    def first(self):
        return _execute(self._client, self._css, False)

    def all(self):
        return _execute(self._client, self._css, True)


class QueryProcessor(object):
    """
    Example:

        driver = WebDriver()
        query = QueryProcessor(driver)

        search_wrapper = query.div(id='search').first()
        search_field = query(search_wrapper).input(_class='search').first()
        search_field.send_keys(*'Hello World!')
    """

    def __init__(self, client):
        self._client = client

    def __getattr__(self, item):
        return _handler(self._client, item)

    def __call__(self, client):
        return self.__class__(client)

    def from_object(self, obj):
        """
        :type obj: QueryObject
        """
        if not isinstance(obj, QueryObject):
            raise TypeError('"{}" is not QueryObject instance'.format(type(obj)))

        return self.__getattr__(obj.tag)(**obj.selector)

    def get_text(self):
        if isinstance(self._client, WebElement):
            return self._client.text

        return self._client.find_element_by_tag_name('body').text
