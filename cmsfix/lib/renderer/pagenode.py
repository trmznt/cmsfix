
from cmsfix.lib.renderer import *
from cmsfix.lib.renderer.node import nav
from rhombus.lib.tags import *

def render_pagenode(n, request, toolbar=''):

    html = n.content

    return render_to_response('cmsfix:templates/pagenode/node.mako',
            {   'page': n,
                'toolbar': toolbar,
                'html': html,
            }, request = request )


def page_toolbar(n, request):
    toolbar = nav(class_='navbar navbar-default')[
        div(class_='container-fluid')[
            div(class_='collapse navbar-collapse')[
                ul(class_='nav navbar-nav')[
                    li(a('View', href=request.route_url('node-view', path=n.url))),
                    li(a('Edit', href=request.route_url('node-edit', path=n.url))),
                    li(a('Content', href=request.route_url('node-content', path=n.url))),
                    li(a('Info', href=request.route_url('node-info', path=n.url))),
                    li(a('Add')),
                ],
                ul(class_='nav navbar-nav navbar-right')[
                    li(a('Delete')),
                    li(a('Publish')),
                ]
            ]

        ]

    ]
    return toolbar

def pagenode_editor(n, request):

    html = div()

    return html