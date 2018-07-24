from cmsfix.views import *
from cmsfix.views.node.pagenode import *
from cmsfix.models.node import NodeRelationship, object_session
from pyramid.renderers import render


def render_relationship_table(request, name=None, node1=None, node2=None, type1=None, type2=None,
        header=None, text=None, add_label=None, add_value=None, placeholder=''):

    if node1 and type2:
        items = object_session(node1).query(NodeRelationship).filter(NodeRelationship.node1_id == node1.id).\
                join(NodeRelationship.node2.of_type(type2))
        curnode = node1
        curtype = type2


    elif node2 and type1:
        items = object_session(node2).query(NodeRelationship).filter(NodeRelationship.node2_id == node2.id).\
                join(NodeRelationship.node1.of_type(type1))
        curnode = node2
        curtype = type1

    else:
        raise RuntimeError('FATAL PROG/ERR: either node1 <> type2 or node2 <> type1')


    # compose table

    table_body = tbody()

    for idx, item in enumerate(items):
        n = item.node2 if node1 else item.node1

        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="%s-ids" value="%d">' % (name, item.id))),
                td(a(n.title or n.slug, href=request.route_url('node-content', path=n.url))),
                td(item.text or 'None') if text else ''
            )
        )

    content_table = table(class_='table table-condensed table-striped')
    content_table.add(
        thead(
            tr(
                th('', style="width:2em;"),
                th(header),
                th(text) if text else ''
            )
        ),
        table_body
    )

    # content bar
    content_bar = selection_bar('%s-ids' % name, name='%s_selection_bar' % name,
        action=request.route_url('node-action', path=curnode.url),
        others = button(label=add_label,
                        class_="btn btn-sm btn-success", id='node-%s' % add_value,
                        name='_method', value=add_value, type='button'),
        hiddens=[('node_id', curnode.id), ],
        delete_value='del-%s' % name)
    content_table, content_js = content_bar.render(content_table)

    # popup

    popup_content = div(class_='form-group')
    popup_content.add(
            div(header,
                literal('''<select id="%s-add_id" name="%s-add_id" class='form-control' style='width:100%%;'></select>'''
                    % (curtype.__label__, curtype.__label__)),
                class_='col-md-11 col-md-offset-1'),
            div(text,
                literal('''<input type="text" name="text" class="form-control" />'''),
                class_='col-md-11 col-md-offset-1') if text else '',
        )

    submit_button = submit_bar(add_label, add_value)
    add_popup_form = form( name=add_value+'-form', method='POST',
                            action=request.route_url('node-action', path=curnode.url),
                        )[  popup_content,
                            literal('<input type="hidden" name="node_id" value="%d"/>'
                                % curnode.id),
                            submit_button ]

    popup_table = div(
        div(
            literal( render("rhombus:templates/generics/popup.mako",
            {   'title': add_label,
                'content': add_popup_form,
                'buttons': '',
            }, request = request )),
            id=add_value+'-modal', class_='modal fade', tabindex='-1', role='dialog'
        ),
        content_table
    )

    popup_js = content_js + '''

$('#node-%s').click( function(e) {
    $('#%s-modal').modal('show');
});

''' % (add_value, add_value) +  '''
  $('#%s-add_id').select2( {
        minimumInputLength: 3,
        placeholder: '%s',
        dropdownParent: $("#%s-modal"),
        ajax: {
            url: "%s",
            dataType: 'json',
            data: function(params) { return { q: params.term, t: "%s" }; },
            processResults: function(data, params) { return { results: data }; }
        },
    });
''' % (curtype.__label__, placeholder, add_value, request.route_url('node-lookup'), curtype.__label__)

    return (div(popup_table, class_='col-md-10'), popup_js)
