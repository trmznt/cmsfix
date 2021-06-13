
from rhombus.models import handler as rho_handler
from rhombus.lib.utils import cout, cerr, cexit
from cmsfix.models import node, pagenode, filenode, journalnode

from sqlalchemy.orm import exc


class DBHandler(rho_handler.DBHandler):

    Site = node.Site
    Node = node.Node
    Tag = node.Tag
    PageNode = pagenode.PageNode
    FileNode = filenode.FileNode
    JournalNode = journalnode.JournalNode
    JournalItemNode = journalnode.JournalItemNode


    def initdb(self, create_table=True, init_data=True, rootpasswd=None):
        super().initdb(create_table, init_data, rootpasswd)
        if init_data:
            from cmsfix.models.setup import setup
            setup( self )
            cerr('[cmsfix] Database has been initialized.')

    def get_site(self, fqdn):
        q = self.Site.query(self.session()).filter( self.Site.fqdn == fqdn )
        return q.one()


    def get_node(self, key, site, default=None):
        if key.startswith('/'):
            try:
                # use key as path
                q = self.Node.query(self.session()).filter( self.Node.path == key )
                if site is not None:
                    q = q.join(self.Site)
                    if type(site) == int:
                        q = q.filter( self.Site.id == site )
                    else:
                        q = q.filter( self.Site.fqdn == site )
                return q.one()

            except exc.NoResultFound:
                return None

        return default


    def get_node_by_id(self, node_id):
        return self.Node.get(node_id, self.session())

    def get_nodes_by_ids(self, node_ids):
        return self.Node.query(self.session()).filter( self.Node.id.in_( node_ids ))

    def get_nodes_by_uuids(self, node_uuids):
        if type(node_uuids) == str:
            return self.Node.query(self.session()).filter( self.Node.uuid == node_uuids).one()
        elif type(node_uuids) == list:
            return self.Node.query(self.session()).filter( self.Node.uuid.in_( node_uuids) )

    def get_nodes_by_level(self, level):
        return self.Node.query(self.session()).filter( self.Node.level == level)

    def get_nodes(self, root=None, **kwargs):

        if 'type' in kwargs:
            _type = kwargs['type']
        else:
            _type = self.Node

        q = _type.query(self.session())

        if 'level' in kwargs:
            q = q.filter( _type.level == kwargs['level'] )

        if 'flags' in kwargs:
            q = q.filter( _type.flags.op('&')(kwargs['flags']) == kwargs['flags'] )

        if 'tags' in kwargs:
            # get the tag id
            tags = kwargs['tags']
            tags = [ tags ] if type(tags) != list else tags
            ek_ids = self.EK.getids( tags, grp='@TAG', dbsession=self.session())
            q = q.join(self.Tag).filter(self.Tag.tag_id.in_(ek_ids))

        return q
