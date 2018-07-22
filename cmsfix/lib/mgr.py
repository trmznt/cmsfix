
from rhombus.scripts import setup_settings, arg_parser
from rhombus.lib.utils import cerr, cout, cexit, get_dbhandler
from rhombus.models.core import set_func_userid

from cmsfix.lib import cmds
import transaction

def init_argparser( parser = None ):

    if parser is None:
        p = arg_parser('mgr [options]')
    else:
        p= parser

    p.add_argument('--rm', default=False, action='store_true',
        help = 'remove node')

    p.add_argument('--dump', default=False, action='store_true',
        help = 'dump url to destination directory')

    p.add_argument('--load', default=False, action='store_true',
        help = 'load from source directory')


    p.add_argument('--url', default='/')

    p.add_argument('--srcdir')
    p.add_argument('--dstdir')

    p.add_argument('--recursive', default=False, action='store_true')

    p.add_argument('--login', default='')
    p.add_argument('--commit', default=False, action='store_true')

    return p


def main( args ):

    settings = setup_settings( args )

    if args.commit:
        with transaction.manager:
            do_mgr( args, settings )
            cerr('** COMMIT database **')

    else:
        do_mgr( args, settings )


def userid_factory(user_id):
    def _func():
        return user_id
    return _func


def do_mgr(args, settings, dbh = None):

    if not dbh:
        dbh = get_dbhandler( settings )

    # set default user
    login = args.login or None
    if login:
        user = dbh.get_user(login)
        if not user:
            cexit('ERR: user %s not found' % login)
        set_func_userid( userid_factory( user.id ))
    else:
        set_func_userid( userid_factory(1))


    if args.rm:
        do_rm(args, dbh, settings)

    if args.dump:
        do_dump(args, dbh, settings)

    if args.load:
        do_load(args, dbh, settings)


def do_rm(args, dbh, settings):

    n = cmds.get_node(args.url)
    cmds.rm( n )
    dbh.session().flush()


def do_dump(args, dbh, settings):

    n = cmds.get_node(args.url)
    cmds.dump(args.dstdir, n, args.recursive)


def do_load(args, dbh, settings):

    cmds.load(args.srcdir, recursive=args.recursive)


