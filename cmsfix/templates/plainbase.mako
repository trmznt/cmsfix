## -*- coding: utf-8 -*-
% if request and request.is_xhr:
  ${next.body()}

  <script type="text/javascript">
    //<![CDATA[
    ${self.jscode()}
    //]]>
  </script>

% else:

<!DOCTYPE html>
<html lang="en">
  <head>
  <meta charset="utf-8" />
  <title>${request.get_resource('plasmogen.title', None) or "PlasmoGEN"}</title>
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />

  <!-- styles -->
  <link href="${request.static_url('rhombus:static/bootstrap/css/bootstrap.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/bootstrap/css/bootstrap-theme.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/fonts/source-sans-pro.css')}" rel="stylesheet" />
   <link href="${request.static_url('genaf:static/custom.css')}" rel="stylesheet" />
  ${self.stylelink()}

  </head>
  <body>

    <div class="container-fluid">
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
        <p>(C) 2013 - 2015 Menzies School of Health Research, Australia <br />
           (C) 2013 - 2015 Eijkman Institute for Molecular Biology, Indonesia</p>
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
</%def>
##
##

