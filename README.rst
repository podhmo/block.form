block.form
----------------------------------------

* as container for form
* as validation

container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

prepare ::

    from mako.lookup import TemplateLookup
    from mako.template import Template
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

rendering form with non default values

code ::

    from block.form import Form
    form = Form(PersonSchema(), {}, configure=configure)
    print(render(form, action="#", method="POST"))

output ::

    <form action="#" method="POST">
      <label>name<input c.name="name" type="text" value=""/></label>
      <label>age<input c.name="age" type="text" value="20"/></label>
      <label>group<select name=group>
          <option value="1" selected="selected">1</option>
          <option value="2">2</option>
      </select></label>
    </form>

rendering form with default values

code ::

    from block.form import Form
    form = Form(PersonSchema(), {"name": "foo", "age":10, "group": 2}, configure=configure)
    print(render(form, action="#", method="POST"))

output ::

    <form action="#" method="POST">
      <label>name<input c.name="name" type="text" value="foo"/></label>
      <label>age<input c.name="age" type="text" value="10"/></label>
      <label>group<select name=group>
          <option value="1">1</option>
          <option value="2" selected="selected">2</option>
      </select></label>
    </form>

POST -- success

code ::

    schema = PersonSchema()
    params = {"name": "foobar", "age": 10}
    qualified_data = schema.deserialize(params)
    print("use: {}".format(qualified_data))


POST -- failure

code ::

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

output ::

    <form action="#" method="POST">
      <label>name<input c.name="name" type="text" value=""/></label>
      error:Required
      <label>age<input c.name="age" type="text" value="20"/></label>
      error:Required
      <label>group<select name=group>
          <option value="1" selected="selected">1</option>
          <option value="2">2</option>
      </select></label>
    </form>

forms.mako ::

    <%def name="text(c,default)">
      <label>${c.name}<input c.name="${c.name}" type="text" value="${default}"/></label>
    </%def>

    <%def name="select(c,default)">
      <label>${c.name}<select name=${c.name}>
      %for value, name in c.choices:
        %if value == default:
            <option value="${name}" selected="selected">${value}</option>
        %else:
            <option value="${name}">${value}</option>
        %endif
      %endfor
      </select></label>
    </%def>

    <%def name="field(c,default)">
      ${getattr(self,c.widget)(c,default)}
      %if caller:
        ${caller.body()}
      %endif¥
    </%def>

