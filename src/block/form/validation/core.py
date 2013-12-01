# -*- coding:utf-8 -*-
import itertools

import logging
logger = logging.getLogger(__name__)

from collections import defaultdict
from colander import Invalid
from zope.interface import implementer
from pyramid.exceptions import ConfigurationError

from . import ValidationError
from .pickup import generate_pikup_function
from ..interfaces import (
    IErrorControl,
    IValidationRepository,
    IValidationBoundary,

)

@implementer(IErrorControl)
class AppendListErrorControl(object):
    def __init__(self, mapping, on_not_defined=None, fallback=None):
        self.mapping = mapping
        self.on_not_defined = on_not_defined or self.default_not_defined
        self.fallback = fallback or self.default_fallback

    def update_mapping(self, other, strict=True):
        if strict:
            for k, v in other.items():
                if k in self.mapping:
                    raise ConfigurationError("{k} is already defined".format(k=k))
                self.mapping[k] = v
        else:
            self.mapping.update(other)

    def __call__(self, data, name, exc, errors):
        try:
            fmt = self.mapping[exc.__class__]
        except KeyError as e:
            return self.on_not_defined(data, name, e, errors, original=exc)
        except Exception as e:
            return self.fallback(data, name, e, errors, original=exc)

        try:
            data = exc.args[0]
            if hasattr(data, "items"):
                message = fmt.format(**data)
            elif isinstance(data, (tuple, list)):
                message = fmt.format(*data)
            else:
                message = fmt.format(data)
            errors[name].append(message)
        except (KeyError, IndexError):
            logger.warning("format unmatched. fmt={!r} exc={!r}".format(fmt, repr(exc)))
            errors[name].append("fmt={}, exc={}".format(fmt, repr(exc)))

    def default_not_defined(self, data, name, exc, errors, original=None):
        exc = original
        logger.warning("mapping not defined. exc={!r}".format(repr(exc)))
        errors[name].append(repr(exc))

    def default_fallback(self, data, name, exc, errors, original=None):
        raise exc

    def finish(self, qualified_data, errors):
        if errors:
            raise ValidationError(dict(errors))
        return qualified_data


def append_validators(queue, name, v, pick_extra=None):
    pick = pick_extra or getattr(v, "pick_extra", None)
    queue.append((name, v, pick))

def pop_validators(queue, that):
    return [(name, v, pick) for name, v, pick in queue if v != that]


class ValidationQueue(object):
    def __init__(self, validators=None, name=None):
        self.validators = validators or []

    def add(self, name, validation, pick_extra=None):
        for _, other, pick_extra2 in self.validators:
            if other == validation or (
                    other.__name__ == validation.__name__ 
                    and pick_extra.__name__ == pick_extra2.__name__):
                return self.on_conflict(name, validation, other, pick_extra)
        append_validators(self.validators, name, validation, pick_extra=pick_extra)



    def on_conflict(self, name, validation, other, pick_extra):
        logger.warning("name:{}, function:{} is already added. overwrite it.".format(name, validation))
        self.validators = pop_validators(self.validators, other)
        append_validators(self.validators, name, validation, pick_extra)

    def __iter__(self):
        return iter(self.validators)

    def __call__(self, extra):
        return ValidationIterator(self, extra)


class ValidationIterator(object):
    def __init__(self, queue, extra):
        self.queue = queue
        self.extra = extra
        self.individual_queue = []

    def add(self, name, validation, pick_extra=None):
        append_validators(self.individual_queue, name, validation, pick_extra=pick_extra)

    def __iter__(self):
        for name, validation, pick_extra in itertools.chain(self.queue, self.individual_queue):
            if pick_extra:
                yield name, lambda data : pick_extra(validation, data, self.extra)
            else:
                yield name, validation


@implementer(IValidationRepository)
class ValidationRepository(object):
    def __init__(self, QueueClass=None):
        self.QueueClass = QueueClass or ValidationQueue
        self.store = {}

    def __getitem__(self, keyname):
        try:
            return self.store[keyname]
        except KeyError:
            return self.create_default(keyname)

    def create_default(self, keyname):
        queue = self.store[keyname] = self.QueueClass(name=repr(keyname))
        return queue

    def add(self, keyname, *args, **kwargs):
        self[keyname].add(*args, **kwargs)

    def config(self, keyname, name, positionals=None, optionals=None):
        def wrapped(fn):
            pick_extra = generate_pikup_function(positionals=positionals, optionals=optionals)
            self.add(keyname, name, fn, pick_extra=pick_extra)
            return fn
        return wrapped


@implementer(IValidationBoundary)
class PreparedBoundary(object):
    def __init__(self, schema,
                 next_boundary=None,
                 individual_validations=None,
                 extra=None):
        self.schema = schema
        self.next_boundary = next_boundary
        self.individual_validations = individual_validations or []
        self.extra = extra or {}

    def add(self, name, validation, pick_extra=None):
        self.individual_validations.append((name, validation, pick_extra))

    def validate(self, data, **extra):
        try:
            qualified_data = self.schema.deserialize(data)
        except Invalid as e:
            raise ValidationError(e.asdict())

        if self.next_boundary is None:
            return qualified_data

        next_boundary = self.next_boundary(
            self.schema,
            individual_validations=self.individual_validations,
            extra=self.extra)
        return next_boundary.validate(qualified_data, **extra)


@implementer(IValidationBoundary)
class ValidationBoundary(object):
    def __init__(self, error_control, validation_queue,
                 individual_validations=None,
                 extra=None):
        self.error_control = error_control
        self.validation_queue = validation_queue
        self.individual_validations = individual_validations or []
        self.extra = extra or {}

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

    def validate(self, qualified_data, **extra):
        errors = defaultdict(list)
        iterator = self.get_iterator(extra)

        for name, validation in iterator:
            try:
                validation(qualified_data)
            except Exception as e:
                self.error_control(qualified_data, name, e, errors)
        return self.error_control.finish(qualified_data, errors)
