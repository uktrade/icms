from copy import deepcopy


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
