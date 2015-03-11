# -*- coding: utf-8 -*-

from collections import Iterator


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


class InvalidValueFieldsIterator(Iterator):

    def __init__(self, form, exclude=None):
        exclude = exclude or tuple()

        self.__current_index = 0
        self.__fields = [
            field for field in form._fields
            if field not in exclude and field.invalid_value is not None
        ]

    def next(self):
        try:
            field = self.__fields[self.__current_index]
        except IndexError:
            raise StopIteration

        self.__current_index += 1

        return field


class RequireFieldsIterator(Iterator):

    def __init__(self, form, items=False):
        self.__form = form
        self.__items = items
        self.__current_index = 0
        self.__required_fields = [field for field in form._fields if field.required]

    def next(self):
        try:
            exclude_field = self.__required_fields[self.__current_index]
        except IndexError:
            raise StopIteration

        it = FieldsIterator(
            self.__form,
            exclude=(exclude_field,),
        )

        self.__current_index += 1

        if self.__items:
            return exclude_field, it
        return it


class FieldItemsIterator(Iterator):

    def __init__(self, form, field, items):
        if not isinstance(items, (list, tuple)):
            raise ValueError('values mast be list or tuple')

        self.__form = form
        self.__field = field
        self.__items = items
        self.__current_index = 0

    def next(self):
        try:
            item = self.__items[self.__current_index]
        except IndexError:
            raise StopIteration

        self.__current_index += 1

        return self.__field, item
