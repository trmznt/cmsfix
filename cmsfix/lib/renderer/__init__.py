
from pyramid.renderers import render_to_response

_RENDERER_FUNCS_ = {}

def register_renderer(class_, renderer, toolbar=None, editor=None):
    global _RENDERER_FUNCS_
    _RENDERER_FUNCS_[class_] = (renderer, toolbar, editor)


def render_node(node, request, toolbar=''):
    return _RENDERER_FUNCS_[node.__class__][0](node, request, toolbar)

def render_toolbar(node, request):
    return _RENDERER_FUNCS_[node.__class__][1](node, request)

def render_editor(node, request):
    return _RENDERER_FUNCS_[node.__class__][2](node, request)

