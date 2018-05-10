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


def dump(target_dir, node=None):
	""" dump node and its children to target dir """
	if node == None: node = get_node('/')
	dir_name = target_dir + node.path
	cerr('Dumping node [%s]' % node.path)
	node.dump(dir_name)

	for n in node.children:
		dump(target_dir, n)
	

def load(source_dir):
	""" load node and its children from source_dir """
	cerr('Loading from path: %s' % source_dir)
	node = get_dbhandler().Node.load(source_dir)

	for d in os.listdir(source_dir):
		path = source_dir + '/' + d
		if os.path.isdir(path):
			n = load(path)
			n.parent = node

	return node




# end of file
