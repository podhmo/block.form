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
    def __init__(self, schema, name, node):
        self.__dict__["schema"] = schema
        self.__dict__["name"] = name
        self.__dict__["node"] = node
        self.__dict__["is_changed"] = False

    def __getattr__(self, k):
        return getattr(self.node, k)

    def __setattr__(self, k, v):
        if not self.is_changed:
            self.__dict__["is_changed"] = True
            new_node = self.__dict__["node"].clone()
            self.__dict__["node"] = new_node
            self.schema[self.name] = new_node
        setattr(self.node, k, v)


class Form(object): #only support colander, nesting structure is not supported.
    name = ""
    def __init__(self, schema, params=None, errors=None, action="#", configure=None):
        self.configure = configure
        self.schema = schema
        self.raw_values = params or {}
        self.errors = errors or {}
        self.action = action

        self._field_nodes = []
        for c in self.schema.children:
            field = FieldProxy(schema, c.name, c)
            setattr(self, c.name, field)
            self._field_nodes.append(field)

        if configure:
            configure(self)

    @property
    def fields(self):
        serialized = self.schema.serialize(self.raw_values)
        for c in self._field_nodes:
            yield c, serialized.get(c.name, c.default)

    def attach_errors(self, errors):
        self.errors = errors
