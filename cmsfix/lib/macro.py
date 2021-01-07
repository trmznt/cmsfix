
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.tags import *
from cmsfix.models.node import Node
import re

# the pattern below is either
# ///123
# <<MacroName>>
# [[MacroName]]
pattern = re.compile('///(\d+)|///\{([\w-]+)\}|\&lt\;\&lt\;(.+)\&gt\;\&gt\;|\[\[(.+)\]\]')


# syntax for Macro is:
# [[MacroName|option1|option2|option3]]

class MacroError(RuntimeError):
    pass

def postrender(buffer, node, request):
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
            nb += run_macro(group, node, dbh, request)

        else:
            nb += '{{ ERR: macro pattern unprocessed }}'

        start_pos = m.end()

    nb += buffer[start_pos:]

    return nb


def postedit(content, node):
    """ post edit the content, return a new modified content """

    dbh = get_dbhandler()
    nc = ''
    start_pos = 0

    for m in pattern.finditer(content):

        nc += content[start_pos:m.start()]
        group = m.group()

        if group.startswith('///'):
            if group[3] != '{':
                # convert to UUID
                node = dbh.get_node_by_id(int(group[3:]))
                nc += '///{' + str(node.uuid) + '}'
            else:
                nc += group

        else:
            nc += group

        start_pos = m.end()

    nc += content[start_pos:]
    return nc


def node_link(text, dbh):

    if text[3] == '{':
        node = dbh.get_nodes_by_uuids(text[4:-1])
    else:
        node = dbh.get_node_by_id(int(text[3:]))

    return literal('<a href="/%s">%s</a>' % (node.url, node.title))


def run_macro(text, node, dbh, request):

    global _MACROS_

    text = text[2:-2]
    components = text.split('|')
    macro_name = components[0]

    if macro_name not in _MACROS_:
        return '[[ERR - macro %s not found]]' % macro_name

    try:
        return _MACROS_[macro_name](node, components[1:], request)
    except MacroError as m_err:
        return '[[%s ERR: %s]]' % (macro_name, m_err)


_MACROS_ = {}

def macro(func):

    global _MACROS_

    macro_name = func.__name__
    if not macro_name.startswith('M_'):
        raise RuntimeError('function name does not start with M_')

    _MACROS_[macro_name[2:]] = func

    return func


def macro_dict():
    return _MACROS_

## -- MACRO --
##
## all macro functions should return either html or literal objects
##

@macro
def M_ListChildNodes(node, components, request):
    """ Create list of child nodes.

        [[ListChildNodes|option|option|..]]

        Options:
            type=Nodetype(PageNode,JournalNode, etc)
            order=[+-]slug/id/mtime/title

        Example:
            [[ListChildNodes|type=PageNode|order=+title]]
    """

    nodetype=[]
    children = node.children
    for c in components:
        if c.startswith('type='):
            nodetype.append( c[5:] )
        elif c.startswith('order='):
            order = c[6:].strip().lower()
            desc = False
            if order[0] == '-':
                desc = True
                order = order[1:]
            elif order[0] == '+':
                order = order[1:]
            # we cancel the default ordering first
            children = node.children.order_by(None)
            if order == 'slug':
                if desc: children = children.order_by(Node.slug.desc())
                else: children = children.order_by(Node.slug)
            elif order == 'id':
                if desc: children = children.order_by(Node.id.desc())
                else: children = children.order_by(Node.id)
            elif order == 'mtime':
                if desc: children = children.order_by(Node.stamp.desc())
                else: children = children.order_by(Node.stamp)
            elif order == 'title':
                children_list = sorted( [(n.title or n.slug, n) for n in children.all()],
                                        reverse = desc)
                children = [n for (k, n) in children_list]
            else:
                raise MacroError("unknown order option: %s" % order )

    html = div()

    toc = ul()

    if not nodetype:
        nodetype.append( 'PageNode' )

    for c in children:
        if c.__class__.__name__ in nodetype:
            toc.add(
                li(a(c.title, href=c.path))
            )

    html.add(toc)
    return html


@macro
def M_Img(node, components, request):
    """ Show embedded images in the text.

        [[Img|source|option|option|...]]

        source: link to source (//ID, /images/a.jpg, http://domain/image.jpg, path/to/image.jpg)

        Options:
            currently none
    """

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
def M_ListNode(node, components, request):
    """ Create list of nodes that are accessible by the current user.

        [[ListNode|option|...]]

        Options:

            level = node level

            tags = only nodes which have these tags

        Example:

            [[ListNode|level=2|tags=keyword1;keyword2]]

    """

    kwargs = {}
    for c in components:
        if c.startswith('level='):
            kwargs['level'] = int(c[6:])
        elif c.startswith('tags='):
            kwargs['tags'] = c[5:].split(';')
        elif c.startswith('limit='):
            pass

    nodes = get_dbhandler().get_nodes(**kwargs)
    html = div()
    toc = ul()

    for n in nodes:
        # check user accessibility
        toc.add(
            li(a(n.title or n.slug, href=n.path))
        )

    html.add(toc)
    return html

