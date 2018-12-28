
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.views.generics import *
from rhombus.lib.tags import *


def get_site(request):

    fqdn = request.registry.settings.get('cmsfix.site', None)

    if fqdn is None:
        return '*'

    # if cmsfix.site is None, then do not use site information
    # if cmsfix.site is *, then use hostname 
    if fqdn == '*':
        return request.host

    return fqdn

