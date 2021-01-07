
from cmsfix.models.journalnode import JournalNode, JournalItemNode, object_session
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
            self.breadcrumb(request),
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
        #for n in node.children:
        for n in JournalItemNode.query(object_session(node))\
                .filter(JournalItemNode.parent_id == node.id)\
                .order_by(JournalItemNode.log_date.desc()):
            wf = get_workflow(n)
            tbl_body.add(
                tr(
                    td(a(str(n.log_date), href=request.route_url('node-index', path=n.url))),
                    td(n.create_time.strftime("%Y-%m-%d %H:%M")),
                    td(span(wf.states[n.state], class_=wf.styles[n.state])),
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
                'stickybar': self.statusbar(request),
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


    def new_node(self):

        n = JournalNode()
        n.mimetype_id = get_dbhandler().get_ekey('text/x-rst').id
        return n
