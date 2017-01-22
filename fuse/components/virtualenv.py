from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Virtualenv(Component):

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def prompt(self, payload, pinboard, prompt):
        self.context['prompt'] = prompt(
            load='text',
            text="Prompt for virtualenv",
            default=payload or "(env) ",
        )

    def python_distribution(self, payload, pinboard, prompt):
        self.context['python_distribution'] = prompt(
            load='python_distribution',
            default=payload,
        )

    def directory(self, payload, pinboard, prompt):
        if not 'project_home' in self.context:
            raise pinboard.PinNotProcessed

        def make_local_absolut(directory):
            absolut_dir = directory if directory[0] == '/' else os.path.join(self.context['project_home'], directory)
            return absolut_dir

        self.context['directory'] = directory = prompt(
            load='directory',
            text="Directory",
            description="Local (to project home) or absolute directory",
            default=payload or 'env/',
            pre_validation_hook=make_local_absolut,
        )

        if directory.startswith(self.context['project_home']):
            local_dir = directory.replace(self.context['project_home'], '').strip('/')
            pinboard.post('no_version_control', os.path.join(local_dir, '*'))

    def retrigger(self, payload, pinboard, prompt):
        response = prompt(load='retrigger')

        if response == 'yes':
            for action in reversed(self.actions):
                pinboard.post(action, self.actions[action], upnext=True, handler_filter=lambda h: h is self)

            self.context_stash.append(self.context.copy())

    def finalize(self):
        self.context_stash.append(self.context.copy())
        for context in self.context_stash:
            try:
                os.makedirs(context['directory'])
            except OSError:
                pass

            command = "/usr/local/bin/virtualenv -p python{python_distribution} --quiet --prompt=\"{prompt}\" {directory}"
            command = command.format(**context)

            os.system(command)

