# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
# import sphinx_rtd_theme

# -- Project information -----------------------------------------------------

project = 'Virtual Cycling Environment'
copyright = '2023, Telecommunication Networks (TKN), TU Berlin'
author = 'Telecommunication Networks (TKN), TU Berlin'

# The full version, including alpha/beta/rc tags
release = '0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # 'sphinx_rtd_theme',
    'sphinxcontrib.bibtex',
    'sphinxext.opengraph',  # custom config not needed if hosting on rtd
    'sphinx.ext.todo',
    'sphinx_copybutton',
]

bibtex_bibfiles = ['references.bib']
bibtex_encoding = 'utf-8-sig'
bibtex_default_style = 'alpha'
bibtex_reference_style = 'label'  # label=numbers
bibtex_tooltips = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

numfig = True

todo_include_todos = True


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'sphinx_rtd_theme'
html_theme = "furo"
html_logo = "img/vce_logo_512x512.png"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
