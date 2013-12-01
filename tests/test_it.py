# -*- coding:utf-8 -*-
import unittest

import re
import colander as co
from block.form import Schema

class NameConflict(Exception):
    pass

class UserSchema(Schema):
    name = co.SchemaNode(co.String(),
                         required=True,
                         validator=co.Length(min=4),
                         widget="text")


class ValidationTests(unittest.TestCase):
    def setUp(self):
        from block.form.validation import validation_repository_factory
        validations = validation_repository_factory()

        ## define validation
        @validations.config(UserSchema, "name", positionals=["db"])
        def name_conflict_validation(data, db):
            if data["name"] in db:
                raise NameConflict(data["name"])
        self.repository = validations

    def _callFUT(self, *args, **kwargs):
        return self.repository[UserSchema](*args, **kwargs)

    def test_it(self):
        DB = ["*inserted user*"]
        for name, validation in self._callFUT({"db": DB}):
            validation({"name": "*new name*"})

    def test_it__validation_failure(self):
        DB = ["*inserted user*"]
        with self.assertRaises(NameConflict):
            for name, validation in self._callFUT({"db": DB}):
                validation({"name": "*inserted user*"})

from block.form.testing import get_pyramid_testclasses
PyramidTest, testing = get_pyramid_testclasses()

class BoundaryTests(PyramidTest):
    def tearDown(self):
        testing.tearDown()

    def setUp(self):
        self.config = testing.setUp(autocommit=False)
        self.config.include("block.form")

        from block.form.validation.core import AppendListErrorControl
        error_control = AppendListErrorControl({NameConflict: "conflict. {}"})
        self.config.block_set_error_control(error_control)

        from block.form.validation import validation_repository_factory
        validations = validation_repository_factory()
        self.config.block_set_validation_repository(validations)

        ## define validation
        @validations.config(UserSchema, "name", positionals=["db"])
        def name_conflict_validation(data, db):
            if data["name"] in db:
                raise NameConflict(data["name"])
        self.repository = validations
        self.config.commit()

    def test_boundary(self):
        from block.form.validation import get_validation
        from block.form.validation import ValidationError

        request = testing.DummyRequest(registry=self.config.registry)
        boundary = get_validation(request, UserSchema())

        DB = {"*inserted name*"}
        with self.assertRaises(ValidationError) as e:
            e.expected_regex = re.compile("conflict")
            boundary.validate({"name": "*inserted name*"}, db=DB)

    def test_boundary__add_validation_runtime(self):
        from block.form.validation import get_validation
        from block.form.validation import ValidationError

        request = testing.DummyRequest(registry=self.config.registry)
        boundary = get_validation(request, UserSchema())
        class InvalidStatus(Exception):
            pass
        def new_validation(data):
            if not "token" in data:
                raise InvalidStatus("oops")
        boundary.add("token", new_validation)

        DB = {"*inserted name*"}

        with self.assertRaises(ValidationError) as e:
            e.expected_regex = re.compile("oops")
            boundary.validate({"name": "*new name*"}, db=DB)


if __name__ == '__main__':
    unittest.main()
