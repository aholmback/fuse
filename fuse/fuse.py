from __future__ import absolute_import, division, print_function # , unicode_literals ; unicode_literals messes up with Cement's type checking.
import six
import os
import importlib
import inflection
import blinker
import jinja2
import pkgutil
from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults
from cement.core.controller import CementBaseController, expose

from fuse.utils import prompts, validators, recipes
from fuse.models import Prompt, Resource

if six.PY2:
    import Queue as queue
else:
    import queue

defaults = init_defaults('fuse')
defaults['fuse']['debug'] = False


def run():
    with Fuse() as fuse:
        fuse.run()

class BaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = "Fuse - The template engine that ends all templates"

    @expose(hide=True)
    def default(self):
        self.app.render({}, 'default_base.jinja2')

class StartprojectController(CementBaseController):
    class Meta:
        label = 'startproject'
        description = "Synthesizes a boilerplate based on recipe"
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            ( ['-r', '--recipe'], dict(required=True, action='store', help='Name of the recipe') ),
        ]

    @expose(hide=True)
    def default(self):
        recipe_name = self.app.pargs.recipe
        recipe = recipes.get(recipe_name)

        services = []

        # Instantiate services
        for service_module_name, config in recipe.items():
            service_class_name = inflection.camelize(service_module_name)
            service_module = importlib.import_module('fuse.services.%s' % service_module_name)

            service = getattr(service_module, service_class_name)(
                name=service_module_name,
                config=config,
                queuer=queue.Queue,
                message_dispatcher=blinker,
                template_engine=jinja2.Template,
                prompter=prompts.DefaultPrompt,
                prompts=Prompt,
                resources=Resource,
                validators=validators,
            )

            # TODO: Find out why this works while the same 3 rows in Service.__init__ fails.
            for channel in service.listens_to:
                service.queues[channel] = queue.Queue()
                service.message_dispatcher.signal(channel).connect(service.inbox)

            service.instantiate()
            services.append(service)

        # Let services collect their stuff
        for service in services:
            service.collect()

        # Trigger final configure
        for service in services:
            service.configure()

        # Write to disk
        for service in services:
            service.write()


class RecipeController(CementBaseController):
    class Meta:
        label = 'recipe'
        description = "List and inspect recipes"
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            ( ['-r', '--recipe'], dict(action='store', help='Name of the recipe') ),
        ]

    @expose(hide=True)
    def default(self):
        self.app.render({}, 'default_recipe.jinja2')


    @expose(help="Inspect recipe")
    def inspect(self):
        recipe_name = self.app.pargs.recipe
        recipe = recipes.get(recipe_name)

        context = {
            'recipe': recipe,
            'recipe_name': recipe_name,
        }

        self.app.render(context, 'recipe.jinja2')

    @expose(help="List available recipes", aliases=['list'], aliases_only=True)
    def show_all(self):
        context = {
            'recipes': recipes.ls(),
        }
        self.app.render(context, 'recipes.jinja2')

class Fuse(CementApp):
    class Meta:
        label = 'fuse'
        config_defaults = defaults
        base_controller = 'base'
        handlers = [BaseController, RecipeController, StartprojectController]
        extensions = ['jinja2']
        output_handler = 'jinja2'
        template_module = 'fuse.templates'
        template_dirs = [os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')]
