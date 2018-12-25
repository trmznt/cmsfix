# cmds.py
# shell-like commands

from rhombus.lib.utils import get_dbhandler, cout, cerr
from cmsfix.models.node import Node, object_session

import os, transaction


def get_node(arg):
    """ get a node from arg """
    if isinstance(arg, Node):
        return arg
    if type(arg) == str:
        if arg.isdigit():
            # treat arg as node id
            node_id = int(arg)
            return get_dbhandler().get_node_by_id(node_id)
        else:
            # treat arg as path or url
            return get_dbhandler().get_node(arg)
    if type(arg) == int:
        return get_dbhandler().get_node_by_id(arg)

    return None


def ls(a_node):
    """ list content of a_node """
    a_node = get_node(a_node)
    for n in a_node.children:
        print('%04d  %s' % (n.id, n.path))


def add(parent_node, a_node):
    """ add a_node to parent_node """
    return parent_node.add(a_node)


def update(a_node, data):
    """ update a_node with data (either a dict or a node) """
    prev_yaml = a_node.as_yaml()
    a_node.update(data)
    curr_yaml = a_node.as_yaml()
    # create a diff from prev_yaml -> curr_yaml


def mv(a_node, dest_node):
    """ move a_node to dest_node """
    pass


def rm(a_node, opts=None):
    """ remove a_node, recursively if needed """
    sess = object_session(a_node)
    if not sess:
        sess = get_dbhandler().session()
    sess.delete( a_node )


def dump(target_dir, node=None, recursive=False):
    """ dump node and its children to target dir """

    from cmsfix.lib import dumputils
    return dumputils.dump(target_dir, node, recursive)
    

def load(source_dir, archive=False, recursive=False, user=None, group=None):
    """ load node and its children from source_dir """

    from cmsfix.lib import dumputils
    return dumputils.load(source_dir, archive, recursive, user, group)


def newsite(fqdn):
    """" create a new site """

    dbh = get_dbhandler()
    defgroup = dbh.get_group('__default__')
    a_site = dbh.Site(fqdn=fqdn, group_id = defgroup.id)
    dbh.session().add(a_site)

def newroot(fqdn):
    """ create a new root on site """

    dbh = get_dbhandler()

    sysuserclass = dbh.get_userclass('_SYSTEM_')
    sysuser = sysuserclass.get_user('system')
    sysgroup = dbh.get_group('_SysAdm_')

    a_site = dbh.get_site(fqdn)
    rootpage = dbh.PageNode(site_id = a_site.id, slug='/', path='/',
            user_id=sysuser.id, group_id=sysgroup.id, lastuser_id=sysuser.id,
            ordering=0,
            mimetype = 'text/x-rst')

    dbh.session().add(rootpage)


def reindex():
    """ re-index whoosh database with all nodes """

    from cmsfix.lib.whoosh import index_all, get_index_service
    index_all()

# end of file
