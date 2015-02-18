# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

import noseapp_selenium_ex


if __name__ == '__main__':
    setup(
        name='noseapp_selenium_ex',
        version=noseapp_selenium_ex.__version__,
        packages=find_packages(),
        author='Mikhail Trifonov',
        author_email='mikhail.trifonov@corp.mail.ru',
        description='selenium extension for noseapp lib',
        install_requires=[
            'selenium==2.44.0',
        ],
    )
