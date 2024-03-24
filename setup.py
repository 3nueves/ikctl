from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='ikctl',
    version='0.1.7',
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
