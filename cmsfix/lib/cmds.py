# cmds.py
# shell-like commands

from rhombus.lib.utils import get_dbhandler
from cmsfix.models.node import Node


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
	if not a_node.slug:
		a_node.generate_slug()
	parent_node.add(a_node)
	object_session(a_node).flush()
	a_node.ordering = 19 * a_node.id
	return a_node


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
	pass

# end of file
