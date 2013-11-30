# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)

def generate_pikup_function(positionals=None, optionals=None):
    positionals = positionals or []
    optionals = optionals or []
    def pick(cb, data, extra):
        args = [extra[k] for k in positionals]
        kwargs = {}
        for k in optionals:
            if isinstance(k, (tuple, list)):
                put_k = k[1]
                k = k[0]
            else:
                put_k = k
            v = extra.get(k)
            if v:
                kwargs[put_k] = v
        return cb(data, *args, **kwargs)
    return pick

def pickup(positionals=None, optionals=None):
    def _wrapped(validation_fn):
        if hasattr(validation_fn, "pick"):
            logger.warn("{} has pick, already. overwrite it".format(validation_fn))
        pick = generate_pikup_function(positionals=positionals, optionals=optionals)
        validation_fn.pick_extra = pick
        return validation_fn
    return _wrapped
