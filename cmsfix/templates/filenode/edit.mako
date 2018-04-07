<%inherit file="cmsfix:templates/base.mako" />
<!-- cmsfix:templates/filenode/edit.mako -->

<!-- global progressbar -->
<div id='fileprogress' class='progress progressbar-container' style='display:none'>
  <div class='progress-bar progress-bar-success'></div>
</div>

${breadcrumb}

${eform}

##
##
<%def name='jscode()'>
  <!-- cmsfix:templates/filenode/edit.mako jscode() -->
  ${code | n}
</%def>

##
##
<%def name='stylelink()'>
<link href="${request.static_url('cmsfix:static/jquery.fileupload/css/jquery.fileupload.css')}" rel="stylesheet" />
</%def>
##
##
<%def name='jslink()'>
<script src="${request.static_url('cmsfix:static/jquery.fileupload/js/vendor/jquery.ui.widget.js')}"></script>
<script src="${request.static_url('cmsfix:static/jquery.fileupload/js/jquery.fileupload.js')}"></script>
</%def>


