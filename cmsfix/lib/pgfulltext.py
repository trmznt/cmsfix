#
# this is PostgreSQL-specific full text indexer
# only use this if the underlying rdbms is PostgreSQL

# need to define search interface

class SearchInterface(object):

	def __init__(self):
		pass

	def search(self, query):
		""" return [ node_ids, ... ] in relevance order
		"""
		pass


def set_search_interface(interface):
	pass

def get_search_interface():
	pass