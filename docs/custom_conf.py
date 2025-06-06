import datetime
from typing import Dict, List

# Custom configuration for the Sphinx documentation builder.
# All configuration specific to your project should be done in this file.
#
# The file is included in the common conf.py configuration file.
# You can modify any of the settings below or add any configuration that
# is not covered by the common conf.py file.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

############################################################
### Project information
############################################################

# Product name
project = "Craft Store"
author = "Canonical Group Ltd"

# Uncomment if your product uses release numbers
# release = '1.0'

# The default value uses the current year as the copyright year.
#
# For static works, it is common to provide the year of first publication.
# Another option is to give the first year and the current year
# for documentation that is often changed, e.g. 2022–2023 (note the en-dash).
#
# A way to check a GitHub repo's creation date is to obtain a classic GitHub
# token with 'repo' permissions here: https://github.com/settings/tokens
# Next, use 'curl' and 'jq' to extract the date from the GitHub API's output:
#
# curl -H 'Authorization: token <TOKEN>' \
#   -H 'Accept: application/vnd.github.v3.raw' \
#   https://api.github.com/repos/canonical/<REPO> | jq '.created_at'

copyright = "2021-%s, %s" % (datetime.date.today().year, author)

## Open Graph configuration - defines what is displayed in the website preview
# The URL of the documentation output
ogp_site_url = "https://canonical-craft-store.readthedocs-hosted.com/"
# The documentation website name (usually the same as the product name)
ogp_site_name = project
# An image or logo that is used in the preview
ogp_image = "https://assets.ubuntu.com/v1/253da317-image-document-ubuntudocs.svg"

# Update with the favicon for your product (default is the circle of friends)
html_favicon = "sphinx-docs-starter-pack/.sphinx/_static/favicon.png"

# (Some settings must be part of the html_context dictionary, while others
#  are on root level. Don't move the settings.)
html_context = {
    # Change to the link to your product website (without "https://")
    "product_page": "github.com/canonical/craft-store",
    # Add your product tag to ".sphinx/_static" and change the path
    # here (start with "_static"), default is the circle of friends
    "product_tag": "_static/tag.png",
    # Change to the discourse instance you want to be able to link to
    # using the :discourse: metadata at the top of a file
    # (use an empty value if you don't want to link)
    "discourse": "",
    # Change to the GitHub info for your project
    "github_url": "https://github.com/canonical/craft-store",
    # Change to the branch for this version of the documentation
    "github_version": "main",
    # Change to the folder that contains the documentation
    # (usually "/" or "/docs/")
    "github_folder": "/docs/",
    # Change to an empty value if your GitHub repo doesn't have issues enabled.
    # This will disable the feedback button and the issue link in the footer.
    "github_issues": "enabled",
    # Controls the existence of Previous / Next buttons at the bottom of pages
    # Valid options: none, prev, next, both
    "sequential_nav": "none",
}

# If your project is on documentation.ubuntu.com, specify the project
# slug (for example, "lxd") here.
slug = ""

############################################################
### Redirects
############################################################

# Set up redirects (https://documatt.gitlab.io/sphinx-reredirects/usage.html)
# For example: 'explanation/old-name.html': '../how-to/prettify.html',

redirects: Dict[str, str] = {}

############################################################
### Link checker exceptions
############################################################

# Links to ignore when checking links

linkcheck_ignore: List[str] = [
    "http://127.0.0.1:8000",
    "https://github.com/canonical/craft-store/releases/tag/.*",
]

# Pages on which to ignore anchors
# (This list will be appended to linkcheck_anchors_ignore_for_url)

custom_linkcheck_anchors_ignore_for_url: List[str] = []

############################################################
### Additions to default configuration
############################################################

## The following settings are appended to the default configuration.
## Use them to extend the default functionality.

# Add extensions
custom_extensions: List[str] = [
    "sphinx.ext.autodoc",
    "sphinx_toolbox.collapse",
]

# Add files or directories that should be excluded from processing.
custom_excludes: List[str] = [
    "sphinx-docs-starter-pack/*",
]

# Add CSS files (located in .sphinx/_static/)
custom_html_css_files: List[str] = []

# Add JavaScript files (located in .sphinx/_static/)
custom_html_js_files: List[str] = []

## The following settings override the default configuration.

# Specify a reST string that is included at the end of each file.
# If commented out, use the default (which pulls the reuse/links.txt
# file into each reST file).
# custom_rst_epilog = ''

# By default, the documentation includes a feedback button at the top.
# You can disable it by setting the following configuration to True.
disable_feedback_button = False

############################################################
### Additional configuration
############################################################

## Add any configuration that is not covered by the common conf.py file.
