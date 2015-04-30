# -*- coding: utf-8 -*-

from copy import deepcopy
from contextlib import contextmanager

from noseapp_selenium import QueryProcessor
from noseapp_selenium.forms.fields import FormField
from noseapp_selenium.forms.iterators import FieldsIterator
from noseapp_selenium.forms.fields import SimpleFieldInterface
from noseapp_selenium.forms.iterators import RequiredFieldsIterator
from noseapp_selenium.forms.iterators import FieldsWithContainsInvalidValueIterator


def make_field(group_class, weight=None, name=None):
    """
    Usage group like field

    :type form_class: UIForm
    """
    if not issubclass(group_class, FieldsGroup):
        raise ValueError('group_class is not FieldsGroup subclass')

    return GroupContainer(group_class, weight, name)


@contextmanager
def preserve_original(group, ignore_exc=None):
    """
    Save original group after changes inside contextmanager

    :type group: form.UIForm
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
        group.reload()


def iter_fields(group, exclude=None):
    """
    Example:

        form = MyForm(driver)
        for field in iter_fields(form):
            field.fill()
            ...

    :type exclude: list or tuple
    :return: noseapp_selenium.forms.iterators.FieldsIterator
    """
    assert isinstance(group, FieldsGroup)
    return FieldsIterator(group, exclude=exclude)


def iter_required(group, exclude=None):
    """
    Example:

        form = MyForm(driver)
        for field in iter_required(form):
            form.fill(exclude=(field,))
            form.submit()
            ...

    :type exclude: list or tuple
    :return: noseapp_selenium.forms.iterators.RequiredFieldsIterator
    """
    assert isinstance(group, FieldsGroup)
    return RequiredFieldsIterator(group, exclude=exclude)


def iter_invalid(form, exclude=None):
    """
    Example:

        form = MyForm(driver)
        for field in iter_invalid(form):
            form.fill(exclude=(field,))
            field.fill(field.invalid_value)
            form.submit()
            ...

    :type exclude: list or tuple
    :return: noseapp_selenium.forms.iterators.FieldsWithContainsInvalidValueIterator
    """
    assert isinstance(form, FieldsGroup)
    return FieldsWithContainsInvalidValueIterator(form, exclude=exclude)


class GroupContainer(object):
    """
    Container for group class. Major task is lazy instantiation object.
    """

    def __init__(self, form_class, weight, name):
        self.__form_class = form_class
        self.__weight = weight
        self.__name = name

    @property
    def name(self):
        return self.__name

    def __call__(self, driver, parent):
        return self.__form_class(
            driver,
            parent=parent,
            name=self.__name,
            weight=self.__weight,
        )


class GroupMemento(dict):
    """
    Saved state for the fields group
    """

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
        assert isinstance(field, FormField)
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


class GroupObserver(object):
    """
    Publish method call for field or field group through handler at this class
    """

    def __init__(self, group):
        assert isinstance(group, FieldsGroup)

        self._group = group

        # listeners
        self._parents = []
        self._children = []

    def add_child(self, form):
        assert isinstance(form, FieldsGroup)
        self._children.append(form)

    def add_parent(self, form):
        assert isinstance(form, FieldsGroup)
        self._parents.append(form)

    def reload_handler(self):
        for child in self._children:
            child.reload()

    def reset_memo_handler(self):
        for child in self._children:
            child.reset_memo()

    def fill_handler(self):
        if self._group._settings.get('remember', True):
            for parent in self._parents:
                parent._fill_memo.add(self._group)

    def clear_handler(self):
        for parent in self._parents:
            try:
                parent._fill_memo.remove(self._group)
            except KeyError:
                pass

    def fill_field_handler(self, field):
        assert isinstance(field, FormField)

        if self._group._settings.get('remember', True):
            self._group._fill_memo.add(field)

    def clear_field_handler(self, field):
        assert isinstance(field, FormField)

        try:
            self._group._fill_memo.remove(field)
        except KeyError:
            pass


class FieldsGroup(SimpleFieldInterface):
    """
    Merging fields to group and simple field
    interface providing for each field through this object.
    """

    def __init__(self, driver, weight=None, name=None, parent=None):
        self._fields = []
        self._driver = driver
        self._weight = weight
        self._fill_memo = set()
        self._memento = GroupMemento()
        self._observer = GroupObserver(self)

        self.__query = QueryProcessor(driver)

        if parent is not None:
            self._observer.add_parent(parent)

        if not hasattr(self, 'name'):
            self.name = name

        meta = getattr(self, 'Meta', object())

        self._settings = {
            'remember': getattr(meta, 'remember', True),
            'allow_raises': getattr(meta, 'allow_raises', True),
            'wrapper': getattr(meta, 'wrapper', None),
            'exclude': getattr(meta, 'exclude', tuple()),
        }

        exclude_atr = (
            'query',
        )

        for atr in (a for a in dir(self) if not a.startswith('_') and a not in exclude_atr):
            maybe_field = getattr(self, atr, None)

            if isinstance(maybe_field, FormField) or isinstance(maybe_field, GroupContainer):
                if maybe_field.name in self._settings['exclude']:
                    try:
                        delattr(self, atr)
                    except AttributeError:
                        pass
                    continue

                self.add_field(atr, deepcopy(maybe_field))

    def add_field(self, name, field):
        if isinstance(field, FormField):
            setattr(self, name, field)
            field.bind(self)
            self._memento.add_field(field)
        elif isinstance(field, GroupContainer):
            field = field(self._driver, self)
            setattr(self, name, field)
            self._observer.add_child(field)
        else:
            raise TypeError('Unknown field type')

        self._fields.append(field)
        self._fields.sort(key=lambda f: f.weight)

    @property
    def weight(self):
        return self._weight

    @property
    def query(self):
        wrapper = self.get_wrapper_element()

        if wrapper:
            return self.__query(wrapper)
        return self.__query

    def submit(self):
        """
        Your submit script here
        """
        pass

    def reload(self):
        self._memento.restore(self._fields)
        self._observer.reload_handler()

    def reset_memo(self):
        self._fill_memo.clear()
        self._observer.reset_memo_handler()

    def update(self, **kwargs):
        """
        Update fields values
        """
        for field_name, value in kwargs.items():
            field = getattr(self, field_name, None)

            if isinstance(field, FormField):
                field.value = value
            elif isinstance(field, FieldsGroup) and isinstance(value, dict):
                field.update(**value)

    def fill(self, exclude=None):
        exclude = exclude or tuple()

        for field in self._fields:
            if (field not in self._fill_memo) and (field not in exclude):
                field.fill()

        self.reset_memo()
        self._observer.fill_handler()

    def clear(self):
        for field in self._fields:
            field.clear()

        self.reset_memo()
        self._observer.clear_handler()

    def get_wrapper_element(self):
        """
        Get web element from meta wrapper
        """
        wrapper = self._settings['wrapper']
        if wrapper:
            return self.__query.from_object(wrapper).first()
        return None
