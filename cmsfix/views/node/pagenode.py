
from cmsfix.views import *
from cmsfix.views.node import get_node, get_add_menu
from cmsfix.views.node.node import ( nav, node_submit_bar,
            NodeViewer,
)
from cmsfix.models.pagenode import PageNode
from cmsfix.lib.workflow import get_workflow
from cmsfix.lib import macro
from rhombus.lib.utils import get_dbhandler, cerr, cout
from rhombus.lib.tags import *

import docutils.core
import os

class PageNodeViewer(NodeViewer):

    template_edit = 'cmsfix:templates/pagenode/edit.mako'
    template_view = 'cmsfix:templates/pagenode/node.mako'
    mimetype_filter = lambda c, x: x.startswith('text/')

    def render(self, request):

        node = self.node

        # set the formatter
        if node.mimetype == 'text/x-rst':
            content = literal(render_rst(node.content))
            content = literal(macro.postrender(content, node, request))
        elif node.mimetype == 'text/html':
            content = literal(node.content)
        elif node.mimetype == 'text/plain':
            content = pre(node.content)
        else:
            content = node.content

        # check if we have a custom template
        path = node.path
        if path == '/':
            path = 'home.mako'
        else:
            path = path[1:] + '.mako'
        path = request.registry.settings.get('cmsfix.templatedir', '') + path
        cerr('checking for template %s' % path)
        if os.path.exists(path):
            template_view = path
        else:
            template_view = self.template_view

        return render_to_response(template_view,
            {   'node': node,
                'breadcrumb': self.breadcrumb(request),
                'infobar': self.infobar(request),
                'html': content,
                'stickybar': self.statusbar(request),
                'macro': macro,
            }, request = request )


    def parse_form(self, f, d=None):

        d = super().parse_form(f, d)
        if 'cmsfix-title' in f:
            d['title'] = f['cmsfix-title']
        if 'cmsfix-content' in f:
            d['content'] = macro.postedit(f['cmsfix-content'], self.node)
        if 'cmsfix-summary' in f:
            d['summary'] = f['cmsfix-summary']

        # some of our inherited class might not use keywords
        if 'cmsfix-keywords' in f:
            d['keywords'] = f['cmsfix-keywords']

        if 'cmsfix-options' in f:
            d['view'] = True if 'cmsfix-view' in f else False
            d['flags-on'] = d['flags-off'] = 0
            if 'cmsfix-inmenu' in f:
                d['flags-on'] = d['flags-on'] | self.node.f_inmenu
            else:
                d['flags-off'] = d['flags-off'] | self.node.f_inmenu

        return d


    def edit_form(self, request, create=False):

        dbh = get_dbhandler()
        n = self.node

        eform, jscode = super().edit_form(request, create)
        eform.get('cmsfix.node-main').add(
            input_text('cmsfix-title', 'Title', value=n.title, offset=1),
            input_textarea('cmsfix-content', 'Content', value=n.content, offset=1, size="18x8",
                info =  'Docs on <a href="/dashboard/docs/reST.rst" target="_blank">reStructuredText</a>'
                        ' and <a href="/dashboard/docs/@macro" target="_blank">Macros</a>' ),
            #div(literal(node.content) if node.mimetype == 'text/html' else node.content,
            #    id='cmsfix-content', name='cmsfix-content'),
            input_textarea('cmsfix-summary', 'Summary', value=n.summary, offset=1, size='5x8'),
            input_textarea('cmsfix-keywords', 'Keywords', value=n.keywords, offset=1, size='2x8'),
        )

        #eform.get('cmsfix-option-group').add( 
        #    checkbox_item('cmsfix-view', 'View as index', n.view ),
        #    checkbox_item('cmsfix-inmenu', 'In Menu', n.check_flags(n.f_inmenu)),
        #)
        eform.get('cmsfix-mimetype_id').attrs['onChange'] = 'set_editor(this.value);'
        jscode += 'var html_mimetype=%d;\n' % dbh.EK.getid('text/html', dbh.session(), '@MIMETYPE')

        return eform, jscode


    def properties_form(self, request, create=False):

        dbh = get_dbhandler()
        n = self.node

        pform, jscode = super().properties_form(request, create)

        pform.get('cmsfix-option-group').add( 
            checkbox_item('cmsfix-view', 'View as index', n.view ),
            checkbox_item('cmsfix-inmenu', 'In Menu', n.check_flags(n.f_inmenu)),
        )


        return pform, jscode

    def editingbar(self, request):

        bar = super().editingbar(request)
        bar.get('cmsfix.editingbar.left').add(
            li(a(span('Preview', class_='btn btn-primary navbar-btn'),
                            onclick=literal(r"alert('Not implemented yet');"))),
        )
        return bar


    def new_node(self):
        n = super().new_node()
        n.mimetype_id = get_dbhandler().get_ekey('text/x-rst').id
        return n


def index_xxx(request, node):
    return render_pagenode(node, request)


def view_xxx(request, node):
    return render_pagenode(node, request)

def info_xxx(request, node):
    raise NotImplementedError()

def content_xxx(request, node):
    return render_pagenode_content(node, request)

def edit_xxx(request, node):

    if request.method == 'POST':
        # update data

        d = parse_form(request.params)
        node.update(d)

        if request.params['_method'] == 'save_edit':
            return HTTPFound(location = request.route_url('node-edit', path=node.url))

        print(node.url)
        return HTTPFound(location = request.route_url('node-index', path=node.url))

    eform, jscode = edit_form(node, request)

    return render_to_response('cmsfix:templates/pagenode/edit.mako',
            {   'parent_url': ('/' + node.parent.url) if node.parent else 'None',
                'node': node,
                'toolbar': toolbar(request, node),
                'eform': eform,
                'code': jscode,
            }, request = request )


def add_xxx(request, node):

    if request.method == 'POST':
        # sanity check

        d = parse_form(request.params)
        new_node = PageNode()
        get_workflow(new_node).set_defaults(new_node, request.user, node)
        new_node.update(d)
        if not new_node.slug:
            new_node.generate_slug()
        node.add(new_node)
        get_dbhandler().session().flush()
        new_node.ordering = 19 * new_node.id

        if request.params['_method'].endswith('_edit'):
            return HTTPFound(location = request.route_url('node-edit', path=new_node.url))

        return HTTPFound(location = new_node.path)

    # show the edit form

    # create a dummy node

    dbh = get_dbhandler()

    with dbh.session().no_autoflush:

        new_node = PageNode()
        new_node.parent_id = node.id
        new_node.site = node.site
        new_node.group_id = node.group_id
        new_node.user_id = request.user.id
        new_node.mimetype_id = dbh.get_ekey('text/x-rst').id

        eform, jscode = edit_form(new_node, request, create=True)

        return render_to_response('cmsfix:templates/pagenode/edit.mako',
            {   'parent_url': node.path,
                'node': new_node,
                'toolbar': '', # new node does not have toolbar yet!
                'eform': eform,
                'code': jscode,
            }, request = request )


def action_xxx(request, node):
    raise NotImplementedError()


def render_pagenode_xxx(node, request):

    # set the formatter
    if node.mimetype == 'text/x-rst':
        content = literal(render_rst(node.content))
        content = literal(postrender(content, node))
    elif node.mimetype == 'text/html':
        content = literal(node.content)
    else:
        content = node.content

    return render_to_response('cmsfix:templates/pagenode/node.mako',
            {   'node': node,
                'toolbar': toolbar(request, node),
                'html': content,
            }, request = request )


def render_pagenode_content_xxx(node, request):
    return render_node_content(node, request)


def edit_form_xxx(node, request, create=False):

    dbh = get_dbhandler()

    eform, jscode = node_edit_form(node, request, create)
    eform.get('cmsfix.node-main').add(
        input_text('cmsfix-title', 'Title', value=node.title, offset=1),
        node_submit_bar(create),
        input_textarea('cmsfix-content', 'Content', value=node.content, offset=1, size="18x8"),
        #div(literal(node.content) if node.mimetype == 'text/html' else node.content,
        #    id='cmsfix-content', name='cmsfix-content'),
        input_textarea('cmsfix-summary', 'Summary', value=node.summary, offset=1, size='5x8')
    )

    eform.get('cmsfix-mimetype_id').attrs['onChange'] = 'set_editor(this.value);'
    jscode += 'var html_mimetype=%d;\n' % dbh.EK.getid('text/html', dbh.session(), '@MIMETYPE')

    return eform, jscode


def parse_form_xxx(f, d=None):

    d = node_parse_form(f, d)
    d['title'] = f['cmsfix-title']
    d['content'] = f['cmsfix-content']
    d['summary'] = f['cmsfix-summary']

    return d


def toolbar_xxx(request, n):

    wf = get_workflow()

    if not wf.is_manageable(n, request.user):
        return ''

    bar = nav(class_='navbar navbar-default')[
        div(class_='container-fluid')[
            div(class_='collapse navbar-collapse')[
                ul(class_='nav navbar-nav')[
                    li(a('View', href=request.route_url('node-view', path=n.url))),
                    li(a('Edit', href=request.route_url('node-edit', path=n.url))),
                    li(a('Content', href=request.route_url('node-content', path=n.url))),
                    li(a('Info', href=request.route_url('node-info', path=n.url))),
                    get_add_menu(n, request),
                ],
                ul(class_='nav navbar-nav navbar-right')[
                    li(a('Delete')),
                    wf.show_menu(n, request)
                ]
            ]
        ]
    ]
    return bar


def render_rst(text, format='html'):

    parts = docutils.core.publish_parts( text, writer_name=format,
        settings_overrides={'initial_header_level': 2} )
    if format == 'html':
        return parts['html_body']
    return None
