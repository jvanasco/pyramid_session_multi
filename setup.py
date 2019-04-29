"""pyramid_sessionlike installation script.
"""
import os

from setuptools import setup
from setuptools import find_packages

# store version in the init.py
import re
with open(
        os.path.join(
            os.path.dirname(__file__),
            'pyramid_session_multi', '__init__.py')) as v_file:
    VERSION = re.compile(
        r".*__VERSION__ = '(.*?)'",
        re.S).match(v_file.read()).group(1)

try:
    here = os.path.abspath(os.path.dirname(__file__))
    README = open(os.path.join(here, "README.md")).read()
    README = README.split("\n\n", 1)[0] + "\n"
except:
    README = ''

requires = [
    "pyramid",
]

setup(
    name="pyramid_session_multi",
    version=VERSION,
    description="provides for creating multiple adhoc session binds",
    long_description=README,
    classifiers=[
        "Intended Audience :: Developers",
        "Framework :: Pyramid",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="web pyramid session",
    packages=['pyramid_session_multi',
              'pyramid_session_multi.tests',
              ],
    author="Jonathan Vanasco",
    author_email="jonathan@findmeon.com",
    url="https://github.com/jvanasco/pyramid_session_multi",
    license="MIT",
    include_package_data=True,
    zip_safe=False,
    tests_require = requires,
    install_requires = requires,
    test_suite="pyramid_session_multi.tests",
)
