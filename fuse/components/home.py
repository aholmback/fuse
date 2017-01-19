from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
import os

class Home(Component):

    def instantiate(self):
        self.post_pin('home_directory', None)

    def home_directory(self, _):
        directory = self.prompt(
            'directory',
            text="Project Home",
            default=os.getcwd(),
            pre_validation_hook=os.path.expanduser
        )

        self.post_pin('current_working_directory', directory)

