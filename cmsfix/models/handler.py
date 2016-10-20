
from rhombus.models import handler as rho_handler
from rhombus.lib.utils import cout, cerr, cexit
from cmsfix.models import node, pagenode, filenode, journalnode

from sqlalchemy.orm import exc


class DBHandler(rho_handler.DBHandler):

    Site = node.Site
    Node = node.Node
    PageNode = pagenode.PageNode
    FileNode = filenode.FileNode
    JournalNode = journalnode.JournalNode
    JournalItemNode = journalnode.JournalItemNode


    def initdb(self, create_table=True, init_data=True):
        super().initdb(create_table, init_data)
        if init_data:
            from cmsfix.models.setup import setup
            setup( self )
            cerr('[cmsfix] Database has been initialized.')


    def get_node(self, key, default=None):
        if key.startswith('/'):
            try:
                # use key as path
                q = self.Node.query(self.session()).filter( self.Node.path == key )
                return q.one()

            except exc.NoResultFound:
                return None

        return default


    def get_node_by_id(self, node_id):
        return self.Node.get(node_id, self.session())


    def get_nodes(self, params = None):
        if not params:
            return self.Node.query(self.session())
        raise NotImplementedError()