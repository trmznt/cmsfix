# search interface

from rhombus.lib.utils import get_dbhandler
from rhombus.views import *

from cmsfix.lib.whoosh import get_index_service, SearchScheme
from whoosh.qparser import QueryParser

def index(request):
    """ return a basic form if no params """

    if 'q' in request.params:

        q = request.params.get('q')

        index_service = get_index_service()

        qp = QueryParser('text', schema=index_service.ix.schema)
        query = qp.parse(q)

        with index_service.ix.searcher() as searcher:
            results = searcher.search(query)
            node_ids = [ r['nodeid'] for r in results ]

        dbh = get_dbhandler()

        html = div()
        for nodeid in node_ids:
            node = dbh.get_node_by_id(nodeid)
            html.add(
                div(class_='row')[
                    div(class_='col-md-1')[
                        'Modified at:', br(), 'by', br()
                    ],
                    div(class_='col-md-11')[
                        h3(node.title), br(), node.summary
                    ]
                ]
            )

        return render_to_response('cmsfix:templates/node/generics.mako',
                { 'content': html,
                }, request = request )



    raise NotImplementedError()


def action(request):

    raise NotImplementedError()