
# basic, default renderer

from rhombus.lib.tags import *
from rhombus.views import *

from cmsfix.lib.workflow import get_workflow
from cmsfix.views import *
from cmsfix.views.node import get_toolbar, get_node, get_add_menu


from pyramid.renderers import render_to_response


class NodeViewer(object):


    def __init__(self, node, request):
        self.node = node
        self.request = request


    # HTTP-accessible methods

    def index(self, request=None):
        req = request or self.request
        return self.render(req)

    def view(self, request=None):
        return self.index(request)

    def content(self, request=None):
        req = request or self.request

    def edit(self, request=None):
        req= request or self.request

    def add(self, request=None):
        req = request or self.request

    def info(self, request=None):
        req = request or self.request

    def action(self, request=None):
        req = request or self.request


    # internal methods

    def render(self, request):
        pass

    def edit_form(self, request):
        pass

    def parse_form(self, request):
        pass


    def breadcrumb(self, request):

        leaf = self.node
        slugs = []
        while leaf:
            slugs.append( (leaf.title, leaf.path) )
            leaf = leaf.parent

        slugs = reversed(slugs)

        # use bootstrap's breadcrumb
        html = ol(class_='breadcrumb')
        for (title, url) in slugs:
            html.add(
                li(a(title, href=url))
            )

        return html


    def toolbar(self, request, workflow=None):

        n = self.node

        if not request.user:
            return div('')

        if not workflow:
            wf = get_workflow(n)
        else:
            wf = workflow

        if not wf.is_manageable(n, request.user):
            return div(node_info(request, n))

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

        return div(breadcrumb(request, n), node_info(request, n), bar)


def index(request, node):

    return render_node(node, request)


def render_node(node, request):

    pass


def render_node_content(node, request):

    table_body = tbody()
    for n in node.children:
        wf = get_workflow(n)
        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="node-ids" value="%d">' % n.id)),
                td(a(n.title or n.slug, href=request.route_url('node-index', path=n.url))),
                td(n.id),
                td(n.__class__.__name__),
                td(n.user.login),
                td(str(n.stamp)),
                td(n.lastuser.login),
                td( span(wf.states[n.state], class_=wf.styles[n.state]) )
            )
        )

    content_table = table(class_='table table-condensed table-striped')
    content_table.add(
        thead(
            tr(
                th('', style="width:2em;"),
                th('Title'),
                th('ID'),
                th('Node type'),
                th('User'),
                th('Last modified'),
                th('Last user'),
                th('State')
            )
        ),
        table_body
    )

    content_bar = selection_bar('node-ids',
                action=request.route_url('node-action', path=node.url))
    content_table, content_js = content_bar.render(content_table)

    html = row( div(content_table, class_='col-md-10') )

    return render_to_response('cmsfix:templates/node/content.mako',
            {   'node': node,
                'toolbar': get_toolbar(node, request),
                'html': html,
                'code': content_js,
            }, request = request )


def node_submit_bar(create=True):
    if create:
        return custom_submit_bar(('Create', 'create'), ('Create and continue editing', 'create_edit')).set_offset(1)
    return custom_submit_bar(('Save', 'save'), ('Save and continue editing', 'save_edit')).set_offset(1)


def edit_form(node, request, create=False):

    dbh = get_dbhandler()

    eform = form( name='cmsfix/node', method=POST )
    eform.add(

        fieldset(
            input_hidden(name='cmsfix-parent_id', value=node.parent_id),
            #input_hidden(name='cmsfix-user_id', value=request.user.id),
            input_hidden(name='cmsfix-stamp', value='%15f' % node.stamp.timestamp() if node.stamp else -1),
            input_text('cmsfix-slug', 'Slug', value=node.slug, offset=1),
            multi_inputs(name='cmsfix-group-user-type')[
            input_select('cmsfix-group_id', 'Group', value=node.group_id, offset=1, size=2,
                options = [ (g.id, g.name) for g in dbh.get_group() ]),
            input_select('cmsfix-user_id', 'User', value=node.user_id, offset=1, size=2,
                options = [ (u.id, u.login) for u in dbh.get_user(request.user.id).group_users() ]),
            input_select_ek('cmsfix-mimetype_id', 'MIME type', value=node.mimetype_id,
                parent_ek = dbh.get_ekey('@MIMETYPE'), offset=1, size=2),
            ],
            name='cmsfix.node-header'
        ),
        fieldset(name='cmsfix.node-main'),
        fieldset(
            input_select('cmsfix-tags', 'Tags', offset=1, multiple=True),
            node_submit_bar(create),
            name='cmsfix.node-footer'
        )
    )

    jscode = '''
    $("#cmsfix-tags").select2({
        tags: true,
        tokenSeparators: [',',' '],
        minimumInputLength: 3,
        ajax: {
            url: "%s",
            dataType: 'json',
            data: function(term, page) { return { q: term }; },
            results: function(data, page) { return { results: data }; }
        }
    });
    
    ''' % request.route_url('tag-lookup')
    return eform, jscode



def parse_form( f, d = None ):

    d = d or dict()
    d['_stamp_'] = float(f['cmsfix-stamp'])
    d['slug'] = f.get('cmsfix-slug', None)
    if 'cmsfix-group_id' in f:
        d['group_id'] = int(f.get('cmsfix-group_id'))
    if 'cmsfix-user_id' in f:
        d['user_id'] = int(f.get('cmsfix-user_id'))
    if 'publish_time' in f:
        d['publish_time'] = f.get('cmsfix-publish_time')
    if 'expire_time' in f:
        d['expire_time'] = f.get('cmsfix-expire-_time')
    d['mimetype_id'] = int(f.get('cmsfix-mimetype_id', 0))
    if 'tags' in f:
        d['tags'] = f.getall('cmsfix-tags')

    return d


def toolbar(request, n, workflow=None):

    if not request.user:
        return div(breadcrumb(request, n))

    if not workflow:
        wf = get_workflow(n)
    else:
        wf = workflow

    if not wf.is_manageable(n, request.user):
        return div(breadcrumb(request, n), node_info(request, n))

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

    return div(breadcrumb(request, n), node_info(request, n), bar)


class nav(doubletag):
    _tag = 'nav'


def breadcrumb(request, n):

    leaf = n
    slugs = []
    while leaf:
        slugs.append( (leaf.title, leaf.path) )
        print(leaf)
        leaf = leaf.parent

    slugs = reversed(slugs)

    # use bootstrap's breadcrumb
    html = ol(class_='breadcrumb')
    for (title, url) in slugs:
        html.add(
            li(a(title, href=url))
        )

    return html


def node_info(request, n):
    return p('Site: %s | Page ID: %s | URL: %s' % (n.site.fqdn, n.id, n.path))
