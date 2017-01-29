from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component

class Celery(Component):

    component_type = 'taskrunner'

    def project_home(self, payload):
        self.context['project_home'] = payload

    def project_identifier(self, payload):
        self.context['project_identifier'] = payload

    def broker(self, payload):
        if not 'environment' in self.context:
            raise self.PinNotProcessed

        self.context['broker'] = self.prompt(
                text="Broker (a.k.a. Transport) URI",
                default=payload,
                validators=['url'],
                )

        self.post('service_dependency', self.context['broker'])

        payload = {
            'key': 'CELERY_BROKER_URL',
            'value': self.context['broker'],
            'type': 'string',
            'component_type': self.component_type,
            'component_name': self.name,
            'description': "Transport protocol for message routing",
            'environment': self.context['environment'],
        }

        self.post('global_setting', payload)

    def project_environments(self, payload):
        self.context['project_environments'] = payload

    def environment(self, payload):
        if not 'project_environments' in self.context:
            raise self.PinNotProcessed

        options = tuple(zip(
            self.context['project_environments'] + ['*'],
            self.context['project_environments'] + ["This is a core setting for all environments"],
            ))

        self.context['environment'] = self.prompt(
            text="Which environment should this setting be applied to?",
            default=payload,
            options=options,
            )

    def version(self, payload):
        self.context['version'] = self.prompt(
                text="Version",
                default=payload,
                validators=['semantic_version'],
                )

        self.post('python_dependency', 'celery==%s' % self.context['version'])

    def setup_file(self, payload):
        if not set(['project_identifier', 'project_home']).issubset(self.context):
            raise self.PinNotProcessed

        def render_path(value):
            return value.format(**self.context)

        self.context['setup_file'] = self.prompt(
                text="Location for celery.py",
                default=payload,
                validators=['available_path', 'creatable_path'],
                pre_validation_hook=render_path,
                )

        self.files(
                component=self.name,
                identifier='celery.py',
                path=self.context['setup_file'],
                context=self.context,
                render=self.render,
                )


