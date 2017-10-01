
# workflow

from rhombus.lib.roles import SYSADM, DATAADM
from rhombus.lib.tags import ul, li, a, span


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

    def is_manageable(self, node, user):
        """ can the user add/remove a node from this node, or
            can the user delete this node
        """
        raise NotImplementedError()


    def is_editable(self, node, user):
        """ can the user edit this node """
        raise NotImplementedError()


    def is_accessible(self, node, user):
        """ can the user access (or view) this node """
        raise NotImplementedError()

    def set_defaults(self, node, user, parent_node):
        """ set default parameters for a new node """
        node.group_id = parent_node.group_id
        node.user_id = user.id

    def show_menu(self, node, request):
        raise NotImplementedError()

    def process_menu(self, node, request):
        raise NotImplementedError()


class GroupwareWorkflow(object):
    """ simple workflow, suitable for intranet
        0 - public - all can access
        1 - protected - only logged user can access
        2 - restricted - permission based on group,
                * group owner can edit/manage
                * group member can access
        3 - private - only user can access
    """

    states = { 0: 'public', 1: 'protected', 2: 'restricted', 3: 'private' }
    styles = {  0: 'label label-success', 1: 'label label-info',
                2: 'label label-warning', 3: 'label label-danger '}

    def __init__(self):
        pass

    def is_manageable(self, node, user):
        if not user:
            return False
        if user.has_roles(SYSADM, DATAADM):
            return True
        if node.user_id == user.id:
            return True
        if node.state < 3 and node.group.has_member(user):
            return True
        return False

    def is_editable(self, node, user):
        return self.is_manageable(node, user)

    def is_accessible(self, node, user):
        if node.state == 0:
            return True
        if node.state == 1 and user:
            return True
        return self.is_manageable(node, user)

    def set_defaults(self, node, user, parent_node):
        """ group: inherit parent group """
        node.group_id = parent_node.group_id
        node.user_id = user.id

        # all the rest of node types will be in private before being published
        node.state  = 3
        node.listed = True

    # menu-related methods

    def show_menu(self, node, request):
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


    def process_menu(self, node, request):
        """ process request """

        state = int(request.params.get('state', 3))
        node.state = state

        from rhombus.lib.utils import get_dbhandler
        dbsession = get_dbhandler().session()
        assert dbsession.user, "Fatal Error: user not properly set up"
        assert dbsession.user.id == request.user.id, "Fatal Error: inconsistent user id in db session"


class PublicWorkflow(object):
    """ workflow with reviews, suitable for publishing public articles
        0 - public: all
        1 - restricted: only logged user can view
        2 - editor stage: editor can edit, but not author
        3 - reviewer stage: can put comment, but not edit
        4 - author stage: only author can view & edit
    """

    def __init__(self):
        pass


    def is_manageable(self, node, user):
        if not user:
            return False
        if node.user_id == user.id:
            return True
        if node.state <= 1 and self.is_editor(user):
            return True
        return False

    def is_editable(self, node, user):
        if not user:
            return False
        if node.state == 2 and node.user_id == user.id:
            return True
        if node.state <= 1 and self.is_editor(user):
            return True
        return False

    def is_accessible(self, node, user):
        if node.state == 0:
            return True
        return self.is_manageable(node, user)

    def set_defaults(self, node, user, parent_node):
        """ group: inherit parent group """
        node.group_id = parent_node.group_id
        node.user_id = user.id

        if isinstance(node, CommentNode):
            # comments are directly publishable and won't appear in Content tab
            node.state = 0
            node.listed = False

        else:
            # all the rest of node types will be in author stage
            node.state  = 4
            node.listed = True


class SiteWorkflow(object):
    """ suitable for institutional website
        0 - public - all can view, group member can manage
        1 - restricted - only logged user can view, group member can manage
        2 - protected - only group member can view/manage
    """

    def __init__(self):
        pass

    def is_manageable(self, node, user):
        if not user:
            return False
        if user.in_group(node.group):
            return True
        return False

    def is_editable(self, node, user):
        return self.is_manageable(node, user)

    def is_accessible(self, node, user):
        if node.state == 0:
            return True
        return self.is_manageable(self, node, user)

    def set_defaults(self, node, user, parent_node):
        """ group: inherit parent group """
        node.group_id = parent_node.group_id
        node.user_id = user.id
        node.state  = 2
        node.listed = True


class InheritedWorkflow(BaseWorkflow):
    """ inherited workflow
        all permissions are based on the parent node
    """

    def is_manageable(self, node, user):
        return get_workflow(node.parent_node).is_manageable(node.parent_node, user)

    def is_editable(self, node, user):
        return get_workflow(node.parent_node).is_editable(node.parent_node, user)

    def is_accessible(self, node, user):
        return get_workflow(node.parent_node).is_accessible(node.parent_node, user)

    def set_defaults(self, node, user, parent_node):
        super().set_defaults(node, user, parent_node)


# TODO:
# * make all workflow classes as singleton
