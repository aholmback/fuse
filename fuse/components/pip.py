from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Pip(Component):
    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def python_dependency(self, payload, pinboard, prompt):
        if 'requirements_target' not in self.context:
            raise pinboard.PinNotProcessed

        if 'python_dependencies' not in self.context:
            self.context['python_dependencies'] = []

        self.context['python_dependencies'].append(payload)

        self.files[self.context['requirements_target']] = '\n'.join(self.context['python_dependencies'])

    def requirements_target(self, payload, pinboard, prompt):
        if not 'project_home' in self.context:
            raise pinboard.PinNotProcessed

        self.context['requirements_target'] = prompt(
            'file',
            text="Target location for requirements",
            default=payload or os.path.join(self.context['project_home'], 'requirements.txt'),
            pre_validation_hook=lambda v: os.path.join(self.context['project_home'], v),
        )

        self.files[self.context['requirements_target']] = ''

