from __future__ import absolute_import, division, print_function, unicode_literals
import os
import json
import collections

def get(path):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', path)) as f:
        content = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(f.read())

    return content

