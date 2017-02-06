from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Pip(Component):

    component_type = 'python_dependency_installer'

    def project_home(self, payload):
        self.context['project_home'] = payload

    def python_dependency(self, payload):
        if 'requirements_path' not in self.context:
            raise self.PinNotProcessed

        if 'python_dependencies' not in self.context:
            self.context['python_dependencies'] = []

        self.context['python_dependencies'].append(payload)

        self.files(
                component=self.name,
                identifier='requirements.txt',
                path=self.context['requirements_path'],
                context=self.context,
                render=self.render,
                )

    def requirements_path(self, payload):
        if not 'project_home' in self.context:
            raise self.PinNotProcessed

        self.context['requirements_path'] = self.prompt(
            text="Target location for requirements",
            default=payload or os.path.join(self.context['project_home'], 'requirements.txt'),
            pre_validation_hook=lambda v: v.format(**self.context),
            validators=['available_path','creatable_path'],
        )

        self.post(
            'requirements_path',
            self.context['requirements_path'],
            visitor_filter=lambda visitor: visitor is not self,
        )

