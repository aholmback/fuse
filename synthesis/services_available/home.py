import os
import blinker
from synthesis.cli import validators
from synthesis.util.service import Service

class Home(Service):

    order = 0

    form = (
        {
            'identifier': 'directory',
            'message': "Project Home",
            'help_text': None,
            'default_value': os.getcwd(),
            'validators': [
                validators.creatable_directory,
                validators.writable_directory,
                validators.empty_directory,
            ],
            'retry': True,
            'post_process': lambda v: os.path.expanduser(v),
        },
    )

    form_sample_response = {
        'directory': '/Users/aholmback/test',
    }

    def register(self):
        blinker.signal('current_working_directory', doc="String representing the path of the cwd")

    def configure(self, config):
        self.directory = config['directory']

    def dispatch(self):
        blinker.signal('current_working_directory').send(
            self.name,
            directory=self.directory,
        )

    def write(self):
        self.write_resources(self.directory)
