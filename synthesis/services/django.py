from synthesis.services import Service
import semantic_version
import re

class Django(Service):

    listens_to = [
        'current_working_directory',
    ]

    def configure(self):
        self.get_message('current_working_directory')

        project_name = self.prompt(
            'project_name',
            config_key='project_name_readable',
        )

        self.prompt(
            'project_slug',
            config_key='project_name',
            default=re.sub('[^0-9a-zA-Z]+', '*', project_name.lower()),
        )

        django_version = self.prompt(
            'semantic_version',
            config_key='django_version'
        )

        django_version = semantic_version.Version(django_version)
        self.config['docs_version'] = "%s.%s" % (django_version.major, django_version.minor)

