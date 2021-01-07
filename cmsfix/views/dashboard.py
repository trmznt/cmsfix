# dashboard.py

import os

from rhombus.views import *
from cmsfix.views.node.pagenode import render_rst
from pyramid.response import FileResponse

@roles(PUBLIC)
def index(request):
    pass


@roles(PUBLIC)
def docs(request):

    path = os.path.normpath(request.matchdict.get('path', '') or '/index.rst')
    path = '/' + path if not path.startswith('/') else path
    if path == '@macro':
        return show_macro(request)
    return fso.serve_file(path, mount_point=('/', "cmsfix:../docs/"),
                    formatter = lambda abspath: formatter(abspath, request))

    doc_path = request.registry.settings['cmsfix-doc-path'] + request.matchdict.get('path', '/index.rst')

    with open(doc_path) as f:
        buf = f.read()

    # if html file, just return the content
    if doc_path.endswith('html'):
        return literal(buf)

    # prepare content
    content = literal(render_rst(buf))

    # show content
    return render_to_response('cmsfix:templates/plainpage.mako',
        {
			'html': content,
        }, request = request )


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
