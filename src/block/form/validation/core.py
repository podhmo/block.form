# -*- coding:utf-8 -*-
import colander as co
from colander import Invalid
import itertools

import logging
logger = logging.getLogger(__name__)

from . import ValidationError
from .pickup import generate_pikup_function

class ColanderSchemaControl(object):
    def get_class(self, schema):
        if isinstance(schema, co._SchemaMeta):
            return schema
        else:
            return schema.__class__

    def __call__(self, schema, params):
        try:
            return schema.deserialize(params)
        except Invalid as e:
            raise ValidationError(e.asdict())


class AppendListErrorControl(object):
    def __init__(self, mapping, on_not_defined=None, fallback=None):
        self.mapping = mapping
        self.on_not_defined = on_not_defined or self.default_fallback
        self.fallback = fallback or self.default_fallback

    def __call__(self, data, name, exc, errors):
        try:
            message = self.mapping[exc.__class__].format(exc.args[0])
            errors[name].append(message)
        except KeyError as e:
            self.on_not_defined(data, name, e, errors, original=exc)
        except Exception as e:
            self.fallback(data, name, e, errors, original=exc)


    def default_fallback(self, data, name, exc, errors, original=None):
        raise exc

    def finish(self, qualified_data, errors):
        if errors:
            raise ValidationError(dict(errors))
        return qualified_data


def append_validators(queue, name, v, pick_extra=None):
    pick = pick_extra or getattr(v, "pick_extra")
    queue.append((name, v, pick))

def pop_validators(queue, that):
    return [(name, v, pick) for name, v, pick in queue if v != that]


class ValidationQueue(object):
    def __init__(self, validators=None, name=None):
        self.validators = validators or []

    def add(self, name, v, pick_extra=None):
        for _, other, _ in self.validators:
            if other == v:
                return self.on_conflict(name, v, pick_extra)
        append_validators(self.validators, name, v, pick_extra=pick_extra)


    def on_conflict(self, name, validation, pick_extra):
        logger.warn("name:{}, function:{} is already added. overwrite it.".format(name, validation))
        pop_validators(self.validators, validation)
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
        append_validators(self.individual_queue, validation, pick_extra=pick_extra)

    def __iter__(self):
        for name, validation, pick_extra in itertools.chain(self.queue, self.individual_queue):
            if pick_extra:
                yield name, lambda data : pick_extra(validation, data, self.extra)
            else:
                yield name, validation


class ValidationRepository(object):
    def __init__(self, QueueClass=None):
        self.QueueClass = QueueClass or ValidationQueue
        self.store = {}

    def __getitem__(self, schema):
        try:
            return self.store[schema]
        except KeyError:
            return self.create_default(schema)

    def create_default(self, schema):
        queue = self.store[schema] = self.QueueClass(name=repr(schema))
        return queue

    def add(self, schema, *args, **kwargs):
        self[schema].add(*args, **kwargs)

    def config(self, schema, name, positionals=None, optionals=None):
        def wrapped(fn):
            pick_extra = generate_pikup_function(positionals=positionals, optionals=optionals)
            self.add(schema, name, fn, pick_extra=pick_extra)
            return fn
        return wrapped
