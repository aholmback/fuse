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

    component_type = 'framework'

    def project_home(self, payload, pinboard, prompt):
        self.context['project_home'] = payload

    def global_setting(self, payload, pinboard, prompt):
        if 'settings_path_prefix' not in self.context:
            raise pinboard.PinNotProcessed

        target = '{settings_path_prefix}/{tier}.py'.format(
                settings_path_prefix=self.context['settings_path_prefix'],
                tier=payload['tier'],
                )

        settings_header = '"""\nSettings for tier `{tier}`\n"""\n\n'.format(tier=payload['tier'])
        self.files.setdefault(target, settings_header)

        section_identifier = "## Section {component_type}\n".format(
                component_type=payload['component_type'].replace('_', ' ').title()
                )

        if section_identifier not in self.files[target]:
            self.files[target] += section_identifier

        self.files[target] = self.files[target].replace(
                section_identifier, 
                section_identifier + "\n{settings_to_add}",
                )

        settings_to_add = ['# {description}'.format(description=payload['description'])]

        for key in payload['data']:
            settings_to_add.append("{key}: {value}".format(
                key=key,
                value=payload['data'][key],
                ))

        self.files[target] = self.files[target].format(
                settings_to_add='\n'.join(settings_to_add),
                )


    def project_name(self, payload, pinboard, prompt):
        self.context['project_name'] = prompt(
            load='text',
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
            load='project_slug',
            default=payload or re.sub('[^0-9a-zA-Z]+', '_', self.context['project_name'].lower()),
        )

        pinboard.post(
                'project_slug',
                self.context['project_slug'],
                handler_filter=lambda handler: handler is not self,
                position=pinboard.UPNEXT,
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
        target = os.path.join(
            self.context['project_home'],
            payload['target'].format(project_slug=self.context['project_slug'])
        )

        self.context['settings_path_prefix'] = os.path.dirname(target) + '/'

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

