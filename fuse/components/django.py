from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.components import Component
from fuse.utils.files import FileFactory

import six
import os
from jinja2 import Template

if six.PY2:
    from urllib2 import urlopen, HTTPError
else:
    from urllib.request import urlopen
    from urllib.error import HTTPError

class Django(Component):

    component_type = 'framework'

    def post_setup(self):
        self.project_template_root = 'https://raw.githubusercontent.com/django/django/{version}/django/conf/project_template/'


    def project_home(self, payload):
        self.context['project_home'] = payload

    def global_setting(self, payload):

        self.context.setdefault('components_settings', {})
        entry_identifier = ':'.join([payload['key'], payload['environment']])

        if not payload['environment'] == '*':
            path = os.path.join(
                    self.context['project_home'],
                    '.env.{environment}'.format(
                        environment=payload['environment'],
                        ),
                    )

            env_key = '{prefix}_{key}'.format(
                    prefix=self.context['project_identifier'].upper(),
                    key=payload['key'],
                    )

            self.context.setdefault(path, {})
            #self.files[path][env_key] = payload['value']

            payload['value'] = 'env(%s)' % env_key
            payload['type'] = 'function'


        self.context['components_settings'][entry_identifier] = payload
            
    def project_name(self, payload):
        self.context['project_name'] = self.prompt(
            text="Human-friendly project name",
            default=payload,
        )

        self.post_pin(
                'project_name',
                self.context['project_name'],
                handler_filter=lambda handler: handler is not self,
                position=1,
                )

    def project_identifier(self, payload):
        if not 'project_name' in self.context:
            raise self.PinNotProcessed

        self.context['project_identifier']  = self.prompt(
            text="Project Slug",
            default=payload or re.sub('[^0-9a-zA-Z]+', '_', self.context['project_name'].lower()),
            validators=['identifier'],
        )

        self.post_pin(
            'project_identifier',
            self.context['project_identifier'],
            handler_filter=lambda handler: handler is not self,
            position=0,
        )

    def project_environments(self, payload):
        self.context['project_environments'] = self.prompt(
            text="Comma-separated list of environment identifiers",
            default=payload,
            validators=['identifier_list'],
            pre_validation_hook=lambda v: v.split(','),
        )

        self.post_pin(
            'project_environments',
            self.context['project_environments'],
            handler_filter=lambda handler: handler is not self,
            position=0,
        )

    def version(self, payload):
        self.context['version'] = self.prompt(
            text="Version (semantic)",
            default=payload,
            validators=['semantic_version'],
        )

        self.post_pin('python_dependency', 'django==%s' % self.context['version'])


    def project_template_root(self, payload):
        if not 'version' in self.context:
            raise self.PinNotProcessed

        self.context['project_template_root'] = self.prompt(
            text="Project template root",
            default=payload,
            validators=['url'],
        ).format(version=self.context['version'])

    def settings_file(self, payload):
        self.add_file(payload, 'settings', 'project_name/settings.py-tpl')

    def init_file(self, payload):
        self.add_file(payload, 'project_init', 'project_name/__init__.py-tpl')

    def urls_file(self, payload):
        self.add_file(payload, 'urls', 'project_name/urls.py-tpl')

    def wsgi_file(self, payload):
        self.add_file(payload, 'wsgi', 'project_name/wsgi.py-tpl')

    def manage_file(self, payload):
        self.add_file(payload, 'manage', 'manage.py-tpl')

    def add_file(self, path, identifier, template):
        FileFactory(
                component=self.name,
                identifier=identifier,
                render=self.http_render,
                path=path,
                context=self.context,
                template=template,
                )

    def http_render(self, context, template, out):
        template = self.project_template_root + template
        template = template.format(**self.context)

        try:
            content = urlopen(template).read().decode('utf-8')
        except HTTPError:
            self.log.error("url `{url}` not found".format(url=template))
            raise

        return Template(content).render(
            project_name=self.context['project_identifier'],
            django_version=self.context['version'],
            docs_version='.'.join(self.context['version'].split('.')[:-1])
        )

