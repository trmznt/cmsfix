
from rhombus.models.core import *
from rhombus.models.ek import EK
from rhombus.models.user import User, Group
from rhombus.lib.roles import *
from sqlalchemy.sql import func
from sqlalchemy.ext.orderinglist import ordering_list
import posixpath, time, difflib, yaml

from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy_utils.types.json import JSONType


## the models employed Rhombus' BaseMixIn to provide id, lastuser_id and stamp


class Site(BaseMixIn, Base):
    """ this class manages sites
    """
    __tablename__ = 'sites'

    fqdn = Column(types.String(128), nullable=False, index=True, server_default='*')

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)



class Node(BaseMixIn, Base):
    """ this class manages all objects that have path and permission
    """
    __tablename__ = 'nodes'

    site_id = Column(types.Integer, ForeignKey('sites.id'), nullable=False)
    site = relationship('Site', uselist=False)

    uuid = Column(UUIDType, nullable=False, unique=True)
    slug = Column(types.String(128), nullable=False, index=True)
    path = Column(types.String(1024), nullable=False, server_default='')
    level = Column(types.Integer, nullable=False, server_default='-1')

    parent_id = Column(types.Integer, ForeignKey('nodes.id'), nullable=True, index=True)
    ordering = Column(types.Integer, nullable=False)
    children = relationship('Node',
                        cascade="all, delete-orphan",

                        # many to one + adjacency list - remote_side
                        # is required to reference the 'remote'
                        # column in the join condition.
                        backref=backref("parent", remote_side='Node.id'),

                        # children will be represented as a dictionary
                        # on the "name" attribute.
                        #collection_class=attribute_mapped_collection('slug'),
                        order_by="Node.ordering",
                        collection_class=ordering_list('ordering')
                )

    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    user = relationship(User, uselist=False, foreign_keys=user_id)

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)

    create_time = Column(types.DateTime(timezone=True), nullable=False,
                server_default=func.now())
    publish_time = Column(types.DateTime(timezone=True), nullable=False,
                server_default=func.now())
    expire_time = Column(types.DateTime(timezone=True), nullable=True)

    # state represent the workflow status, with global value of 0 being public
    # the meaning of the values depends on the workflow
    state = Column(types.Integer, nullable=False, server_default='0')

    # flags can be used to indicate special meta-information for the node
    # the lowest 16-bit may be interpreted freely by any viewer of each Node-subclass
    # the highest 16-bit is preserved for system

    flags = Column(types.Integer, nullable=False, server_default='0')

    # boolean to indicate whether this node will appear in the Content tab
    listed = Column(types.Boolean, nullable=False, server_default='1')

    mimetype_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    mimetype = EK.proxy('mimetype_id', '@MIMETYPE')

    json_code = deferred(Column(JSONType, nullable=False, server_default='{}'))
    # for more options on the above, see note at the end of this file

    polymorphic_type = Column(types.Integer, nullable=False, server_default='0', index=True)

    __mapper_args__ = { 'polymorphic_on': polymorphic_type, 'polymorphic_identity': 0 }
    __table_args__ = (  UniqueConstraint('path', 'site_id'),
                        UniqueConstraint('parent_id', 'ordering'), )

    __strict_container__ = None
    __mimetypes__ = None


    def __init__(self, UUID=None, **kwargs):
        if not UUID:
            self.uuid = uuid.uuid1()
        else:
            self.uuid = UUID
        self._versioning = None

        super().__init__(**kwargs)


    def update(self, obj):

        if 'slug' in obj and obj['slug']:
            self.slug = obj['slug']
        if 'user_id' in obj and type(obj['user_id']) == int:
            self.user_id = obj['user_id']
        if 'group_id' in obj and type(obj['group_id']) == int:
            self.group_id = obj['group_id']
        if 'mimetype_id' in obj and type(obj['mimetype_id']) == int:
            self.mimetype_id = obj['mimetype_id']
        if 'listed' in obj:
            self.listed = bool(obj['listed'])


    def clear(self):
        """ this clear all child nodes and perform necessary cleanup """

        session = object_session(self)

        for child in self.children:
            child.clear()
            session.delete(child)


    def generate_slug(self):
        """ generate random slug based on time """
        self.slug = str(time.time())


    def generate_path(self):
        if not self.slug:
            raise RuntimeError('Node slug needs to be initialized first!')
        if self.parent.path == '/':
            self.path = posixpath.normpath('/%s' % self.slug)
        else:
            self.path = posixpath.normpath('%s/%s' % (self.parent.path, self.slug))
        return self.path


    def render_title(self):
        return self.title


    def is_manageable(self, user):
        # check if user has ADMIN role or owner of this page
        if not user:
            return False
        if self.user == user or user.has_roles(SYSADM, DATAADM):
            return True
        # check if user is a member of the group and group is writable:
        if self.group.has_member(user):
            return True
        return False


    # Flags related functions

    def is_commentable(self):
        return self.flags & (1 << 15)

    def set_commentable(self, val=True):
        self.flags |= ((1 if val else 0) << 15)

    def is_inmenu(self):
        return self.flags & (1 << 14)

    def set_inmenu(self, val=True):
        self.flags |= ((1 if val else 0) << 14)


    def add(self, n):
        if not n.slug:
            n.generate_slug()
        n.site_id = self.site_id
        n.level = self.level + 1
        self.children.append(n)
        n.generate_path()
        object_session(n).flush()
        n.ordering = 19 * n.id
        return n


    @property
    def url(self):
        return self.path[1:]


    @classmethod
    def container(cls, item_cls):
        global _containers_
        try:
            _containers_[cls].append( item_cls )
        except KeyError:
            _containers_[cls] = [ item_cls ]
        return item_cls


    @classmethod
    def inherited_container(cls, item_cls):
        global _inherited_containers_
        try:
            _inherited_containers_[cls].append( item_cls )
        except KeyError:
            _inherited_containers_[cls] = [ item_cls ]
        return item_cls


    @classmethod
    def get_item_classes(cls):
        global _containers_, _inherited_containers_
        if hasattr(cls, '__strict_container__') and cls.__strict_container__ != None:
            return cls.__strict_container__
        cls_set = _containers_.get(cls, [])
        for c,l in _inherited_containers_.items():
            if issubclass(cls, c):
                cls_set = cls_set + l
        return cls_set


    @classmethod
    def search(cls, text, site_id):
        raise NotImplementedError


    @classmethod
    def get_label(cls):
        return getattr(cls, '__label__', cls.__name__)


    def as_dict(self):
        return dict(
            _type_ = type(self).__name__,
            site = self.site.fqdn,
            uuid = self.uuid,
            slug = self.slug,
            path = self.path,
            level = self.level,
            parent_url = self.parent.url if self.parent else '',
            ordering = self.ordering,
            user = self.user.login,
            group = self.group.name,
            create_time = self.create_time,
            publish_time = self.publish_time,
            expire_time = self.expire_time,
            state = self.state,
            flags = self.flags,
            listed = self.listed,
            mimetype = self.mimetype,
            json_code = self.json_code,
        )


    def as_yaml(self):
        return yaml.dump(self.as_dict(), default_flow_style=False)

    @classmethod
    def from_dict(d, obj=None):
        if not obj:
            obj = Node()
        obj.update(d)
        # update the low-level data
        obj.user = None
        obj.group = None


    def ascendant(self, node):
        """ check wheter self is an ascendant of node """
        if self.level < node.level: return False
        if self.level == node.level:
            return True if self == node else False
        parent_node = self.parent
        while parent_node.level >= node.level:
            if parent_node == node:
                return True
            parent_node = self.parent
        return False


    def versioning(self):
        self._versioning = self.as_yaml().splitlines()


    def diff(self):
        curr_yaml = self.as_yaml().splitlines()
        # difflib between self._versioning and curr_yaml
        return difflib.context_diff(self._versioning, curr_yaml, n=1)


    def difflog(self):
        diff = ''.join(self.diff())
        # create a difflog
        difflog_item = DiffLog()
        difflog_item.node = self
        difflog_item.diff = diff
        object_session(self).flush(difflog_item)
        return difflog_item


    def search_text(self):
        return ''


    def search_keywords(self):
        return ''


    def __repr__(self):
        return '<%s|%s|%s|%s>' % (self.__class__.__name__, self.id, self.path, self.title)


class DiffLog(BaseMixIn, Base):

    __tablename__ = 'difflogs'

    node_id = Column(types.Integer, ForeignKey('nodes.id'), nullable=False)
    node = relationship(Node, uselist=False,
        backref=backref('difflog', cascade='all, delete-orphan'))

    diff = Column(types.Text, nullable=False, server_default='')

    def __repr__(self):
        return '<DiffLog|%d|%s>' % (self.node_id, self.stamp)


class Workflow(BaseMixIn, Base):

    __tablename__ = 'workflows'

    node_id = Column(types.Integer, ForeignKey('nodes.id'), nullable=False)
    node = relationship(Node, uselist=False)

    state = Column(types.Integer, nullable=False, server_default='0')
    # state indicates the position in the workflow step
    # 0 - the final step, ie. published

    log = Column(types.String(256), nullable=False, server_default='')

    __table_args__ = ( UniqueConstraint('node_id', 'state'), )



class ACL(BaseMixIn, Base):

    __tablename__ = 'xacls'

    node_id = Column(types.Integer, ForeignKey('nodes.id'), nullable=False, index=True)
    node = relationship(Node, uselist=False)

    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=True)

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=True)

    mode = Column(types.Integer, nullable=False, server_default='0')

    __table_args__ = (  UniqueConstraint('node_id', 'user_id'),
                        UniqueConstraint('node_id', 'group_id'),
    )



class Tag(Base):

    __tablename__ = 'tags'

    id = Column(types.Integer, primary_key=True)

    node_id = Column(types.Integer, ForeignKey('nodes.id'), nullable=False, index=True)
    node = relationship(Node, uselist=False, backref=backref('tags'))

    tag_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False, index=True)

    user_id = Column(types.Integer, ForeignKey('users.id'))

    __table_args__ = (  UniqueConstraint('node_id', 'tag_id'), )



## container related

_containers_ = {}
_inherited_containers_ = {}

def self_container(item_cls):
    global _containers_
    try:
        _containers_[item_cls].append( item_cls )
    except KeyError:
        _containers_[item_cls] = [ item_cls ]
    return item_cls


__NOTE__ = '''

json_code can be used to further control a node.
Below are options used in json_code:

strict_containers: [ ]


'''
