from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Celery(Component):

    component_type = 'taskrunner'

    def deployment_tiers(self, payload, pinboard, prompt):
        self.context['deployment_tiers'] = payload

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def project_slug(self, payload, pinboard, prompt):
        self.context['project_slug'] = payload

    def broker(self, payload, pinboard, prompt):
        self.context['broker'] = prompt(
                text="Broker (a.k.a. Transport) URI",
                default=payload,
                validators=['url'],
                )

        pinboard.post('service_dependency', self.context['broker'])

    def version(self, payload, pinboard, prompt):
        self.context['version'] = prompt(
                text="Version",
                default=payload,
                validators=['semantic_version'],
                )

        pinboard.post('python_dependency', 'celery==%s' % self.context['version'])

    def environment(self, payload, pinboard, prompt):
        if not 'broker' in self.context:
            raise pinboard.PinNotProcessed

        self.context['tier'] = prompt(
                default=payload,
                )

        pinboard.post(
                'global_setting',
                {
                    'description': "Transport protocol for message routing",
                    'data': {'CELERY_BROKER_URL': "'%s'" % self.context['broker']},
                    'tier': self.context['tier'],
                    'component_type': self.component_type,
                    }
                )


    def setup_file(self, payload, pinboard, prompt):
        if not set(['project_slug', 'project_home']).issubset(self.context):
            raise pinboard.PinNotProcessed

        def render_path(value):
            return value.format(**self.context)

        self.context['setup_file'] = prompt(
                text="Location for celery.py",
                default=payload,
                validators=['available_path', 'creatable_path'],
                pre_validation_hook=render_path,
                )

        self.files[self.context['setup_file']] = self.render(self.context, 'celery/celery.py.j2', out=None)


    def retrigger(self, payload, pinboard, prompt):
        response = prompt(
                text="Configure another instance of this component?",
                default=payload,
                options: ['y','n']
                )

        if response == 'y':

            self.context_stash.append(self.context.copy())

            for action in reversed(self.actions):
                if action in ('setup_file',):
                    continue

                pinboard.post(
                        action,
                        self.actions[action],
                        position=pinboard.UPNEXT,
                        handler_filter=lambda h: h is self,
                        )


