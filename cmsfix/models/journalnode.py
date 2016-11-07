
from cmsfix.models.node import *
from cmsfix.models.pagenode import PageNode
from cmsfix.models.filenode import FileNode
from cmsfix.lib.workflow import set_workflow, get_workflow, GroupwareWorkflow


@Node.inherited_container
class JournalNode(Node):
    """ this is journal container node """
    __label__ = 'Journal'
    __tablename__ = 'journalnodes'

    id = Column(types.Integer, ForeignKey('nodes.id'), primary_key=True)

    title = Column(types.String(256), nullable=False, server_default='')
    desc = Column(types.String(1024), nullable=False, server_default='')
    settings = Column(YAMLCol(1024), nullable=False, server_default='')
    order = Column(types.String(1), nullable=False, server_default='D')
    #flag = Column(types.Integer, nullable=False, server_default='0')
    # bitwise flags -> 1 << 0 (group or user-only addition)
    # bitwise flags -> 1 << 1 (group or user-only editing)
    # bitwise flags -> 1 << 2 (group-only or  public view)


    __mapper_args__ = { 'polymorphic_identity': 3 }


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

class JournalWorkflow(GroupwareWorkflow):

    def set_defaults(self, node, user, parent_node):
        node.group_id = parent_node.group_id
        node.user_id = user.id
        node.state = 2 # journal can only be re
        node.listed = False

    def is_editable(self, node, user):
        if node.user_id == user.id:
            return True
        return False

    def is_manageable(self, node, user):
        if node.user_id == user.id or node.parent.user_id == user.id:
            return True
        if user.has_roles(SYSADM, DATAADM):
            return True
        return False

    def is_accessible(self, node, user):
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
    styles = { 100: 'label label-success', 101: 'label label-info', 102: 'label label-danger '}

    def set_defaults(self, node, user, parent_node):
        node.group_id = parent_node.group_id
        node.user_id = user.id
        node.state = 102
        node.listed = False

    def is_editable(self, node, user):
        if node.state == 100:
            return False
        if node.state == 101:
            return True
        if node.state == 102:
            return True

    def is_manageable(self, node, user):
        print('node.state=%d' % node.state)
        if node.state == 100:
            return False
        if node.state == 101:
            return True
        if node.state == 102:
            return True
        return False

    def is_accessible(self, node, user):
        # journal node is accessible to owner and container's user
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
            return get_workflow(node.parent).is_accessible(node.parent, user)
        return False

# JournalWorkflow and JournalItemWorkflow are specials, created here first
journal_wf = JournalWorkflow()
journalitem_wf = JournalItemWorkflow()
set_workflow(journal_wf, JournalNode)
set_workflow(journalitem_wf, JournalItemNode)
