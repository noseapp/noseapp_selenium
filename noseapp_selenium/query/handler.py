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


def replace_tag(tag_name):
    """
    Replace name of tag, for usability only
    """
    return REPLACE_TAGS.get(tag_name, tag_name)


def replace_attribute(atr_name):
    """
    Replace name of attribute for
    exclusion conflict with global names
    """
    return REPLACE_ATTRIBUTES.get(atr_name, atr_name).replace('_', '-')


def make_result(client, tag):
    """
    Factory for creation QueryResult object

    :type client: selenium.webdriver.remote.webdriver.WebDriver
    :param tag: html tag name
    """
    def handle(**selector):
        query = [replace_tag(tag)]

        def get_format(value):
            if isinstance(value, contains):
                return u'[{}*="{}"]'
            return u'[{}="{}"]'

        query.extend(
            (
                get_format(val).format(replace_attribute(atr), val)
                for atr, val in selector.items()
            ),
        )

        return QueryResult(client, ''.join(query))

    return handle
