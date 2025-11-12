# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "tasktronaut"
author = "Chris Stefano"
copyright = f"2025, {author}"  # pylint: disable=redefined-builtin

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Auto-generate docs from docstrings
    "sphinx_autodoc_typehints",  # Include type hints in docs
    "sphinx_rtd_theme",  # Use Read the Docs theme
]

templates_path = ["_templates"]
exclude_patterns = []
add_module_names = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = "tasktronaut Documentation"
