
# basic, default renderer

from rhombus.lib.tags import *
from rhombus.views import *
from rhombus.lib.utils import random_string

from cmsfix.lib.workflow import get_workflow
from cmsfix.lib import cmds
from cmsfix.views import *
from cmsfix.views.node import get_toolbar, get_node, get_add_menu, get_class


from pyramid.renderers import render_to_response

import json


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
            get_workflow(n).set_defaults(n, req, parent_node)
            n.update(self.parse_form(req.params))
            #if not n.slug:
            #    n.generate_slug()
            #parent_node.add(n)
            #get_dbhandler().session().flush()
            #n.ordering = 19 * n.id
            cmds.add(parent_node, n)

            self.post_save_node(req)

            if req.params['_method'].endswith('_edit'):
                return HTTPFound(location = req.route_url('node-edit', path=n.url))

            return HTTPFound(location = req.route_url(self.next_route_name, path=n.url))

        dbh = get_dbhandler()
        with dbh.session().no_autoflush:

            # create a dummy instance just for the purpose of showing edit form
            self.node = self.new_node()
            get_workflow(self.node).set_defaults(self.node, req, parent_node)
            # temporarily assigning parent for breadcrumb purposes
            #self.node.parent_id = parent_node.id
            #self.node.site = parent_node.site
            #self.node.user_id = req.user.id

            eform, jscode = self.edit_form(req, create=True)

        return self.render_edit_form(req, eform, jscode, parent_node)


    def info(self, request=None):
        req = request or self.request
        return self.render_info(req)


    def properties(self, request=None):
        req = request or self.request

        n = self.node
        if req.method == 'POST':
            # update data

            n.update( self.parse_form(req.params) )

            print(n.url)
            return HTTPFound(location = req.route_url('node-properties', path=n.url))

        pform, jscode = self.properties_form(req)

        return self.render_properties_form(req, pform, jscode)


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
        children = list(node.children)
        for idx, n in enumerate(children):
            prev_idx = max(0, idx-1)
            next_idx = min(idx+1, len(children)-1)
            wf = get_workflow(n)
            table_body.add(
                tr(
                    td(literal('<input type="checkbox" name="node-ids" value="%d">' % n.id)),
                    td(a(n.title or n.slug, href=request.route_url('node-content', path=n.url))),
                    td(n.id),
                    td(n.__class__.__name__),
                    td(n.user.login),
                    td(str(n.stamp)),
                    td(n.lastuser.login if n.lastuser else '-'),
                    td(a(literal('&#9650;'),
                            href=request.route_url('node-action', path=n.url,
                            _query = { '_method': 'swap-order',
                                        'nodeid1': children[idx].id,
                                        'ordering1': children[idx].ordering,
                                        'nodeid2': children[prev_idx].id,
                                        'ordering2': children[prev_idx].ordering,
                            })),
                        literal('&nbsp;'),
                        a(literal('&#9660;'),
                            href=request.route_url('node-action', path=n.url,
                            _query = { '_method': 'swap-order',
                                        'nodeid1': children[idx].id,
                                        'ordering1': children[idx].ordering,
                                        'nodeid2': children[next_idx].id,
                                        'ordering2': children[next_idx].ordering,
                            }))
                    ),
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
                    th('Order'),
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


    def render_properties_form(self, request, pform, jscode):
        """ properties form """

        node = self.node
        pform.get('cmsfix.node-footer').add(
            custom_submit_bar(('Save', 'save')).set_offset(1),
            )

        return render_to_response(self.template_edit,
            {   'parent_url': ('/' + node.parent.url) if node.parent else 'None',
                'node': node,
                'breadcrumb': self.breadcrumb(request),
                'stickybar': self.statusbar(request),
                'eform': pform,
                'code': jscode,
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
        if 'cmsfix-publish_time' in f:
            d['publish_time'] = f.get('cmsfix-publish_time')
        if 'cms-expire_time' in f:
            d['expire_time'] = f.get('cmsfix-expire_time')
        if 'cmsfix-mimetype_id' in f:
            d['mimetype_id'] = int(f.get('cmsfix-mimetype_id', 0))
        if 'cmsfix-tags' in f:
            d['tags'] = [ int(i) for i in f.getall('cmsfix-tags') ]
        if 'cmsfix-options' in f:
            d['listed'] = True if 'cmsfix-listed' in f else False
        if 'cmsfix-json_code' in f:
            d['json_code'] = json.loads(f.get('cmsfix-json_code').strip() or '{}')

        return d


    def edit_form(self, request, create=False):

        if create:
            pform, jscode = self.properties_form(request, create=create)

        else:
            pform, jscode = self.properties_form(request)

        # add node_submit_bar
        pform.get('cmsfix.node-footer').add( node_submit_bar(create).set_hide(True) )

        return pform, jscode


    def properties_form(self, request, create=False, static=False):

        dbh = get_dbhandler()
        node = self.node

        # prepare tags
        tags = node.tags
        tag_ids = [ t.tag_id for t in tags ]
        tag_options = [ (t.tag_id, '%s [ %s ]' % (t.tag.key, t.tag.desc)) for t in tags ]

        pform = form( name='cmsfix/node', method=POST )
        pform.add(

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
                input_select('cmsfix-tags', 'Tags', offset=1, multiple=True,
                    options = tag_options, value = tag_ids ),
                # below is a mean to flag that we have options in the form
                input_hidden(name='cmsfix-options', value=1),
                checkboxes('cmsfix-option-group', 'Options', [
                    ('cmsfix-listed', 'Listed', node.listed),
                ], offset=1 ),
                input_textarea('cmsfix-json_code', 'JSON Code',
                    value=json.dumps(node.json_code), offset=1, size='5x8'),
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
                data: function(params) { return { q: params.term }; },
                processResults: function(data, params) { return { results: data }; }
            }
        });

        ''' % request.route_url('tag-lookup')

        return pform, jscode


    def pre_save_node(self, request):
        pass

    def post_save_node(self, request):
        pass

    def new_node(self):
        return get_class(type(self))()

    def hidden_fields(self, request, node=None):
        node = node or self.node
        return fieldset (
            input_hidden(name='cmsfix-parent_id', value=node.parent_id),
            input_hidden(name='cmsfix-stamp', value='%15f' % node.stamp.timestamp() if node.stamp else -1),
            input_hidden(name='cmsfix-sesskey', value=generate_sesskey(request.user.id, node.id)),
            name="cmsfix.node-hidden"
        )


    def breadcrumb_xxx(self, request):

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
                li(a(title, href=url), class_='breadcrumb-item')
            )

        return nav(html)


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

        if not wf.is_manageable(n, request):
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

        if not wf.is_manageable(n, request):
            bar = div(class_='collapse navbar-collapse')[
                    span('[Node ID: %d]' % n.id, class_='navbar-text'),
                ]

        else:
            bar = div(class_='collapse navbar-collapse')[
                    span('[Node ID: %d]' % n.id, class_='navbar-text'),

                    ul(name='cmsfix.statusbar.left', class_='navbar-nav mr-auto')[
                        li(
                            a('View', href=request.route_url('node-view', path=n.url),
                                class_='nav-link'), class_='nav-item'),
                        li(
                            a('Edit', href=request.route_url('node-edit', path=n.url),
                                class_='nav-link'), class_='nav-item'),
                        li(
                            a('Content', href=request.route_url('node-content', path=n.url),
                                class_='nav-link'), class_='nav-item'),
                        li(
                            a('Info', href=request.route_url('node-info', path=n.url),
                                class_='nav-link'), class_='nav-item'),

                        li(
                            a('Properties', href=request.route_url('node-properties', path=n.url),
                                class_='nav-link'), class_='nav-item'),

                        get_add_menu(n, request),
                    ],
                    ul(class_='navbar-nav')[
                        li(a('Delete', class_='nav-link'), class_='nav-item'),
                        wf.show_menu(n, request)
                    ]
                ]

        return nav(class_='navbar fixed-bottom navbar-default navbar-expand-sm '
            'navbar-light statusbar')[
                bar
        ]


    def editingbar(self, request, workflow=None):

        n = self.node
        wf = workflow or get_workflow(n)

        if not wf.is_editable(n, request):
            bar = div(class_='collapse navbar-collapse')[
                    ul(name='cmsfix.editingbar.left', class_='nav navbar-nav')[
                        li('[Node ID: %d]' % n.id if n.id else '[Node ID: Undefined]'),
                    ],
                    ul(name='cmsfix.editingbar.right', class_='nav navbar-nav navbar-right')
                ]

        else:
            labels = self.submit_bar_text()
            bar = div(class_='collapse navbar-collapse dropup')[
                    span(('[Node ID: %d]' % n.id) if n.id else ('[Node ID: Undefined]'),
                        class_='navbar-text mr-2'),

                    ul(name='cmsfix.editingbar.left', class_='navbar-nav mr-auto')[

                        li(
                            span(labels[0], class_='btn btn-primary navbar-btn mr-2',
                                onclick=literal(r"$('#_method\\.save').click();"))),
                        li(
                            span(labels[1], class_='btn btn-primary navbar-btn mr-2',
                                onclick=literal(r"$('#_method\\.save_edit').click();"))),

                    ],
                    ul(name='cmsfix.editingbar.right', class_='navbar-nav')[
                        li(span('Cancel', class_='btn btn-warning navbar-btn'),
                                onclick=literal("alert('Not implemented yet');")),
                    ]
                ]

        return nav(class_='navbar fixed-bottom navbar-default navbar-expand-sm '
            'navbar-light statusbar')[
                bar
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


def index_xxx(request, node):

    return render_node(node, request)


def render_node_xxx(node, request):

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
