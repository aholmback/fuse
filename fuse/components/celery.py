from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Celery(Component):

    component_type = 'taskrunner'

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def project_slug(self, payload, pinboard, prompt):
        self.context['project_slug'] = payload

    def broker(self, payload, pinboard, prompt):
        self.context['broker'] = prompt(
                load='url',
                text="Broker (a.k.a. Transport) URI",
                default=payload,
                )

        pinboard.post('service_dependency', self.context['broker'])

    def version(self, payload, pinboard, prompt):
        self.context['version'] = prompt(
                load='semantic_version',
                text="Version",
                default=payload,
                )

        pinboard.post('python_dependency', 'celery==%s' % self.context['version'])

    def environment(self, payload, pinboard, prompt):
        if not 'broker' in self.context:
            raise pinboard.PinNotProcessed

        self.context['tier'] = prompt(
                load='tier',
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
                load='file',
                text="Location for celery.py",
                default=payload,
                pre_validation_hook=render_path,
                )

        self.files[self.context['setup_file']] = self.render(self.context, 'celery/celery.py.j2', out=None)


    def retrigger(self, payload, pinboard, prompt):
        response = prompt(
                load='retrigger',
                default=payload,
                )

        if response == 'yes':

            self.context_stash.append(self.context.copy())

            for action in reversed(self.actions):
                if action in ('setup_file',):
                    continue

                pinboard.post(
                        action,
                        self.actions[action],
                        upnext=True,
                        handler_filter=lambda h: h is self,
                        )


