# -*- coding:utf-8 -*-
from zope.interface.interface import InterfaceClass
from zope.interface import (
    providedBy,
    provider
)
import logging
logger = logging.getLogger(__name__)

from ..interfaces import(
    IErrorControl,
    IValidationRepository,
    IValidationBoundaryFactory,
    ISequence,
    IBlockSchema
)

class ValidationError(Exception):
    @property
    def errors(self):
        return self.args[0]


def add_block_directive(config, name, fn):
    config.add_directive("block_{}".format(name), fn)


def includeme(config):
    add_block_directive(config, "set_error_control", set_error_control)
    add_block_directive(config, "set_validation_repository", set_validation_repository)
    add_block_directive(config, "add_error_mapping", add_error_mapping)

    def check__dependent_components(config):
        RegisterSchemaValidation(config).register()
    config.action(None, check__dependent_components, args=(config, ), order=9999)


## use definition phase
def validation_repository_factory(QueueClass=None):
    from .core import ValidationRepository
    return ValidationRepository(QueueClass=QueueClass)


## use configugration phase
def set_error_control(config, control):
    config.registry.registerUtility(config.maybe_dotted(control), IErrorControl)

def add_error_mapping(config, mapping, strict=True):
    queue = config.registry.adapters.lookup1(IErrorControl, ISequence)
    if queue is None:
        queue = []
        config.registry.adapters.register([IErrorControl], ISequence, "", queue)
    queue.append((mapping, strict))


def set_validation_repository(config, repository, overwrite=False):
    repository = config.maybe_dotted(repository)
    if config.registry.queryUtility(repository, IValidationRepository):
        if not overwrite:
            from pyramid.exceptions import ConfigurationError
            raise ConfigurationError("validation repository is already set.")
        else:
            logger.warning("validation repository is already set. overwrite.")
    config.registry.registerUtility(repository, IValidationRepository)


## use runtime phase .. api
def register_validation(registry, required, name):
    from .core import ValidationBoundary
    error_control = registry.getUtility(IErrorControl)
    repository = registry.getUtility(IValidationRepository)

    @provider(IValidationBoundaryFactory)
    def factory(required):
        queue = repository[required]
        return ValidationBoundary(error_control, queue)
    registry.adapters.register(required, IValidationBoundaryFactory, name, factory)
    return factory


def normalize_provided1(provided):
    if isinstance(provided, InterfaceClass):
        return provided
    else:
        return providedBy(provided)

def get_validation(request, provided, name=""):
    iface = normalize_provided1(provided)
    registry = request.registry
    factory = registry.adapters.lookup([iface], IValidationBoundaryFactory, name=name)
    if factory is None:
        ## speedup
        factory = register_validation(registry, iface, name)
    return factory(provided)


## uggg.
class RegisterSchemaValidation(object):
    def __init__(self, config):
        self.config = config

    def register(self):
        control = self.prepare_for_control()
        repository = self.prepare_for_repository(control)
        self.prepare_for_schema(control, repository)

    def prepare_for_control(self):
        from pyramid.exceptions import ConfigurationError
        control = self.config.registry.queryUtility(IErrorControl)
        if control is None:
            raise ConfigurationError("""
            forgetting:: calling config.block_set_error_control ?
            (please autocommit option is false)""")
        return control

    def prepare_for_repository(self, control):
        from pyramid.exceptions import ConfigurationError
        queue = self.config.registry.adapters.lookup1(IErrorControl, ISequence)
        if queue:
            for mapping, strict in queue:
                control.update_mapping(mapping, strict=strict)

        repository = self.config.registry.queryUtility(IValidationRepository)
        if repository is None:
            raise ConfigurationError("""
            forgeting:: calling config.block_set_validation_repository ?
            (please autocommit option is false)""")
        return repository

    def prepare_for_schema(self, error_control, repository):
        from .core import (
            ValidationBoundary,
            PreparedBoundary
        )
        registry = self.config.registry
        def next_boundary(schema, individual_validations, extra):
            queue = repository[schema.__class__] #hmm.
            return ValidationBoundary(error_control, queue,
                                      individual_validations=individual_validations,
                                      extra=extra)

        @provider(IValidationBoundaryFactory)
        def factory(schema):
            return PreparedBoundary(schema, next_boundary)
        registry.adapters.register([IBlockSchema], IValidationBoundaryFactory, "", factory)

