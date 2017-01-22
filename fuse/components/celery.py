from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Celery(Component):
    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def broker(self, payload, pinboard, prompt):
        self.context['broker'] = prompt(
                load='url',
                text="Broker (a.k.a. Transport) URI",
                default=payload,
                )

        self.context['environment'] = prompt(
                load='tier',
                )

        pinboard.post(
                'global_setting',
                {
                    'data': {'BROKER_URL': self.context['broker']},
                    'environment': self.context['environment'],
                    }
                )

        pinboard.post('service_dependency', self.context['broker'])

    def retrigger(self, payload, pinboard, prompt):
        response = prompt(load='retrigger')

        if response == 'yes':
            for action in reversed(self.actions):
                pinboard.post(action, self.actions[action], upnext=True, handler_filter=lambda h: h is self)

