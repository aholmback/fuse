from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
from fuse.utils.files import FileFactory
import os

class Git(Component):

    component_type = 'version_control_system'

    def project_home(self, payload):
        self.context['project_home'] = payload
        self.context['gitignore'] = os.path.join(self.context['project_home'], '.gitignore')

    def no_version_control(self, payload):
        if 'project_home' not in self.context:
            raise pinboard.PnNotProcessed

        if 'no_version_control' not in self.context:
            self.context['no_version_control'] = []

        self.context['no_version_control'].append(payload)

        FileFactory(
                component=self.name,
                identifier='gitignore',
                path=self.context['gitignore'],
                context=self.context,
                render=self.render,
                )




