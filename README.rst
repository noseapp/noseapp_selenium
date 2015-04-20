============
Installation
============

::

    pip install noseapp_selenium


Install extension from app
--------------------------

config module ::

    from noseapp.ext.selenium import make_config


    SELENIUM_EX = make_config()

    SELENIUM_EX.configure(
        implicitly_wait=30,
        maximize_window=True,
    )

    SELENIUM_EX.remote_configure(
        capabilities={
            drivers.CHROME: {
                'version': '41',
            },
        },
        options={
            'keep_alive': True,
            'command_executor': 'url to selenium hub',
        },
    )

    etc...


app module ::

    from noseapp import NoseApp
    from noseapp.ext.selenium import SeleniumEx


    class MyApp(NoseApp):

        def initialize(self):
            SeleniumEx.install(self)


suite ::

    from noseapp import Suite
    from noseapp import TestCase


    suite = Suite(__name__, require=['selenium'])


    class MyTestCase(TestCase):

        def setUp(self):
            self.driver = self.selenium.get_driver()

        def tearDown(self):
            self.driver.quit()

        def test_go_to(self):
            self.driver.get('http://google.ru')
            search_field = self.driver.query.input(id='gs_htif0').first()
            search_field.send_keys("ok google, let's get testing")
            self.assertIn('ok google', self.driver.query.get_text())


Simple usage
------------

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

    from noseapp.ext.selenium.query import contains

    search_wrapper = driver.query.div(_class='search-wrap').first()
    search_field = driver.query(search_wrapper).input(id='search').first()
    search_field.send_keys(...)

    # driver.query.div(id=contains('hello')).wait()
    # driver.query.div(id=contains('hello')).exist
    # driver.query.div(id=contains('hello')).all()
    # driver.query.div(id=contains('hello')).get(3)


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

    # Query to form wrapper

    form.query.div(...).first()


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


    # Create relationship

    PageRouter.add_rule('/my_page/', MyPage)


    router = PageRouter(driver, base_path='http://my-site.com')
    page = router.get('/my_page/')  # or page = MyPage(driver)
    form = page.get_my_form()

    page.element.click()

    # Query to page object wrapper

    page.query.link(...).first()
