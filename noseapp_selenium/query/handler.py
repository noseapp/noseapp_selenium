# -*- coding: utf-8 -*-

import logging

from noseapp_selenium.query.base import contains
from noseapp_selenium.query.result import QueryResult


logger = logging.getLogger(__name__)


REPLACE_ATTRIBUTES = {
    '_id': 'id',
    '_class': 'class',
    '_type': 'type',
}

REPLACE_TAGS = {
    'link': 'a',
}


def _replace_attribute(atr_name):
    """
    Replacing attribute name for
    excluding conflict with names of globals
    """
    return REPLACE_ATTRIBUTES.get(atr_name, atr_name).replace('_', '-')


def _replace_tag(tag_name):
    """
    Replacing tag name for usability
    """
    return REPLACE_TAGS.get(tag_name, tag_name)


def make_result(client, tag):
    """
    :type client: selenium.webdriver.remote.webdriver.WebDriver
    :param tag: html tag name
    """
    def handle(**selector):
        query = [_replace_tag(tag)]

        def get_format(value):
            if isinstance(value, contains):
                return u'[{}*="{}"]'
            return u'[{}="{}"]'

        query.extend(
            (
                get_format(val).format(_replace_attribute(atr), val)
                for atr, val in selector.items()
            ),
        )

        return QueryResult(client, ''.join(query))

    return handle
