# -*- coding: utf-8 -*-

from selenium.common.exceptions import NoSuchElementException

from noseapp_selenium.tools import make_object
from noseapp_selenium.query import QueryObject


def selector(**kwargs):
    """
    proxy for tag attributes
    """
    return kwargs


class FieldError(BaseException):
    pass


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
                 parent=None,
                 weight=None):

        self.name = name

        if not isinstance(selector, dict):
            raise ValueError('incorrect selector')

        self._memo = None
        self._query = None
        self._settings = None
        self._weight = weight
        self._parent = parent
        self._selector = selector

        self.value = value
        self.required = required
        self.error_mess = error_mess
        self.invalid_value = invalid_value

    def __call__(self, query, parent, memo, settings):
        self._init_query(query)

        if self._parent is None:
            self._init_parent(parent)

        self._init_memo(memo)
        self._init_settings(settings)

        return self

    def _init_query(self, query):
        if self._query is not None:
            raise FieldError('query did initialize')

        self._query = query

    def _init_parent(self, parent):
        if parent is None:
            return

        if not isinstance(parent, QueryObject):
            raise TypeError('Parent object is not instance query.QueryObject')

        self._parent = parent

    def _init_memo(self, memo):
        """
        :type memo: set
        """
        if self._memo is not None:
            raise FieldError('Memo did initialize')

        self._memo = memo

    def _init_settings(self, settings):
        """
        :type settings: dict
        """
        self._settings = settings

    @property
    def weight(self):
        return self._weight

    def remember_fill(self):
        if self._settings['remember'] and self._memo is not None:
            self._memo.add(self)

    def forget_fill(self):
        try:
            self._memo.remove(self)
        except (KeyError, AttributeError):
            pass

    def get_web_element(self):
        if self._parent is not None:
            parent = self._query.from_object(self._parent).first()
            return self._query(parent).from_object(
                QueryObject(self.Meta.tag, **self._selector),
            ).first()

        return self._query.from_object(
            QueryObject(self.Meta.tag, **self._selector),
        ).first()

    @property
    def obj(self):
        return make_object(self.get_web_element())


class SimpleFieldInterface(object):

    def fill(self, value=None):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


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

    def fill(self, value=None):
        if value is None:
            value = self.value

        if callable(value):
            value = value()

        self.get_web_element().send_keys(*value)
        self.remember_fill()

    def clear(self):
        self.get_web_element().clear()
        self.forget_fill()


class TextArea(Input):

    class Meta:
        tag = 'textarea'


class Checkbox(field_on_base(SimpleFieldInterface)):

    class Meta:
        tag = 'input'

    def fill(self, value=None):
        if value is None:
            value = self.value

        el = self.get_web_element()
        current_value = el.is_selected()

        if self._settings['allow_raises']:

            if current_value and value:
                raise FieldError('Oops, checkbox did selected')
            elif not current_value and not value:
                raise FieldError('Oops, checkbox did unselected')

        if (value and not current_value) or (not value and current_value):
            el.click()

        self.remember_fill()

    def clear(self):
        el = self.get_web_element()

        if el.is_selected():
            el.click()

        self.forget_fill()


class RadioButton(Checkbox):

    class Meta:
        tag = 'input'

    def fill(self, value=None):
        if value is None:
            value = self.value

        el = self.get_web_element()
        current_value = el.is_selected()
        changed = False

        if (value and not current_value) or (not value and current_value):
            el.click()
            changed = True

        self.remember_fill()

        return changed

    def clear(self):
        self.forget_fill()


class Select(field_on_base(SimpleFieldInterface)):

    class Meta:
        tag = 'select'

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

        self.remember_fill()

    def clear(self):
        self.forget_fill()
