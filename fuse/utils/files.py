import os
from fuse.utils.decorators import static_vars
from cement.core.exc import FrameworkError
import fuse

def get_files():
    return FileFactory.files

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
        self.render = None
        self.path = None
        self.context = None
        self.template = self.get_default_template()

        self.setup(*args, **kwargs)

    def setup(self, render=None, path=None, context=None, template=None, write=True):
        self.render = render or self.render
        self.path = path or self.path
        self.context = context or self.context
        self.template = template or self.template
        self.do_write = write or self.do_write

        try:
            self.content = self.render(self.context, self.template, out=None)
        except FrameworkError:
            fuse.log.error("couldn't load template `{template}` for file `{identifier}`".format(
                template=self.template,
                identifier=self.identifier,
            ))
            raise

        self.path = self.path.format(**self.context)

    def get_default_template(self):
        return os.path.join(self.component, '{file_name}.j2'.format(
            file_name=self.identifier,
            ))

    def write(self):
        if not self.do_write:
            return

        try:
            os.makedirs(os.path.dirname(self.path))
        except OSError:
            pass

        with open(self.path, 'w') as fp:
            fp.write(self.content)



