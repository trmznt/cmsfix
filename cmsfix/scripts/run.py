
import sys, os
import argparse

from rhombus.scripts.run import main as rhombus_main, set_config
from rhombus.lib.utils import cout, cerr, cexit

from cmsfix.models.handler import DBHandler


def greet():
    cerr('cmsfix-run - command line utility for CMSFix/rhombus')


def usage():
    cerr('cmsfix-run - command line utility for CMSFix/rhombus')
    cerr('usage:')
    cerr('\t%s scriptname [options]' % sys.argv[0])
    sys.exit(0)


set_config( environ='CMSFIX_CONFIG',
            paths = ['cmsfix.scripts.'],
            greet = greet,
            usage = usage,
            dbhandler_class = DBHandler
)

main = rhombus_main


