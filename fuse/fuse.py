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

from fuse.utils import prompts, validators, lineups
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
        description = "Synthesizes a boilerplate based on lineup"
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            ( ['-l', '--lineup'], dict(required=True, action='store', help='Name of the lineup') ),
        ]

    @expose(hide=True)
    def default(self):
        lineup_name = self.app.pargs.lineup
        lineup = lineups.get(lineup_name)

        components = []

        # Instantiate components
        for component_module_name, config in lineup.items():
            component_class_name = inflection.camelize(component_module_name)
            component_module = importlib.import_module('fuse.components.%s' % component_module_name)

            component = getattr(component_module, component_class_name)(
                name=component_module_name,
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
            for channel in component.listens_to:
                component.queues[channel] = queue.Queue()
                component.message_dispatcher.signal(channel).connect(component.inbox)

            component.instantiate()
            components.append(component)

        # Let components collect their stuff
        for component in components:
            component.collect()

        # Trigger final configure
        for component in components:
            component.configure()

        # Write to disk
        for component in components:
            component.write()


class RecipeController(CementBaseController):
    class Meta:
        label = 'lineup'
        description = "List and inspect lineups"
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            ( ['-l', '--lineup'], dict(action='store', help='Name of the lineup') ),
        ]

    @expose(hide=True)
    def default(self):
        self.app.render({}, 'default_lineup.jinja2')


    @expose(help="Inspect lineup")
    def inspect(self):
        lineup_name = self.app.pargs.lineup
        lineup = lineups.get(lineup_name)

        context = {
            'lineup': lineup,
            'lineup_name': lineup_name,
        }

        self.app.render(context, 'lineup.jinja2')

    @expose(help="List available lineups", aliases=['list'], aliases_only=True)
    def show_all(self):
        context = {
            'lineups': lineups.ls(),
        }
        self.app.render(context, 'lineups.jinja2')

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
