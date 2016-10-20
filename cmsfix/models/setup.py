


def setup( dbh ):

    # insert EnumKey's CMSFix specifics
    dbh.EK.bulk_insert( ek_initlist, dbsession = dbh.session() )


    # create default group: default and domain: '*'
    defgroup = dbh.get_group('__default__')
    if defgroup is None:
        raise RuntimeError('default group does not exist!')
    defsite = dbh.Site(fqdn='*', group_id=defgroup.id)
    dbh.session().add(defsite)

    # create index page, belongs to _system_
    sysuserclass = dbh.get_userclass('_SYSTEM_')
    sysuser = sysuserclass.get_user('system')
    sysgroup = dbh.get_group('_SysAdm_')

    rootpage = dbh.PageNode(site_id=defsite.id, slug='/', path='/',
            user_id=sysuser.id, group_id=sysgroup.id, lastuser_id=sysuser.id,
            ordering=0,
            mimetype = 'text/x-rst')

    dbh.session().add(rootpage)


ek_initlist = [
    (   '@SYSNAME', 'System names',
        [
            ( 'CMSFix', 'CMSFix' ),
        ]
    ),
    (   '@TAG', 'Tag container',
        [],
        ),
]
