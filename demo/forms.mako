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
