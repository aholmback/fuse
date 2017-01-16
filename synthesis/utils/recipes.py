import os
import json
import collections


def parse_filename(f):
    f = os.path.basename(f)
    return os.path.splitext(os.path.basename(f))

def file_is_recipe(f):
    name, extension = parse_filename(f)

    if name[0] in ('.', '_'):
        return False

    if not extension in ('.json'):
        return False

    return True

def ls(filter_function=None):
    if filter_function is None:
        filter_function = lambda recipe: True

    recipes = [parse_filename(f)[0] for f in os.listdir(os.path.join('synthesis/recipes')) if file_is_recipe(f)]

    return filter(filter_function, recipes)

def get(recipe_name):
    with open('synthesis/recipes/%s.json' % recipe_name) as f:
        recipe = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(f.read())

    return recipe
