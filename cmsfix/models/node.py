
from rhombus.models.core import *
from rhombus.models.ek import EK
from rhombus.models.user import User, Group
from rhombus.lib.roles import *
from rhombus.lib.utils import cerr, cout, get_dbhandler
from sqlalchemy.sql import func
from sqlalchemy.ext.orderinglist import ordering_list
import posixpath, time, difflib, yaml

from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy_utils.types.json import JSONType

import os


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

    ## flag options
    f_commentable = (1 << 15)
    f_inmenu = (1 << 14)


    def __init__(self, UUID=None, **kwargs):
        if not UUID:
            self.uuid = uuid.uuid1()
        else:
            self.uuid = UUID
        self._versioning = None
        self.flags = 0

        super().__init__(**kwargs)


    def update(self, obj):

        if 'site_id' in obj:
            self.site_id = obj['site_id']
        if 'slug' in obj and obj['slug']:
            self.slug = obj['slug']
        if 'path' in obj and obj['path']:
            self.path = obj['path']
        if 'user_id' in obj and type(obj['user_id']) == int:
            self.user_id = obj['user_id']
        if 'lastuser_id' in obj and type(obj['lastuser_id']) == int:
            self.lastuser_id = obj['lastuser_id']
        if 'group_id' in obj and type(obj['group_id']) == int:
            self.group_id = obj['group_id']
        if 'mimetype_id' in obj and type(obj['mimetype_id']) == int:
            self.mimetype_id = obj['mimetype_id']
        if 'listed' in obj:
            self.listed = bool(obj['listed'])
        if 'level' in obj:
            self.level = int(obj['level'])

        if 'ordering' in obj:
            self.ordering = int(obj['ordering'])
        if 'json_code' in obj:
            self.json_code = obj['json_code']

        # tags
        if 'tags' in obj:
            if not self.id:
                raise RuntimeError('FATAL ERR: node does not have id while performing tagging')
            Tag.sync_tags( self.id, obj['tags'], session = object_session(self) )

        # flags
        if 'flags-on' in obj:
            self.flags |= obj['flags-on']
        if 'flags-off' in obj:
            self.flags &= ~ obj['flags-off']


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

    def check_flags(self, flag):
        return self.flags & flag

    def set_flags(self, flag, val):
        self.flags = (self.flags | flag) if val == True else (self.flags & ~flag)


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
        register_nodeclass(item_cls)
        try:
            _containers_[cls].append( item_cls )
        except KeyError:
            _containers_[cls] = [ item_cls ]
        return item_cls

    @classmethod
    def explicit_container(cls, item_cls):
        global _explicit_containers_
        register_nodeclass(item_cls)
        try:
            _explicit_containers_[cls].append( item_cls )
        except KeyError:
            _explicit_containers_[cls] = [ item_cls ]
        return item_cls


    @classmethod
    def inherited_container(cls, item_cls):
        global _inherited_containers_
        register_nodeclass(item_cls)
        try:
            _inherited_containers_[cls].append( item_cls )
        except KeyError:
            _inherited_containers_[cls] = [ item_cls ]
        return item_cls


    def get_item_classes(self):
        global _containers_, _inherited_containers_, _explicit_containers_
        if hasattr(self, '__strict_container__') and self.__strict_container__ != None:
            return self.__strict_container__
        #raise RuntimeError
        if 'strict_container' in self.json_code:
            classnames = self.json_code['strict_container']
            classitems = ( _containers_.get(self.__class__, [])
                            + self.get_inherited_item_classes()
                            + _explicit_containers_.get(self.__class__, [])
                        )
            classitems_d = {}
            for classitem in classitems:
                classitems_d[classitem.__name__] = classitem
            return [ classitems_d[n] for n in classnames ]
        cls_set = _containers_.get(self.__class__, [])
        for c,l in _inherited_containers_.items():
            if issubclass(self.__class__, c):
                cls_set = cls_set + l
        return cls_set

    def get_inherited_item_classes(self):
        cls_set = []
        for c,l in _inherited_containers_.items():
            if issubclass(self.__class__, c):
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
            user = '%s/%s' % (self.user.login, self.user.userclass.domain),
            lastuser = '%s/%s' % (self.lastuser.login, self.lastuser.userclass.domain),
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
    def from_dict(cls, d, obj=None):
        if not obj:
            obj = cls()
            cerr('Created instance of [%s]' % obj.__class__.__name__)
        obj.update(d)
        # update the low-level data
        #obj.user = None
        #obj.group = None
        return obj


    # export/import

    def dump(self, target_dir):
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        with open(target_dir + '/_c.yaml', 'w') as f:
            f.write( self.as_yaml() )

    @classmethod
    def _load(cls, d, source_dir):

        # restore user & group
        dbh = get_dbhandler()
        d['site_id'] = dbh.get_site(d['site']).id
        user = dbh.get_user(d['user'])
        print(user)
        d['user_id'] = user.id
        lastuser = dbh.get_user(d.get('lastuser', d['user']))
        d['lastuser_id'] = lastuser.id
        group = dbh.get_group(d['group'])
        d['group_id'] = group.id
        mimetype = dbh.get_ekey(d['mimetype'])
        d['mimetype_id'] = mimetype.id

        # recreate node
        n = cls.from_dict(d)
        print(n)
        dbh.session().add(n)
        return n

    @staticmethod
    def load(source_dir):
        with open(source_dir + '/_c.yaml') as f:
            d = yaml.load(f.read())
        nodeclass = _nodeclasses_[ d['_type_'] ]
        print('NodeClass:', nodeclass)
        return nodeclass._load(d, source_dir)


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
    node = relationship(Node, uselist=False, backref=backref('tags', cascade='delete, delete-orphan'))

    tag_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False, index=True)
    tag = relationship(EK, uselist=False, )

    user_id = Column(types.Integer, ForeignKey('users.id'))

    __table_args__ = (  UniqueConstraint('node_id', 'tag_id'), )


    @classmethod
    def sync_tags(cls, node_id, tag_ids, user_id = None, session = None):
        # synchronize node_id and tag_ids

        # check user_id first
        if not user_id:
            user_id = get_userid()

        if not session:
            session = get_dbhandler().session()

        tags = cls.query(session).filter(cls.node_id == node_id)
        in_sync = []
        for tag in tags:
            if tag.tag_id in tag_ids:
                in_sync.append( tag.tag_id )
            else:
                # remove this tag
                session.delete(tag)

        print(in_sync)
        for tag_id in tag_ids:
            if tag_id in in_sync: continue
            print('add %d' % tag_id)
            cls.add_tag(node_id, tag_id, user_id, session)


    @classmethod
    def add_tag(cls, node_id, tag_id, user_id, session):
        tag = cls(node_id = node_id, tag_id = tag_id, user_id = user_id)
        if not session:
            session = get_dbhandler().session()
        session.add(tag)


    @classmethod
    def remove_tag(cls, node_id, tag_id, user_id, session):
        tag = cls.query().filter(cls.node_id == node_id, cls.tag_id == tag_id).one()
        session.delete(tag)


## container related
## the structure for below variabels is:
## d[cls] = [ cls1, cls2, ... ]

_containers_ = {}
_inherited_containers_ = {}
_explicit_containers_ = {}

def self_container(item_cls):
    global _containers_
    register_nodeclass(item_cls)
    try:
        _containers_[item_cls].append( item_cls )
    except KeyError:
        _containers_[item_cls] = [ item_cls ]
    return item_cls


_nodeclasses_ = {}

def register_nodeclass(cls):
    global _nodeclasses_
    cerr('Registering [%s]' % cls.__name__)
    if not cls.__name__ in _nodeclasses_:
        _nodeclasses_[cls.__name__] = cls



__NOTE__ = '''

json_code can be used to further control a node.
Below are options used in json_code:

strict_containers: [ ]


'''
