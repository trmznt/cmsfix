
from rhombus.lib.utils import get_dbhandler, cout, cerr
from rhombus.views import *
from rhombus.views.generics import error_page
from rhombus.lib.tags import *

from cmsfix.lib.workflow import get_workflow

import pyramid.httpexceptions as exc

import posixpath


def index(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_accessible(n, request.user):
        return error_page(request, 'Page is not accessible!')

    module = get_module(n.__class__)
    return module.index(request, n)


@roles(PUBLIC)
def view(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request.user):
        return error_page(request, 'Page is not manageable by current user!')

    module = get_module(n.__class__)
    return module.view(request, n)


@roles(PUBLIC)
def content(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request.user):
        return error_page(request, 'You are not authorized to view the content of this node!')

    module = get_module(n.__class__)
    return module.content(request, n)


@roles(PUBLIC)
def info(request):

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request.user):
        return error_page(request, 'You are not authorized to view this node meta information')

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


def manage(request):
    pass


@roles(PUBLIC)
def edit(request):
    """ edit & save a node """

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request.user):
        return error_page(request, 'You are not authorized to edit this node!')

    # check stamp consistency
    if request.method == 'POST' and abs( n.stamp.timestamp() - float(request.params['cmsfix-stamp']) ) > 0.01:
            return error_page(request,
                'Data entry has been modified by %s at %s. Please cancel and re-edit your entry.'
                % (n.lastuser.login, n.stamp)
            )

    module = get_module(n.__class__)
    return module.edit(request, n)


@roles(PUBLIC)
def add(request):
    """ add & save a node """

    n = get_node(request)
    wf = get_workflow(n)

    if not wf.is_manageable(n, request.user):
        return error_page(request, 'You are not authorized to add a new node here!')

    # get the node type
    node_type = request.params.get('type', '')
    if not node_type:
        return error_page(request, 'ERR: no node type to add!')

    for (cls, module) in __MODULES__.items():
        if cls.__name__ == node_type:
            return module.add(request, n)

    return error_page(request, 'ERR: unknown node type!!')


@roles(PUBLIC)
def action(request):

    n = get_node(request)

    if request.GET:

        # get
        if request.GET['_method'] == 'set-state':
            wf = get_workflow()
            wf.process_menu(n, request)

            # return to referrer
            return HTTPFound(location = request.referrer)

    elif request.POST:

        # post
        raise NotImplementedError('Not implemented yet!')

    return error_page(request, 'HTTP method not implemented!')



def tag_lookup(request):
    """ return JSON for autocomplete tag """

    q = request.params.get('q')
    if not q:
        return error_page(request, 'No q parameter!')

    q = '%' + q.lower() + '%'

    result = [ { 'id': 'abc', 'text': 'abc'} ]

    return result

__MODULES__ = {}
__NODETYPES__ = {}


def register_module(nodeclass, module):
    global __MODULES__, __NODETYPES__
    __MODULES__[nodeclass] = module
    __NODETYPES__[getattr(nodeclass, '__label__', nodeclass.__name__)] = nodeclass


def get_module(nodeclass):
    return __MODULES__[nodeclass]


def get_path(request):

    urlpath = posixpath.normpath('/' + request.matchdict.get('path', ''))
    cerr('Req path: %s' % urlpath)
    return urlpath


def get_node(request):

    path = get_path(request)

    dbh = get_dbhandler()
    n = dbh.get_node(path)
    if not n:
        raise exc.HTTPNotFound('Node %s is not found in the system' % path)

    return n


def get_toolbar(node, request):

    if node.is_manageable(request.user):
        module = get_module(node.__class__)
        return module.toolbar(request, node)
    return ''


def get_add_menu(node, request):
    """ create Add menu items """

    #
    add_menu_list = li(class_ = "dropdown" )[
        a(class_='dropdown-toggle', role='button',
                    **  { 'data-toggle': 'dropdown',
                            'aria-haspopup': 'true',
                            'aria-expanded': 'false',
                        }
                )[
                    'Add ',
                    span(class_='caret')
                ],
        ul(class_='dropdown-menu')[
            tuple(
                li(
                    a(c.get_label(),
                        href=request.route_url('node-add',
                                    path=node.url, _query={ 'type': c.__name__ }))
                ) for c in node.get_item_classes()
            )
        ]

    ]

    return add_menu_list