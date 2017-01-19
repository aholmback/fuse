from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Virtualenv(Component):

    def instantiate(self):
        self.post_pin('virtualenv_python_major_version', None)
        self.post_pin('virtualenv_prompt', None)
        self.post_pin('virtualenv_directory', None)

    def current_working_directory(self, project_home):
        self.project_home = project_home

    def virtualenv_python_major_version(self, _):
        self.prompt(
            'python_major_version',
            text="Python Major Version",
            options=['2','3'],
            prefill=self.prefill['python_major_version']
        )

    def virtualenv_prompt(self, _):
        self.prompt(
            'prompt',
            text="Prompt for virtualenv",
            default="(env) "
        )

    def virtualenv_directory(self, _):

        def make_local_absolut(directory):
            absolut_dir = directory if directory[0] == '/' else os.path.join(self.project_home, directory)
            return absolut_dir

        directory = self.prompt(
            'directory',
            text="Directory",
            description="Local (to project home) or absolute directory",
            default='env/',
            pre_validation_hook=make_local_absolut,
        )

        self.config['directory'] = directory = make_local_absolut(directory)

        if directory.startswith(self.project_home):
            local_dir = directory.replace(self.project_home, '')
            self.send_message('no_version_control', payload=os.path.join(local_dir, '*'),
            )


    def write(self):
        try:
            os.makedirs(self.config['directory'])
        except OSError:
            pass

        command = "/usr/local/bin/virtualenv -p python{python_major_version} --quiet --prompt=\"{prompt}\" {directory}"
        command = command.format(**self.config)

        os.system(command)

