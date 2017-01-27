from __future__ import absolute_import, division, print_function, unicode_literals
import os
import fuse
from fuse.utils import pinboards
from fuse.utils.prompting import prompt

pinboard = pinboards.get_pinboard('components')
component_type = 'developer_tool'
context = {}

def project_home(payload):
    context['project_home'] = payload

def label(payload):
    context['label'] = prompt(
        text="Prompt for virtualenv",
        default=payload or "(env) ",
    )

def python_distribution(payload):
    options=[
        ('2', '2.7+'),
        ('3', '3.5+'),
    ]

    context['python_distribution'] = prompt(
        text="Choose python distribution",
        default=payload,
        options=options,
    )

def directory(payload):
    if not 'project_home' in context:
        raise PinNotProcessed

    def make_local_absolut(directory):
        absolut_dir = directory if directory[0] == '/' else os.path.join(context['project_home'], directory)
        return absolut_dir

    context['directory'] = directory = prompt(
        text="Directory",
        description="Local (to project home) or absolute directory",
        default=payload or 'env/',
        validators=['creatable_path','writable_directory','empty_directory'],
        pre_validation_hook=make_local_absolut,
    )

    if directory.startswith(context['project_home']):
        local_dir = directory.replace(context['project_home'], '').strip('/')
        pinboard.post('no_version_control', os.path.join(local_dir, '*'))

def retrigger(payload):
    options = (
        (True, 'yes'),
        (False, 'no'),
    )

    response = prompt(
        text="Configure another instance of this component?",
        default=payload,
        options=options,
        )

    if response:
        for action in reversed(actions):
            post_pin(action, actions[action], position=pinboard.UPNEXT, visitor_filter=lambda visitor: visitor == __name__)

        self.context_stash.append(self.context.copy())

def post_write(self):
    self.context_stash.append(self.context.copy())
    for context in self.context_stash:
        try:
            os.makedirs(context['directory'])
        except OSError:
            pass

        command = "/usr/local/bin/virtualenv -p python{python_distribution} --quiet --prompt=\"{label}\" {directory}"
        command = command.format(**context)

        os.system(command)

