from synthesis.services import Service
import semantic_version
import re

class Django(Service):

    listens_to = [
        'current_working_directory',
    ]

    def collect(self):
        self.get_message('current_working_directory')

        self.config['project_phrase'] = self.prompt('project_name')

        self.config['project_name'] = self.prompt(
            'project_slug',
            default=re.sub('[^0-9a-zA-Z]+', '_', self.config['project_phrase'].lower()),
        )

        django_version = self.prompt('semantic_version')

        django_version = semantic_version.Version(django_version)
        self.config['docs_version'] = "%s.%s" % (django_version.major, django_version.minor)
        self.config['django_version'] = django_version

