
from rhombus.lib.utils import cerr, get_dbhandler
from rhombus.scripts import setup_settings, arg_parser
from cmsfix.scripts import run
from cmsfix.lib.whoosh import IndexService, set_index_service
import sys

def greet():
    cerr('cmsfix-shell - shell for CMSFix')


def usage():
    cerr('cmsfix-shell - shell for CMSFix')
    cerr('usage:')
    cerr('\t%s scriptname [options]' % sys.argv[0])
    sys.exit(0)


def main():
    greet()

    # preparing everything
    p = arg_parser('cmsfix-shell')
    args = p.parse_args(sys.argv[1:])

    settings = setup_settings( args )
    dbh = get_dbhandler(settings)
    set_index_service( IndexService(settings['cmsfix.whoosh.path']) )

    from IPython import embed
    from cmsfix.lib import cmds
    import transaction
    embed()

