# -*- coding: utf-8 -*-

"""
Example:

    from . import fields
    from . import form

    class MyForm(form.UIForm):

        title = fields.Input(u'Title',
            value='Hello World',
            selector=fields.selector(id='title'),
        )
        description = fields.TextArea(u'Description',
            required=True,
            value='Hello, my name is Tester',
            selector=fields.selector(_class='desc'),
        )

        @property
        def is_save(self):
            wrapper = self._query.div(id='form-wrapper').first()
            text = wrapper.text
            return u'Saved' in text

        def submit(self):
            button = self._query.input(name='submit-button).first()
            button.click()

    form = MyForm(driver)
    form.fill()
    form.submit()
    form.assert_save()

    Fill by one field:

    form.title.fill()
    # Set value
    form.title.fill('Title')
"""

from noseapp_selenium.forms import fields
from noseapp_selenium.forms.form import UIForm
from noseapp_selenium.forms.form import make_field



__all__ = (
    fields,
    UIForm,
    make_field,
)
