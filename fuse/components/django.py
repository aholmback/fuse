from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
from fuse.utils import edit
from jinja2 import Template
import hashlib
import semantic_version
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
        """
        Expected structure:

        payload:
            comment: section comment
            identifier: section identifier (hash)
            entries
                key1: value1
                key2: value2
            
        """

        if 'settings_path' not in self.context:
            raise pinboard.PinNotProcessed

        this.context.setdefault('sections', {})
        this.context['sections'][payload['identifier']] = {
            'name': payload['name'],
            'entries': payload['entries'],
            }
            

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

    def project_slug(self, payload, pinboard, prompt):
        if not 'project_name' in self.context:
            raise pinboard.PinNotProcessed

        self.context['project_slug']  = prompt(
            text="Project Slug",
            default=payload or re.sub('[^0-9a-zA-Z]+', '_', self.context['project_name'].lower()),
            validators=['variable_name'],
        )

        pinboard.post(
                'project_slug',
                self.context['project_slug'],
                handler_filter=lambda handler: handler is not self,
                position=pinboard.UPNEXT,
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
        if not set(['project_template_root', 'project_slug', 'project_home']).issubset(self.context):
            raise pinboard.PinNotProcessed

        source = self.context['project_template_root'] + payload['source']
        content = urlopen(source).read().decode('utf-8')
        target = os.path.join(
            self.context['project_home'],
            payload['target'].format(project_slug=self.context['project_slug'])
        )

        self.context[context_identifier] = target

        self.files[target] = Template(content).render(
            project_name=self.context['project_slug'],
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







