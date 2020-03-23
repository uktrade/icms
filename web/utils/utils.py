import os
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


def url_path_join(*args):
    clean_args = [x.rstrip('/') for x in args]
    return "/".join(clean_args)


def merge_dictionaries(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
  both a and bhave a key who's value is a dict then dict_merge is called
  on both values and the result stored in the returned dictionary.'''
    if not b:
        return a
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict):
            result[k] = merge_dictionaries(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result


class FilevalidationService():
    """
        Basic file validation service
    """
    EXTENSION_BLACKLIST = [
        'bat', 'bin', 'com', 'dll', 'exe', 'htm', 'html', 'msc', 'msi', 'msp',
        'ocx', 'scr', 'wsc', 'wsf', 'wsh'
    ]

    def has_valid_extenstion(self, file):
        """
            Checks if a file extension is not bacllisted

            Arguments:
                file -- Any object with a name property

            Returns:
                True - if extension is NOT blacklisted
                False - if extension is blacklisted
        """
        file_name, file_extension = os.path.splitext(file.name)

        return file_extension.strip('.') not in self.EXTENSION_BLACKLIST

    def is_valid(self, file):
        """
            Aggregator function, runs all validation functions

            Returns:
                True - if all validations pass
                False - if any validation fails
        """
        if not self.has_valid_extenstion(file):
            return False

        return True
