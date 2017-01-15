import os
import blinker
from synthesis.util.service import Service
from synthesis.cli import validators

class VirtualEnv(Service):
    order = 2

    form = (
        {
            'identifier': 'directory',
            'message': "Directory for virtualenv",
            'help_text': None,
            'default_value': 'env/',
            'validators': [validators.text],
            'retry': True,
        },
        {
            'identifier': 'prompt',
            'message': "Prompt for virtualenv",
            'help_text': None,
            'default_value': '(env) ',
            'validators': [validators.text],
            'retry': True,
        },
        {
            'identifier': 'python3',
            'message': "Python 3",
            'help_text': None,
            'default_value': '(env) ',
            'validators': [validators.text],
            'retry': True,
        },
    )

    form_sample_response = {
        'directory': 'env/',
        'prompt': '(env) ',
        'python3': 'y',
    }

    def register(self):
        blinker.signal('current_working_directory').connect(self.set_cwd)

    def configure(self, config, resources):
        self.config = config

    def dispatch(self):
        if not self.config['directory'][0] == '/':
            self.config['directory'] = os.path.join(self.cwd, self.config['directory'])

        if self.config['directory'].startswith(self.cwd):
            local_dir = self.config['directory'].replace(self.cwd, '')

            blinker.signal('no_version_control').send(
                self.name,
                pattern=os.path.join(local_dir, '*'),
            )

    def write(self):
        try:
            os.makedirs(self.config['directory'])
        except FileExistsError:
            pass

        os.system("virtualenv --quiet --prompt=\"%s\" %s" % (self.config['prompt'], self.config['directory']))

    def set_cwd(self, sender, directory):
        self.cwd = directory
