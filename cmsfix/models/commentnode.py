from cmsfix.models.node import *
from cmsfix.lib.workflow import set_workflow, GroupwareWorkflow

#@self_container             # a comment can contain another comment(s)
#@Node.inherited_container   # Node class and all of its derivatives can contain comment(s)
#comment is handled by special workflow
class CommentNode(Node):

    __tablename__ = 'comments'

    id = Column(types.Integer, ForeignKey('nodes.id'), primary_key=True)
    content = Column(types.String(1024), nullable=False, server_default='')

    __mapper_args__ = { 'polymorphic_identity': 5 }

    def update(self, obj):

        if isinstance(obj, dict):
            super().update(obj)

            if 'content' in obj:
                self.content = obj['content']


    def update(self, obj):
        super().update(obj)

        if instance(obj, dict):
            if 'content' in obj:
                self.content = obj['content']

# workflow

class CommentWorkflow(GroupwareWorkflow):

    states = { 0: 'posted', 1: 'drafted' }
    styles = { 0: 'label label-success', 1: 'label label-danger'}

    def set_defaults(self, node, user, parent_node):
        node.group_id = parent_node.group_id
        node.user_id = user.id
        node.state = 2
        node.listed = False

    def is_accessible(self, node, user):
        """ comments follow the parent node """
        container_node = self.get_container_node(node)
        return container_node.is_accessible(node, user)

    def is_manageable(self, node, user):
        container_node = self.get_container_node(node)
        return container_node.is_manageable(node, user)

    def is_editable(self, node, user):
        # check whether this is the user
        if node.user.id == user.id:
            return True
        container_node = self.get_container_node(node)
        return container_node.is_editable(node, user)

    def get_container_node(self, node):
        parent_node = node.parent
        while True:
            if not isinstance(parent_node, CommentNode):
                return parent_node
            parent_node = parent_node.parent
        raise RuntimeError('FATAL ERR: this code should not be executed!!')

# CommentWorkflow created here
comment_wf = CommentWorkflow()
set_workflow(comment_wf, CommentNode)
