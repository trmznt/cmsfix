
# basic, default renderer

from rhombus.lib.tags import *
from rhombus.views import *
from rhombus.lib.utils import random_string

from cmsfix.lib.workflow import get_workflow
from cmsfix.views import *
from cmsfix.views.node import get_toolbar, get_node, get_add_menu


from pyramid.renderers import render_to_response


class NodeViewer(object):

    template_edit = 'cmsfix:templates/node/edit.mako'
    template_view = 'cmsfix:templates/node/node.mako'
    next_route_name = 'node-index'


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
        return self.render_content(req)

    def edit(self, request=None):
        req = request or self.request

        n = self.node
        if req.method == 'POST':
            # update data

            n.update( self.parse_form(req.params) )

            if req.params['_method'] == 'save_edit':
                return HTTPFound(location = req.route_url('node-edit', path=n.url))

            print(n.url)
            return HTTPFound(location = req.route_url(self.next_route_name, path=n.url))

        eform, jscode = self.edit_form(req)

        return self.render_edit_form(req, eform, jscode)


    def add(self, request=None, parent_node=None):

        req = request or self.request

        assert(parent_node != None)

        # all permission has been taken care by workflow, so assume
        # every sanity checked has been performed

        if req.method == 'POST':

            self.pre_save_node(req)

            n = self.node = self.new_node()
            get_workflow(n).set_defaults(n, req.user, parent_node)
            n.update(self.parse_form(req.params))
            if not n.slug:
                n.generate_slug()
            parent_node.add(n)
            get_dbhandler().session().flush()
            n.ordering = 19 * n.id

            self.post_save_node(req)

            if req.params['_method'].endswith('_edit'):
                return HTTPFound(location = req.route_url('node-edit', path=n.url))

            return HTTPFound(location = req.route_url(self.next_route_name, path=n.url))

        dbh = get_dbhandler()
        with dbh.session().no_autoflush:

            # create a dummy instance just for the purpose of showing edit form
            self.node = self.new_node()
            get_workflow(self.node).set_defaults(self.node, req.user, parent_node)
            # temporarily assigning parent for breadcrumb purposes
            #self.node.parent_id = parent_node.id
            #self.node.site = parent_node.site
            #self.node.user_id = req.user.id

            eform, jscode = self.edit_form(req, create=True)

        return self.render_edit_form(req, eform, jscode, parent_node)


    def info(self, request=None):
        req = request or self.request
        return self.render_info(req)

    def action(self, request=None):
        req = request or self.request


    # renderer methods

    def render(self, request):
        pass

    def render_edit_form(self, request, eform, jscode, parent_node=None):

        node = self.node

        return render_to_response(self.template_edit,
            {   'parent_url': ('/' + node.parent.url) if node.parent else 'None',
                'node': node,
                'breadcrumb': self.breadcrumb(request, parent_node) if parent_node else self.breadcrumb(request),
                'stickybar': self.editingbar(request),
                'eform': eform,
                'code': jscode,
            }, request = request )


    def render_content(self, request):

        node = self.node
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
                    'breadcrumb': self.breadcrumb(request),
                    'html': html,
                    'stickybar': self.statusbar(request),
                    'code': content_js,
                }, request = request )


    def render_info(self, request):

        n = self.node

        html = div()
        html.add( p('Creator: %s' % n.user.login) )
        html.add( p('Group: %s' % n.group.name) )

        return render_to_response('cmsfix:templates/node/info.mako',
                {   'node': n,
                    'breadcrumb': self.breadcrumb(request),
                    'stickybar': self.statusbar(request),
                    'html': html,
                }, request = request )


    # editing methods

    def parse_form(self, f, d=None):

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


    def edit_form(self, request, create=False):

        dbh = get_dbhandler()
        node = self.node

        eform = form( name='cmsfix/node', method=POST )
        eform.add(

            self.hidden_fields( request, node ),
            
            fieldset(
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
                node_submit_bar(create).set_hide(True),
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


    def pre_save_node(self, request):
        pass

    def post_save_node(self, request):
        pass

    def hidden_fields(self, request, node=None):
        node = node or self.node
        return fieldset (
            input_hidden(name='cmsfix-parent_id', value=node.parent_id),
            input_hidden(name='cmsfix-stamp', value='%15f' % node.stamp.timestamp() if node.stamp else -1),
            input_hidden(name='cmsfix-sesskey', value=generate_sesskey(request.user.id, node.id)),
            name="cmsfix.node-hidden"
        )


    def breadcrumb(self, request):

        leaf = self.node
        slugs = []
        while leaf:
            slugs.append( (leaf.title, leaf.path) )
            leaf = leaf.parent

        slugs = reversed(slugs)

        # use bootstrap's breadcrumb
        html = div(ol(class_='breadcrumb'))
        for (title, url) in slugs:
            html.add(
                li(a(title, href=url))
            )

        return html

    def breadcrumb(self, request, node=None):

        leaf = node or self.node
        slugs = []
        while leaf:
            slugs.append( (leaf.render_title(), leaf.path) )
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


    def toolbar(self, request, workflow=None):

        n = self.node

        if not n.id:
            # this is a new node, we don't full provide toolbar
            return div('Please create and save this node to get full toolbar.')

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


    def statusbar(self, request, workflow=None):

        if not request.user:
            return ''

        n = self.node
        wf = workflow or get_workflow(n)

        if not wf.is_manageable(n, request.user):
            bar = div(class_='collapse navbar-collapse')[
                    ul(name='cmsfix.statusbar.left', class_='nav navbar-nav')[
                        li(a('[Node ID: %d]' % n.id)),
                    ]
                ]

        else:
            bar = div(class_='collapse navbar-collapse dropup')[
                    ul(name='cmsfix.statusbar.left', class_='nav navbar-nav')[
                        li(a('[Node ID: %d]' % n.id)),
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

        return nav(class_='navbar navbar-default')[
            div(class_='container-fluid')[
                bar
            ]
        ]


    def editingbar(self, request, workflow=None):

        n = self.node
        wf = workflow or get_workflow(n)

        if not wf.is_editable(n, request.user):
            bar = div(class_='collapse navbar-collapse')[
                    ul(name='cmsfix.editingbar.left', class_='nav navbar-nav')[
                        li('[Node ID: %d]' % n.id if n.id else '[Node ID: Undefined]'),
                    ],
                    ul(name='cmsfix.editingbar.right', class_='nav navbar-nav navbar-right')
                ]

        else:
            labels = self.submit_bar_text()
            bar = div(class_='collapse navbar-collapse dropup')[
                    ul(name='cmsfix.editingbar.left', class_='nav navbar-nav')[
                        li(a('[Node ID: %d]' % n.id) if n.id else a('[Node ID: Undefined]')),
                        li(a(span(labels[0], class_='btn btn-primary navbar-btn'),
                                onclick=literal(r"$('#_method\\.save').click();"))),
                        li(a(span(labels[1], class_='btn btn-primary navbar-btn'),
                                onclick=literal(r"$('#_method\\.save_edit').click();"))),
                    ],
                    ul(name='cmsfix.editingbar.right', class_='nav navbar-nav navbar-right')[
                        li(a(span('Cancel', class_='btn btn-primary navbar-btn'),
                                onclick=literal("alert('Not implemented yet');"))),
                    ]
                ]

        return nav(class_='navbar navbar-default')[
            div(class_='container-fluid')[
                bar
            ]
        ]


    def submit_bar_text(self):
        if not self.node.id:
            return ('Create', 'Create and continue editing')
        return ('Save', 'Save and continue editing')


def generate_sesskey(user_id, node_id=None):
    if node_id:
        node_id_part = '%08x' % node_id
    else:
        node_id_part = 'XXXXXXXX'

    return '%08x%s%s' % (user_id, random_string(8), node_id_part)


def index(request, node):

    return render_node(node, request)


def render_node(node, request):

    pass


def render_node_content_xxx(node, request):

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
        return custom_submit_bar(('Create', 'save'), ('Create and continue editing', 'save_edit')).set_offset(1)
    return custom_submit_bar(('Save', 'save'), ('Save and continue editing', 'save_edit')).set_offset(1)


def edit_form_xxx(node, request, create=False):

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



def parse_form_xxx( f, d = None ):

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


def toolbar_xxx(request, n, workflow=None):

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
        slugs.append( (leaf.render_title(), leaf.path) )
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
