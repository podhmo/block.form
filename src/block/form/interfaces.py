# -*- coding:utf-8 -*-
from zope.interface import Interface

class ISequence(Interface):
    def append(x):
        pass

class IBlockSchema(Interface):
    pass

class ISchemaControl(Interface):
    def __call__(schema, params):
        pass

class IErrorControl(Interface):
    def __call__(data, name, exc, errors):
        pass

class IValidationBoundary(Interface):
    def validate(params, **extra):
        pass

class IValidationBoundaryFactory(Interface):
    def __call__(self, schema):
        pass

class IValidationRepository(Interface):
    pass
