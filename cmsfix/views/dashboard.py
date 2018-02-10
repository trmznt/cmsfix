# dashboard.py

import os

from rhombus.views import *
from pyramid.response import FileResponse

@roles(PUBLIC)
def index(request):
    pass


@roles(PUBLIC)
def docs(request):

    path = os.path.normpath(request.matchdict.get('path', '/index.rst'))
    return fso.serve_file(path, mount_point=('/', "cmsfix:docs/"), formatter = formatter)

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
            content = render_rst(text)

        return render_to_response('cmsfix:templates/plainpage.mako',
            {
                'html': content,
            }, request = request )


    elif ext == '.md':
        raise NotImplementedError

    else:
        return FileResponse( abspath )
