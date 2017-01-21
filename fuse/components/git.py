from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Git(Component):

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload
        self.context['gitignore'] = os.path.join(self.context['project_home'], '.gitignore')

    def no_version_control(self, payload, pinboard, prompt):
        if 'project_home' not in self.context:
            raise pinboard.PnNotProcessed

        if 'no_version_control' not in self.context:
            self.context['no_version_control'] = []

        self.context['no_version_control'].append(payload)
        self.files[self.context['gitignore']] = '\n'.join(self.context['no_version_control'])



