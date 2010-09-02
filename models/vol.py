# -*- coding: utf-8 -*-

"""
    Volunteer Management System

    @author: zubair assad
    @author: nursix
"""

module = "vol"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = module + "_" + resource
    table = db.define_table(tablename,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)

    # -------------------------------------------------------------------------
    # pr_volunteer (Component of pr_person)
    #   describes a person's availability as a volunteer

    pr_volunteer_status_opts = {
    1: T("active"),
    2: T("retired")
    }

    resource = "volunteer"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp,
                    person_id,
                    # TODO: A person may volunteer for more than one org.
                    # Remove this -- the org can be inferred from the project
                    # or team in which the person participates.
                    organisation_id,
                    Field("date_avail_start", "date"),
                    Field("date_avail_end", "date"),
                    Field("hrs_avail_start", "time"),
                    Field("hrs_avail_end", "time"),
                    Field("status", "integer",
                        requires = IS_IN_SET(pr_volunteer_status_opts, zero=None),
                        # default = 1,
                        label = T("Status"),
                        represent = lambda opt: pr_volunteer_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("special_needs", "text"),
                    migrate=migrate)

    # Settings and Restrictions

    # Field labels
    table.date_avail_start.label = T("Available from")
    table.date_avail_end.label = T("Available until")
    table.hrs_avail_start.label = T("Working hours start")
    table.hrs_avail_end.label = T("Working hours end")
    table.special_needs.label = T("Special needs")

    # Representation function
    def shn_vol_volunteer_represent(id):
        person = db((db.vol_volunteer.id == id) & (db.pr_person.id == db.vol_volunteer.person_id)).select(
                    db.pr_person.first_name,
                    db.pr_person.middle_name,
                    db.pr_person.last_name,
                    limitby=(0, 1))
        if person:
            return vita.fullname(person.first())
        else:
            return None

    # CRUD Strings
    ADD_VOLUNTEER = Tstr("Add Volunteer Registration")
    VOLUNTEERS = T("Volunteer Registrations")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_VOLUNTEER,
        title_display = T("Volunteer Registration"),
        title_list = VOLUNTEERS,
        title_update = T("Edit Volunteer Registration"),
        title_search = T("Search Volunteer Registrations"),
        subtitle_create = ADD_VOLUNTEER,
        subtitle_list = VOLUNTEERS,
        label_list_button = T("List Registrations"),
        label_create_button = T("Add Volunteer Registration"),
        msg_record_created = T("Volunteer registration added"),
        msg_record_modified = T("Volunteer registration updated"),
        msg_record_deleted = T("Volunteer registration deleted"),
        msg_list_empty = T("No volunteer information registered"))

    # Reusable field
    vol_volunteer_id = db.Table(None, "vol_volunteer_id",
        FieldS3("vol_volunteer_id", db.vol_volunteer, sortby=["first_name", "middle_name", "last_name"],
        requires = IS_NULL_OR(IS_ONE_OF(db(db.vol_volunteer.status == 1), "vol_volunteer.id", shn_vol_volunteer_represent)),
        represent = lambda id: (id and [shn_vol_volunteer_represent(id)] or ["None"])[0],
        # TODO: Creating a vol_volunteer entry requires a person, so does this
        # make sense?  For now, turn this into add person.  Could add _next
        # to go edit form for vol components.  How would we get the new person id?
        comment = DIV(A(ADD_VOLUNTEER, _class="colorbox", _href=URL(r=request, c="pr", f="person", args="create", vars=dict(format="popup")), _target="top", _title=ADD_VOLUNTEER), DIV( _class="tooltip", _title=ADD_VOLUNTEER + "|" + Tstr("Add new person."))),
        ondelete = "RESTRICT",
        ))

    s3xrc.model.add_component(module, resource,
                              multiple=False,
                              joinby=dict(pr_person="person_id"),
                              deletable=True,
                              editable=True)

    s3xrc.model.configure(table,
                          list_fields=["organisation_id",
                                       "status"])

    # -------------------------------------------------------------------------
    # vol_resource (Component of pr_person)
    #   describes resources (e.g. vehicles, tools) of a volunteer

    # TODO: Skills are now separate.  Either repurpose "resources" or remove it.
    vol_resource_type_opts = {
        2:T("Resources"),
        3:T("Restrictions"),
        99:T("Other")
    }

    vol_resource_subject_opts = {
        1:T("Animals"),
        2:T("Automotive"),
        3:T("Baby And Child Care"),
        4:T("Tree"),
        5:T("Warehouse"),
        99:T("Other")
    }

    vol_resource_deployment_opts = {
        1:T("Building Aide"),
        2:T("Vehicle"),
        3:T("Warehouse"),
        99:T("Other")
    }

    vol_resource_status_opts = {
        1:T("approved"),
        2:T("unapproved"),
        3:T("denied")
    }

    resource = "resource"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp,
                    person_id,
                    Field("type", "integer",
                        requires = IS_IN_SET(vol_resource_type_opts, zero=None),
                        # default = 99,
                        label = T("Resource"),
                        represent = lambda opt: vol_resource_type_opts.get(opt, UNKNOWN_OPT)),
                    Field("subject", "integer",
                        requires = IS_IN_SET(vol_resource_subject_opts, zero=None),
                        # default = 99,
                        label = T("Subject"),
                        represent = lambda opt: vol_resource_subject_opts.get(opt, UNKNOWN_OPT)),
                    Field("deployment", "integer",
                        requires = IS_IN_SET(vol_resource_deployment_opts, zero=None),
                        # default = 99,
                        label = T("Deployment"),
                        represent = lambda opt: vol_resource_deployment_opts.get(opt, UNKNOWN_OPT)),
                    Field("status", "integer",
                        requires = IS_IN_SET(vol_resource_status_opts, zero=None),
                        # default = 2,
                        label = T("Status"),
                        represent = lambda opt: vol_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    migrate=migrate)

    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(pr_person="person_id"),
                              deletable=True,
                              editable=True)

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "type",
                                       "subject",
                                       "deployment",
                                       "status"])

    # CRUD Strings
    ADD_RESOURCE = T("Add Resource")
    RESOURCES = T("Resources")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_RESOURCE,
        title_display = T("Resource Details"),
        title_list = RESOURCES,
        title_update = T("Edit Resource"),
        title_search = T("Search Resources"),
        subtitle_create = T("Add New Resource"),
        subtitle_list = RESOURCES,
        label_list_button = T("List Resources"),
        label_create_button = ADD_RESOURCE,
        msg_record_created = T("Resource added"),
        msg_record_modified = T("Resource updated"),
        msg_record_deleted = T("Resource deleted"),
        msg_list_empty = T("No resources currently registered"))

    # TODO: Rather than the hours a volunteer "has a position" this will likely
    # become hours the volunteer "works on a task", so vol_postion_id will
    # switch to the task id.
    # -------------------------------------------------------------------------
    # vol_hours:
    #   documents the hours a volunteer has a position
    #
    #resource = "hours"
    #table = module + "_" + resource
    #db.define_table(table,
    #                person_id,
    #                vol_position_id,
    #                Field("shift_start", "datetime", label=T("shift_start"), notnull=True),
    #                Field("shift_end", "datetime", label=T("shift_end"), notnull=True),
    #                migrate=migrate)

    #db[table].shift_start.requires=[IS_NOT_EMPTY(),
    #                                      IS_DATETIME]
    #db[table].shift_end.requires=[IS_NOT_EMPTY(),
    #                                      IS_DATETIME]

    # TODO: Remove?
    # -----------------------------------------------------------------------------
    # courier
    #resource = "courier"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #db.define_table("vol_courier", timestamp, uuidstamp,
    #    Field("message_id", "integer", label=T("message_id"), notnull=True),
    #    Field("to_id", "string", label=T("to_id"), notnull=True),
    #    Field("from_id", "string", label=T("from_id"), notnull=True),
    #    migrate=migrate)

    #db[table].message_id.requires = IS_NOT_EMPTY()
    #db[table].to_id.requires = IS_NOT_EMPTY()
    #db[table].from_id.requires = IS_NOT_EMPTY()
    #db[table].message_id.requires = IS_NOT_NULL()

    # TODO: Which of these are requests for access or granted access,
    # associated with a particular volunteer, and which represent types of
    # access or types of requests?  Anything tied to a particular volunteer
    # should be a component of pr.
    # -----------------------------------------------------------------------------
    # vol_access_request
    #resource = "access_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", "integer", notnull=True),
    #    Field("act", "string", length=100, label=T("act")),
    #    Field("vm_action", "string", length=100, label=T("vm_action")),
    #    Field("description", "string", length=300, label=T("description")),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_constraint
    #resource = "access_constraint"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("constraint_id","string", length=30, notnull=True, default=" ", label=T("constraint_id")),
    #    Field("description","string", length=200,label=T("description")),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_constraint_to_request
    #resource = "access_constraint_to_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", db.vol_access_request),
    #    Field("constraint_id", db.vol_access_constraint),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_classification_to_request
    #resource = "access_classification_to_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", "integer", length=11, notnull=True, default=0),
    #    Field("table_name", "string", length=200, notnull=True, default=" ", label=T("table_name")),
    #    Field("crud", "string", length=4, notnull=True, default=" ", label=T("crud")),
    #    migrate=migrate)

    # TODO: Is this in use?  Have project location fields changed, since a
    # project could have multiple locations?
    # -------------------------------------------------------------------------
    # shn_org_project_search_location:
    #   form function to search projects by location
    #
    def shn_org_project_search_location(xrequest, **attr):

        if attr is None:
            attr = {}

        if not shn_has_permission("read", db.org_project):
            session.error = UNAUTHORISED
            redirect(URL(r=request, c="default", f="user", args="login", vars={"_next":URL(r=request, args="search_location", vars=request.vars)}))

        if xrequest.representation=="html":
            # Check for redirection
            if request.vars._next:
                next = str.lower(request.vars._next)
            else:
                next = str.lower(URL(r=request, c="org", f="project", args="[id]"))

            # Custom view
            response.view = "%s/project_search.html" % xrequest.prefix

            # Title and subtitle
            title = T("Search for a Project")
            subtitle = T("Matching Records")

            # Select form:
            l_opts = [OPTION(_value="")]
            l_opts += [OPTION(location.name, _value=location.id)
                    for location in db(db.gis_location.deleted == False).select(db.gis_location.ALL, cache=(cache.ram, 3600))]
            form = FORM(TABLE(
                    TR(T("Location: "),
                    SELECT(_name="location", *l_opts, **dict(name="location", requires=IS_NULL_OR(IS_IN_DB(db, "gis_location.id"))))),
                    TR("", INPUT(_type="submit", _value="Search"))
                    ))

            output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

            # Accept action
            items = None
            if form.accepts(request.vars, session):

                table = db.org_project
                query = (table.deleted == False)

                if form.vars.location is None:
                    results = db(query).select(table.ALL)
                else:
                    query = query & (table.location_id == form.vars.location)
                    results = db(query).select(table.ALL)

                if results and len(results):
                    records = []
                    for result in results:
                        href = next.replace("%5bid%5d", "%s" % result.id)
                        records.append(TR(
                            A(result.name, _href=href),
                            result.start_date or "None",
                            result.end_date or "None",
                            result.description or "None",
                            result.status and org_project_status_opts[result.status] or "unknown",
                            ))
                    items=DIV(TABLE(THEAD(TR(
                        TH("Name"),
                        TH("Start date"),
                        TH("End date"),
                        TH("Description"),
                        TH("Status"))),
                        TBODY(records), _id="list", _class="display"))
                else:
                        items = T("None")

            try:
                label_create_button = s3.crud_strings["org_project"].label_create_button
            except:
                label_create_button = s3.crud_strings.label_create_button

            add_btn = A(label_create_button, _href=URL(r=request, c="org", f="project", args="create"), _class="action-btn")

            output.update(dict(items=items, add_btn=add_btn))

            return output

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Plug into REST controller
    s3xrc.model.set_method(module, "project", method="search_location", action=shn_org_project_search_location )


    # -------------------------------------------------------------------------
    # vol_skill_types
    #   Customize to add more client defined Skill
    #

    resource = "skill_types"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
            Field("name",  length=128,notnull=True),
            Field("category", "string", length=50),
            Field("description"),
            migrate=migrate)

    # Field settings
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
    table.name.label = T("Name")
    table.name.comment = SPAN("*", _class="req")

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Skill Type"),
        title_display = T("Skill Type Details"),
        title_list = T("Skill Types"),
        title_update = T("Edit Skill Type"),
        title_search = T("Search Skill Types"),
        subtitle_create = T("Add New Skill Type"),
        subtitle_list = T("Skill Types"),
        label_list_button = T("List Skill Types"),
        label_create_button = T("Add Skill Types"),
        label_delete_button = T("Delete Skill Type"),
        msg_record_created = T("Skill Type added"),
        msg_record_modified = T("Skill Type updated"),
        msg_record_deleted = T("Skill Type deleted"),
        msg_list_empty = T("No Skill Types currently set"))

    # Representation function
    def vol_skill_types_represent(id):
        if id:
            record = db(db.vol_skill_types.id == id).select().first()
            category = record.category
            name = record.name
            if category:
                return "%s: %s" % (category, name)
            else:
                return name
        else:
            return None

    skill_types_id = db.Table(None, "skill_types_id",
                              FieldS3("skill_types_id", db.vol_skill_types,
                                      sortby = ["category", "name"],
                                      requires = IS_ONE_OF(db, "vol_skill_types.id", vol_skill_types_represent),
                                      represent = vol_skill_types_represent,
                                      label = T("Skill"),
                                      ondelete = "RESTRICT"))


    # -------------------------------------------------------------------------
    # vol_skill
    #   A volunteer's skills (component of pr)
    #

    resource = "skill"
    tablename = module + "_" + resource
    table = db.define_table(
        tablename, timestamp, uuidstamp, deletion_status,
        person_id, skill_types_id,
        Field("status",
              requires=IS_IN_SET(["approved","unapproved","denied"]),
              label=T("Status"),
              notnull=True,
              default="unapproved"),
        migrate=migrate)

    s3xrc.model.add_component(module, resource,
        multiple=True,
        joinby=dict(pr_person="person_id"),
        deletable=True,
        editable=True)

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "skill_types_id",
                                       "status"])

    # CRUD Strings
    ADD_SKILL = T("Add Skill")
    SKILL = T("Skill")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SKILL,
        title_display = T("Skill Details"),
        title_list = SKILL,
        title_update = T("Edit Skill"),
        title_search = T("Search Skills"),
        subtitle_create = T("Add New Skill"),
        subtitle_list = SKILL,
        label_list_button = T("List Skills"),
        label_create_button = ADD_SKILL,
        label_delete_button = T("Delete Skill"),
        msg_record_created = T("Skill added"),
        msg_record_modified = T("Skill updated"),
        msg_record_deleted = T("Skill deleted"),
        msg_list_empty = T("No skills currently set"))

    # shn_pr_group_represent -------------------------------------------------
    #
    def teamname(record):
        """
            Returns the Team Name
        """

        tname = ""
        if record and record.name:
            tname = "%s " % record.name.strip()
        return tname

    def shn_pr_group_represent(id):

        def _represent(id):
            table = db.pr_group
            group = db(table.id == id).select(table.name)
            if group:
                return teamname(group[0])
            else:
                return None

        name = cache.ram("pr_group_%s" % id, lambda: _represent(id))
        return name
