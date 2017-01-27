# unicode_literals messes up with Cement's type checking.
from __future__ import absolute_import, division, print_function
import os
from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults
from cement.core.controller import CementBaseController, expose
import fuse
from fuse.lineup import Lineup


defaults = init_defaults('fuse')
defaults['fuse']['debug'] = False

def run():
    with Fuse() as fuse_cement:
        fuse_cement.run()

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
            print("fuse {version}".format(version=fuse.__version__))
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

        fuse.log = self.app.log
        fuse.render = self.app.render
        fuse.settings = {
            'confirm': self.app.pargs.confirm,
        }

        lineup = Lineup(self.app.pargs.lineup)
        lineup.fuse()

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
