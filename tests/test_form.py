# -*- coding:utf-8 -*-
import unittest
import colander as co

class PersonSchema(co.Schema):
    name = co.SchemaNode(co.String(),
                         required=True,
                         missing="",
                         validator=co.Length(min=4),
                         widget="text")
    age = co.SchemaNode(co.Int(),
                        missing=20,
                        required=True,
                        widget="text")
    group = co.SchemaNode(co.Int(),
                          required=False,
                          choices=[],
                          widget="select")




class Tests(unittest.TestCase):
    def _getTarget(self):
        from block.form import Form
        return Form

    def _makeOne(self, *args, **kwargs):
        return self._getTarget()(PersonSchema(), *args, **kwargs)

    def test_create__without_params(self):
        target = self._makeOne()
        self.assertEqual(target.raw_values, {})

        fields = list(target.fields)
        self.assertEqual(fields[0][0].name, "name")
        self.assertEqual(fields[0][0].widget, "text")
        self.assertEqual(fields[0][1], "")
        self.assertEqual(fields[1][0].name, "age")
        self.assertEqual(fields[1][0].widget, "text")
        self.assertEqual(fields[1][1], 20)
        self.assertEqual(fields[2][0].name, "group")
        self.assertEqual(fields[2][0].widget, "select")
        self.assertEqual(fields[2][0].choices, [])
        self.assertEqual(fields[2][1], "")

    def test_create__with_params(self):
        params = {"name": "foobar", "age": 10}
        target = self._makeOne(params)
        self.assertEqual(target.raw_values, params)

        fields = list(target.fields)
        self.assertEqual(fields[0][0].name, "name")
        self.assertEqual(fields[0][0].widget, "text")
        self.assertEqual(fields[0][1], "foobar")
        self.assertEqual(fields[1][0].name, "age")
        self.assertEqual(fields[1][0].widget, "text")
        self.assertEqual(fields[1][1], 10)
        self.assertEqual(fields[2][0].name, "group")
        self.assertEqual(fields[2][0].widget, "select")
        self.assertEqual(fields[2][0].choices, [])
        self.assertEqual(fields[2][1], "")

    def test_create__with_configure(self):
        params = {}
        def configure(form):
            choices = [(i, i) for i in range(1, 3)]
            form.group.choices = choices
            form.group.missing = choices[0][1]
        target = self._makeOne(params, configure=configure)
        self.assertEqual(target.raw_values, params)

        fields = list(target.fields)
        self.assertEqual(fields[0][0].name, "name")
        self.assertEqual(fields[0][0].widget, "text")
        self.assertEqual(fields[0][1], "")
        self.assertEqual(fields[1][0].name, "age")
        self.assertEqual(fields[1][0].widget, "text")
        self.assertEqual(fields[1][1], 20)
        self.assertEqual(fields[2][0].name, "group")
        self.assertEqual(fields[2][0].widget, "select")
        self.assertEqual(fields[2][0].choices, [(1, 1), (2, 2)])
        self.assertEqual(fields[2][1], 1)

    def test_after_validate__with_errors(self): #hmm.
        from block.form.validation import ValidationError
        params = {"name": "foo", "age": "20"}
        try:
            from block.form.validation.core import ColanderSchemaControl
            ColanderSchemaControl()(PersonSchema(), params)
        except ValidationError as e:
            target = self._makeOne(params, errors=e.errors)
            self.assertEqual(target.raw_values, params)

            fields = list(target.fields)
            self.assertEqual(fields[0][0].name, "name")
            self.assertEqual(fields[0][0].widget, "text")
            self.assertEqual(fields[0][1], "foo")
            self.assertEqual(target.errors["name"], 'Shorter than minimum length 4')
            self.assertEqual(fields[1][0].name, "age")
            self.assertEqual(fields[1][0].widget, "text")
            self.assertEqual(fields[1][1], "20")
            self.assertEqual(fields[2][0].name, "group")
            self.assertEqual(fields[2][0].widget, "select")
            self.assertEqual(fields[2][0].choices, [])
            self.assertEqual(fields[2][1], "")


if __name__ == '__main__':
    unittest.main()
