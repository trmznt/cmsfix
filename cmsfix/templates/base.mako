## -*- coding: utf-8 -*-
% if request and request.is_xhr:
  ${next.body()}

  <script type="text/javascript">
    //<![CDATA[
    ${self.jscode()}
    //]]>
  </script>

% else:
<%! from rhombus.views.user import user_menu %>
<!DOCTYPE html>
<html lang="en">
  <head>
  <meta charset="utf-8" />
  <title>${request.get_resource('cmsfix.title', None) or "CMSFix"}</title>
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />

  <!-- styles -->
  <link href="${request.static_url('rhombus:static/bootstrap/css/bootstrap.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/bootstrap/css/bootstrap-theme.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/fonts/source-sans-pro.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/font-awesome-4.5.0/css/font-awesome.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/select2/css/select2.min.css')}" rel="stylesheet" />

  <link href="${request.static_url('rhombus:static/rst/rst.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/rst/theme.css')}" rel="stylesheet" />

  <link href="${request.static_url('cmsfix:static/fonts/merriweather/merriweather.css')}" rel="stylesheet" />
  <link href="${request.static_url('cmsfix:static/fonts/gentiumbb/gentiumbb.css')}" rel="stylesheet" />
  <link href="${request.static_url('cmsfix:static/fonts/lato/lato.css')}" rel="stylesheet" />
  <link href="${request.static_url('cmsfix:static/custom.css')}" rel="stylesheet" />
  ${self.stylelink()}

  </head>
  <body>

    <!-- Static navbar -->
    <nav class="navbar navbar-default navbar-static-top">
      <div class="container-fluid">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="/">${request.get_resource('cmsfix.title', 'CMSFix')}</a>
        </div>
        <div id="navbar" class="navbar-collapse collapse">
          ${user_menu(request)}
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="container-fluid">
      <div class="row">
      ${flash_msg()}
      </div>
      <div class="row">

        <div class="col-md-12">

        ${next.body()}

        </div>

      </div>

    </div>
    <footer>
    <div class="container-fluid">
      <div class='row'>
      <div class='col-md-12'>
        <!-- font: Nobile -->
        <p>(C) 2016 Eijkman Institute for Molecular Biology, Indonesia</p>
      </div>
      </div>
    </div>
    </footer>

${self.scriptlinks()}

  </body>

</html>
% endif
##
##
<%def name="stylelink()">
</%def>
##
##
<%def name="scriptlinks()">
    <script src="${request.static_url('rhombus:static/js/jquery.js')}"></script>
    <script src="${request.static_url('rhombus:static/bootstrap/js/bootstrap.min.js')}"></script>
    <script src="${request.static_url('rhombus:static/select2/js/select2.min.js')}"></script>

    ${self.jslink()}
    <script type="text/javascript">
        //<![CDATA[
        ${self.jscode()}
        //]]>
    </script>
</%def>
##
##
<%def name='flash_msg()'>
% if request.session.peek_flash():

  % for msg_type, msg_text in request.session.pop_flash():
   <div class="alert alert-${msg_type}">
     <a class="close" data-dismiss="alert">×</a>
     ${msg_text}
   </div>
  % endfor

% endif
</%def>

##
<%def name='jscode()'>
${ code or '' | n }
</%def>

##
<%def name="jslink()">
${ codelink or '' | n }
</%def>
