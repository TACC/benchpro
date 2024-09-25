from glob import glob
from setuptools import setup, find_packages
from io import open
import os
import pathlib
import sys

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

# Parse requirements
required_packages = [x.strip() for x in all_reqs if ('git+' not in x) and (
    not x.startswith('#')) and (not x.startswith('-'))]

setup (
    name='benchpro',
    version='1.8.7',
    description="A utility that automates building applications, running benchmarks and collecting results.",
    packages=['src', 'benchpro'],
    include_package_data=True,
    zip_safe=False,
    install_requires = required_packages,
    python_requires='>=3.7',
    author = "Matthew Cawood",
    keywords = "automation, performance benchmarking, compilation, provenance data",
    long_description = open('README.md').read(),
    license='MIT',
    url='https://github.com/TACC/benchpro-site',
    author_email = 'mcawood@tacc.utexas.edu',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    scripts=['src/benchpro', 'src/benchset', 'src/stage', 'src/toggle_dev_prod'],
)
