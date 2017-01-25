from __future__ import absolute_import, division, print_function, unicode_literals
import semantic_version as semantic_version_module
import six
import os
import re

def not_none(value):
    """
    Value cannot be empty
    """
    return not value is None

def text(value):
    """
    Value can contain any readable character
    """
    return True

def variable_name(value):
    """
    Value can only contain alphanumerical characters and underscore
    """

    result = bool(re.match('^[a-zA-Z_$][a-zA-Z_$0-9]*$', value))

    if six.PY3:
        assert value.isidentifier() == result

    return result

def available_path(value):
    return not os.path.exists(value)

def creatable_path(value):
    """
    Directory must exist or be possible to create
    """
    def exists(path):
        if os.path.exists(path):
            return path
        return exists(os.path.split(path)[0])

    if os.path.isdir(value):
        return True

    return writable_directory(exists(value))

def writable_directory(value):
    """
    Must be writeable directory
    """
    if not os.path.exists(value):
        return True

    return os.access(value, os.W_OK)

def empty_directory(value):
    """
    Must be en empty directory
    """
    if not os.path.exists(value):
        return True

    return not os.listdir(value)

def semantic_version(value):
    """
    Value must be a valid semantic version
    """
    try:
        semantic_version_module.Version(value)
        return True
    except ValueError:
        return False

def comma_separated_identifiers(values):
    """
    Value must be a list of valid identifiers (alphanumerical + underscore)
    """
    return all(identifier(value) for value in values.split(','))

def url(value):
    """
    Value must be valid url
    """
    return True
    pattern = re.compile(
                r'^(?:http|ftp)s?://' # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                r'localhost|' #localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                r'(?::\d+)?' # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return bool(pattern.match(value))
