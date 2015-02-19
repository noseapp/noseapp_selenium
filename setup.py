# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

import noseapp_selenium_ex


with open('requirements.txt') as fp:
    requirements = [req.strip() for req in fp.readlines() if not req.startswith('--')]


if __name__ == '__main__':
    setup(
        name='noseapp_selenium_ex',
        url='https://github.com/trifonovmixail/noseapp_selenium',
        version=noseapp_selenium_ex.__version__,
        packages=find_packages(),
        author='Mikhail Trifonov',
        author_email='mikhail.trifonov@corp.mail.ru',
        description='selenium extension for noseapp lib',
        include_package_data=True,
        zip_safe=False,
        platforms='any',
        install_requires=requirements,
    )
