"""c_tools's setup"""

import re
from pathlib import Path

from setuptools import find_packages, setup

try:
    from sphinx.setup_command import BuildDoc

except ModuleNotFoundError:
    from distutils.cmd import Command

    class BuildDoc(Command):
        """Fallback BuildDoc class"""

        def initialize_options(self):
            ...

        def finalize_options(self):
            ...

        def run(self):
            print("Dependencies for building documentation missing.")
            print('Run "pip install -r requirements_docs.txt"')


_FILE_DIR = Path(__file__).absolute().parent


def get_version():
    file = _FILE_DIR / PROJECT_NAME / "__init__.py"
    if file.exists():
        with file.open() as f:
            version_pattern = r"[\d\w\._-]*"
            pattern = r"__version__ *= *('{0}'|\"{0}\")".format(version_pattern)
            regex = re.compile(pattern)
            for match in regex.finditer(f.read()):
                if (version := match.groups()[0]) :
                    return version[1:-1]
    return "unknown"


PROJECT_NAME = "c_tools"
PROJECT_VERSION = get_version()
PROJECT_AUTHOR = "Marko Vačovnik"
PROJECT_AUTHOR_EMAIL = "marko.vacovnik@gorenje.com"
PROJECT_URL = "http://rdegitlab.gorenje.si/testing/py_c_tools"
PROJECT_DESC = "Project consists of tools for translating c objects to ctypes objects"

MIN_PY_VERSION = "3.8"

with (_FILE_DIR / "requirements.txt").open() as f:
    INSTALL_REQUIREMENTS = list(filter(None, f.read().split("\n")))

CMD_DOC = "build_doc"
CMD_CLASS = {CMD_DOC: BuildDoc}
COMMAND_OPTIONS = {
    CMD_DOC: {
        "project": ("setup.py", PROJECT_NAME),
        "version": ("setup.py", PROJECT_VERSION),
        "release": ("setup.py", PROJECT_VERSION),
        "source_dir": ("setup.py", "documentation"),
    }
}


if __name__ == "__main__":
    setup(
        name=PROJECT_NAME,
        version=PROJECT_VERSION,
        packages=[#find_packages(exclude=["tests", "tests.*"]),
            "c_tools",
            "c_tools.parser",
            "c_tools.parser.code",
            "c_tools.parser.elf",
            "c_tools.preprocessor",
            "c_tools.specializations",
            "c_tools.specializations.io_param",
            "c_tools.specializations.mat",
        ],
        author=PROJECT_AUTHOR,
        author_email=PROJECT_AUTHOR_EMAIL,
        url=PROJECT_URL,
        description=PROJECT_DESC,
        install_requires=INSTALL_REQUIREMENTS,
        python_requires=f">={MIN_PY_VERSION}",
        test_suite="tests",
        tests_require=INSTALL_REQUIREMENTS,
        cmdclass=CMD_CLASS,
        command_options=COMMAND_OPTIONS,
    )
