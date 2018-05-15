import os
import time
import bge


class FunctionList(list):
    def fire(self, *args, **kwargs):
        for funct in self:
            funct(*args, **kwargs)

class NamedList(list):
    def __getitem__(self, name):
        return next(i for i in self if i.name == name)


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
