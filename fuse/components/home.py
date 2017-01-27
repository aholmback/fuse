from __future__ import absolute_import, division, print_function, unicode_literals
import os
import fuse
from fuse.utils import pinboards
from fuse.utils.prompting import prompt

pinboard = pinboards.get_pinboard('components')

component_type = 'global_parameter'
context = {}

def project_home(payload):

    context['project_home'] = prompt(
        text="Project Home",
        default=payload or os.getcwd(),
        validators=['creatable_path','writable_directory','empty_directory'],
        pre_validation_hook=os.path.expanduser,
    )

    pinboard.post(
        action='project_home',
        payload=context['project_home'],
        visitor_filter=lambda visitor: not visitor == __name__,
        position=0,
        )

