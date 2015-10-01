# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages


__version__ = '1.2.3'


if __name__ == '__main__':
    setup(
        name='noseapp_selenium',
        url='https://github.com/trifonovmixail/noseapp_selenium',
        version=__version__,
        packages=find_packages(),
        author='Mikhail Trifonov',
        author_email='mikhail.trifonov@corp.mail.ru',
        description='selenium extension for noseapp lib',
        long_description=open('README.rst').read(),
        include_package_data=True,
        zip_safe=False,
        platforms='any',
        install_requires=[
            'noseapp>=1.0.9',
            'selenium==2.46.0',
        ],
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Topic :: Software Development :: Testing',
        ],
    )
