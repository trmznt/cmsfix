<%inherit file="rhombus:templates/base.mako" />

${toolbar}

<p>Parent url: ${parent_url or ''}</p>

${eform}

##
##
<%def name='jscode()'>
  ${code | n}
</%def>


