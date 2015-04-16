============
Installation
============

::

    pip install noseapp_selenium


=====
Usage
=====

::

    from noseapp.ext.selenium import drivers
    from noseapp.ext.selenium import SeleniumEx
    from noseapp.ext.selenium import make_config

    config = make_config()
    config.chrome_configure(
        executable_path='/path/to/chrome_driver_bin',
    )
    # for remote use
    config.remote_configure(
        capabilities={
            drivers.CHROME: {
                'version': '40',
            },
        },
        options={
            'command_executor': SELENIUM_HUB_URL,
        },
    )

    selenium = SeleniumEx(
        config,
        use_remote=False,  # use True for remote driver
        implicitly_wait=30,
        maximize_window=True,
        driver_name=drivers.CHROME,
    )

    driver = selenium.get_driver()


Create query
------------

::

    from noseapp.ext.selenium import QueryProcessor
    from noseapp.ext.selenium.query import contains

    query = QueryProcessor(driver)

    search_wrapper = query.div(_class='search-wrap').first()
    search_field = query(search_wrapper).input(id='search').first()
    search_field.send_keys(...)

    # query.div(id=contains('hello')).wait()
    # query.div(id=contains('hello')).exist
    # query.div(id=contains('hello')).all()
    # query.div(id=contains('hello')).get(3)


Forms
-----

::

    from noseapp.ext.selenium.forms import UIForm
    from noseapp.ext.selenium.forms import fields
    from noseapp.ext.selenium.query import contains
    from noseapp.ext.selenium.forms import make_field
    from noseapp.ext.selenium.forms import FieldsGroup
    from noseapp.ext.selenium.query import QueryObject


    class FirstFieldsGroup(FieldsGroup):
        class Meta:
            wrapper = QueryObject('div', _class='wrapper')

        field_one = fields.Input(
            'field name',
            weight=1,
            value='hello',
            require=True,
            invalid_value='1',
        )
        field_two = fields.Checkbox(
            'checkbox name',
            weight=2,
            value=True,
        )


    class MyForm(UiForm):
        class Meta:
            wrapper = QueryObject('div', _class=contains('form-wrapper'))

        description = fields.TextArea(
            'description',
            weight=1,
            value=lambda: 'Hello World!',
        )

        first_group = make_field(FirstFieldsGroup, weight=2)

        def submit():
            button = self.query.input(id='button').first()
            button.click()


    form = MyForm(driver)

    form.fill()
    form.submit()


    # Iterators

    from noseapp.ext.selenium.forms import iter_fields
    from noseapp.ext.selenium.forms import iter_invalid
    from noseapp.ext.selenium.forms import iter_required
    from noseapp.ext.selenium.forms import preserve_original

    # by fields
    for field in iter_fields(form):
        field.fill()
    form.submit()

    # by required fields
    for field in iter_required(form):
        form.fill(exclude=[field])
    form.submit()

    # by fields with having invalid value
    for field in iter_invalid(form):
        with preserve_original(form):
            field.value = field.invalid_value
            form.fill()
        form.submit()


    # Memorizing action

    form.first_group.field_one.fill('another value')
    form.fill()
    form.submit()


Page Object
-----------

::

    from noseapp.ext.selenium import PageObject
    from noseapp.ext.selenium import PageRouter
    from noseapp.ext.selenium.page_object import WaitConfig


    class MyPage(PageObject):
        class Meta:
            wrapper = QueryObject('div', _class='wrapper')
            wait_config = WaitConfig(  # wait_complete method configuration
                objects=(
                    QueryObject('input', value='input value'),
                    QueryObject('div', _class='hello'),
                ),
                one_of_many=True,
            )

        element = QueryObject('li', data_blank='data-blank')

        def get_my_form(self):
            """
            Factory method for my form
            """
            return MyForm(self._driver)


    PageRouter.add_rule('/my_page/', MyPage)


    router = PageRouter(driver, base_path='http://my-site.com')
    page = router.get('/my_page/')  # or page = MyPage(driver)
    form = page.get_my_form()

    page.element.click()
