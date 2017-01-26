from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
from fuse.utils.files import FileFactory
import os

class Celery(Component):

    component_type = 'taskrunner'

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def project_identifier(self, payload, pinboard, prompt):
        self.context['project_identifier'] = payload

    def broker(self, payload, pinboard, prompt):
        if not 'environment' in self.context:
            raise pinboard.PinNotProcessed

        self.context['broker'] = prompt(
                text="Broker (a.k.a. Transport) URI",
                default=payload,
                validators=['url'],
                )

        pinboard.post('service_dependency', self.context['broker'])

        payload = {
            'key': 'CELERY_BROKER_URL',
            'value': self.context['broker'],
            'type': 'string',
            'component_type': self.component_type,
            'component_name': self.name,
            'description': "Transport protocol for message routing",
            'environment': self.context['environment'],
        }

        pinboard.post('global_setting', payload)

    def project_environments(self, payload, pinboard, prompt):
        self.context['project_environments'] = payload

    def environment(self, payload, pinboard, prompt):
        if not 'project_environments' in self.context:
            raise pinboard.PinNotProcessed

        options = tuple(zip(
            self.context['project_environments'] + ['*'],
            self.context['project_environments'] + ["This is a core setting for all environments"],
            ))

        self.context['environment'] = prompt(
            text="Which environment should this setting be applied to?",
            default=payload,
            options=options,
            )

    def version(self, payload, pinboard, prompt):
        self.context['version'] = prompt(
                text="Version",
                default=payload,
                validators=['semantic_version'],
                )

        pinboard.post('python_dependency', 'celery==%s' % self.context['version'])

    def setup_file(self, payload, pinboard, prompt):
        if not set(['project_identifier', 'project_home']).issubset(self.context):
            raise pinboard.PinNotProcessed

        def render_path(value):
            return value.format(**self.context)

        self.context['setup_file'] = prompt(
                text="Location for celery.py",
                default=payload,
                validators=['available_path', 'creatable_path'],
                pre_validation_hook=render_path,
                )

        FileFactory(
                component=self.name,
                identifier='celery.py',
                path=self.context['setup_file'],
                context=self.context,
                render=self.render,
                )


