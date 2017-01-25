# unicode_literals messes up with Cement's type checking.
from __future__ import absolute_import, division, print_function
import six
import os
import sys
import importlib
import inflection
from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults
from cement.core.controller import CementBaseController, expose
from cement.core.exc import CaughtSignal

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
            (
                ['-v', '--version'],
                {
                    'required': False,
                    'action': 'store_true',
                    'help': 'Display version',
                },
            )
        ]

    @expose(hide=True)
    def default(self):
        if self.app.pargs.version:
            print("fuse {version}".format(version=__version__))
        else:
            self.app.render({}, 'default_base.jinja2')


class StartprojectController(CementBaseController):
    class Meta:
        label = 'startproject'
        description = "Create boilerplate based on lineup"
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (
                ['-l', '--lineup'],
                {
                    'required': True,
                    'action': 'store',
                    'help': 'Name of the lineup',
                }
            ),
            (
                ['--confirm'],
                {
                    'required': False,
                    'dest': 'confirm',
                    'action': 'store_true',
                    'help': "Confirm each option (default)",
                    'default': True,
                }
            ),
            (
                ['--no-confirm'],
                {
                    'required': False,
                    'dest': 'confirm',
                    'action': 'store_false',
                    'help': "Use defaults without confirmation",
                }
            ),
        ]

    @expose(hide=True)
    def default(self):
        lineup_name = self.app.pargs.lineup
        lineup = lineups.get(lineup_name)
        self.app.log.info("Found lineup `{lineup}'".format(lineup=lineup_name))

        pinboard = pinboards.Pinboard()

        components = []

        # Setup components based on specified lineup
        for component_module_name in lineup:

            actions = lineup[component_module_name]
            component_class_name = inflection.camelize(component_module_name)

            try:
                component_module = importlib.import_module(
                    'fuse.components.%s' % component_module_name)
                self.app.log.info("Loading component `{component}`".format(
                    component=component_module_name)
                    )
            except ImportError:
                self.app.log.error("Could not load component `{component}`".format(
                    component=component_module_name)
                    )
                sys.exit(1)

            component = getattr(component_module, component_class_name)(
                name=component_module_name,
                logger=self.app.log,
                render=self.app.render,
            )

            component.setup(pinboard, actions)
            components.append(component)

        # Configure all components
        all_components_configured = False
        new_pins = len(pinboard)
        iteration = 0

        while not all_components_configured or new_pins > 0:
            # Keep track of iteration for informative user messages
            iteration += 1

            # If last iteration didn't result in any new pins
            # this will be the last chance for components to
            # process their pins: A deferral-attempt will raise
            # RuntimeError.
            last_chance = not new_pins

            self.app.log.info(
                    ("[Iteration {iteration}] new_pins={new_pins}, "
                     "all_components_configured={all_components_configured}, "
                     "last_chance={last_chance}").format(
                        iteration=iteration,
                        all_components_configured=all_components_configured,
                        last_chance=last_chance,
                        new_pins=new_pins,
                        )
                    )

            # Assume all components configured.
            all_components_configured = True

            # Store number of pins before configure components
            pinboard_length = len(pinboard)

            # Configure all components in defined order.
            for component in components:

                self.app.log.info(
                        "Configuring component `{component}`".format(
                            component=component.name,
                            ))

                try:
                    component_configured = component.configure(
                            pinboard,
                            prompt=self.prompt,
                            last_chance=last_chance,
                            )
                except CaughtSignal as e:
                    print(e)
                    self.app.log.info("Exit")
                    sys.exit(1)

                if component_configured:
                    self.app.log.info(
                            "All current pins processed by component `{component}`".format(
                                component=component.name,
                                ))
                else:
                    self.app.log.info(
                            "Not all current pins processed by component `{component}`".format(
                                component=component.name,
                                ))
                    all_components_configured = False


            # Check if pinboard has new pins
            new_pins = len(pinboard) - pinboard_length


        # Write to disk
        for component in components:
            component.write()

        # Run post-write actions
        for component in components:
            component.finalize()

    def prompt(
            self, load=None, text='', description='',
            validators=None, options=None,  default=None,
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
            self.app.log.error(
                "Couldn't load prompt `{prompt}`, set load=None or add it to pr"
                "ompts.json.".format(prompt=load))
            load = {}

        context['text'] = text = text or load.get('text', None)
        context['default'] = default = default or load.get('default', None)
        context['options'] = options = options or load.get('options', None)

        context['description'] = description = (
            description or load.get('description', None))

        validators = validators or load.get('validators', None)

        # Replace validator descriptors with actual functions
        if validators is None:
            validators = validator_descriptions = []
        else:
            try:
                validators = [getattr(validator_functions, validator)
                              for validator in validators]
            except AttributeError:
                self.app.log.error(
                    "Validator `{validator}` was declared in lineup but doesn't"
                    " exist in validator module.".format(validator=validator)
                )
                validators = []

            validator_descriptions = [validator.__doc__.strip() for validator
                                      in validators if validator.__doc__]

        # If options is a list with elements, create a validator on the
        # fly and replace all other potential validators.
        if options is not None:
            validators = [lambda v: v in options]

        context['validators'] = validator_descriptions
        context['default'] = default

        # Set user input to default if confirm is disabled
        if self.app.pargs.confirm or default is None:
            user_input = None
        else:
            user_input = pre_validation_hook(default)

        while user_input is None or not all(validator(user_input) for validator in validators):
            context['user_input'] = user_input
            user_message = self.app.render(context, 'prompt.jinja2', out=None).strip()

            user_input = input_fn(user_message) or default

            if user_input is not None:
                user_input = pre_validation_hook(user_input)

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
        handlers = [BaseController, LineupController, StartprojectController]
        extensions = ['jinja2']
        output_handler = 'jinja2'
        template_module = 'fuse.templates'
        template_dirs = [os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')]
