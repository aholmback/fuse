from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Dotenv(Component):

    component_type = 'environment_variable_shim'

    def project_home(self, payload):
        self.context['project_home'] = payload

    def environment_variable(self, payload):
        """
        Expected structure:
        payload = {
            'key': Environment variable name
            'value': Environment variable value
            'environment': Deployment environment
            }
        """

        if 'dotenv_directory' not in self.context:
            raise self.PinNotProcessed

        self.context.setdefault(payload['environment'], {
            'name': payload['environment'],
            'variables': {},
        })

        # Look at all those words.. :-/
        self.context[payload['environment']]['variables'][payload['key']] = payload['value']
        self.context[payload['environment']]['dotenv_directory'] = self.context['dotenv_directory']
        self.context[payload['environment']]['environment'] = payload['environment']


        self.files(
            component=self.name,
            identifier=payload['environment'],
            render=self.render,
            path='{dotenv_directory}/.env.{environment}',
            context=self.context[payload['environment']],
            template='dotenv/.env.j2',
        )


    def dotenv_directory(self, payload):
        if 'project_home' not in self.context:
            raise self.PinNotProcessed

        payload = payload.format(**self.context)

        self.context['dotenv_directory'] = self.prompt(
            text="Directory for dotenv source files",
            default=payload or self.context['project_home'],
            validators=['creatable_path','writable_directory','empty_directory'],
            pre_validation_hook=os.path.expanduser,
        )

        self.post(
                action='dotenv_directory',
                payload=self.context['dotenv_directory'],
                visitor_filter=lambda handler: handler is not self,
                position=self.FIRST,
                )

