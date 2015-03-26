# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages


__version__ = '0.0.0'


if __name__ == '__main__':
    setup(
        name='noseapp_selenium',
        url='https://github.com/trifonovmixail/noseapp_selenium',
        version=__version__,
        packages=find_packages(),
        author='Mikhail Trifonov',
        author_email='mikhail.trifonov@corp.mail.ru',
        description='selenium extension for noseapp lib',
        include_package_data=True,
        zip_safe=False,
        platforms='any',
        install_requires=[
            'noseapp',
            'selenium==2.44.0',
        ],
    )
