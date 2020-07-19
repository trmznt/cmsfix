# search interface

from rhombus.lib.utils import get_dbhandler
from rhombus.views import *
from cmsfix.views import *

from cmsfix.lib.workflow import get_workflow
from cmsfix.lib.whoosh import get_index_service, SearchScheme
from whoosh.qparser import QueryParser
from whoosh.query import Term

def index(request):
    """ return a basic form if no params """

    html = div()[ div(h3('Search'))]

    q = request.params.get('q', '')
    html.add(
        form(action="/search", name="search-form")[
            input_text("q", label = "Query", offset=1, value=q),
        ],
        br()

    )

    if q:

        fqdn = get_site(request)

        dbh = get_dbhandler()
        siteid = dbh.get_site(fqdn).id

        index_service = get_index_service()

        qp = QueryParser('text', schema=index_service.ix.schema)
        query = qp.parse(q)
        allow_q = Term('siteid', siteid)

        with index_service.ix.searcher() as searcher:
            results = searcher.search(query, filter=allow_q)
            node_ids = [ r['nodeid'] for r in results ]

        html.add( div(h4('Search Result')) )
        for nodeid in node_ids:
            node = dbh.get_node_by_id(nodeid)

            # check for accessibility of the node toward current user
            if not get_workflow(node).is_accessible(node, request):
                continue

            html.add(
                div(class_='row')[
                    div(class_='col-md-1')[
                        node.stamp.date(), 'by', node.lastuser.login,
                    ],
                    div(class_='col-md-11')[
                        a(div(node.path, br(), h5(node.title)), href=node.url), br(),
                        node.summary if hasattr(node, 'summary') else 
                        ( node.desc if hasattr(node, 'desc') else '')
                    ]
                ]
            )

        return render_to_response('cmsfix:templates/node/generics.mako',
                { 'content': html,
                }, request = request )


    return render_to_response('cmsfix:templates/node/generics.mako',
            { 'content': html,
            }, request = request )


def action(request):

    raise NotImplementedError()