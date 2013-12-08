# -*- coding:utf-8
import colander as co
from mako.lookup import TemplateLookup
from mako.template import Template

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


lookup = TemplateLookup(
    directories=".", 
    input_encoding='utf-8',
    output_encoding='utf-8',)

def render(form, action, method="GET"):
    template = Template(u"""
    <%namespace name="w" file="forms.mako"/>

    <form action="${action}" method="${method}">
    %for c, val in fields:
      <%w:field c="${c}" default="${val}">
      %if c.name in errors:
        error:${errors[c.name]}
      %endif
      </%w:field>
    %endfor
    </form>
    """, lookup=lookup)
    return template.render(fields=form.fields, action=action, method=method, errors=form.errors)

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
