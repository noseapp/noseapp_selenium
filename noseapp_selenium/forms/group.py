# -*- coding: utf-8 -*-

from copy import deepcopy
from contextlib import contextmanager

from noseapp_selenium.proxy import to_proxy_object
from noseapp_selenium.forms.fields import FormField
from noseapp_selenium.tools import set_default_to_meta
from noseapp_selenium.forms.fields import field_on_base
from noseapp_selenium.tools import get_query_from_driver
from noseapp_selenium.forms.iterators import FieldsIterator
from noseapp_selenium.tools import get_meta_info_from_object
from noseapp_selenium.forms.fields import SimpleFieldInterface
from noseapp_selenium.forms.iterators import RequiredFieldsIterator
from noseapp_selenium.page_object.base import BaseInterfaceObjectOfPage
from noseapp_selenium.forms.iterators import FieldsWithContainsInvalidValueIterator


def make_field(group_class, weight=None, name=None):
    """
    Usage group like field

    :type group_class: UIForm
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
    Container for group class.
    Major task is lazy instantiation for group object.
    """

    def __init__(self, group_class, weight, name):
        self.__group_class = group_class
        self.__weight = weight
        self.__name = name

    @property
    def name(self):
        return self.__name

    def __call__(self, group):
        return self.__group_class(
            group.driver,
            parent=group,
            name=self.__name,
            weight=self.__weight,
        )


class GroupMemento(dict):
    """
    Save state for fields of group
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


class FieldsGroupMeta(type):
    """
    Install fields at group
    """

    def __call__(self, *args, **kwargs):
        instance = super(FieldsGroupMeta, self).__call__(*args, **kwargs)

        for atr in (a for a in dir(instance) if not a.startswith('_') and a != 'query'):
            maybe_field = getattr(instance, atr, None)

            if isinstance(maybe_field, (FormField, GroupContainer)):
                if maybe_field.name in instance.meta['exclude']:
                    try:
                        delattr(instance, atr)
                    except AttributeError:
                        pass
                    continue

                instance.add_field(atr, deepcopy(maybe_field))

        return instance


class FieldsGroup(field_on_base(SimpleFieldInterface, BaseInterfaceObjectOfPage)):
    """
    Merging fields to group and simple field
    interface providing for each field through this object.
    """

    __metaclass__ = FieldsGroupMeta

    def __init__(self, driver, weight=None, name=None, parent=None):
        if not hasattr(self, 'name'):
            self.name = name

        self.meta = get_meta_info_from_object(self)

        set_default_to_meta(self.meta, 'wrapper', None)
        set_default_to_meta(self.meta, 'exclude', tuple())
        set_default_to_meta(self.meta, 'remember', True)
        set_default_to_meta(self.meta, 'allow_raises', True)

        self._fields = []
        self._memento = GroupMemento()

        self.__parent = parent
        self.__weight = weight
        self.__fill_memo = set()
        self.__driver = to_proxy_object(driver)

    @property
    def driver(self):
        """
        WebDriver or WebElement instance of current object
        """
        return self.__driver

    @property
    def query(self):
        """
        QueryProcessor instance.
        Wrapper will be counted.
        """
        return get_query_from_driver(
            self.__driver,
            wrapper=self.meta['wrapper'],
        )

    @property
    def wrapper(self):
        """
        QueryObject of wrapper element.
        If did not set then None.
        """
        return self.meta['wrapper']

    @property
    def weight(self):
        """
        Weight for sorting
        """
        return self.__weight

    @property
    def fill_memo(self):
        """
        For storage fields that been filled
        """
        return self.__fill_memo

    def use_with(self, obj_or_driver):
        """
        Reset driver from object with implemented
        BaseInterfaceObjectOfPage.
        Can be similarly WebDriver or WebElement instance.
        """
        if isinstance(obj_or_driver, BaseInterfaceObjectOfPage):
            self.__driver = obj_or_driver.driver
        else:
            self.__driver = obj_or_driver

    def add_field(self, name, field):
        """
        Append field to group
        """
        if isinstance(field, GroupContainer):
            field = field(self)
            setattr(self, name, field)
        elif isinstance(field, FormField):
            setattr(self, name, field)
            field.bind(self)
            self._memento.add_field(field)
        else:
            raise TypeError('Unknown field type')

        self._fields.append(field)
        self._fields.sort(key=lambda f: f.weight)

    def add_subgroup(self, name, cls, weight=None):
        """
        Append class of FieldsGroup like field
        """
        assert issubclass(cls, FieldsGroup),\
            '"{}" is not FieldsGroup subclass'.format(cls.__name__)

        self.add_field(
            name,
            make_field(
                cls, weight=weight, name=name,
            ),
        )

    def add_subform(self, *args, **kwargs):
        """
        Proxy for add_subgroup
        """
        self.add_subgroup(*args, **kwargs)

    def submit(self):
        """
        Your submit script here
        """
        pass

    def reload(self):
        """
        Restore values of fields after changes
        """
        self._memento.restore(self._fields)

    def reset_memo(self):
        """
        To reset fill memo
        """
        self.__fill_memo.clear()

        groups = (
            field for field in self.__fill_memo
            if isinstance(field, FieldsGroup)
        )

        for group in groups:
            group.reset_memo()

    def update(self, **kwargs):
        """
        Update fields values
        """
        for field_name, value in kwargs.items():
            field = getattr(self, field_name, None)

            if isinstance(field, FieldsGroup):
                field.update(**value)
            elif isinstance(field, FormField):
                field.value = value
            else:
                raise LookupError(
                    'Field "{}" not found'.format(field_name),
                )

    def fill(self, exclude=None):
        """
        Fill all fields in group
        """
        exclude = exclude or tuple()

        for field in self._fields:
            if (field not in self.__fill_memo) and (field not in exclude):
                field.fill()

        if self.__parent:
            self.__parent.fill_memo.add(self)

        self.reset_memo()

    def clear(self):
        """
        Fields to clear
        """
        for field in self._fields:
            field.clear()

        self.reset_memo()

    def get_wrapper_element(self):
        """
        Get web element from meta wrapper
        """
        wrapper = self.meta['wrapper']

        if wrapper:
            return self.__driver.query.from_object(wrapper).first()

        return None


assert issubclass(FieldsGroup, (SimpleFieldInterface, BaseInterfaceObjectOfPage))
