# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='marshmallow-mongoengine',
    version='0.30.0',
    description='Mongoengine integration with the marshmallow '
                '(de)serialization library',
    long_description=read('README.rst'),
    author='Emmanuel Leblond',
    author_email='emmanuel.leblond@gmail.com',
    url='https://github.com/touilleMan/marshmallow-mongoengine',
    packages=find_packages(exclude=("test*", )),
    package_dir={'marshmallow-mongoengine': 'marshmallow-mongoengine'},
    include_package_data=True,
    install_requires=['mongoengine>=0.9.0'],
    extras_require={
        'toasted': ['toastedmarshmallow>=0.2.6'],
        'marshmallow': ['marshmallow>=3.0.0b7'],
    },
    license='MIT',
    zip_safe=False,
    keywords='mongoengine marshmallow',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
)
