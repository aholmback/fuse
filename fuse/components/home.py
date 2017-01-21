from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Home(Component):

    def project_home(self, payload, pinboard, prompt):

        self.context['project_home'] = prompt(
            'directory',
            text="Project Home",
            default=os.getcwd(),
            prefill=payload,
            pre_validation_hook=os.path.expanduser
        )

        pinboard.post('project_home', self.context['project_home'], handler_filter=lambda handler: handler is not self)

