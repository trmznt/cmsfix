
# workflow

from cmsfix.lib.roles import SYSADM, DATAADM, EDITOR, REVIEWER
from rhombus.lib.tags import ul, li, a, span, div

from ipaddress import ip_address, ip_network


## global workflow
__WORKFLOW__ = None

## each node child class can have its own specific workflow
__WORKFLOW_DICT__ = {}


def set_workflow(obj, cls=None):
    global __WORKFLOW__, __WORKFLOW_DICT__
    if not cls:
        # set global workflow
        __WORKFLOW__ = obj
    else:
        # set specific node child class workflow
        __WORKFLOW_DICT__[cls] = obj


def get_workflow(instance=None):

    try:
        if instance:
            # try specific workflow first
            return __WORKFLOW_DICT__[instance.__class__]
    except KeyError:
        pass
    return __WORKFLOW__


class BaseWorkflow(object):

    states = {}
    styles = {}

    def __init__(self):
        pass

    def is_manageable(self, node, request):
        """ can the request (user) add/remove a node from this node, or
            can the request (user) delete this node
        """
        raise NotImplementedError()


    def is_editable(self, node, request):
        """ can the request (user) edit this node """
        raise NotImplementedError()


    def is_accessible(self, node, request):
        """ can the request (user) access (or view) this node """
        raise NotImplementedError()

    def set_defaults(self, node, request, parent_node):
        """ set default parameters for a new node;
            set group_id to parent_node's group_id
        """
        node.group_id = parent_node.group_id
        node.user_id = request.user.id
        node.site_id = parent_node.site_id
        node.parent_id = parent_node.id

    def show_menu(self, node, request):
        raise NotImplementedError()

    def process_menu(self, node, request):
        raise NotImplementedError()


    def state_style(self, node):
        return (self.states[node.state], self.styles[node.state])


    # menu-related methods

    def show_menu(self, node, request):
        """ based on user authorization, show workflow menu; return a <li> element """
        html = li(class_='nav-item dropup')
        html.add(
            a(span(self.states[node.state], class_=self.styles[node.state]), span(class_='caret'),
                href="#", class_='nav-link dropdown-toggle',
            **{ "data-toggle": "dropdown", "role": "button", "aria-haspopup": "true",
                "aria-expanded": "false"})
        )
        html.add(
            div(class_='dropdown-menu dropdown-menu-right')[
                tuple(
                    a(self.states[i], class_='dropdown-item',
                            href=request.route_url('node-action', path=node.url,
                                        _query = { '_method': 'set-state', 'state': i })
                    ) for i in sorted(self.states.keys(), reverse=True)
                )
            ]
        )
        return html


    def process_menu(self, node, request):
        """ process request """

        state = int(request.params.get('state', 3))
        node.state = state

        from rhombus.lib.utils import get_dbhandler
        dbsession = get_dbhandler().session()
        assert dbsession.user, "Fatal Error: user not properly set up"
        assert dbsession.user.id == request.user.id, "Fatal Error: inconsistent user id in db session"


class BlogWorkflow(BaseWorkflow):
    """ a basic workflow, suitable for blogging platform
        0 - public - all can access
        1 - draft - only owner & admin can access & modify
    """

    states = { 0: 'public', 1: 'draft' }
    styles = {  0: 'badge badge-success', 1: 'badge badge-danger' }

    def is_manageable(self, node, request):
        user = request.user
        if not user:
            return False
        if user.has_roles(SYSADM, DATAADM):
            return True
        if node.user_id == user.id:
            return True
        return False

    def is_accessible(self, node, request):
        if node.state == 0:
            return True
        return self.is_manageable(node, request)

    def set_defaults(self, node, request, parent_node):
        """ group: inherit parent group """
        super().set_defaults(node, request, parent_node)

        # all the rest of node types will be in private before being published
        node.state  = 1
        node.listed = True


class GroupwareWorkflow(BaseWorkflow):
    """ simple workflow, suitable for intranet
        0 - public - all can access within internal network
        1 - protected - only logged user can access
        2 - restricted - permission based on group,
                * group owner can edit/manage
                * group member can access
        3 - private - only user can access
    """

    states = { 0: 'public', 1: 'protected', 2: 'restricted', 3: 'private' }
    styles = {  0: 'badge badge-success', 1: 'badge badge-info',
                2: 'badge badge-warning', 3: 'badge badge-danger '}

    def __init__(self, networks = ['127.0.0.0/8', '10.0.0.0/8', '192.168.0.0/16']):
        super().__init__()
        self.networks = [ ip_network(n) for n in networks ]

    def in_internal_networks(self, ipaddr):
        ip_addr = ip_address(ipaddr)
        for n in self.networks:
            if ip_addr in n:
                return True
        return False

    def is_manageable(self, node, request):
        user = request.user
        if not user:
            return False
        if user.has_roles(SYSADM, DATAADM):
            return True
        if node.user_id == user.id:
            return True
        if node.state < 3 and node.group.is_admin(user):
        	# check if user is an admin of node.group 
            return True
        return False

    def is_editable(self, node, request):
        return self.is_manageable(node, request)

    def is_accessible(self, node, request):
        user = request.user
        if not user and not self.in_internal_networks(request.remote_addr):
            return False
        if node.state == 0:
            return True
        if node.state == 1 and user:
            return True
        if node.state >= 2 and user:
        	return user.in_group(node.group)
        return self.is_manageable(node, request)

    def set_defaults(self, node, request, parent_node):
        """ group: inherit parent group """
        super().set_defaults(node, request, parent_node)

        # all the rest of node types will be in private before being published
        node.state  = 3
        node.listed = True

    # menu-related methods

    def show_menu_xxx(self, node, request):
        """ based on user authorization, show workflow menu; return a <li> element """
        html = li(class_='dropdown')
        html.add(
            a(span(self.states[node.state], class_=self.styles[node.state]), span(class_='caret'), href="#", class_='dropdown-toggle',
            **{ "data-toggle": "dropdown", "role": "button", "aria-haspopup": "true",
                "aria-expanded": "false"})
        )
        html.add(
            ul(class_='dropdown-menu')[
                tuple(
                    li(
                        a(self.states[i],
                            href=request.route_url('node-action', path=node.url,
                                        _query = { '_method': 'set-state', 'state': i })) )
                    for i in sorted(self.states.keys(), reverse=True)
                )
            ]
        )
        return html


    def process_menu_xxx(self, node, request):
        """ process request """

        state = int(request.params.get('state', 3))
        node.state = state

        from rhombus.lib.utils import get_dbhandler
        dbsession = get_dbhandler().session()
        assert dbsession.user, "Fatal Error: user not properly set up"
        assert dbsession.user.id == request.user.id, "Fatal Error: inconsistent user id in db session"


class PublicWorkflow(BaseWorkflow):
    """ workflow with reviews, suitable for publishing public articles
        0 - public: all
        1 - restricted: only logged user can view
        2 - editor stage: editor can edit, but not author
        3 - reviewer stage: can put comment, but not edit
        4 - author stage: only author can view & edit
    """

    states = { 0: 'public', 1: 'restricted', 2: 'editor', 3: 'reviewer', 4: 'draft' }
    styles = {  0: 'badge badge-success', 1: 'badge badge-info', 2: 'badge badge-info',
                3: 'badge badge-warning', 4: 'badge badge-danger '}

    def __init__(self):
        pass


    def is_manageable(self, node, request):
        user = request.user
        if not user:
            return False
        if user.has_roles(SYSADM, DATAADM):
            return True
        if node.state == 4 and node.user_id == user.id:
            return True
        if node.state == 2 and user.has_roles(EDITOR):
            return True
        return False

    def is_editable(self, node, request):
        return self.is_manageable(node, request)
        if not user:
            return False
        if node.state == 4 and node.user_id == user.id:
            return True
        if node.state == 2 and user.has_roles(EDITOR):
            return True
        return False

    def is_accessible(self, node, request):
        user = request.user
        if node.state == 0:
            return True
        if not user:
            return False
        if node.user_id == user.id:
            return True
        if node.state == 1 and user:
            return True
        if node.state == 2 and user.has_roles(EDITOR):
            return True
        if node.state == 3 and user.has_roles(EDITOR, REVIEWER):
            return True
        return self.is_manageable(node, request)

    def set_defaults(self, node, request, parent_node):
        """ group: inherit parent group """
        super().set_defaults(node, request, parent_node)

        from cmsfix.models.commentnode import CommentNode

        if isinstance(node, CommentNode):
            # comments are directly publishable and won't appear in Content tab
            node.state = 0
            node.listed = False

        else:
            # all the rest of node types will be in author stage
            node.state  = 4
            node.listed = True


class SiteWorkflow(BaseWorkflow):
    """ suitable for institutional website
        0 - public - all can view, group member can manage
        1 - restricted - only logged user can view, group member can manage
        2 - protected - only group member can view/manage
    """

    states = { 0: 'public', 1: 'restricted', 2: 'protected' }
    styles = {  0: 'badge badge-success', 1: 'badge badge-info',
                2: 'badge badge-danger '}

    def __init__(self):
        pass

    def is_manageable(self, node, request):
        user = request.user
        if not user:
            return False
        if user.in_group(node.group):
            return True
        return False

    def is_editable(self, node, request):
        return self.is_manageable(node, request)

    def is_accessible(self, node, request):
        if node.state == 0:
            return True
        return self.is_manageable(node, request)

    def set_defaults(self, node, request, parent_node):
        """ group: inherit parent group """
        super().set_defaults(node, request, parent_node)
        node.state  = 2
        node.listed = True


class InheritedWorkflow(BaseWorkflow):
    """ inherited workflow
        all permissions are based on the parent node
    """

    states = { 0: 'Not Applicable' }
    styles = { 0: 'badge badge-info'}

    def is_manageable(self, node, request):
        parent_node = self.get_parent_node(node)
        return get_workflow(parent_node).is_manageable(parent_node, request)

    def is_editable(self, node, request):
        parent_node = self.get_parent_node(node)
        return get_workflow(parent_node).is_editable(parent_node, request)

    def is_accessible(self, node, request):
        parent_node = self.get_parent_node(node)
        return get_workflow(parent_node).is_accessible(parent_node, request)

    def set_defaults(self, node, request, parent_node):
        super().set_defaults(node, request, parent_node)
        # for new node, we add to temporary variable as a hack
        node._parent_node = parent_node

    def get_parent_node(self, node):
        if node.parent is None:
            if not hasattr(node, '_parent_node'):
                raise RuntimeError(
                    'FATAL ERR: need to define either node.parent or node._parent_node')
            return node._parent_node
        return node.parent



# TODO:
# * make all workflow classes as singleton
