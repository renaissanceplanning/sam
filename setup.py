# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 16:02:52 2022

@author: AZ7
"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")
setup(name="sam",
      version="0.1",
      packages=find_packages(),
      url="https://github.com/renaissanceplanning/sam",
      license="",
      author="Aaron Weinstock",
      author_email="aweinstock@citiesthatwork.com",
      description="standard planning dataset downloads",
      long_description=long_description,
      long_description_content_type="text/markdown",
      install_requires=[])