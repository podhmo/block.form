# -*- coding:utf-8 -*-
import unittest

def get_pyramid_testclasses():
    try:
        from pyramid import testing
        return unittest.TestCase, testing
    except ImportError:
        return object, None
