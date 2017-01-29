from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Pip(Component):

    component_type = 'python_dependency_installer'

    def project_home(self, payload):
        self.context['project_home'] = payload

    def python_dependency(self, payload):
        if 'requirements_target' not in self.context:
            raise self.PinNotProcessed

        if 'python_dependencies' not in self.context:
            self.context['python_dependencies'] = []

        self.context['python_dependencies'].append(payload)

        self.files(
                component=self.name,
                identifier='requirements.txt',
                path=self.context['requirements_target'],
                context=self.context,
                render=self.render,
                )


    def requirements_target(self, payload):
        if not 'project_home' in self.context:
            raise self.PinNotProcessed

        self.context['requirements_target'] = self.prompt(
            text="Target location for requirements",
            default=payload or os.path.join(self.context['project_home'], 'requirements.txt'),
            pre_validation_hook=lambda v: os.path.join(self.context['project_home'], v),
            validators=['available_path','creatable_path'],
        )

