"""Python setup.py for project_name package"""
from setuptools import find_packages, setup

setup(
    name='constance',
    version='0.0.0',
    description='Object-oriented parsing of binary data.',
    url='https://github.com/bswck/constance/',
    long_description_content_type='text/markdown',
    author="bswck",
    packages=find_packages(exclude=['tests', '.github']),
    # entry_points={
    #     'console_scripts': ['constance = constance.__main__:main']
    # },
    extras_require={'test': ['pytest']},
)
