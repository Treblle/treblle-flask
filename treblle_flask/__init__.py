# coding=utf-8

"""
treblle_flask
~~~~~~~~~~~~~~~~~~~~~~~

Treblle Flask allows you to easily integrate Treblle into your Flask application
it uses environment variables to configure the extension. If you want to
override the default configuration, you can pass a dictionary of options
to the constructor.
"""

from .extension import Treblle

__all__ = ['Treblle']
