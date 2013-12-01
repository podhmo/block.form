# -*- coding:utf-8 -*-
import unittest
import colander as co

class MaybeInt(co.Number):
    @staticmethod
    def num(v):
        if v == "":
            return v
        else:
            return int(v)

class PersonSchema(co.Schema):
    name =  co.SchemaNode(co.String(),
                          default="",
                          validator = co.Length(min=4),
                          widget="text")
    age = co.SchemaNode(co.Int(),
                        default=20,
                        widget="text")
    group = co.SchemaNode(MaybeInt(),
                          missing=None,
                          default="",
                          choices=[],
                          widget="select")


class Tests(unittest.TestCase):
    def _getTarget(self):
        from block.form import Form
        return Form

    def _makeOne(self, schema, *args, **kwargs):
        return self._getTarget()(schema, *args, **kwargs)

    def test_create__without_params(self):
        target = self._makeOne(PersonSchema())
        self.assertEqual(target.raw_values, {})

        fields = list(target.fields)
        self.assertEqual(fields[0][0].name, "name")
        self.assertEqual(fields[0][0].widget, "text")
        self.assertEqual(fields[0][1], "")
        self.assertEqual(fields[1][0].name, "age")
        self.assertEqual(fields[1][0].widget, "text")
        self.assertEqual(fields[1][1], "20")
        self.assertEqual(fields[2][0].name, "group")
        self.assertEqual(fields[2][0].widget, "select")
        self.assertEqual(fields[2][0].choices, [])
        self.assertEqual(fields[2][1], "")

    def test_create__with_params(self):
        params = {"name": "foobar", "age": 10}
        target = self._makeOne(PersonSchema(), params)
        self.assertEqual(target.raw_values, params)

        fields = list(target.fields)
        self.assertEqual(fields[0][0].name, "name")
        self.assertEqual(fields[0][0].widget, "text")
        self.assertEqual(fields[0][1], "foobar")
        self.assertEqual(fields[1][0].name, "age")
        self.assertEqual(fields[1][0].widget, "text")
        self.assertEqual(fields[1][1], "10")
        self.assertEqual(fields[2][0].name, "group")
        self.assertEqual(fields[2][0].widget, "select")
        self.assertEqual(fields[2][0].choices, [])
        self.assertEqual(fields[2][1], "")

    def test_create__with_configure(self):
        params = {}
        def configure(form):
            choices = [(i, i) for i in range(1, 3)]
            form.group.choices = choices
            form.group.default = choices[0][1]

        target = self._makeOne(PersonSchema(), params, configure=configure)
        self.assertEqual(target.raw_values, params)

        fields = list(target.fields)
        self.assertEqual(fields[0][0].name, "name")
        self.assertEqual(fields[0][0].widget, "text")
        self.assertEqual(fields[0][1], "")
        self.assertEqual(fields[1][0].name, "age")
        self.assertEqual(fields[1][0].widget, "text")
        self.assertEqual(fields[1][1], "20")
        self.assertEqual(fields[2][0].name, "group")
        self.assertEqual(fields[2][0].widget, "select")
        self.assertEqual(fields[2][0].choices, [(1, 1), (2, 2)])
        self.assertEqual(fields[2][1], "1")

    def test_after_validate__with_errors(self): #hmm.
        from block.form.validation import ValidationError
        params = {"name": "foo", "age": "20"}
        schema = PersonSchema()
        try:
            from block.form.validation.core import ColanderSchemaControl
            ColanderSchemaControl()(schema, params)
        except ValidationError as e:
            target = self._makeOne(schema, params, errors=e.errors)
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


    def test__display_name__for_human(self):
        class UserSchema(co.Schema):
            fullname = co.SchemaNode(co.String(), widget="text",
                                      title="名前",
                                      description="full name of user")

        target = self._makeOne(UserSchema())
        self.assertEqual(target.fullname.title, "名前")
        self.assertEqual(target.fullname.description, "full name of user")

        target = self._makeOne(UserSchema())
        self.assertEqual(target.fullname.title, "名前")


    def test__attributes__without_change(self):
        class UserSchema(co.Schema):
            fullname = co.SchemaNode(co.String(), widget="text",
                                     attributes={"class": "ui-autocomplete"})
        target = self._makeOne(UserSchema())
        self.assertEqual(target.fullname.attributes,
                         {"class": "ui-autocomplete"})

    def test_attributes__overwrite(self):
        class UserSchema(co.Schema):
            fullname = co.SchemaNode(co.String(), widget="text",
                                     attributes={"class": "ui-autocomplete"})

        target = self._makeOne(UserSchema())
        target.fullname.attributes = {"style": "display:none;"}
        self.assertEqual(target.fullname.attributes,
                         {"style": "display:none;"})

        ## another instance is not changed.
        target = self._makeOne(UserSchema())
        self.assertEqual(target.fullname.attributes,
                         {"class": "ui-autocomplete"})

    ## misc
    def test__maybe_int(self):
        class UserSchema(co.Schema):
            age = co.SchemaNode(MaybeInt(),
                                widget="text",
                                default="",
                                missing=None)

        ## on validation
        qualified_data = UserSchema().deserialize({})
        self.assertEqual(qualified_data, {"age": None})

        ## on rendering
        target = self._makeOne(UserSchema())
        fields = list(target.fields)
        self.assertEqual(fields[0][0].name, "age")
        self.assertEqual(fields[0][1], "")

    def test__nested(self):
        class SelectDay(co.Schema):
            year = co.SchemaNode(co.Int(), widget="select", default=2013, missing=2013)
            month = co.SchemaNode(co.Int(), widget="select", default=1)
            day = co.SchemaNode(co.Int(), widget="select", default=1)
        class Schema(co.Schema):
            day = SelectDay(widget="day-triple")

        ## on validation
        qualified_data = Schema().deserialize({"day": {"month": "1", "day": "1"}})
        self.assertEqual(qualified_data,
                         {"day": {"year": 2013, "month": 1, "day": 1}})

        ## on rendering
        target = self._makeOne(Schema())
        fields = list(target.fields)
        self.assertEqual(fields[0][0].name, "day")
        self.assertEqual(fields[0][1], {"year": "2013", "month": "1", "day": "1"})

        ## editing nested node
        self.assertEqual(target.day["year"].widget, "select")
        target.day["year"].widget = "myselect"
        self.assertEqual(target.day["year"].widget, "myselect")

        target2 = self._makeOne(Schema())
        self.assertEqual(target2.day["year"].widget, "select")

if __name__ == '__main__':
    unittest.main()
