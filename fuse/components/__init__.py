from __future__ import absolute_import, division, print_function, unicode_literals
from fuse.utils.files import FileFactory
from fuse.utils import prompting, pinboards
import fuse


class Component(object):
    def __init__(self, name):
        self.name = name
        pinboard = pinboards.get_pinboard('components')

        self.prompt = prompting.prompt
        self.post = pinboard.post
        self.context = {}
        self.context_stash = []
        self.files = FileFactory
        self.render = fuse.render
        self.log = fuse.log

        self.FIRST = pinboard.FIRST
        self.PinNotProcessed = pinboard.PinNotProcessed

    def pre_process(self):
        pass

    def post_process(self):
        pass
