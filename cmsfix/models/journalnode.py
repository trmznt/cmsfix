
from cmsfix.models.node import *
from cmsfix.models.pagenode import PageNode
from cmsfix.models.filenode import FileNode
from cmsfix.lib.workflow import set_workflow, get_workflow, GroupwareWorkflow

import time


@Node.inherited_container
class JournalNode(Node):
    """ this is journal container node """
    __label__ = 'Journal'
    __tablename__ = 'journalnodes'

    id = Column(types.Integer, ForeignKey('nodes.id'), primary_key=True)

    title = Column(types.String(256), nullable=False, server_default='')
    desc = Column(types.String(1024), nullable=False, server_default='')
    settings = Column(types.JSON, nullable=False, server_default='null')
    order = Column(types.String(1), nullable=False, server_default='D')
    #flag = Column(types.Integer, nullable=False, server_default='0')
    # bitwise flags -> 1 << 0 (group or user-only addition)
    # bitwise flags -> 1 << 1 (group or user-only editing)
    # bitwise flags -> 1 << 2 (group-only or  public view)


    __mapper_args__ = { 'polymorphic_identity': 3 }

    # JournalNode can not be added by toolbar menu!
    __strict_container__ = []


    def update(self, obj):

        super().update(obj)

        if type(obj) == dict:

            if 'title' in obj:
                self.title = obj['title']
            if 'desc' in obj:
                self.desc = obj['desc']
            if 'settings' in obj:
                self.settings = obj['settings']
            if 'order' in obj:
                self.order = obj['order']
            if 'flag' in obj:
                self.flag = obj['flag']


    def as_dict(self):
        d = super().as_dict()
        d.update(
            title = self.title,
            desc = self.desc,
            settings = self.settings,
            order = self.order,
            #flag = self.flag,
        )
        return d


    def generate_slug(self):
        self.slug = hex(int(time.time()*1e6))[6:]


    def render_title(self):
        return "%s [Journal]" % self.title


    def set_permission(self, default=True):
        """ JournalNode default set_permission
                group: user's primary group
        """
        self.group_id = self.user.primarygroup_id


@JournalNode.container
class JournalItemNode(PageNode):
    """ this is Journal """

    __tablename__ = 'journalitemnodes'

    id = Column(types.Integer, ForeignKey('pagenodes.id'), primary_key=True)

    #title = Column(types.String(256), nullable=False, server_default='')
    #content = Column(types.String, nullable=False, server_default='')
    log_date = Column(types.Date, nullable=False)
    version = Column(types.Integer, nullable=False, server_default='1')

    __mapper_args__ = { 'polymorphic_identity': 4 }

    __strict_container__ = [ FileNode ]


    def update(self, obj):

        super().update(obj)

        if type(obj) == dict:
            if 'log_date' in obj:
                self.log_date = obj['log_date']
            if 'version' in obj:
                self.version = obj['version']


    def as_dict(self):
        d = super().as_dict()
        d.update(
            log_date = self.log_date,
            version = self.version,
        )
        return d


    def generate_slug(self):
        self.slug = hex(int(time.time()*1e6))[6:]


class JournalWorkflow(GroupwareWorkflow):
    """ journal workflow
        0 - public - all can access
        1 - protected - only logged user can access
        2 - restricted - permission based on group,
                * group admins can edit/manage items
                * group member can access and add items
        3 - private - only user & group admins can access

        XXX: the above is not implemented yet.
    """

    def set_defaults(self, node, request, parent_node):
        super().set_defaults(node, request, parent_node)
        node.state = 2 # journal can only be re
        node.listed = False

    def is_editable(self, node, request):
        if node.user_id == request.user.id:
            return True
        return False

    def is_manageable(self, node, request):
        user = request.user
        if node.user_id == user.id or node.parent.user_id == user.id:
            return True
        if user.has_roles(SYSADM, DATAADM):
            return True
        return False

    def is_accessible(self, node, request):
        user = request.user
        if not node or not user:
            return False
        if node.user_id == user.id or node.parent.user_id == user.id:
            return True
        if node.group.has_member(user) or node.parent.group.has_member(user):
            return True
        if user.has_roles(SYSADM, DATAADM):
            return True
        return False



class JournalItemWorkflow(GroupwareWorkflow):
    """ spesific workflow for JournalItemNode type:
        100 - sealed -> nobody can edit anymore
        101 - reviewed -> container owner can edit and change the state
        102 - draft -> user can edit and change to 101

        journalnode can only be editted by user/owner, group owner or JournalNode parent user
    """

    states = { 100: 'sealed', 101: 'reviewed', 102: 'drafted' }
    styles = { 100: 'badge badge-success', 101: 'badge badge-info', 102: 'badge badge-danger '}

    def set_defaults(self, node, request, parent_node):
        super().set_defaults(node, request, parent_node)
        node.state = 102
        node.listed = False

    def is_editable(self, node, request):
        if node.state == 100:
            return False
        if node.state == 101:
            return True
        if node.state == 102:
            return True

    def is_manageable(self, node, request):
        print('node.state=%d' % node.state)
        if node.state == 100:
            return False
        if node.state == 101:
            return True
        if node.state == 102:
            return True
        return False

    def is_accessible(self, node, request):
        # journal node is accessible to owner and container's user
        user = request.user
        if not user:
            return False
        print('check is_accessible()')
        if node.user_id == user.id:
            return True
        if isinstance(node, JournalNode):
            print('check parent container')
            if node.parent.user_id == user.id:
                return True
        if isinstance(node, JournalItemNode):
            return get_workflow(node.parent).is_accessible(node.parent, request)
        return False

# JournalWorkflow and JournalItemWorkflow are specials, created here first
journal_wf = JournalWorkflow()
journalitem_wf = JournalItemWorkflow()
set_workflow(journal_wf, JournalNode)
set_workflow(journalitem_wf, JournalItemNode)
