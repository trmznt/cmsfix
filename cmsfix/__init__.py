from pyramid.config import Configurator
from rhombus import init_app
from rhombus.lib.utils import cerr, cout, cexit, get_dbhandler
from rhombus.models.core import set_func_userid

# set configuration in cmsfix.scripts.run
from cmsfix.scripts import run

# for rendering configuration

from cmsfix.models.node import Node
from cmsfix.models.pagenode import PageNode
from cmsfix.models.journalnode import JournalNode, JournalItemNode
from cmsfix.models.filenode import FileNode
from cmsfix.models.commentnode import CommentNode
from cmsfix.views.node import register_module, register_viewer
from cmsfix.views.node import node as node_mod, pagenode as pagenode_mod
from cmsfix.views.node import journalnode as journalnode_mod, journalitemnode as journalitemnode_mod
from cmsfix.views.node import filenode as filenode_mod
from cmsfix.views.node import commentnode as commentnode_mod
from cmsfix.lib.workflow import set_workflow, GroupwareWorkflow
from cmsfix.lib.whoosh import IndexService, set_index_service


def includeme( config ):
    """ this configuration must be included as last order
    """

    # CMSFix configuration

    set_func_userid( get_userid_func )

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')
    config.add_view('cmsfix.views.home.index', route_name='home')

    config.add_route('login', '/login')
    config.add_view('cmsfix.views.home.login', route_name='login')

    config.add_route('logout', '/logout')
    config.add_view('cmsfix.views.home.logout', route_name='logout')

    config.add_route('search', '/search')
    config.add_view('cmsfix.views.search.index', route_name='search')

    config.add_route('tag-lookup', '/tag-lookup')
    config.add_view('cmsfix.views.node.tag_lookup', route_name='tag-lookup', renderer='json')

    config.add_route('filenode-upload', '/fileupload/{sesskey:.*}')
    config.add_view('cmsfix.views.node.filenode.fileupload', route_name='filenode-upload', renderer='json')

    config.add_route('node-view', '{path:.*}@@view')
    config.add_view('cmsfix.views.node.view', route_name='node-view')

    config.add_route('node-content', '{path:.*}@@content')
    config.add_view('cmsfix.views.node.content', route_name='node-content')

    config.add_route('node-info', '{path:.*}@@info')
    config.add_view('cmsfix.views.node.info', route_name='node-info')

    config.add_route('node-manage', '{path:.*}@@manage')
    config.add_view('cmsfix.views.node.manage', route_name='node-manage')

    config.add_route('node-add', '{path:.*}@@add')
    config.add_view('cmsfix.views.node.add', route_name='node-add')

    config.add_route('node-edit', '{path:.*}@@edit')
    config.add_view('cmsfix.views.node.edit', route_name='node-edit')

    config.add_route('node-action', '{path:.*}@@action')
    config.add_view('cmsfix.views.node.action', route_name='node-action')

    config.add_route('node-index', '{path:.*}')
    config.add_view('cmsfix.views.node.index', route_name='node-index')

    register_module(Node, node_mod)
    register_module(PageNode, pagenode_mod)
    register_module(FileNode, filenode_mod)
    register_module(JournalNode, journalnode_mod)
    register_module(JournalItemNode, journalitemnode_mod)

    register_viewer(Node, node_mod.NodeViewer)
    register_viewer(PageNode, pagenode_mod.PageNodeViewer)
    register_viewer(FileNode, filenode_mod.FileNodeViewer)

    config.override_asset('rhombus:templates/base.mako', 'cmsfix:templates/base.mako')
    config.override_asset('rhombus:templates/plainbase.mako', 'cmsfix:templates/plainbase.mako')

    # set index service
    set_index_service(IndexService(config.registry.settings['cmsfix.whoosh.path']))


def get_userid_func():
    return get_dbhandler().session().user.id


def main_xxx(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_view('cmsfix.views.home.index', route_name='home')
    config.include( includeme )
    set_workflow(GroupwareWorkflow())
    #config.scan()
    return config.make_wsgi_app()


def main(global_config, **settings):
    cerr('CMSFix main() is running...')
    config = init_app(global_config, settings, prefix='/mgr')
    config.include(includeme)
    set_workflow(GroupwareWorkflow())

    return config.make_wsgi_app()
