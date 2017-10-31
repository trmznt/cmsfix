# dashboard.py

from rhombus.views import *

@roles(PUBLIC)
def index(request):
    pass


@roles(PUBLIC)
def docs(request):

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
