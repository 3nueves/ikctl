from setuptools import setup, find_packages


setup(
    name='ikctl',
    version='1.0.0',
    description="Installing kits in remote servers",
    author="David Moya López",
    package_dir={"": "ikctl"},
    # packages=find_packages(),
    install_requires=[
        'paramiko',
        'pyaml'
    ],
    entry_points={
        'console_scripts': [
            'ikctl = main:create_parser',
        ],
    },
)
