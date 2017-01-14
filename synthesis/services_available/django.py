from synthesis.cli import validators
from synthesis.util.service import Service
import blinker
import semantic_version

class Django(Service):

    order = 1

    form = (
        {
            'identifier': 'project_name_readable',
            'message': "Project Name",
            'help_text': None,
            'default_value': None,
            'validators': [validators.text],
            'retry': True,
        },
        {
            'identifier': 'project_name',
            'message': "Project Slug",
            'help_text': None,
            'default_value': "{{ project_name.lower()|replace(' ', '_')|replace('-', '_') }}",
            'validators': [validators.variable_name],
            'retry': True,
        },
        {
            'identifier': 'django_version',
            'message': "Django Version",
            'help_text': None,
            'default_value': None,
            'validators': [validators.semantic_version],
            'retry': True,
        },
    )

    form_sample_response = {
        'project_name_readable': "Sample Project",
        'project_name': 'sample_project',
        'django_version': '1.10.5',
    }

    def register(self):
        blinker.signal('current_working_directory').connect(self.set_cwd)

    def configure(self, config):
        django_version = semantic_version.Version(config['django_version'])
        self.config = config
        self.config['docs_version'] = "%s.%s" % (django_version.major, django_version.minor)
        self.load_resources()

    def dispatch(self):
        pass

    def write(self):
        self.write_resources(self.cwd)

    def set_cwd(self, sender, directory):
        self.cwd = directory

