# -*- coding:utf-8 -*-
import unittest
import re
from block.form.testing import get_pyramid_testclasses
PyramidTest, testing = get_pyramid_testclasses()

class ConfigurationRemindTests(PyramidTest):
    def tearDown(self):
        testing.tearDown()

    def setUp(self):
        self.config = testing.setUp(autocommit=False)
        self.config.include("block.form")

    def test__forget__set_error_control(self):
        self.config.block_set_validation_repository(object())

        from pyramid.exceptions import ConfigurationError
        with self.assertRaises(ConfigurationError) as e:
            e.expected_regex = re.compile("set_error_control")
            self.config.commit()

    def test__forget__set_validation_repository(self):
        self.config.block_set_error_control(object())

        from pyramid.exceptions import ConfigurationError
        with self.assertRaises(ConfigurationError) as e:
            e.expected_regex = re.compile("set_validation_repository")
            self.config.commit()

    def test_it(self):
        self.config.block_set_validation_repository(object())
        self.config.block_set_error_control(object())
        self.config.commit()

    def test_add_mapping__strict(self):
        from pyramid.exceptions import ConfigurationError
        from block.form.validation.core import AppendListErrorControl
        mapping = {}
        self.config.block_set_error_control(AppendListErrorControl(mapping))
        self.config.block_set_validation_repository(object())

        self.config.block_add_error_mapping({"a": "b", "x": "1", "y": 2}, strict=True)
        self.config.block_add_error_mapping({"x": 2, "z": 3}, strict=True)

        with self.assertRaises(ConfigurationError):
            self.config.commit()


    def test_add_mapping__nostrict(self):
        from block.form.validation.core import AppendListErrorControl
        mapping = {}
        self.config.block_set_error_control(AppendListErrorControl(mapping))
        self.config.block_set_validation_repository(object())

        self.config.block_add_error_mapping({"a": "b", "x": "1", "y": 2}, strict=False)
        self.config.block_add_error_mapping({"x": 2, "z": 3}, strict=False)
        self.config.commit()
        self.assertEqual(mapping, {'a': 'b', 'z': 3 , 'y': 2, 'x': 2})

if __name__ == '__main__':
    unittest.main()
