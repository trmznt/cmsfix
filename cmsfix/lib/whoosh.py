
# this class provide whoosh interface

from whoosh.fields import SchemaClass, TEXT, ID, NUMERIC, STORED, KEYWORD
from whoosh.index import create_in, open_dir

from rhombus.models.meta import RhoSession
from rhombus.lib.utils import get_dbhandler, cerr
from cmsfix.models.node import Node
from sqlalchemy import event

import os

class SearchScheme(SchemaClass):

    # Whoosh base Searchable object

    nodeid = NUMERIC(stored=True, unique=True)
    mtime = STORED
    keywords = KEYWORD(lowercase=True, commas=True, scorable=True)
    text = TEXT


class Searchable(object):

    __slots__ = ['nodeid', 'mtime', 'text', 'keywords']

    def __init__(self, nodeid, mtime, text, keywords='' ):
        self.nodeid = nodeid
        self.mtime = mtime
        self.keywords = keywords
        self.text = text


class IndexService(object):

    def __init__(self, path):
        self.ix = None

        if not os.path.exists(path):
            os.mkdir(path)
            self.ix = create_in(path, SearchScheme)
        else:
            self.ix = open_dir(path)

        event.listen(RhoSession, "after_flush", self.after_flush)
        event.listen(RhoSession, "after_commit", self.after_commit)
        event.listen(RhoSession, "after_rollback", self.after_rollback)


    def after_flush(self, session, context):

        updater = self.get_updater(session)

        for n in session.new:
            if isinstance(n, Node):
                updater.created_objects[n.id] = Searchable(n.id, n.stamp, n.search_text(), n.search_keywords())

        for n in session.dirty:
            if isinstance(n, Node):
                updater.updated_objects[n.id] = Searchable(n.id, n.stamp, n.search_text(), n.search_keywords())

        for n in session.deleted:
            if isinstance(n, Node):
                updater.deleted_objects[n.id] = None


    def after_commit(self, session):

        updater = self.get_updater(session)

        with self.ix.writer() as writer:

            for nodeid in updater.deleted_objects:
                writer.delete_by_term('nodeid', nodeid)

            for obj in updater.created_objects.values():
                writer.add_document(nodeid=obj.nodeid, mtime=obj.mtime, text=obj.text, keywords=obj.keywords)

            for obj in updater.updated_objects.values():
                writer.delete_by_term('nodeid', obj.nodeid)
                writer.add_document(nodeid=obj.nodeid, mtime=obj.mtime, text=obj.text, keywords=obj.keywords)

        updater.reset()


    def after_rollback(self, session):

        updater = self.get_updater(session)
        updater.reset()


    def get_updater(self, session):

        if hasattr(session, 'ix_updater'):
            print('initialize updater')
            return getattr(session, 'ix_updater')

        updater = Updater()
        setattr(session, 'ix_updater', updater)
        return updater


# note of the design:
# Whoosh writer will be created for each db commit
# Whoosh reader will be attached to dbsession

class Updater(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.created_objects = {}
        self.updated_objects = {}
        self.deleted_objects = {}


_INDEX_SERVICE_ = None

def set_index_service(index_service):
    global _INDEX_SERVICE_
    _INDEX_SERVICE_ = index_service


def get_index_service():
    return _INDEX_SERVICE_


# utilities

def index_all():

    dbh = get_dbhandler()
    index_service = get_index_service()

    with index_service.ix.writer() as writer:

        for n in dbh.get_nodes():
            writer.delete_by_term('nodeid', n.id)
            writer.add_document(nodeid=n.id, mtime=n.stamp, text=n.search_text(), keywords=n.search_keywords())
            cerr('indexing node: %d' % n.id)

