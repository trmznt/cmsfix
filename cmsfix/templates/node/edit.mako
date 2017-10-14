<%inherit file="rhombus:templates/base.mako" />

${breadcrumb}

<p>Parent url: ${parent_url or ''}</p>

${eform}

##
##
<%def name='jscode()'>
  ${code | n}
</%def>


