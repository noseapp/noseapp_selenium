# -*- coding: utf-8 -*-

from copy import deepcopy

from noseapp_selenium import QueryProcessor
from noseapp_selenium.forms.fields import FormField
from noseapp_selenium.forms.iterators import FieldsIterator
from noseapp_selenium.tools import Container as FormContainer
from noseapp_selenium.forms.iterators import RequiredIterator
from noseapp_selenium.forms.fields import SimpleFieldInterface
from noseapp_selenium.forms.iterators import ReplaceValueIterator
from noseapp_selenium.forms.iterators import ValueToInvalidValueIterator


def make_field(form_class):
    """
    Usage form as field

    :type form_class: UIForm
    """
    if not issubclass(form_class, UIForm):
        raise ValueError('form class is not UIForm subclass')

    return FormContainer(form_class)


class FormMemento(dict):

    def _set_field(self, filed):
        """
        :type filed: fields.BaseField
        """
        self[filed] = {
            'value': filed.value,
            'required': filed.required,
            'invalid_value': filed.invalid_value,
        }

    def get_field(self, filed):
        return self.get(filed)

    def add_field(self, field):
        self._set_field(field)

    def restore(self, field_list):
        for field in field_list:
            orig = self.get_field(field)

            if orig:
                field.value = orig['value']
                field.required = orig['required']
                field.invalid_value = orig['invalid_value']
            else:
                continue


class UIForm(SimpleFieldInterface):

    def __init__(self, driver):
        self._fields = []
        self._driver = driver
        self._fill_memo = set()
        self._memento = FormMemento()
        self._query = QueryProcessor(driver)

        meta = getattr(self, 'Meta', object())

        fields_settings = {
            'remember': getattr(meta, 'remember', True),
            'allow_raises': getattr(meta, 'allow_raises', True),
        }

        wrapper = getattr(meta, 'wrapper', None)
        exclude = getattr(meta, 'exclude', tuple())

        for atr in (a for a in dir(self) if not a.startswith('_')):
            maybe_field = getattr(self, atr, None)

            if isinstance(maybe_field, FormField):

                if maybe_field.name in exclude:
                    delattr(self, atr)
                    continue

                exactly_field = deepcopy(maybe_field)
                setattr(self, atr, exactly_field)
                exactly_field(
                    self._query,
                    wrapper,
                    self._fill_memo,
                    fields_settings,
                )
                self._fields.append(exactly_field)
                self._memento.add_field(exactly_field)
            elif isinstance(maybe_field, FormContainer):
                setattr(self, atr, maybe_field(driver))

        self._fields.sort(key=lambda f: f.weight)

    @classmethod
    def copy(cls, driver=None):
        if driver:
            return deepcopy(cls)(driver)

        return deepcopy(cls)

    @property
    def is_submit(self):
        return False

    @property
    def field_names(self):
        return [field.name for field in self._fields]

    def submit(self):
        pass

    def reload(self):
        self._memento.restore(self._fields)

    def reset_memo(self):
        self._fill_memo.clear()

    def fill(self, exclude=None):
        exclude = exclude or tuple()

        for field in self._fields:
            if (field.name not in self._fill_memo) and (field not in exclude):
                field.fill()

        self.reset_memo()

    def clear(self):
        for field in self._fields:
            field.clear()

    def assert_submit(self):
        assert self.is_submit, 'Form "{}" is not saved'.format(self.__class__.__name__)

    def assert_not_submit(self):
        assert not self.is_submit, 'Form "{}" is saved'.format(self.__class__.__name__)

    def each_required(self):
        """
        Example:

            form = MyForm(driver)
            for fields in form.each_required():
                fields.fill()
                form.submit()
                ...

        :return: iterators.RequiredIterator
        """
        return RequiredIterator(self)

    def each_fields(self, exclude=None):
        """
        Example:

            form = MyForm(driver)
            for field in form.each_fields():
                field.fill()
                ...

        :type exclude: list or tuple
        :return: iterators.FieldsIterator
        """
        return FieldsIterator(self, exclude=exclude)

    def each_replace(self, field, values):
        """
        Example:

            form = MyForm(driver)
            for altered_form in form.each_replace(form.title, ('Hello', 'World', '!')):
                with altered_form():
                    form.fill()
                    form.submit()
                    ...

        :type field: fields.FormField
        :type values: list or tuple
        :return: iterators.ReplaceValueIterator
        """
        return ReplaceValueIterator(self, field, values)

    def each_invalid(self, exclude=None):
        """
        Example:

            form = MyForm(driver)
            for altered_form in form.each_invalid():
                with altered_form():
                    form.fill()
                    form.submit()
                    ...

        :type exclude: list or tuple
        """
        return ValueToInvalidValueIterator(self, exclude=exclude)
