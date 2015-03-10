# -*- coding: utf-8 -*-

from collections import Iterator
from contextlib import contextmanager


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


def altered_form(form):
    """
    :type form: form.UIForm
    """
    def wrapper(ignore_exc=None):
        return preserve_original(form, ignore_exc=ignore_exc)
    return wrapper


class FieldsIterator(Iterator):

    def __init__(self, form, exclude=None):
        exclude = exclude or tuple()

        self.__current_index = 0
        self.__fields = [field for field in form._fields if field not in exclude]

    def fill(self):
        for field in self.__fields:
            field.fill()

    def clear(self):
        for field in self.__fields:
            field.clear()

    def next(self):
        try:
            field = self.__fields[self.__current_index]
        except IndexError:
            raise StopIteration

        self.__current_index += 1

        return field


class ValueToInvalidValueIterator(Iterator):

    def __init__(self, form, exclude=None):
        exclude = exclude or tuple()

        self.__form = form
        self.__current_index = 0
        self.__fields = [field for field in form._fields if field not in exclude]

    def _make_next(self):
        try:
            field = self.__fields[self.__current_index]
        except IndexError:
            raise StopIteration

        self.__current_index += 1

        invalid_value = field.invalid_value

        if invalid_value is not None:
            field.value = invalid_value
        else:
            self._make_next()

    def next(self):
        self._make_next()
        return altered_form(self.__form)


class RequiredIterator(Iterator):

    def __init__(self, form):
        self.__form = form
        self.__current_index = 0
        self.__required_fields = [field for field in form._fields if field.required]

    def next(self):
        try:
            it = FieldsIterator(
                self.__form,
                exclude=(self.__required_fields[self.__current_index],),
            )
        except IndexError:
            raise StopIteration

        self.__current_index += 1

        return it


class ReplaceValueIterator(Iterator):

    def __init__(self, form, field, values):
        if not isinstance(values, (list, tuple)):
            raise ValueError('values mast be list or tuple')

        self.__form = form
        self.__field = field
        self.__values = values
        self.__current_index = 0

    def next(self):
        try:
            self.__field.value = self.__values[self.__current_index]
        except IndexError:
            raise StopIteration

        self.__current_index += 1

        return altered_form(self.__form)
