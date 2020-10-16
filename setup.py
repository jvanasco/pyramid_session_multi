"""pyramid_sessionlike installation script.
"""
import os

from setuptools import setup
from setuptools import find_packages

# store version in the init.py
import re

with open(
    os.path.join(os.path.dirname(__file__), "pyramid_session_multi", "__init__.py")
) as v_file:
    VERSION = re.compile(r'.*__VERSION__ = "(.*?)"', re.S).match(v_file.read()).group(1)

# pyramid 1.5 == SignedCookieSessionFactory
requires = [
    "pyramid>=1.5",
    "zope.interface",  # installed by pyramid
]
tests_require = [
    "pytest",
    "pyramid_debugtoolbar>=4.0",
]
testing_extras = tests_require + []

setup(
    name="pyramid_session_multi",
    version=VERSION,
    description="Provides a framwork for creating multiple adhoc session binds in Pyramid",
    long_description="easily manage multiple sessions in your Pyramid application",
    classifiers=[
        "Intended Audience :: Developers",
        "Framework :: Pyramid",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="web pyramid session",
    packages=["pyramid_session_multi", "pyramid_session_multi.tests"],
    author="Jonathan Vanasco",
    author_email="jonathan@findmeon.com",
    url="https://github.com/jvanasco/pyramid_session_multi",
    license="MIT",
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    extras_require={
        "testing": testing_extras,
    },
    test_suite="pyramid_session_multi.tests",
)
