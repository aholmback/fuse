from __future__ import absolute_import, division, print_function # , unicode_literals ; unicode_literals messes up with Cement's type checking.
import six
import os
import importlib
import inflection
import jinja2
import pkgutil
from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults
from cement.core.controller import CementBaseController, expose

from fuse.utils import validators as validator_functions
from fuse.utils import pinboards, json
from fuse import lineups, __version__


defaults = init_defaults('fuse')
defaults['fuse']['debug'] = False


def run():
    with Fuse() as fuse:
        fuse.run()

class BaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = "Fuse - Generate configurations"
        arguments = [
            ( ['-v', '--version'], dict(required=False, action='store_true', help='Display version') ),
        ]

    @expose(hide=True)
    def default(self):
        if self.app.pargs.version:
            print("fuse {version}".format(version=__version__))
        else:
            self.app.render({}, 'default_base.jinja2')

class ResetController(CementBaseController):
    class Meta:
        label = 'reset'
        description = 'Resets database'
        stacked_on = 'base'
        stacked_type = 'nested'

    @expose(hide=True)
    def default(self):
        try:
            models.db.create_tables([models.Prompt, models.Resource])
            models.data()
        except models.OperationalError:
            print("Didn't create or do anything cus stuff already exist")

class StartprojectController(CementBaseController):
    class Meta:
        label = 'startproject'
        description = "Synthesizes a boilerplate based on lineup"
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            ( ['-l', '--lineup'], dict(required=True, action='store', help='Name of the lineup') ),
            ( ['--no-prefill'], dict(required=False, dest='prefill', action='store_false', help="Use prefill") ),
            ( ['--prefill'], dict(required=False, dest='prefill', action='store_true', help="Don't use prefill") ),
        ]

    @expose(hide=True)
    def default(self):
        lineup_name = self.app.pargs.lineup
        lineup = lineups.get(lineup_name)
        
        pinboard = pinboards.Pinboard()

        components = []

        # Instantiate components
        for component_module_name, actions in lineup.items():

            component_class_name = inflection.camelize(component_module_name)
            component_module = importlib.import_module('fuse.components.%s' % component_module_name)

            component = getattr(component_module, component_class_name)(
                name=component_module_name,
                logger=self.app.log,
            )

            component.setup(pinboard, actions)
            components.append(component)

        # Configure as long as components are processing pins
        while True:
            pins_processed = sum(component.configure(pinboard, prompt=self.prompt) for component in components)

            if pins_processed == 0:
                break

        # Write to disk
        for component in components:
            component.write()

        for component in components:
            component.finalize()

    def prompt(
            self, load=None, text='', description='', validators=None,
            options=None, prefill=None, default=None,
            pre_validation_hook=None, post_validation_hook=None):

        # Set input function
        input_fn = raw_input if six.PY2 else input

        # Set pre/post validation hook to return-input lambdas if None
        if pre_validation_hook is None:
            pre_validation_hook = lambda v: v

        if post_validation_hook is None:
            post_validation_hook = lambda v: v

        # Context for template engine
        # Fill in empty parameters from persistent storage if present
        context = {}
        try:
            load = {} if load is None else json.get('prompts.json')[load]
        except KeyError:
            self.app.log.error("Couldn't load prompt `{prompt}`, set load=None or add it to prompts.json.".format(prompt=load))
            load = {}

        context['text'] = text = text or load.get('text', None)
        context['description'] = description = description or load.get('description', None)
        context['default'] = default = default or load.get('default', None)
        context['options'] = options = options or load.get('options', None)
        validators = validators or load.get('validators', None)

        # Replace validator descriptors with actual functions
        if validators is None:
            validators = validator_descriptions = []
        else:
            try:
                validators = [getattr(validator_functions, validator) for validator in validators]
            except AttributeError:
                self.app.log.error(
                    "Validator `{validator}` was declared in lineup but doesn't exist in validator module.".format(
                        validator=validator
                    )
                )
                validators = []

            validator_descriptions = [validator.__doc__.strip() for validator in validators if validator.__doc__]

        # If options is a list with elements, create a validator on the
        # fly and replace all other potential validators.
        if options is not None:
            validators = [lambda v: v in options]

        context['validators'] = validator_descriptions

        # Set the default value to prefill (if present)
        context['prefill'] = prefill
        context['default'] = default

        # Set user input to prefill if prefill is enabled
        user_input = pre_validation_hook(prefill) if self.app.pargs.prefill else None

        while user_input is None or not all(validator(user_input) for validator in validators):
            context['user_input'] = user_input
            user_message = self.app.render(context, 'prompt.jinja2', out=None).strip()

            try:
                user_input = pre_validation_hook(input_fn(user_message)) or default
            except EOFError:
                print('\n')
                break

        return post_validation_hook(user_input)

class LineupController(CementBaseController):
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
        handlers = [BaseController, LineupController, StartprojectController, ResetController]
        extensions = ['jinja2']
        output_handler = 'jinja2'
        template_module = 'fuse.templates'
        template_dirs = [os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')]
