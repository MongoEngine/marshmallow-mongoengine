# -*- coding: utf-8 -*-
from setuptools import find_packages, setup


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name="marshmallow-mongoengine",
    version="0.31.1",
    description="Mongoengine integration with the marshmallow "
    "(de)serialization library",
    long_description=read("README.rst"),
    author="Emmanuel Leblond, Patrick Huck",
    author_email="phuck@lbl.gov",
    url="https://github.com/MongoEngine/marshmallow-mongoengine",
    packages=find_packages(exclude=("test*",)),
    package_dir={"marshmallow-mongoengine": "marshmallow-mongoengine"},
    include_package_data=True,
    install_requires=["mongoengine>=0.9.0", "marshmallow>=3.10.0"],
    license="MIT",
    zip_safe=False,
    keywords="mongoengine marshmallow",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
)
