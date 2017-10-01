
from cmsfix.models.journalnode import JournalNode, JournalItemNode
from cmsfix.views import *
from cmsfix.views.node.node import ( nav, node_submit_bar,
            breadcrumb, node_info,
            NodeViewer,
)
from cmsfix.lib.workflow import get_workflow


class JournalNodeViewer(NodeViewer):

    def index(self, request=None):

        # journal and journal item always require authenticated users

        request = request or self.request
        if not request.user:
            return error_page(request, 'Forbidden page!')

        return self.render(request)


    def render(self, request):

        node = self.node
        #content = div(breadcrumb(request, node), node_info(request, node))
        content = div(
            h2(node.title),
        )

        if node.user_id == request.user.id:
            content.add(
                a('Create new log', class_='btn btn-success',
                    href=request.route_url('node-add', path=node.url,
                            _query = { 'type': JournalItemNode.__name__})
                ),
            )

        tbl_body = tbody()
        for n in node.children:
            tbl_body.add(
                tr(
                    td(a(str(n.log_date), href=request.route_url('node-index', path=n.url))),
                    td(str(n.create_time)),
                    td('draft'),
                    td(n.title)
                )
            )
        log_table = table(class_='table table-condensed table-striped')
        log_table.add(
            thead(
                tr(
                    th('Date', style='width: 6em;'),
                    th('Submitted at', style='width: 12em;'),
                    th('Status', style='width: 6em;'),
                    th('Title')
                )
            )
        )
        log_table.add( tbl_body )

        content.add( log_table )

        return render_to_response('cmsfix:templates/node/generics.mako',
            {
                'content': content,
                'toolbar': self.toolbar(request),
            }, request = request)


    def edit_form(self, request, create=False):

        dbh = get_dbhandler()
        n = self.node

        eform, jscode = super().edit_form(request, create)
        eform.get('cmsfix.node-main').add(
            input_text('cmsfix-title', 'Title', value=n.title, offset=1),
            input_textarea('cmsfix-desc', 'Description', value=n.desc, offset=1, size="3x8")
        )

        return eform, jscode


    def parse_form(self, f, d=None):

        d = super().parse_form(f, d)
        d['title'] = f['cmsfix-title']
        d['desc'] = f['cmsfix-desc']

        return d


    def toolbar_xxx(self, request):
        """ a much simple toolbar, only has view, edit, delete and publish button """

        n = self.node
        bar = nav(class_='navbar navbar-default')[
            div(class_='container-fluid')[
                div(class_='collapse navbar-collapse')[
                    ul(class_='nav navbar-nav')[
                        li(a('View', href=request.route_url('node-view', path=n.url))),
                        li(a('Edit', href=request.route_url('node-edit', path=n.url))),
                        #get_add_menu(n, request),
                    ],
                    ul(class_='nav navbar-nav navbar-right')[
                        li(a('Delete')),
                        li(a('Publish')),
                    ]
                ]

            ]

        ]
        return bar


def index_xxx(request, node):

    if not request.user:
        return error_page(request, 'Forbidden page!')

    return view(request, node)


def view_xxx(request, node):

    content = div(breadcrumb(request, node), node_info(request, node))
    content.add(
        h2(node.title),
    )

    if node.user_id == request.user.id:
        content.add(
            a('Create new log', class_='btn btn-success',
                href=request.route_url('node-add', path=node.url,
                        _query = { 'type': JournalItemNode.__name__})
            ),
        )

    tbl_body = tbody()
    for n in node.children:
        tbl_body.add(
            tr(
                td(a(str(n.log_date), href=request.route_url('node-index', path=n.url))),
                td(str(n.create_time)),
                td('draft'),
                td(n.title)
            )
        )
    log_table = table(class_='table table-condensed table-striped')
    log_table.add(
        thead(
            tr(
                th('Date', style='width: 6em;'),
                th('Submitted at', style='width: 12em;'),
                th('Status', style='width: 6em;'),
                th('Title')
            )
        )
    )
    log_table.add( tbl_body )

    content.add( log_table )


    return render_to_response('cmsfix:templates/node/generics.mako',
        {
            'content': content,
        }, request = request)


def content_xxx(request, node):
    pass


def add_xxx(request, node):

    if request.method == 'POST':

        # XXX: need sanity check

        d = parse_form(request.params)
        n = JournalNode()
        get_workflow().set_defaults(n, request.user, node)
        n.update(d)
        if not n.slug:
            n.generate_slug()
        node.add(n)
        get_dbhandler().session().flush()
        n.ordering = 19 * n.id

        if request.params['_method'].endswith('_edit'):
            return HTTPFound(location = request.route_url('node-edit', path=n.url))

        return HTTPFound(location = n.path)

    with get_dbhandler().session().no_autoflush:

        new_node = JournalNode()
        new_node.parent_id = node.id
        new_node.site = node.site
        new_node.user_id = request.user.id
        new_node.group_id = node.group_id

        eform, jscode = edit_form(new_node, request, create=True)

        return render_to_response('cmsfix:templates/node/edit.mako',
            {   'parent_url': node.path,
                'node': new_node,
                'toolbar': '', # new node does not have toolbar yet!
                'eform': eform,
                'code': jscode,
            }, request = request )


def edit_xxx(request, node):

    if request.POST:


        pass

    eform, jscode = edit_form(node, request)

    return render_to_response('cmsfix:templates/node/edit.mako',
        {   'parent_url': node.path,
            'node': node,
            'toolbar': '', # new node does not have toolbar yet!
            'eform': eform,
            'code': jscode,
        }, request = request )


def toolbar_xxx(request, node):
    """ a much simple toolbar, only has view, edit, delete and publish button """

    bar = nav(class_='navbar navbar-default')[
        div(class_='container-fluid')[
            div(class_='collapse navbar-collapse')[
                ul(class_='nav navbar-nav')[
                    li(a('View', href=request.route_url('node-view', path=n.url))),
                    li(a('Edit', href=request.route_url('node-edit', path=n.url))),
                    get_add_menu(n, request),
                ],
                ul(class_='nav navbar-nav navbar-right')[
                    li(a('Delete')),
                    li(a('Publish')),
                ]
            ]

        ]

    ]
    return bar


## internal functions

def edit_form_xxx(node, request, create=False):

    dbh = get_dbhandler()

    eform, jscode = node_edit_form(node, request, create)
    eform.get('cmsfix.node-main').add(
        input_text('cmsfix-title', 'Title', value=node.title, offset=1),
        input_textarea('cmsfix-desc', 'Description', value=node.desc, offset=1, size="3x8")
    )

    return eform, jscode


def parse_form_xxx(f, d=None):

    d = node_parse_form(f, d)
    d['title'] = f['cmsfix-title']
    d['desc'] = f['cmsfix-desc']

    return d
