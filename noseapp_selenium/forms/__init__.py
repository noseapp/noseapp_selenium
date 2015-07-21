# -*- coding: utf-8 -*-

from noseapp_selenium.forms import fields
from noseapp_selenium.forms.group import make_field
from noseapp_selenium.forms.group import FieldsGroup
from noseapp_selenium.forms.group import iter_fields
from noseapp_selenium.forms.group import iter_invalid
from noseapp_selenium.forms.group import iter_required
from noseapp_selenium.forms.group import preserve_original


class UIForm(FieldsGroup):
    """
    For usability only
    """
    pass


__all__ = (
    fields,
    UIForm,
    make_field,
    FieldsGroup,
    iter_fields,
    iter_invalid,
    iter_required,
    preserve_original,
)
