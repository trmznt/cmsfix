<%inherit file="rhombus:templates/base.mako" />

${breadcrumb}

${eform}

##
##
<%def name='jscode()'>
  ${code | n}

  var editor = null;

  function set_editor(mimetype) {
  	if (mimetype == html_mimetype) {
  		if (editor != null) {
  			editor.destroy();
  		}
  		editor = null;
  		$('#cmsfix-content').trumbowyg();
  	}
  	else {
  		$('#cmsfix-content').trumbowyg('destroy');
  		editor = new Behave({
    		textarea: document.getElementById('cmsfix-content')
    		}
    	);
  	}
  };

  set_editor($('#cmsfix-mimetype_id').value);

</%def>

##
<%def name='jslink()'>
    <script src="/static/trumbowyg/dist/trumbowyg.min.js"></script>
    <script src="/static/behave/behave.js"></script>
</%def>

##
<%def name='stylelink()'>
    <link rel="stylesheet" href="/static/trumbowyg/dist/ui/trumbowyg.min.css">
</%def>


