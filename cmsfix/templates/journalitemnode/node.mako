<%inherit file="cmsfix:templates/base.mako" />

${breadcrumb}

<h3>${'Log date: %s | Title: %s' % (node.log_date, node.title)}</h3>

${html}

<h4>File Attachment:</h4>

${macro.M_ListChildNodes(node, [ 'type=FileNode'])}

