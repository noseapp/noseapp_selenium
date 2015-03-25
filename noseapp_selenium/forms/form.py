# -*- coding: utf-8 -*-

from copy import deepcopy
from contextlib import contextmanager

from noseapp_selenium import QueryProcessor
from noseapp_selenium.forms.fields import FormField
from noseapp_selenium.forms.iterators import FieldsIterator
from noseapp_selenium.forms.fields import SimpleFieldInterface
from noseapp_selenium.forms.iterators import FieldItemsIterator
from noseapp_selenium.forms.iterators import RequireFieldsIterator
from noseapp_selenium.forms.iterators import InvalidValueFieldsIterator


def make_field(form_class, weight=None, name=None):
    """
    Usage form as field

    :type form_class: UIForm
    """
    if not issubclass(form_class, UIForm):
        raise ValueError('form class is not UIForm subclass')

    return FormContainer(form_class, weight, name)


@contextmanager
def preserve_original(form, ignore_exc=None):
    """
    :type form: form.UIForm
    :type ignore_exc: BaseException class or tuple
    """
    try:
        if ignore_exc:
            try:
                yield
            except ignore_exc:
                pass
        else:
            yield
    finally:
        form.reload()


class FormContainer(object):

    def __init__(self, _form_cls, weight, name):
        self.__form_cls = _form_cls
        self.__weight = weight
        self.__name = name

    def __call__(self, driver, parent):
        return self.__form_cls(
            driver,
            parent=parent,
            name=self.__name,
            weight=self.__weight,
        )


class FormMemento(dict):

    def _set_field(self, filed):
        """
        :type filed: fields.BaseField
        """
        self[filed] = {
            'value': filed.value,
            'required': filed.required,
            'error_mess': filed.error_mess,
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
                field.error_mess = orig['error_mess']
                field.invalid_value = orig['invalid_value']
            else:
                continue


class UIForm(SimpleFieldInterface):

    def __init__(self, driver, weight=None, name=None, parent=None):
        self._fields = []
        self._sub_forms = []
        self._driver = driver
        self._weight = weight
        self._parent = parent
        self._fill_memo = set()
        self._memento = FormMemento()
        self._query = QueryProcessor(driver)

        if not hasattr(self, 'name'):
            self.name = name

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
                exactly_field = maybe_field(driver, self)

                if exactly_field.name in exclude:
                    delattr(self, atr)
                    continue

                setattr(self, atr, exactly_field)

                self._fields.append(exactly_field)
                self._sub_forms.append(exactly_field)

        self._fields.sort(key=lambda f: f.weight)

    @classmethod
    def copy(cls, driver=None):
        if driver:
            return deepcopy(cls)(driver)

        return deepcopy(cls)

    @property
    def weight(self):
        return self._weight

    @property
    def is_submit(self):
        return False

    @property
    def field_names(self):
        return [field.name for field in self._fields]

    def submit(self):
        """
        Your submit script is there
        """
        pass

    def reload(self):
        self._memento.restore(self._fields)

        if self._sub_forms:
            for sub_form in self._sub_forms:
                sub_form.reload()

    def reset_memo(self):
        self._fill_memo.clear()

        if self._sub_forms:
            for sub_form in self._sub_forms:
                sub_form.reset_memo()

    def fill(self, exclude=None):
        exclude = exclude or tuple()

        if self._parent is not None:
            self._parent._fill_memo.add(self)

        for field in self._fields:
            if (field not in self._fill_memo) and (field not in exclude):
                field.fill()

        self.reset_memo()

    def clear(self):
        for field in self._fields:
            field.clear()

        self.reset_memo()

    def assert_submit(self):
        assert self.is_submit, 'Form "{}" is not saved'.format(self.__class__.__name__)

    def assert_not_submit(self):
        assert not self.is_submit, 'Form "{}" is saved'.format(self.__class__.__name__)

    def each_required(self, items=False):
        """
        Example:

            form = MyForm(driver)
            for fields in form.each_required():
                fields.fill()
                #
                # for field in fields:
                #     ...
                form.submit()
                ...

        :return: iterators.RequiredIterator
        """
        return RequireFieldsIterator(self, items=items)

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

    def each_items(self, field, items):
        """
        Example:

            form = MyForm(driver)
            for field, value in form.each_items(form.title, ('Hello', 'World', '!')):
                form.fill(exclude=[field])
                field.fill(value)
                form.submit()
                ...

        :type field: fields.FormField
        :type values: list or tuple
        :return: iterators.FieldItemsIterator
        """
        return FieldItemsIterator(self, field, items)

    def each_invalid(self, exclude=None):
        """
        Example:

            form = MyForm(driver)
            for field in form.each_invalid():
                form.fill(exclude=[field])
                field.fill(field.invalid_value)
                form.submit()
                ...

        :type exclude: list or tuple
        """
        return InvalidValueFieldsIterator(self, exclude=exclude)

    def get_wrapper_element(self):
        """
        Get web element from meta wrapper
        """
        return self._query.from_object(self.Meta.wrapper).first()
