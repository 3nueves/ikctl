""" setup app """
import os

from setuptools import setup, find_packages

def read(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with open(os.path.join(here, rel_path)) as fp:
        return fp.read()


def get_version(rel_path: str) -> str:
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            # __version__ = "0.9"
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='ikctl',
    version=get_version("ikctl/config/config.py"),
    description="App to installer packages on remote servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/3nueves/ikctl",
    author="David Moya López",
    author_email="3nueves@gmail.com",
    license="Apache v2.0",
    packages=find_packages(include=['ikctl','ikctl.*']),
    install_requires=[
        'paramiko',
        'pyaml',
        'envyaml'
    ],
    python_requires=">=3.10",
    entry_points={
        'console_scripts': [
            'ikctl=ikctl.main:create_parser'
        ]
    }
)
