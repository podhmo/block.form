# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)

def includeme(config):
    config.include(".validation")

import colander as co
from zope.interface import implementer
from .interfaces import IBlockSchema
Schema = implementer(IBlockSchema)(co.Schema)

class FieldProxy(object):
    def __init__(self, node):
        self.__dict__["node"] = node
    def __getattr__(self, k):
        return getattr(self.node, k)
    def __setattr__(self, k, v):
        self.__dict__[k] = v

class Form(object): #only support colander
    name = ""
    def __init__(self, schema, params=None, errors=None, configure=None):
        self.configure = configure
        self.schema = schema
        self.raw_values = params or {}
        self.errors = errors or {}

        self._field_nodes = []
        for c in self.schema.children:
            field = FieldProxy(c)
            setattr(self, c.name, field)
            self._field_nodes.append(field)

        if configure:
            configure(self)

    @property
    def fields(self):
        for c in self._field_nodes:
            v = self.raw_values.get(c.name, c.missing)
            if v is co.required:
                yield c, ""
            else:
                yield c, v

    def attach_errors(self, errors):
        self.errors = errors
