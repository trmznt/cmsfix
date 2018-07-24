
from rhombus.lib.utils import cerr, get_dbhandler
from cmsfix.lib.cmds import get_node

import os, transaction

def dump(target_dir, node=None, recursive=False):
	if node == None: node = get_node('/')
	dir_name = target_dir + node.path
	cerr('Dumping node [%s]' % node.path)
	node.dump(dir_name)

	if recursive:
		for n in node.children:
			dump(target_dir, n, recursive)	


def load(source_dir, archive=False, recursive=False, user=None, group=None):
	dbh = get_dbhandler()
	if not archive:
		# ignore before_update temporarily
		dbh.session().set_before_update_event(False)

	load_from_directory(source_dir, recursive, user, group, dbh)

	transaction.commit()
	if not archive:
		# return before_update event
		dbh.session().set_before_update_event(True)


def load_from_directory(source_dir, recursive, user, group, dbh):
	cerr('Loading from path: %s' % source_dir)
	node = dbh.Node.load(source_dir)

	if recursive:
		for d in os.listdir(source_dir):
			path = source_dir + '/' + d
			if os.path.isdir(path):
				n = load_from_directory(path, recursive, user, group, dbh)
				n.parent = node

	return node


def check_dump(source_dir, recursive=False, user=None, group=None):
	pass
