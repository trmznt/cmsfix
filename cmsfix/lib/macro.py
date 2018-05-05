
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.tags import *
import re

# the pattern below is either
# ///123
# <<MacroName>>
# [[MacroName]]
pattern = re.compile('///(\d+)|\&lt\;\&lt\;(.+)\&gt\;\&gt\;|\[\[(.+)\]\]')


# syntax for Macro is:
# [[MacroName|option1|option2|option3]]

def postrender(buffer, node):
    """ return a new buffer """

    dbh = get_dbhandler()

    nb = ''
    start_pos = 0

    for m in pattern.finditer(buffer):

        nb += buffer[start_pos:m.start()]

        group = m.group()

        print(group)

        if group.startswith('///'):
            nb += node_link(group, dbh)

        elif group.startswith('[['):
            nb += run_macro(group, node, dbh)

        start_pos = m.end()

    nb += buffer[start_pos:]

    return nb


def node_link(text, dbh):

    node = dbh.get_node_by_id(int(text[3:]))

    return literal('<a href="/%s">%s</a>' % (node.url, node.title))


def run_macro(text, node, dbh):

    global _MACROS_

    text = text[2:-2]
    components = text.split('|')
    macro_name = components[0]

    if macro_name not in _MACROS_:
        return '[[ERR - macro %s not found]]' % macro_name

    return _MACROS_[macro_name](node, components[1:])


_MACROS_ = {}

def macro(func):

    global _MACROS_

    macro_name = func.__name__
    if not macro_name.startswith('M_'):
        raise RuntimeError('function name does not start with M_')

    _MACROS_[macro_name[2:]] = func

    return func

## -- MACRO --
##
## all macro functions should return either html or literal objects
##

@macro
def M_ListChildNodes(node, components):

    nodetype=[]
    for c in components:
        if c.startswith('type='):
            nodetype.append( c[5:] )

    html = div()

    toc = ul()

    if not nodetype:
        nodetype.append( 'PageNode' )

    for c in node.children:
        if c.__class__.__name__ in nodetype:
            toc.add(
                li(a(c.title, href=c.path))
            )

    html.add(toc)
    return html


@macro
def M_Img(node, components):

    path = components[0]
    if path.startswith('http') or path.startswith('ftp'):
        url = path
    elif path.startswith('//'):
        image_node_id = int(path[2:])
        image_node = get_dbhandler().get_node_by_id(image_node_id)
        if not image_node:
            return '[[ Invalid image macro: non existent node %d]]' % image_node_id
        url = image_node.path
    elif path.startswith('/'):
        # check node with this path
        path_node = get_dbhandler().get_node_by_path(path)
        if not path_node:
            return '[[ Invalid image macro: not existent path %s ]]' % path
        url = path
    else:
        url = '/%s/%s' % (node.url, path)
        #return '[[ Invalid image macro (%s) ]]' % path

    return literal('<img src="%s" />' % url)


@macro
def M_ListNode(node, components):

    kwargs = {}
    for c in components:
        if c.startswith('level='):
            kwargs['level'] = int(c[6:])
        elif c.startswith('tags='):
            kwargs['tags'] = c[5:].split(';')

    nodes = get_dbhandler().get_nodes(**kwargs)
    html = div()
    toc = ul()

    for n in nodes:
        toc.add(
            li(a(n.title, href=n.path))
        )

    html.add(toc)
    return html

