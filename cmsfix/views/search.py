# search interface

from rhombus.lib.utils import get_dbhandler
from rhombus.views import *
from cmsfix.views import *

from cmsfix.lib.whoosh import get_index_service, SearchScheme
from whoosh.qparser import QueryParser
from whoosh.query import Term

def index(request):
    """ return a basic form if no params """

    if 'q' in request.params:

        q = request.params.get('q')
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

        html = div()[ div(h3('Search Result'))]
        for nodeid in node_ids:
            node = dbh.get_node_by_id(nodeid)
            html.add(
                div(class_='row')[
                    div(class_='col-md-1')[
                        node.stamp.date(), br(), 'by', node.lastuser.login, br()
                    ],
                    div(class_='col-md-11')[
                        a(h5(node.title), href=node.url), br(), node.summary
                    ]
                ]
            )

        return render_to_response('cmsfix:templates/node/generics.mako',
                { 'content': html,
                }, request = request )



    raise NotImplementedError()


def action(request):

    raise NotImplementedError()