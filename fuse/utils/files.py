import os
from fuse.utils.decorators import static_vars

@static_vars(files={})
def FileFactory(component, identifier, *args, **kwargs):

    if identifier not in FileFactory.files:
        FileFactory.files[identifier] = File(component, identifier, *args, **kwargs)
    else:
        FileFactory.files[identifier].setup(*args, **kwargs)

    return FileFactory.files[identifier]

class File(object):

    def __init__(self, component, identifier, *args, **kwargs):
        self.component = component
        self.identifier = identifier
        self.setup(*args, **kwargs)

    def setup(self, render, path, context, template=None):
        self.render = render
        self.path = path
        self.context = context
        self.template = template

    def get_default_template(self):
        return os.path.join(self.component, '{file_name}.j2'.format(
            file_name=self.identifier,
            ))

    def write(self):
        template = self.template or self.get_default_template()
        path = self.path.format(**self.context)
        content = self.render(self.context, template, out=None)


        try:
            os.makedirs(os.path.dirname(path))
        except OSError:
            pass

        with open(path, 'w') as fp:
            fp.write(content)



