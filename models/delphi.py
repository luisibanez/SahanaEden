# coding: utf8

"""
    Delphi decision maker
"""

module = "delphi"
if deployment_settings.has_module(module):

    ########
    # Groups
    ########
    resource = 'group'
    tablename = module + '_' + resource
    table = db.define_table(tablename, timestamp,
        Field('name', notnull=True),
        Field('description', 'text'),
        Field('active', 'boolean', default=True),
        migrate=migrate)

    table.name.label = T("Group Title")
    table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "delphi_group.name")]

    # CRUD Strings
    ADD_GROUP = T('Add Group')
    LIST_GROUPS = T('List Groups')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_GROUP,
        title_display = T('Group Details'),
        title_list = LIST_GROUPS,
        title_update = T('Edit Group'),
        title_search = T('Search Groups'),
        subtitle_create = T('Add New Group'),
        subtitle_list = T('Groups'),
        label_list_button = LIST_GROUPS,
        label_create_button = ADD_GROUP,
        msg_record_created = T('Group added'),
        msg_record_modified = T('Group updated'),
        msg_record_deleted = T('Group deleted'),
        msg_list_empty = T('No Groups currently defined'))

    s3xrc.model.configure(table, list_fields=['id', 'name', 'description'])

    ##################
    # Group Membership
    ##################
    delphi_role_opts = {
        1:T('Guest'),
        2:T('Contributor'),
        3:T('Participant'),
        4:T('Moderator')
    }
    resource = 'user_to_group'
    tablename = module + '_' + resource
    table = db.define_table(tablename,
        Field('group_id', db.delphi_group, notnull=True),
        Field('user_id', db.auth_user, notnull=True),
        Field('description'),
        Field('req', 'boolean', default=False),
        Field('status', 'integer', default=1),
        migrate=migrate)

    table.group_id.label = T('Problem Group')
    table.group_id.requires = IS_IN_DB(db, 'delphi_group.id', '%(name)s')
    table.group_id.represent = lambda id: (id and [db(db.delphi_group.id == id).select(limitby=(0, 1)).first().name] or ["None"])[0]
    table.user_id.label = T('User')
    table.user_id.represent = lambda user_id: (user_id == 0) and '-' or '%(first_name)s %(last_name)s [%(id)d]' % db(db.auth_user.id==user_id).select()[0]
    #table.user_id.requires = IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s [%(id)d]')
    table.user_id.requires = IS_IN_DB(db, 'auth_user.id', shn_user_represent)
    table.status.requires = IS_IN_SET(delphi_role_opts, zero=None)
    table.status.represent = lambda opt: delphi_role_opts.get(opt, UNKNOWN_OPT)

    # CRUD Strings
    ADD_MEMBERSHIP = T('Add Membership')
    LIST_MEMBERSHIPS = T('List Memberships')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MEMBERSHIP,
        title_display = T('Membership Details'),
        title_list = LIST_MEMBERSHIPS,
        title_update = T('Edit Membership'),
        title_search = T('Search Memberships'),
        subtitle_create = T('Add New Membership'),
        subtitle_list = T('Memberships'),
        label_list_button = LIST_MEMBERSHIPS,
        label_create_button = ADD_MEMBERSHIP,
        msg_record_created = T('Membership added'),
        msg_record_modified = T('Membership updated'),
        msg_record_deleted = T('Membership deleted'),
        msg_list_empty = T('No Memberships currently defined'))

    s3xrc.model.configure(table, list_fields=['id', 'group_id', 'user_id', 'status', 'req'])

    ##########
    # Problems
    ##########
    resource = 'problem'
    tablename = module + '_' + resource
    table = db.define_table(tablename,
        Field('group_id', db.delphi_group, notnull=True),
        Field('name', notnull=True),
        Field('description', 'text'),
        Field('criteria', 'text', notnull=True),
        Field('active', 'boolean', default=True),
        Field('created_by', db.auth_user, writable=False, readable=False),
        Field('last_modification','datetime', default=request.now, writable=False),
        migrate=migrate)

    table.name.label = T('Problem Title')
    table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "delphi_problem.name")]
    table.created_by.default = auth.user.id if auth.user else 0
    table.group_id.label = T('Problem Group')
    table.group_id.requires = IS_IN_DB(db, 'delphi_group.id', '%(name)s')
    table.group_id.represent = lambda id: (id and [db(db.delphi_group.id == id).select(limitby=(0, 1)).first().name] or ["None"])[0]

    # CRUD Strings
    ADD_PROBLEM = T('Add Problem')
    LIST_PROBLEMS = T('List Problems')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_PROBLEM,
        title_display = T('Problem Details'),
        title_list = LIST_PROBLEMS,
        title_update = T('Edit Problem'),
        title_search = T('Search Problems'),
        subtitle_create = T('Add New Problem'),
        subtitle_list = T('Problems'),
        label_list_button = LIST_PROBLEMS,
        label_create_button = ADD_PROBLEM,
        msg_record_created = T('Problem added'),
        msg_record_modified = T('Problem updated'),
        msg_record_deleted = T('Problem deleted'),
        msg_list_empty = T('No Problems currently defined'))

    s3xrc.model.configure(table, list_fields=['id', 'group_id', 'name', 'created_by', 'last_modification'])

    def get_last_problem_id():
        last_problems = db(db.delphi_problem.id > 0).select(db.delphi_problem.id, orderby =~ db.delphi_problem.id, limitby = (0, 1))
        if last_problems:
            return last_problems[0].id

    ###########
    # Solutions
    ###########
    resource = 'solution'
    tablename = module + '_' + resource
    table = db.define_table(tablename,
        Field('problem_id', db.delphi_problem, notnull=True),
        Field('name'),
        Field('description', 'text'),
        Field('suggested_by', db.auth_user, writable=False, readable=False),
        Field('last_modification', 'datetime', default=request.now, writable=False),
        migrate=migrate)

    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T('Title')
    table.suggested_by.default = auth.user.id if auth.user else 0
    table.problem_id.label = T('Problem')
    table.problem_id.default = get_last_problem_id()
    table.problem_id.requires = IS_IN_DB(db, 'delphi_problem.id', '%(id)s: %(name)s')
    table.problem_id.represent = lambda id: (id and [db(db.delphi_problem.id == id).select(limitby=(0, 1)).first().name] or ["None"])[0]

    # CRUD Strings
    ADD_SOLUTION = T('Add Solution')
    LIST_SOLUTIONS = T('List Solutions')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SOLUTION,
        title_display = T('Solution Details'),
        title_list = LIST_SOLUTIONS,
        title_update = T('Edit Solution'),
        title_search = T('Search Solutions'),
        subtitle_create = T('Add New Solution'),
        subtitle_list = T('Solutions'),
        label_list_button = LIST_SOLUTIONS,
        label_create_button = ADD_SOLUTION,
        msg_record_created = T('Solution added'),
        msg_record_modified = T('Solution updated'),
        msg_record_deleted = T('Solution deleted'),
        msg_list_empty = T('No Solutions currently defined'))

    s3xrc.model.configure(table, list_fields=['id', 'problem_id', 'name', 'suggested_by', 'last_modification'])

    #######
    # Votes
    #######
    resource = 'vote'
    tablename = module + '_' + resource
    table = db.define_table(tablename,
        Field('problem_id', db.delphi_problem, notnull=True),
        Field('solution_id', db.delphi_solution, notnull=True),
        Field('rank', 'integer'),
        Field('user_id', db.auth_user, writable=False, readable=False),
        Field('last_modification','datetime', default=request.now, writable=False),
        migrate=migrate)

    table.problem_id.label = T("Problem")
    table.solution_id.label = T("Solution")
    table.user_id.label = T("User")
    table.user_id.default = auth.user.id if auth.user else 0

    #############
    # Forum Posts
    #############
    resource = 'forum_post'
    tablename = module + '_' + resource
    table = db.define_table(tablename,
        Field('solution_id', db.delphi_solution, notnull=True),
        Field('title'),
        Field('post', 'text', notnull=True),
        Field('post_html', 'text', default=""),
        Field('user_id', db.auth_user, writable=False, readable=False),
        Field('last_modification','datetime', default=request.now, writable=False),
        migrate=migrate)

    table.solution_id.label = T("Solution")
    table.user_id.label = T("User")
    table.user_id.default = auth.user.id if auth.user else 0
