
from rhombus.lib.utils import cout, cerr, get_dbhandler
from rhombus.lib.tags import *
from cmsfix.lib.renderer import *


def render_node(n, request):

    toolbar = ''
    if n.is_manageable(request.user):
        # show admin bar
        toolbar = node_toolbar(n, request)

    html = 'Hello, from node'

    return render_to_response('cmsfix:templates/node/node.mako',
            {   'node': n,
                'toolbar': toolbar,
                'html': html,
            }, request = request )


class nav(doubletag):
    _tag = 'nav'


def node_toolbar(n, request):
    """ return node toolbar """

    return '<div id="toolbar>Tool Bar</div>'


def menu_level_1(n, request):
    """ return top-most level navigation """
    dbh = get_dbhandler()
    root_page = dbh.get_node('/')


def menu_level_2(n, request):
    """ return 2nd level navigation """
    pass