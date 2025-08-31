"""pyramid_session_multi installation script.
"""

import os
import re  # store version in the init.py

from setuptools import find_packages
from setuptools import setup


HERE = os.path.dirname(__file__)

long_description = description = (
    "Provides a framwork for creating multiple adhoc session binds in Pyramid."
)
with open(os.path.join(HERE, "README.md")) as r_file:
    long_description = r_file.read()

with open(os.path.join(HERE, "src", "pyramid_session_multi", "__init__.py")) as v_file:
    VERSION = re.compile(r'.*__VERSION__ = "(.*?)"', re.S).match(v_file.read()).group(1)  # type: ignore[union-attr]

requires = [
    "pyramid>=2",
    "typing_extensions",
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
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Developers",
        "Framework :: Pyramid",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    keywords="pyramid session web",
    author="Jonathan Vanasco",
    author_email="jonathan@findmeon.com",
    url="https://github.com/jvanasco/pyramid_session_multi",
    license="MIT",
    packages=find_packages(
        where="src",
    ),
    package_dir={"": "src"},
    package_data={
        "": [
            "py.typed",
            "debugtoolbar/panels/templates/*",
        ],
    },
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    extras_require={
        "testing": testing_extras,
    },
    test_suite="tests",
)
