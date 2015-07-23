# -*- coding: utf-8 -*-

import logging

from noseapp.utils.common import waiting_for
from noseapp.utils.common import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException


logger = logging.getLogger(__name__)


DEFAULT_SLEEP = 0.01
DEFAULT_WAIT_TIMEOUT = 30


def _error_handler(e, client, css):
    """
    To extend error message
    """
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


def _execute(client, css, get_all=False, allow_polling=True):
    """
    Execute css query
    """
    logger.debug(u'CSS: {} Get all: {}'.format(css, 'Yes' if get_all else 'No'))

    css_executors = {
        True: 'find_elements_by_css_selector',
        False: 'find_element_by_css_selector',
    }

    try:
        if allow_polling:
            result = getattr(client, css_executors[bool(get_all)])(css)
        elif hasattr(client, 'disable_polling'):
            with client.disable_polling():
                result = getattr(client, css_executors[bool(get_all)])(css)
        else:
            result = getattr(client, css_executors[bool(get_all)])(css)

        return result

    except WebDriverException as e:
        _error_handler(e, client, css)
        raise


class QueryResult(object):
    """
    Execute actions by css query and returning result
    """

    def __init__(self, client, css):
        self._client = client
        self._css = css

    def __getattr__(self, item):
        return getattr(
            self._client.query.__class__(self.first()), item,
        )

    @property
    def exist(self):
        """
        Check element exist
        """
        self._client.config.implicitly_wait(0)

        try:
            el = _execute(self._client, self._css, allow_polling=False)

            if el:
                self._client.config.apply_implicitly_wait()
                return True
            self._client.config.apply_implicitly_wait()
            return False
        except WebDriverException:
            self._client.config.apply_implicitly_wait()
            return False
        except BaseException:
            self._client.config.apply_implicitly_wait()
            raise

    @property
    def with_wait(self):
        self.wait()
        return self

    def wait(self, timeout=None, sleep=None):
        """
        Waiting for web element exist
        """
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
        """
        Get web element by index
        """
        try:
            return _execute(self._client, self._css, get_all=True)[index]
        except IndexError:
            raise NoSuchElementException(
                'Result does not have element with index "{}". Css: "{}".'.format(
                    index, self._css,
                ),
            )

    def first(self):
        """
        Get first element on page
        """
        return _execute(self._client, self._css)

    def all(self):
        """
        Get all elements of appropriate query
        """
        return _execute(self._client, self._css, get_all=True)
