# dashboard.py

import os

from rhombus.views import *
from rhombus.views import roles, get_dbhandler, render_to_response, fso
from rhombus.lib import roles as r
from rhombus.lib import tags_b46 as t
from cmsfix.lib.workflow import get_workflow
from cmsfix.views.node.pagenode import render_rst
from pyramid.response import FileResponse


@roles(r.PUBLIC)
def index(request):
    """ return a generic dashboard """

    html = t.div()
    html.add(t.h2('Dashboard'))

    html.add(t.h4('Latest updated pages'))

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
            t.div(class_='row')[
                t.div(class_='col-md-1')[
                    node.stamp.date(),
                ],
                t.div(class_='col-md-1')[
                    node.lastuser.login,
                ],
                t.div(class_='col-md-10')[
                    node.parent.title if node.parent else '', ' >> ', t.a(node.title or 'N/A', href=node.url),
                    '|', node.path,
                ]
            ]
        )

    return render_to_response('cmsfix:templates/node/generics.mako', {
        'content': html,
    }, request=request)


@roles(r.PUBLIC)
def docs(request):

    path = os.path.normpath(request.matchdict.get('path', '') or '/index.rst')
    path = '/' + path if not path.startswith('/') else path
    if path == '/@macro':
        return show_macro(request)
    return fso.serve_file(path, mount_point=('/', "cmsfix:../docs/"),
                          formatter=lambda abspath: formatter(abspath, request))


def formatter(abspath, request):

    basepath, ext = os.path.splitext(abspath)

    if ext == '.rst':
        # restructuredtext
        with open(abspath) as f:
            text = f.read()
            content = t.literal(render_rst(text))

        return render_to_response('cmsfix:templates/plainpage.mako', {
            'html': content,
        }, request=request)

    elif ext == '.md':
        raise NotImplementedError

    else:
        return FileResponse(abspath)


def show_macro(request):

    from cmsfix.lib.macro import macro_dict

    html = t.div()
    macros = macro_dict()

    macro_names = sorted(macros.keys())

    for n in macro_names:

        f = macros[n]

        html.add(
            t.h4(n),
            t.div(class_='ml-5')[
                t.literal(render_rst(f.__doc__)) if f.__doc__ else '',
            ]
        )

    return render_to_response('cmsfix:templates/node/generics.mako', {
        'content': html,
    }, request=request)

# EOF
