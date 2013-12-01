# -*- coding:utf-8 -*-
from zope.interface import providedBy, provider
from collections import defaultdict
from ..interfaces import(
    ISchemaControl,
    IErrorControl,
    IValidationRepository,
    IValidationBoundaryFactory,
    ISequence
)

class ValidationError(Exception):
    @property
    def errors(self):
        return self.args[0]

class ValidationBoundary(object):
    def __init__(self, schema_control, error_control, schema, validation_queue):
        self.schema = schema
        self.schema_control = schema_control
        self.error_control = error_control
        self.validation_queue = validation_queue
        self.individual_validations = []
        self.extra = {}

    def add(self, name, validation, pick_extra=None):
        self.individual_validations.append((name, validation, pick_extra))

    def get_iterator(self, extra):
        kwargs = {}
        kwargs.update(self.extra)
        kwargs.update(extra)
        iterator = self.validation_queue(kwargs)

        for name, validation, pick_extra in self.individual_validations:
            iterator.add(name, validation, pick_extra=pick_extra)
        return iterator

    def validate(self, params, **extra):
        qualified_data = self.schema_control(self.schema, params)
        errors = defaultdict(list)
        iterator = self.get_iterator(extra)

        for name, validation in iterator:
            try:
                validation(qualified_data)
            except Exception as e:
                self.error_control(qualified_data, name, e, errors)
        return self.error_control.finish(qualified_data, errors)


def add_block_directive(config, name, fn):
    config.add_directive("block_{}".format(name), fn)


def includeme(config):
    add_block_directive(config, "set_schema_control", set_schema_control)
    add_block_directive(config, "set_error_control", set_error_control)
    add_block_directive(config, "set_validation_repository", set_validation_repository)
    add_block_directive(config, "add_error_mapping", add_error_mapping)

    from .core import ColanderSchemaControl
    config.block_set_schema_control(ColanderSchemaControl())

    from pyramid.exceptions import ConfigurationError
    def check__dependent_components(config):
        control = config.registry.queryUtility(IErrorControl)
        if control is None:
            raise ConfigurationError("forgetting:: calling config.block_set_error_control ?\n (please autocommit option is false)")

        queue = config.registry.adapters.lookup1(IErrorControl, ISequence)
        if queue:
            for mapping, strict in queue:
                control.update_mapping(mapping, strict=strict)

        repository = config.registry.queryUtility(IValidationRepository)
        if repository is None:
            raise ConfigurationError("forgeting:: calling config.block_set_validation_repository ?\n (please autocommit option is false)")
    config.action(None, check__dependent_components, args=(config, ), order=9999)


## use definition phase
def validation_repository_factory(QueueClass=None):
    from .core import ValidationRepository
    return ValidationRepository(QueueClass=QueueClass)


## use configugration phase
def set_schema_control(config, control):
    config.registry.registerUtility(config.maybe_dotted(control), ISchemaControl)

def set_error_control(config, control):
    config.registry.registerUtility(config.maybe_dotted(control), IErrorControl)

def add_error_mapping(config, mapping, strict=True):
    queue = config.registry.adapters.lookup1(IErrorControl, ISequence)
    if queue is None:
        queue = []
        config.registry.adapters.register([IErrorControl], ISequence, "", queue)
    queue.append((mapping, strict))


def set_validation_repository(config, repository):
    config.registry.registerUtility(config.maybe_dotted(repository), IValidationRepository)

def register_validation(registry, required, schema, name):
    schema_control = registry.getUtility(ISchemaControl)
    error_control = registry.getUtility(IErrorControl)
    schema_class = schema_control.get_class(schema)
    repository = registry.getUtility(IValidationRepository)
    def create_validation(schema):
        return ValidationBoundary(schema_control,
                                  error_control,
                                  schema,
                                  repository[schema_class]
        )
    create_validation.__name__ = "validation_for_{schema!r}".format(schema=schema)
    registry.adapters.register(required, IValidationBoundaryFactory, name, create_validation)
    return create_validation


## use runtime phase .. api
def get_validation(request, schema, name=""):
    registry = request.registry
    required = [providedBy(schema), ISchemaControl, IErrorControl]
    factory = registry.adapters.lookup(required, IValidationBoundaryFactory, name=name)
    if factory is None:
        ## speedup
        factory = register_validation(registry, required, schema, name)
    return factory(schema)

