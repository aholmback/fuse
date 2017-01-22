from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
from jinja2 import Template
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

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def project_name(self, payload, pinboard, prompt):
        self.context['project_name'] = prompt(
            load='text',
            text="Human-friendly project name:",
            default=payload,
        )

    def project_slug(self, payload, pinboard, prompt):
        if not 'project_name' in self.context:
            raise pinboard.PinNotProcessed

        self.context['project_slug']  = prompt(
            load='project_slug',
            default=payload or re.sub('[^0-9a-zA-Z]+', '_', self.context['project_name'].lower()),
        )

    def version(self, payload, pinboard, prompt):
        self.context['version'] = prompt(
            load='semantic_version',
            default=payload,
        )

        pinboard.post('python_dependency', 'django==%s' % self.context['version'])

    def project_template_root(self, payload, pinboard, prompt):
        if not 'version' in self.context:
            raise pinboard.PinNotProcessed

        self.context['project_template_root'] = prompt(
            load='url',
            text="Project template root",
            default=payload,
        ).format(version=self.context['version'])

    def settings_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt)

    def init_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt)

    def urls_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt)

    def wsgi_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt)

    def manage_file(self, payload, pinboard, prompt):
        self.add_file(payload, pinboard, prompt)

    def add_file(self, payload, pinboard, prompt):
        if not set(['project_template_root', 'project_slug', 'project_home']).issubset(self.context):
            raise pinboard.PinNotProcessed

        source = self.context['project_template_root'] + payload['source']
        content = urlopen(source).read().decode('utf-8')
        target = os.path.join(
            self.context['project_home'],
            payload['target'].format(project_slug=self.context['project_slug'])
        )

        self.files[target] = Template(content).render(
            project_name=self.context['project_slug'],
            django_version=self.context['version'],
            docs_version='.'.join(self.context['version'].split('.')[:-1])
        )

