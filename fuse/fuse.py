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
                ['lineup'],
                {
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


class Fuse(CementApp):
    class Meta:
        label = 'fuse'
        config_defaults = defaults
        base_controller = 'base'
        handlers = [BaseController, StartprojectController]
        extensions = ['jinja2']
        output_handler = 'jinja2'
        template_module = 'fuse.templates'
        template_dirs = [os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')]
