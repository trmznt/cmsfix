
from rhombus.lib.utils import get_dbhandler, cout, cerr
from rhombus.views import *
from rhombus.views.generics import error_page, not_authorized
from rhombus.views.user import get_login_url
from rhombus.lib.tags import *
from rhombus.lib.modals import popup, modal_delete

from cmsfix.lib.workflow import get_workflow
from cmsfix.views import *

import pyramid.httpexceptions as exc

import posixpath


def index(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_accessible(n, request):
        return not_authorized(request, 'Your login is not authorized to access the page.'
            if request.user else a('Please login first.', href=get_login_url(request)))

    #module = get_module(n.__class__)
    viewer = get_viewer(n.__class__)
    return viewer(n, request).index()
    #return module.index(request, n)


@roles(PUBLIC)
def view(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request):
        return not_authorized(request, 'Page is not manageable by current user!')

    #module = get_module(n.__class__)
    viewer = get_viewer(n.__class__)
    return viewer(n, request).view()
    #return module.view(request, n)


@roles(PUBLIC)
def content(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request):
        return not_authorized(request, 'You are not authorized to view the content of this node!')

    viewer = get_viewer(n.__class__)
    return viewer(n, request).content()

    module = get_module(n.__class__)
    return module.content(request, n)


@roles(PUBLIC)
def info(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request):
        return not_authorized(request, 'You are not authorized to view this node meta information')

    viewer = get_viewer(n.__class__)
    return viewer(n, request).info()

    module = get_module(n.__class__)
    toolbar = module.toolbar(request, n)

    html = div()
    html.add( p('Creator: %s' % n.user.login) )
    html.add( p('Group: %s' % n.group.name) )

    return render_to_response('cmsfix:templates/node/info.mako',
            {   'node': n,
                'toolbar': toolbar,
                'html': html,
            }, request = request )


@roles(PUBLIC)
def properties(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request):
        return not_authorized(request, 'You are not authorized to view this node properties')

    # check stamp consistency
    result = check_stamp(request, n)
    if result != True: return result

    viewer = get_viewer(n.__class__)
    return viewer(n, request).properties()


def manage(request):
    pass


@roles(PUBLIC)
def edit(request):
    """ edit & save a node """

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_editable(n, request):
        return not_authorized(request, 'You are not authorized to edit this node!')

    # check stamp consistency
    result = check_stamp(request, n)
    if result != True: return result

    viewer = get_viewer(n.__class__)
    return viewer(n, request).edit()

    module = get_module(n.__class__)
    return module.edit(request, n)


@roles(PUBLIC)
def add(request):
    """ add & save a node """

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request):
        return not_authorized(request, 'You are not authorized to add a new node here!')

    # get the node type
    node_type = request.params.get('type', '')
    if not node_type:
        return error_page(request, 'ERR: no node type to add!')

    for (cls, viewer) in __VIEWERS__.items():
        if cls.__name__ == node_type:
            return viewer(None, request).add(request=None, parent_node=n)

    for (cls, module) in __MODULES__.items():
        if cls.__name__ == node_type:
            return module.add(request, n)

    return error_page(request, 'ERR: unknown node type!!')


@roles(PUBLIC)
def edit_next(request):
    """ forward to next edit url """
    n = get_node(request)
    wf = get_workflow()

    if not wf.is_manageable(n, request):
        return not_authorized(request, 'You are not authorized to view the content of this node!')

    viewer = get_viewer(n.__class__)
    return viewer(n, request).edit_next()

@roles(PUBLIC)
def yaml(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_accessible(n, request):
        return not_authorized(request, 'Page is not accessible!')

    return Response(n.as_yaml(), content_type='text/plain')


@roles(PUBLIC)
def action(request):

    n = get_node(request)

    if request.GET:

        return action_get(request, n)

    elif request.POST:

        return action_post(request, n)

    return error_page(request, 'HTTP method not implemented!')


def action_get(request, node):

    n = node

    if request.GET['_method'] == 'set-state':
        wf = get_workflow(n)
        wf.process_menu(n, request)

        # return to referrer
        return HTTPFound(location = request.referrer)

    elif request.GET['_method'] == 'swap-order':

        nodeid1 = int(request.params.get('nodeid1'))
        nodeid2 = int(request.params.get('nodeid2'))
        if nodeid1 == nodeid2:
            return HTTPFound(location = request.referrer)

        ordering1 = int(request.params.get('ordering1'))
        ordering2 = int(request.params.get('ordering2'))

        dbh = get_dbhandler()

        node_1 = dbh.get_node_by_id(nodeid1)
        node_2 = dbh.get_node_by_id(nodeid2)

        if node_1.ordering != ordering1 or node_2.ordering != ordering2:
            return error_page(request, 'Node order has changed. Please reload page first!')

        node_1.ordering = -1
        node_2.ordering = -2
        dbh.session().flush()
        node_1.ordering = ordering2
        node_2.ordering = ordering1

        return HTTPFound(location = request.referrer)

    return error_page(request, 'action get not implemented')


def action_post(request, node):

    method = request.params.get('_method')
    dbh = get_dbhandler()

    if method == 'delete':

        node_ids = [ int(x) for x in request.params.getall('node-ids')]
        nodes = dbh.get_nodes_by_ids(node_ids)

        if nodes.count() == 0:
            return Response(modal_error)

        return Response(
            modal_delete(
                title = 'Removing Node(s)',
                content = literal(
                    'You are going to remove the following node(s): '
                    '<ul>' +
                    ''.join( '<li>%s</li>' % n.title for n in nodes) +
                    '</ul>'
                ),
                request = request,

            ),
            request = request
        )

    elif method == 'delete/confirm':

        node_ids = [ int(x) for x in request.params.getall('node-ids')]
        nodes = dbh.get_nodes_by_ids(node_ids)

        for n in nodes:
            n.clear()
            dbh.session().delete(n)

        dbh.session().flush()
        request.session.flash(
            'success', 'Node(s) %s has been removed.' %
            '; '.join( str(x) for x in node_ids ))

        return HTTPFound( location = request.referrer or node.path )

    else:

        ret = get_viewer(node.__class__)(node, request).action_post()
        if ret == True:
            return HTTPFound( location = request.referrer or node.path )
        if ret not in [False, None]:
            return ret

    return error_page(request, 'action post not implemented')


def tag_lookup(request):
    """ return JSON for autocomplete tag """

    q = request.params.get('q')
    if not q:
        return error_page(request, 'No q parameter!')

    q = '%' + q.lower() + '%'

    dbh = get_dbhandler()
    g_key = dbh.get_ekey('@TAG')

    ekeys = dbh.EK.query(dbh.session()).filter( dbh.EK.key.ilike(q),
            dbh.EK.member_of_id == g_key.id)

    # formating for select2 consumption
    # tags use the actual key for id

    result = [
        { 'id': ':%d ' % k.id, 'text': '%s [ %s ]' % (k.key, k.desc) }
        for k in ekeys]

    return result



    result = [ { 'id': 'abc', 'text': 'abc'} ]

    return result


@roles(PUBLIC)
def node_lookup(request):

    q = request.params.get('q')
    if not q:
        return error_page(request, 'No q parameter!')

    t = request.params.get('t', 'Page').strip()
    nodetype = get_class(t)

    q = '%' + q.lower() + '%'

    dbh = get_dbhandler()
    nodes = nodetype.query( dbh.session() ).filter( nodetype.title.ilike(q))

    result = [
        { 'id': n.id, 'text': '%s' % (n.title) }
        for n in nodes ]

    return result

__MODULES__ = {}
__NODETYPES__ = {}


def register_module(nodeclass, module):
    global __MODULES__, __NODETYPES__
    __MODULES__[nodeclass] = module
    __NODETYPES__[getattr(nodeclass, '__label__', nodeclass.__name__)] = nodeclass


def get_module(nodeclass):
    return __MODULES__[nodeclass]


__VIEWERS__ = {}
__NODECLASSES__ = {}
__NODES__ = {}

def register_viewer(nodeclass, viewerclass):
    global __VIEWERS__, __NODECLASSES__, NODES
    __VIEWERS__[nodeclass] = viewerclass
    __NODECLASSES__[getattr(nodeclass, '__label__', nodeclass.__name__)] = nodeclass
    __NODES__[viewerclass] = nodeclass


def get_viewer(nodeclass):
    return __VIEWERS__[nodeclass]


def get_class(label_or_viewer):
    if type(label_or_viewer) == str:
        return __NODECLASSES__[label_or_viewer]
    return __NODES__[label_or_viewer]


def get_path(request):

    urlpath = posixpath.normpath('/' + request.matchdict.get('path', ''))
    cerr('Req path: %s' % urlpath)
    return urlpath


def get_node(request):
    # get_node() needs to check host and cmsfix.site and decide which site
    # to use to get node

    path = get_path(request)
    site = get_site(request)

    dbh = get_dbhandler()
    if path.startswith('/!'):
        n = dbh.get_node_by_id( int(path[2:]))
    else:
        n = dbh.get_node(path, site=site)
    if not n:
        raise exc.HTTPNotFound('Node %s is not found in the system' % path)

    return n


def get_toolbar(node, request):

    if node.is_manageable(request):
        module = get_module(node.__class__)
        return module.toolbar(request, node)
    return ''


def get_add_menu(node, request):
    """ create Add menu items """

    item_classes = node.get_item_classes()

    # check if the node can be added by this function
    if len(item_classes) == 0:
        return ''

    add_menu_list = li(class_ = "nav-item dropup" )[
        a(class_='nav-link dropdown-toggle', role='button', id='addMenu',
                    **  { 'data-toggle': 'dropdown',
                            'aria-haspopup': 'true',
                            'aria-expanded': 'false',
                        }
                )[
                    'Add ',
                    span(class_='caret')
                ],
        div(class_='dropdown-menu')[
            tuple(
                a(c.get_label(), class_='dropdown-item',
                        href=request.route_url('node-add',
                                    path=node.url, _query={ 'type': c.__name__ })
                ) for c in item_classes
            )
        ]
    ]

    return add_menu_list


def check_stamp(request, node):
    if (request.method == 'POST' and 
        abs( node.stamp.timestamp() - float(request.params['cmsfix-stamp']) ) > 0.01):
            return error_page(request,
                'Data entry has been modified by %s at %s. Please cancel and re-edit your entry.'
                % (node.lastuser.login, node.stamp)
            )
    return True
