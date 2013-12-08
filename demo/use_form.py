# -*- coding:utf-8

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


def configure(form):
    choices = [(str(i), str(i)) for i in range(1, 3)]
    form.group.choices = choices
    form.group.default = choices[0][1]
    return form

class Widget(object):
    @classmethod
    def text(cls, c, default=""):
        return """<label>{name}<input name="{name}" type="text" value="{value}"/></label>""".format(
            name=c.name, value=default)

    @classmethod
    def select(cls, c, choices, default=object()):
        r = ["<label>{name}<select name={name}>".format(name=c.name)]
        for value, name in choices:
            if value == default:
                r.append("""<option value="{name}" selected="selected">{value}</option>""".format(
                    name=name, value=value))
            else:
                r.append("""<option value="{name}">{value}</option>""".format(
                    name=name, value=value))
        r.append("</select></label>")
        return "\n".join(r)

    @classmethod
    def render(cls, c, default, error=""):
        r = []
        if c.widget == "select":
            r.append(cls.select(c, c.choices, default=default))
        else:
            r.append(getattr(cls, c.widget)(c, default=default))
        if error:
            if not isinstance(error, (list, tuple)):
                error = [error]
            r.append("""<div class="error">""")
            r.extend(error)
            r.append("</p></div>")
        return "\n".join(r)

def render(form, action, method="GET"):
    r = ["""<form action="{action}" method="{method}">""".format(action=action, method=method)]
    errors = form.errors
    r.extend([Widget.render(c, val, errors.get(c.name, "")) for c, val in form.fields])
    r.append("""</form>""")
    return "\n".join(r)

## using form with non default values
from block.form import Form
form = Form(PersonSchema(), {}, configure=configure)
print(render(form, action="#", method="POST"))

print("\n")

## using form with default values
from block.form import Form
form = Form(PersonSchema(), {"name": "foo", "age":10, "group": 2}, configure=configure)
print(render(form, action="#", method="POST"))

print("\n")

## POST -- failure 
from colander import Invalid
schema = PersonSchema()
params = {}
try:
    qualified_data = schema.deserialize(params)
    raise Exception("dont call")
except Invalid as e:
    errors = e.asdict()
form = Form(schema, params, errors=errors, configure=configure)
print(render(form, action="#", method="POST"))

print("\n")

## POST -- success
schema = PersonSchema()
params = {"name": "foobar", "age": 10}
qualified_data = schema.deserialize(params)
print("use: {}".format(qualified_data))
