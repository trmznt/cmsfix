# dashboard.py

import os

from rhombus.views import *
from cmsfix.lib.workflow import get_workflow
from cmsfix.views.node.pagenode import render_rst
from pyramid.response import FileResponse

@roles(PUBLIC)
def index(request):
    """ return a generic dashboard """

    html = div()
    html.add( h2('Dashboard') )

    html.add( h4('Latest updated pages') )

    dbh = get_dbhandler()
    nodes = dbh.session().query(dbh.PageNode).order_by(dbh.PageNode.stamp.desc())

    accessible_nodes = []
    limit = 10
    counter = 0

    for n in nodes:
        if get_workflow(n).is_accessible(n, request):
            accessible_nodes.append(n)
            counter += 1
            if counter > limit:
                break

    for node in accessible_nodes:
        html.add(
            div(class_='row')[
                div(class_='col-md-1')[
                    node.stamp.date(),
                ],
                div(class_='col-md-1')[
                    node.lastuser.login,
                ],
                div(class_='col-md-10')[
                    node.parent.title if node.parent else '', ' >> ', a(node.title or 'N/A', href=node.url),
                    '|', node.path,
                ]
            ]
        )

    return render_to_response('cmsfix:templates/node/generics.mako',
                { 'content': html,
                }, request = request )


@roles(PUBLIC)
def docs(request):

    path = os.path.normpath(request.matchdict.get('path', '') or '/index.rst')
    path = '/' + path if not path.startswith('/') else path
    if path == '/@macro':
        return show_macro(request)
    return fso.serve_file(path, mount_point=('/', "cmsfix:../docs/"),
                    formatter = lambda abspath: formatter(abspath, request))


def formatter( abspath, request ):

    basepath, ext = os.path.splitext( abspath )

    if ext == '.rst':
        # restructuredtext
        with open(abspath) as f:
            text = f.read()
            content = literal(render_rst(text))

        return render_to_response('cmsfix:templates/plainpage.mako',
            {
                'html': content,
            }, request = request )


    elif ext == '.md':
        raise NotImplementedError

    else:
        return FileResponse( abspath )


def show_macro(request):

    from cmsfix.lib.macro import macro_dict

    html = div()
    macros = macro_dict()

    macro_names = sorted(macros.keys())

    for n in macro_names:

        f = macros[n]

        html.add(
            h4(n),
            div(class_='ml-5')[
                literal(render_rst(f.__doc__)) if f.__doc__ else '',
            ]
        )


    return render_to_response('cmsfix:templates/node/generics.mako',
                { 'content': html,
                }, request = request )
