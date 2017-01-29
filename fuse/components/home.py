from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Home(Component):

    component_type = 'global_parameter'

    def project_home(self, payload):

        self.context['project_home'] = self.prompt(
            text="Project Home",
            default=payload or os.getcwd(),
            validators=['creatable_path','writable_directory','empty_directory'],
            pre_validation_hook=os.path.expanduser,
        )

        self.post(
                action='project_home',
                payload=self.context['project_home'],
                visitor_filter=lambda handler: handler is not self,
                position=self.FIRST,
                )

