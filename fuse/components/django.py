from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
from fuse.utils import edit
from jinja2 import Template
import semantic_version
import hashlib
import re
import six
import os

if six.PY2:
    from urllib2 import urlopen, HTTPError
else:
    from urllib.request import urlopen
    from urllib.error import HTTPError

class Django(Component):

    component_type = 'framework'

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def global_setting(self, payload, pinboard, prompt):

        self.context.setdefault('components_settings', {})
        entry_identifier = ':'.join([payload['key'], payload['environment']])

        self.context['components_settings'][entry_identifier] = payload
            
    def project_name(self, payload, pinboard, prompt):
        self.context['project_name'] = prompt(
            text="Human-friendly project name",
            default=payload,
        )

        pinboard.post(
                'project_name',
                self.context['project_name'],
                handler_filter=lambda handler: handler is not self,
                position=pinboard.UPNEXT,
                )

    def project_identifier(self, payload, pinboard, prompt):
        if not 'project_name' in self.context:
            raise pinboard.PinNotProcessed

        self.context['project_identifier']  = prompt(
            text="Project Slug",
            default=payload or re.sub('[^0-9a-zA-Z]+', '_', self.context['project_name'].lower()),
            validators=['identifier'],
        )

        pinboard.post(
            'project_identifier',
            self.context['project_identifier'],
            handler_filter=lambda handler: handler is not self,
            position=pinboard.FIRST,
        )

    def environments(self, payload, pinboard, prompt):
        self.context['environments'] = prompt(
            text="Comma-separated list of environment identifiers",
            default=payload,
            validators=['identifier_list'],
            pre_validation_hook=lambda v: v.split(','),
        )

        pinboard.post(
            'environments',
            self.context['environments'],
            handler_filter=lambda handler: handler is not self,
            position=pinboard.FIRST,
        )

    def version(self, payload, pinboard, prompt):
        self.context['version'] = prompt(
            text="Version (semantic)",
            load='semantic_version',
            default=payload,
            validators=['semantic_version'],
        )

        pinboard.post('python_dependency', 'django==%s' % self.context['version'])


    def project_template_root(self, payload, pinboard, prompt):
        if not 'version' in self.context:
            raise pinboard.PinNotProcessed

        self.context['project_template_root'] = prompt(
            text="Project template root",
            default=payload,
            validators=['url'],
        ).format(version=self.context['version'])

    def settings_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt, 'settings_path')

    def init_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt, 'project_init_path')

    def urls_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt, 'root_urls_path')

    def wsgi_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt, 'wsgi_path')

    def manage_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt, 'manage_path')

    def add_file(self, payload, pinboard, prompt, context_identifier):
        if not set(['project_template_root', 'project_identifier', 'project_home']).issubset(self.context):
            raise pinboard.PinNotProcessed

        source = self.context['project_template_root'] + payload['source']
        content = urlopen(source).read().decode('utf-8')
        target = os.path.join(
            self.context['project_home'],
            payload['target'].format(project_identifier=self.context['project_identifier'])
        )

        self.context[context_identifier] = target

        self.files[target] = Template(content).render(
            project_name=self.context['project_identifier'],
            django_version=self.context['version'],
            docs_version='.'.join(self.context['version'].split('.')[:-1])
        )

    def pre_write(self):
        self.context['django_settings'] = self.files[self.context['settings_path']]

        self.files[self.context['settings_path']] = self.render(
                self.context,
                'django/settings.py.j2',
                out=None,
                )

