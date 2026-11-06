"""stream's setup"""

import re
from pathlib import Path

from setuptools import find_packages, setup


def get_version():
    file = Path(__file__).absolute().parent / PROJECT_NAME / "__init__.py"
    if file.exists():
        with file.open() as f:
            version_pattern = r"[\d\w\._-]*"
            pattern = r"__version__ *= *('{0}'|\"{0}\")".format(version_pattern)
            regex = re.compile(pattern)
            for match in regex.finditer(f.read()):
                if (version := match.groups()[0]) :
                    return version[1:-1]
    return "unknown"


PROJECT_NAME = "stream"
PROJECT_VERSION = get_version()
PROJECT_AUTHOR = "Marko Vačovnik"
PROJECT_AUTHOR_EMAIL = "marko.vacovnik@gorenje.com"
PROJECT_URL = "http://rdegitlab.gorenje.si/testing/py_stream"
PROJECT_DESC = "Project consists of stream bases and various stream implementations"

MIN_PY_VERSION = "3.8"

with open("requirements.txt") as f:
    INSTALL_REQUIREMENTS = [line.strip() for line in f if line.strip()]


setup(
    name=PROJECT_NAME,
    version=PROJECT_VERSION,
    packages=find_packages(exclude=["tests", "tests.*"]),
    author=PROJECT_AUTHOR,
    author_email=PROJECT_AUTHOR_EMAIL,
    url=PROJECT_URL,
    description=PROJECT_DESC,
    install_requires=INSTALL_REQUIREMENTS,
    python_requires=f">={MIN_PY_VERSION}",
    test_suite="tests",
    tests_require=[
        *INSTALL_REQUIREMENTS,
    ],
)
