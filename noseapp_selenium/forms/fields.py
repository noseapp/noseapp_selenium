# -*- coding: utf-8 -*-

from functools import wraps

from selenium.common.exceptions import NoSuchElementException

from noseapp_selenium.tools import make_object
from noseapp_selenium.query import QueryObject
from noseapp_selenium.query import QueryProcessor


def selector(**kwargs):
    """
    proxy for tag attributes
    """
    return kwargs


def fill_field_handler(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        result = f(self, *args, **kwargs)

        if self._settings.get('remenber', True):
            self._observer.fill_field_handler(self)

        return result
    return wrapper


def clear_field_handler(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        result = f(self, *args, **kwargs)

        self._observer.clear_field_handler(self)

        return result
    return wrapper


class FieldError(BaseException):
    pass


class SimpleFieldInterface(object):

    @property
    def weight(self):
        raise NotImplementedError

    def fill(self, value=None):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class FormField(object):
    """
    Base class for all fields
    """

    class Meta:
        tag = None

    def __init__(self,
                 name,
                 value=None,
                 required=False,
                 selector=None,
                 error_mess=None,
                 invalid_value=None,
                 weight=None):

        self.name = name

        if not isinstance(selector, dict):
            raise ValueError('incorrect selector')

        self.__is_bind = False

        self._query = None
        self._settings = {}
        self._observer = None
        self._weight = weight
        self._selector = selector

        self.value = value
        self.required = required
        self.error_mess = error_mess
        self.invalid_value = invalid_value

    def bind(self, group):
        try:
            self._query = group._driver.query
        except AttributeError:
            self._query = QueryProcessor(group._driver)

        self._observer = group._observer
        self._settings = group._settings

        if callable(self.value):
            self.value = self.value()

        if callable(self.invalid_value):
            self.invalid_value = self.invalid_value()

        self.__is_bind = True

    @property
    def weight(self):
        return self._weight

    def get_web_element(self):
        if not self.__is_bind:
            raise FieldError('Field is not binding to group')

        wrapper = self._settings.get('wrapper', None)

        if isinstance(wrapper, QueryObject):
            query = self._query(
                self._query.from_object(wrapper).first(),
            )
        else:
            query = self._query

        return query.from_object(
            QueryObject(self.Meta.tag, **self._selector),
        ).first()

    @property
    def obj(self):
        return make_object(self.get_web_element())


def field_on_base(*interfaces):
    """
    Create parent class on base interfaces
    """
    if not hasattr(field_on_base, '__classes__'):
        field_on_base.__classes__ = {}

    bases = tuple([FormField] + sorted(list(interfaces)))

    try:
        return field_on_base.__classes__[bases]
    except KeyError:
        field_on_base.__classes__[bases] = type('BaseField', bases, {})
        return field_on_base.__classes__[bases]


class Input(field_on_base(SimpleFieldInterface)):

    class Meta:
        tag = 'input'

    @fill_field_handler
    def fill(self, value=None):
        if value is None:
            value = self.value

        self.get_web_element().send_keys(*value)

    @clear_field_handler
    def clear(self):
        self.get_web_element().clear()


class TextArea(Input):

    class Meta:
        tag = 'textarea'


class Checkbox(field_on_base(SimpleFieldInterface)):

    class Meta:
        tag = 'input'

    @fill_field_handler
    def fill(self, value=None):
        if value is None:
            value = self.value

        el = self.get_web_element()
        current_value = el.is_selected()

        if self._settings.get('allow_raises', True):

            if current_value and value:
                raise FieldError('Oops, checkbox did selected')
            elif not current_value and not value:
                raise FieldError('Oops, checkbox did unselected')

        if (value and not current_value) or (not value and current_value):
            el.click()

    @clear_field_handler
    def clear(self):
        el = self.get_web_element()

        if el.is_selected():
            el.click()


class RadioButton(Checkbox):

    class Meta:
        tag = 'input'

    @fill_field_handler
    def fill(self, value=None):
        if value is None:
            value = self.value

        el = self.get_web_element()
        current_value = el.is_selected()
        changed = False

        if (value and not current_value) or (not value and current_value):
            el.click()
            changed = True

        return changed

    @clear_field_handler
    def clear(self):
        pass


class Select(field_on_base(SimpleFieldInterface)):

    class Meta:
        tag = 'select'

    @fill_field_handler
    def fill(self, value=None):
        if value is None:
            value = self.value

        select = self.get_web_element()

        options = filter(
            lambda opt: opt.get_attribute('value') == value,
            select.find_elements_by_tag_name('option'),
        )

        if options:
            options[0].click()
        else:
            raise NoSuchElementException(
                u'Cant do selected value for field "{}", selector "{}", option "{}"'.format(
                    self.name, str(self._selector), value
                ),
            )

    @clear_field_handler
    def clear(self):
        pass
