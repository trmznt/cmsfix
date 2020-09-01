
from rhombus.lib.utils import get_dbhandler
from rhombus.views import *
from rhombus.views.home import login as rb_login, logout as rb_logout

from cmsfix.views import node

def index(request):

    # get the landing home
    landing_url = request.registry.settings.get('cmsfix.landing', None)
    if not landing_url:
        landing_url = '/'

    try:
        return node.index(request)

    except:
        raise

    return render_to_response('cmsfix:templates/home.mako',
                    {},
                    request = request)

def login(request):
    return rb_login(request)

def logout(request):
    return rb_logout(request)
