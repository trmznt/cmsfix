
from cmsfix.models.node import *

import io

@Node.inherited_container
class FileNode(Node):
    """ this class holds File
    """
    __label__ = 'File'
    __tablename__ = 'filenodes'

    id = Column(types.Integer, ForeignKey('nodes.id'), primary_key=True)

    filename = Column(types.String(256), nullable=False)
    pathname = Column(types.String(256), nullable=False)
    desc = Column(types.String(1024), nullable=False, server_default='')
    data = Column(types.Binary(), nullable=False)
    size = Column(types.Integer, nullable=False, server_default='0')

    __mapper_args__ = { 'polymorphic_identity': 2 }


    @classmethod
    def search(cls, text, site_id):
        """ search on filename and desc column """
        raise NotImplementedError()


    def update(self, obj):

        super().update(obj)

        if type(obj) == dict:
            if 'desc' in obj:
                self.desc = obj['desc']
            if 'size' in obj:
                self.size = obj['size']
            if 'filename' in obj:
                self.filename = obj['filename']

            return self

        raise NotImplementedError('Update object must use dictionary!')


    def write(self, istr):

        istr.seek(0, 2)
        self.size = istr.tell()
        istr.seek(0, 0)

        if self.size < 5000000:
            self.data = istr.read()
            self.pathname = ''

        else:
            assert(node.id)
            node_id = '%08x' % node.id

            raise NotImplementedError()


    def read(self):
        pass


    @property
    def fp(self):
        if self.pathname:
            return open(self.pathname, 'rb')
        return io.BytesIO( self.data )

    @property
    def title(self):
        return self.slug

    def search_text(self):
        return self.desc

