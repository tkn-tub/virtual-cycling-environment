#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Python packaging file for EVI."""

import io
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup


def read(*names, **kwargs):
    """Safely get a file's contents."""
    fname = join(dirname(__file__), *names)
    with io.open(fname, encoding=kwargs.get("encoding", "utf8")) as fle:
        return fle.read()


setup(
    name="evi",
    version="0.15.5",
    description=(
        "An Ego Vehicle Interface for real-time communication "
        "between Sumo, Veins and a real-time simulator."
    ),
    long_description="{}\n\n{}".format(
        read("README.md"),
        read("CHANGELOG.md"),
    ),
    maintainer="Dominik S. Buse",
    maintainer_email="buse@ccs-labs.org",
    url="http://www.hy-nets.org",  # TODO: update to EVI project url
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    scripts=[
        'scripts/evid.py'
    ],
    console_scripts=[],
    classifiers=[
        # complete classifier list:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities",
    ],
    install_requires=[
        "typing_extensions",
        "protobuf>=3.0.0",
        "psutil",
        "pyproj",
        "pyzmq>=17.0.0",
        "sumolib==1.6.0",
        "traci==1.6.0",
        "evi-asm-protocol>=0.14.0",
        "shapely",
        "scipy",
        "numpy",
        "PyYAML",
        "rtree",
    ],
    extras_require={},
)
