
from cmsfix.models.node import *
from cmsfix.lib.workflow import set_workflow, InheritedWorkflow

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
    data = Column(types.LargeBinary(), nullable=False)
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

    def as_dict(self):
        d = super().as_dict()
        d['desc'] = self.desc
        d['size'] = self.size
        d['filename'] = self.filename
        return d

    @classmethod
    def from_dict(cls, d, obj=None):
        if not obj:
            obj = cls()
        obj = super().from_dict(d, obj)
        # update content
        return obj

    @classmethod
    def _load(cls, d, source_dir):
        node = super()._load(d, source_dir)
        with open(source_dir + '/_c.bin', 'rb') as f:
            node.write(f)
        return node

    def dump(self, target_dir):
        super().dump(target_dir)
        # write content
        with open(target_dir + '/_c.bin', 'wb') as f:
            f.write( self.fp.read() )


    def search_text(self):
        return self.desc


file_wf = InheritedWorkflow()
set_workflow(file_wf, FileNode)
