from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Virtualenv(Component):

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def prompt(self, payload, pinboard, prompt):
        self.context['prompt'] = prompt(
            'project_name',
            text="Prompt for virtualenv",
            default="(env) ",
            prefill=payload,
        )

    def python_distribution(self, payload, pinboard, prompt):
        self.context['python_distribution'] = prompt(
            'python_distribution',
            prefill=payload,
        )

    def directory(self, payload, pinboard, prompt):
        if not 'project_home' in self.context:
            raise pinboard.PinNotProcessed

        def make_local_absolut(directory):
            absolut_dir = directory if directory[0] == '/' else os.path.join(self.context['project_home'], directory)
            return absolut_dir

        self.context['directory'] = directory = prompt(
            'directory',
            text="Directory",
            description="Local (to project home) or absolute directory",
            default='env/',
            pre_validation_hook=make_local_absolut,
            prefill=payload,
        )

        if directory.startswith(self.context['project_home']):
            local_dir = directory.replace(self.context['project_home'], '').strip('/')
            pinboard.post('no_version_control', os.path.join(local_dir, '*'))

    def finalize(self):
        try:
            os.makedirs(self.context['directory'])
        except OSError:
            pass

        command = "/usr/local/bin/virtualenv -p python{python_distribution} --quiet --prompt=\"{prompt}\" {directory}"
        command = command.format(**self.context)

        os.system(command)

