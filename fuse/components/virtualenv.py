from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Virtualenv(Component):

    component_type = 'developer_tool'

    def project_home(self, payload):
        self.context['project_home'] = payload

    def label(self, payload):
        self.context['label'] = self.prompt(
            text="Prompt for virtualenv",
            default=payload or "(env) ",
        )

    def python_distribution(self, payload):
        options=[
            ('2', '2.7+'),
            ('3', '3.5+'),
        ]

        self.context['python_distribution'] = self.prompt(
            text="Choose python distribution",
            default=payload,
            options=options,
        )

    def directory(self, payload):
        if not 'project_home' in self.context:
            raise self.PinNotProcessed

        def make_local_absolut(directory):
            absolut_dir = directory if directory[0] == '/' else os.path.join(self.context['project_home'], directory)
            return absolut_dir

        self.context['directory'] = directory = self.prompt(
            text="Directory",
            description="Local (to project home) or absolute directory",
            default=payload or 'env/',
            validators=['creatable_path','writable_directory','empty_directory'],
            pre_validation_hook=make_local_absolut,
        )

        if directory.startswith(self.context['project_home']):
            local_dir = directory.replace(self.context['project_home'], '').strip('/')
            self.post_pin('no_version_control', os.path.join(local_dir, '*'))

    def retrigger(self, payload):
        options = (
            (True, 'yes'),
            (False, 'no'),
        )

        response = self.prompt(
            text="Configure another instance of this component?",
            default=payload,
            options=options,
            )

        if response:
            for action in reversed(self.actions):
                self.post_pin(action, self.actions[action], position=pinboard.UPNEXT, handler_filter=lambda h: h is self)

            self.context_stash.append(self.context.copy())

    def post_write(self):
        self.context_stash.append(self.context.copy())
        for context in self.context_stash:
            try:
                os.makedirs(context['directory'])
            except OSError:
                pass

            command = "/usr/local/bin/virtualenv -p python{python_distribution} --quiet --prompt=\"{label}\" {directory}"
            command = command.format(**context)

            os.system(command)

