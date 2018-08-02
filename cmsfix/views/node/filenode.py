from cmsfix.views import *
from cmsfix.models.filenode import FileNode
from cmsfix.views.node.node import ( nav, node_submit_bar,
            NodeViewer,
)

from rhombus.views.fso import save_file
from rhombus.views import *
from rhombus.lib.utils import random_string

from pyramid.response import FileResponse, Response, FileIter

import os.path, mimetypes

class FileNodeViewer(NodeViewer):

    template_edit = 'cmsfix:templates/filenode/edit.mako'

    def render(self, request):

        if self.node.pathname:
            return FileResponse( self.node.pathname, content_type=self.node.mimetype,
                        request=request )
        else:
            return Response( app_iter = FileIter(self.node.fp),
                        content_type = self.node.mimetype, request=request )

        raise NotImplementedError()


    def new_node(self):
        n = FileNode()
        n.pathname = ''
        n.data = b''
        return n


    def edit_form(self, request, create=False):

        node = self.node

        eform, jscode = super().edit_form(request, create)
        eform.get('cmsfix.node-main').add(
            input_textarea('cmsfix-desc', 'Description', value=node.desc, offset=1, size="2x8" ),
            input_hidden('cmsfix-filename', value='')
        )

        eform = div(
            div(class_='row')[
                div(class_='col-md-2 col-md-offset-1')[
                    span(class_="btn btn-success fileinput-button")[
                        span('Select file to upload/change'),
                        inputtag(id='upload', type='file', name='files[]'),
                    ]
                ]
            ],
            div(class_='row')[
                div(class_='col-md-8 col-md-offset-1')[
                    table(class_='table table-condensed')[
                        tr(
                            td('Original filename'),
                            td(node.filename if node.id else '-', id="cmsfix-basename")
                        ),
                        tr(
                            td('File size'),
                            td(node.size if node.id else '-', id="cmsfix-size")
                        ),
                    ]
                ]
            ],
            eform
        )

        jscode = jscode + '''
        'use strict';

        $('#upload').fileupload({
            url: '%(parent_url)s',
            dataType: 'json',
            maxChunkSize: 1000000,
            done: function (e, data) {
                $('#cmsfix-slug').val( data.result.basename );
                $('#cmsfix-basename').text( data.result.basename );
                $('#cmsfix-size').text( data.result.size );
                $('#cmsfix-filename').val( data.result.basename )
                $('#cmsfix-mimetype_id').val( data.result.mimetype_id );
            },
            progressall: function (e, data) {
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $('#fileprogress .progress-bar').css('width', progress + '%%');
            },
            start: function (e) {
                $('#fileprogress .progress-bar').css('width','0%%');
                $('#fileprogress').show();
            },
            stop: function(e) {
                $('#fileprogress').hide();
            }
        }).prop('disabled', !$.support.fileInput)
            .parent().addClass($.support.fileInput ? undefined : 'disabled');
        ''' 

        sesskey = eform.get('cmsfix-sesskey').value
        return eform, jscode % dict( parent_url = request.route_url("filenode-upload", sesskey=sesskey) )


    def parse_form(self, f, d=None):

        d = super().parse_form(f, d)
        if 'cmsfix-filename' in f:
            d['filename'] = f['cmsfix-filename']
        d['desc'] = f['cmsfix-desc']

        return d

    def pre_save_node(self, request):

        sesskey = request.POST.get('cmsfix-sesskey')

        # sanity and authorization check
        user_id, _ = tokenize_sesskey(sesskey)
        if user_id != request.user.id:
            raise RuntimeError('Invalid session key!')


    def post_save_node(self, request):

        n = self.node
        sesskey = request.POST.get('cmsfix-sesskey')

        tmp_dir = request.registry.settings['cmsfix.tmpdir']
        dest_path = tmp_dir + '%s.payload' % sesskey

        with open(dest_path, 'rb') as f:
            n.write( f )

        os.unlink( dest_path)


    def edit_next(self, request=None):
        req = request or self.request
        return HTTPFound(location = req.route_url('node-content', path=self.node.parent.url))


# exposable functions

def index(request, node):

    return view(request, node)


def view(request, node):

    if node.pathname:
        return FileResponse( node.pathname, content_type=node.mimetype, request=request )

    else:

        return Response( app_iter = FileIter(node.fp), content_type=node.mimetype, request=request )


    raise NotImplementedError()


def content(request, node):
    raise NotImplementedError()


def add(request, node):

    if request.POST:

        sesskey = request.POST.get('sesskey')

        # sanity and authorization check
        user_id, _ = tokenize_sesskey(sesskey)
        if user_id != request.user.id:
            raise RuntimeError('Invalid session key!')

        d = parse_form(request.POST)
        n = FileNode()
        n.update(d)
        n.lastuser_id = n.user_id = request.user.id
        n.pathname = ''
        n.data = b''
        node.add(n)

        dbh = get_dbhandler()
        dbh.session().flush()

        tmp_dir = request.registry.settings['cmsfix.tmpdir']
        dest_path = tmp_dir + '%s.payload' % sesskey

        with open(dest_path, 'rb') as f:
            n.write( f )

        os.unlink( dest_path)

        if request.params['_method'].endswith('_edit'):
            return HTTPFound(location = request.route_url('node-edit', path=n.url))

        return HTTPFound(location = request.route_url('node-content', path=node.url))


    with get_dbhandler().session().no_autoflush:

        sesskey = generate_sesskey(request.user.id)

        n = FileNode()
        n.site = node.site

        eform, jscode = edit_form(n, request, create=True)
        eform.get('sesskey').value = sesskey
        jscode = jscode % dict( parent_url = request.route_url("filenode-upload", sesskey=sesskey) )

        return render_to_response('cmsfix:templates/filenode/edit.mako',
            {   'parent_url': node.path,
                'node': n,
                'toolbar': '', # new node does not have toolbar yet!
                'eform': eform,
                'code': jscode,
            }, request = request )


def edit(request, node):

    if request.POST:

        # update data

        sesskey = request.POST.get('sesskey')

        # sanity and authorization check
        user_id, _ = tokenize_sesskey(sesskey)
        if user_id != request.user.id:
            raise RuntimeError('Invalid session key!')

        d = parse_form(request.POST)
        node.update(d)

        tmp_dir = request.registry.settings['cmsfix.tmpdir']
        dest_path = tmp_dir + '%s.payload' % sesskey

        if os.path.exists(dest_path):
            with open(dest_path, 'rb') as f:
                node.write( f )
            os.unlink( dest_path)

        if request.params['_method'].endswith('_edit'):
            #raise RuntimeError
            return HTTPFound(location = request.route_url('node-edit', path=node.url))

        return HTTPFound(location = request.route_url('node-info', path=node.url))


    with get_dbhandler().session().no_autoflush:

        sesskey = generate_sesskey(request.user.id)

        eform, jscode = edit_form(node, request, create=False)
        eform.get('sesskey').value = sesskey
        jscode = jscode % dict( parent_url = request.route_url("filenode-upload", sesskey=sesskey) )

        return render_to_response('cmsfix:templates/filenode/edit.mako',
            {   'parent_url': node.path,
                'node': node,
                'toolbar': toolbar(request, node), # new node does not have toolbar yet!
                'eform': eform,
                'code': jscode,
            }, request = request )


def action(request, node):
    raise NotImplementedError()


def toolbar(request, node):
    return ''


@roles( PUBLIC )
def fileupload(request):

    sesskey = request.matchdict.get('sesskey')
    user_id, node_id = tokenize_sesskey(sesskey)
    if user_id != request.user.id:
        raise RuntimeError('Invalid session key!')

    filestorage = request.POST.get('files[]')
    filename = os.path.basename(filestorage.filename)

    tmp_dir = request.registry.settings['cmsfix.tmpdir']
    dest_path = tmp_dir + '%s.payload' % sesskey

    size, total = save_file(dest_path, filestorage, request)

    if size == total:
        dbh = get_dbhandler()
        file_mimetype = mimetypes.guess_type(filename)
        try:
            if not file_mimetype[0]:
                mimetype_id = dbh.EK._id('application/unknown')
            else:
                mimetype_id = dbh.EK._id( file_mimetype[0])
        except KeyError:
            mimetype_id = dbh.EK._id( 'application/unknown' )

        return { 'basename': filename, 'size': size, 'mimetype_id': mimetype_id }

    return {}


## internal functions


def edit_form(node, request, create=False):

    eform, jscode = node_edit_form(node, request, create)
    eform.get('cmsfix.node-main').add(
        input_textarea('cmsfix-desc', 'Description', value=node.desc, offset=1, size="2x8" ),
        input_hidden('sesskey', value=''),
        input_hidden('cmsfix-filename', value='')
    )

    eform = div(
        div(class_='row')[
            div(class_='col-md-2 col-md-offset-1')[
                span(class_="btn btn-success fileinput-button")[
                    span('Select file to upload/change'),
                    inputtag(id='upload', type='file', name='files[]'),
                ]
            ]
        ],
        div(class_='row')[
            div(class_='col-md-8 col-md-offset-1')[
                table(class_='table table-condensed')[
                    tr(
                        td('Original filename'),
                        td(node.filename if node.id else '-', id="cmsfix-basename")
                    ),
                    tr(
                        td('File size'),
                        td(node.size if node.id else '-', id="cmsfix-size")
                    ),
                ]
            ]
        ],
        eform
    )

    jscode = jscode + '''
    'use strict';

    $('#upload').fileupload({
        url: '%(parent_url)s',
        dataType: 'json',
        maxChunkSize: 1000000,
        done: function (e, data) {
            $('#cmsfix-slug').val( data.result.basename );
            $('#cmsfix-basename').text( data.result.basename );
            $('#cmsfix-size').text( data.result.size );
            $('#cmsfix-filename').val( data.result.basename )
            $('#cmsfix-mimetype_id').val( data.result.mimetype_id );
        },
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#fileprogress .progress-bar').css('width', progress + '%%');
        },
        start: function (e) {
            $('#fileprogress .progress-bar').css('width','0%%');
            $('#fileprogress').show();
        },
        stop: function(e) {
            $('#fileprogress').hide();
        }
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');
    '''

    return eform, jscode


def parse_form(f, d=None):

    d = node_parse_form(f, d)
    d['filename'] = f['cmsfix-filename']
    d['desc'] = f['cmsfix-desc']

    return d


def generate_sesskey(user_id, node_id=None):
    if node_id:
        node_id_part = '%08x' % node_id
    else:
        node_id_part = 'XXXXXXXX'

    return '%08x%s%s' % (user_id, random_string(8), node_id_part)


def tokenize_sesskey(sesskey):

    user_id = int(sesskey[:8], 16)
    node_id_part = sesskey[16:]
    if node_id_part == 'XXXXXXXX':
        node_id = None
    else:
        node_id = int(node_id_part, 16)

    return (user_id, node_id)


def upload_file(request, node):

    sesskey = request.POST['sesskey']

    # sanity and authorization checks
    _, sesskey_user_id = tokenize_sesskey(sesskey)
    if sesskey_user_id != request.user.id:
        raise RuntimeError('Invalid session key')

    filestorage = request.POST['files[]']
    filename = os.path.basename(filestorage.filename)
    current_size, total = uploader_session.add_file()
    if current_size == total:
        pass

    return JSON_Response


class Uploader(object):

    def __init__(self, sesskey, user_id):
        check_sesskey(sesskey, user_id)

    def add_file(self, filename, request):

        current


    def finalize(self):
        pass
