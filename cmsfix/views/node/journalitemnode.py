from cmsfix.models.journalnode import JournalItemNode
from cmsfix.views import *
from cmsfix.views.node.node import ( nav, node_submit_bar, breadcrumb,
)
from cmsfix.views.node.pagenode import render_rst, PageNodeViewer
from cmsfix.lib.workflow import get_workflow
from dateutil.parser import parse as parse_date
from cmsfix.lib.macro import postrender


import time, datetime


class JournalItemNodeViewer(PageNodeViewer):

    template_view = 'cmsfix:/templates/journalitemnode/node.mako'


    def new_node(self):
        n = JournalItemNode()
        n.log_date = datetime.date.today()
        n.mimetype_id = get_dbhandler().get_ekey('text/x-rst').id
        return n


    def edit_form(self, request, create=False):
        """ use a simple interface for journal """

        dbh = get_dbhandler()
        n = self.node

        eform = form( name='cmsfix/node', method=POST )
        eform.add(

            self.hidden_fields(request, n),

            fieldset(
                input_text('cmsfix-log_date', 'Log Date', value=n.log_date, offset=1) if create else
                input_show('', 'Log Date', value=n.log_date, offset=1),
                input_hidden('cmsfix-mimetype_id', value=dbh.EK.getid('text/x-rst', dbh.session())),
                name='cmsfix.node-header'
            ),

            fieldset(
                input_text('cmsfix-title', 'Title', value=n.title, offset=1),
                input_textarea('cmsfix-content', 'Content', value=n.content, offset=1, size="18x8"),
                input_textarea('cmsfix-summary', 'Summary', value=n.summary, offset=1, size="3x8"),
                name='cmsfix.node-main'),

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
        })
        ''' % request.route_url('tag-lookup')

        jscode += 'var html_mimetype=%d;\n' % dbh.EK.getid('text/html', dbh.session())

        return eform, jscode


    def parse_form(self, f, d = None):

        d = super().parse_form(f, d)
        if 'cmsfix-log_date' in f:
            d['log_date'] = parse_date(f['cmsfix-log_date'], dayfirst=False)
        return d


    def statusbar(self, request):

        bar = super().statusbar(request)
        states, styles = get_workflow(self.node).state_style(self.node)
        if states == 'sealed':
            bar.get('cmsfix.statusbar.left').add(
                li(a('This record has been sealed and cannot be edited anymore')),
                )
        return bar


def xxx_index(request, node):
    return view(request, node)

def xxx_view(request, node):

    content = div()[
        #div( breadcrumb(request, node.parent) ),
        toolbar(request, node),
        h3('Log date: %s | Title: %s' % (node.log_date, node.title) ),

    ]

    if node.mimetype == 'text/x-rst':
        html = literal(render_rst(node.content))
    else:
        html = node.content

    content.add( html )

    return render_to_response('cmsfix:templates/node/generics.mako',
            { 'content': content,
            }, request = request )


def xxx_content(request, node):
    raise NotImplementedError()


def xxx_add(request, node):

    if request.method == 'POST':
        # sanity check

        if node.user_id != request.user.id:
            return error_page(request, 'Journal can only be added by its owner!')

        d = parse_form(request.params)
        n = JournalItemNode()
        wf = get_workflow(n)
        print(wf)
        wf.set_defaults(n, request.user, node)
        n.update(d)
        n.slug = str(time.time())
        node.add(n)
        #n.user_id = request.user.id
        #n.group_id = node.group_id
        #n.lastuser_id = request.user.id
        get_dbhandler().session().flush()
        n.ordering = 19 * n.id

        if request.params['_method'].endswith('_edit'):
            return HTTPFound(location = request.route_url('node-edit', path=n.url))

        return HTTPFound(location = request.route_url('node-index', path=n.url))

    dbh = get_dbhandler()
    with dbh.session().no_autoflush:

        new_node = JournalItemNode()
        new_node.parent_id = node.id
        new_node.site = node.site
        new_node.user_id = request.user.id
        new_node.log_date = datetime.date.today()
        new_node.mimetype_id = dbh.get_ekey('text/x-rst').id

        eform, jscode = edit_form(new_node, request, create=True)

        return render_to_response('cmsfix:templates/node/edit.mako',
            {   'parent_url': '%s <%s>' % (node.title, node.path),
                'node': new_node,
                'toolbar': '', # new node does not have toolbar yet!
                'eform': eform,
                'code': jscode,
            }, request = request )


def xxx_edit(request, node):

    if request.method == "POST":

        # sanity check
        if node.user_id != request.user.id:
            return error_page(request, 'Journal can only be added by its owner!')

        d = parse_form(request.params)
        node.update(d)

        if request.params['_method'].endswith('_edit'):
            return HTTPFound(location = request.route_url('node-edit', path=node.url))

        return HTTPFound(location = request.route_url('node-index', path=node.url))

    else:

        eform, jscode = edit_form(node, request)

        return render_to_response('cmsfix:templates/node/edit.mako',
            {   'parent_url': '%s <%s>' % (node.title, node.path),
                'node': node,
                'toolbar': toolbar(request, node),
                'eform': eform,
                'code': jscode,
            }, request = request )



def xxx_info(request, node):
    raise NotImplementedError()


##

def xxx_edit_form(node, request, create=False):
    """ use a simple interface for journal """

    dbh = get_dbhandler()

    eform = form( name='cmsfix/node', method=POST )
    eform.add(

        fieldset(
            input_hidden(name='cmsfix-stamp', value='%15f' % node.stamp.timestamp() if node.stamp else -1),
            input_text('cmsfix-log_date', 'Log Date', value=node.log_date, offset=1) if create else
            input_show('', 'Log Date', value=node.log_date, offset=1),
            input_select_ek('cmsfix-mimetype_id', 'MIME type', value=node.mimetype_id,
                parent_ek = dbh.get_ekey('@MIMETYPE'), offset=1),
            name='cmsfix.node-header'
        ),
        fieldset(
            input_text('cmsfix-title', 'Title', value=node.title, offset=1),
            node_submit_bar(create),
            input_textarea('cmsfix-content', 'Content', value=node.content, offset=1, size="18x8"),
            input_textarea('cmsfix-summary', 'Summary', value=node.summary, offset=1, size="3x8"),
            name='cmsfix.node-main'),
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
    })
    ''' % request.route_url('tag-lookup')
    return eform, jscode



def xxx_parse_form( f, d = None ):

    d = pagenode_parse_form(f, d)
    if 'cmsfix-log_date' in f:
        d['log_date'] = parse_date(f['cmsfix-log_date'], dayfirst=False)
    return d
