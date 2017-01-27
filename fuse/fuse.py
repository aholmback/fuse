# unicode_literals messes up with Cement's type checking.
from __future__ import absolute_import, division, print_function
import os
import sys
import importlib
import inflection
from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults
from cement.core.controller import CementBaseController, expose
from cement.core.exc import CaughtSignal
from fuse import lineups, __version__
from fuse.utils import pinboards, json, prompting
from fuse.utils.files import FileFactory


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
            self.app.render({}, 'default_base.j2')


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
        for component_module_name, actions in lineup.items():

            # The class name of a component is always in CamelCase 
            # while module name is always in snake_case
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

            component_prompt = prompting.get_prompter(
                render=self.app.render,
                log=self.app.log,
                confirm=self.app.pargs.confirm
            )

            # Instantiates Component
            component = getattr(component_module, component_class_name)(
                name=component_module_name,
                log=self.app.log,
                render=self.app.render,
                prompt=component_prompt,
                post_pin=pinboard.post,
            )

            component.pre_setup()
            component.setup(pinboard, actions)
            component.post_setup()
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

        # Run pre-write actions
        for component in components:
            component.pre_write()

        # Write to disk
        for component in components:
            component.write()

        # Run post-write actions
        for component in components:
            component.post_write()


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
        self.app.render({}, 'default_lineup.j2')


    @expose(help="Inspect lineup")
    def inspect(self):
        lineup_name = self.app.pargs.lineup
        lineup = lineups.get(lineup_name)

        context = {
            'lineup': lineup,
            'lineup_name': lineup_name,
        }

        self.app.render(context, 'lineup.j2')

    @expose(help="List available lineups", aliases=['list'], aliases_only=True)
    def show_all(self):
        context = {
            'lineups': lineups.ls(),
        }
        self.app.render(context, 'lineups.j2')

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
