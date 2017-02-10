# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


REQUIRES = (
    'marshmallow>=2.1.0',
    'mongoengine>=0.9.0',
)


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='marshmallow-mongoengine',
    version='0.7.8',
    description='Mongoengine integration with the marshmallow '
                '(de)serialization library',
    long_description=read('README.rst'),
    author='Emmanuel Leblond',
    author_email='emmanuel.leblond@gmail.com',
    url='https://github.com/touilleMan/marshmallow-mongoengine',
    packages=find_packages(exclude=("test*", )),
    package_dir={'marshmallow-mongoengine': 'marshmallow-mongoengine'},
    include_package_data=True,
    install_requires=REQUIRES,
    license='MIT',
    zip_safe=False,
    keywords='mongoengine marshmallow',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
)
