
from cmsfix.models.node import *

@self_container
@Node.container
class PageNode(Node):
    """ this is base Page
    """
    __label__ = 'Page'
    __tablename__ = 'pagenodes'

    id = Column(types.Integer, ForeignKey('nodes.id'), primary_key=True)

    # whether to render view or render content as default index
    view = Column(types.Boolean, nullable=False, default=True)

    title = Column(types.String(256), nullable=False, server_default='')
    keywords = Column(types.String(256), nullable=False, server_default='')
    summary = Column(types.String(512), nullable=False, server_default='')
    content = Column(types.String, nullable=False, server_default='')

    __mapper_args__ = { 'polymorphic_identity': 1 }

    __mimetypes__ = [ 'text/*', ]


    def update(self, obj):

        super().update(obj)

        if 'title' in obj:
            self.title = obj['title']
        if 'content' in obj:
            self.content = obj['content']
        if 'summary' in obj:
            self.summary = obj['summary']
        if 'keywords' in obj:
            self.keywords = obj['keywords']

    def generate_slug(self):
        self.slug = self.title.replace(' ','-').replace('--','-').replace("'",'').replace('#','').replace('%','').lower()

    def search_text(self):
        return ' '.join( (self.title, self.content, self.summary) )

    def search_keywords(self):
        return self.keywords

    @classmethod
    def search(cls, text, site_id):
        """ search on title, keywords, summary and content column """
        raise NotImplementedError()

    def as_dict(self):
        d = super().as_dict()
        d.update(
            view = self.view,
            title = self.title,
            content = self.content,
            summary = self.summary,
            keywords = self.keywords,
        )
        return d
