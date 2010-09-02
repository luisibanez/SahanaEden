# -*- coding: utf-8 -*-

"""
    Organisation Registry - Controllers

    @author: Fran Boon
    @author: Michael Howden
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions" Views)
response.menu_options = org_menu

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

def sector():
    """
        RESTful CRUD controller
        @ToDo: Rename as Cluster? (Too UN/INGO-focussed?)
    """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # CRUD strings
    LIST_SECTORS = T("List Clusters")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SECTOR,
        title_display = T("Cluster Details"),
        title_list = LIST_SECTORS,
        title_update = T("Edit Cluster"),
        title_search = T("Search Clusters"),
        subtitle_create = T("Add New Cluster"),
        subtitle_list = T("Clusters"),
        label_list_button = LIST_SECTORS,
        label_create_button = ADD_SECTOR,
        msg_record_created = T("Cluster added"),
        msg_record_modified = T("Cluster updated"),
        msg_record_deleted = T("Cluster deleted"),
        msg_list_empty = T("No Clusters currently registered"))
    
    return shn_rest_controller(module, resource, listadd=False)

def organisation():
    """ RESTful CRUD controller """

    resource = request.function

    def org_prep(jr):
        if jr.representation == "html":
            # Redirect to Dashboard after adding/editing an Organisation to add Offices/Staff/Projects
            crud.settings.create_next = URL(r=request, f="dashboard")
            crud.settings.update_next = URL(r=request, f="dashboard")
        return True
    # Dashboard is deprecated now we have components
    #response.s3.prep = org_prep

    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    rheader = lambda r: shn_org_rheader(r,
                                        tabs = [(T("Basic Details"), None),
                                                (T("Offices"), "office"),
                                                (T("Staff"), "staff"),
                                                (T("Activities"), "activity"),
                                                #(T("Projects"), "project"),
                                                #(T("Tasks"), "task"),
                                                #(T("Donors"), "organisation"),
                                                #(T("Sites"), "site"),  # Ticket 195
                                               ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 listadd=False,
                                 rheader=rheader)

    return output

def office():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    if isinstance(request.vars.organisation_id, list):
        request.vars.organisation_id = request.vars.organisation_id[0]

    # Pre-processor
    def prep(jr):
        # No point in downloading large dropdowns which we hide, so provide a smaller represent
        # the update forms are not ready. when they will - uncomment this and comment the next one
        #if jr.method in ("create", "update"):
        if jr.method == "create":
            table.organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_organisation.id"))
            if request.vars.organisation_id and request.vars.organisation_id != "None":
                session.s3.organisation_id = request.vars.organisation_id
                # Organisation name should be displayed on the form if organisation_id is pre-selected
                session.s3.organisation_name = db(db.org_organisation.id == int(session.s3.organisation_id)).select(db.org_organisation.name).first().name
        return True
    response.s3.prep = prep
    
    # Post-processor
    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    rheader = lambda r: shn_org_rheader(r,
                                        tabs = [(T("Basic Details"), None),
                                                (T("Contact Data"), "pe_contact"),
                                                (T("Staff"), "staff"),
                                               ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 listadd=False,
                                 rheader=rheader)

    return output


def staff():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # Pre-processor
    def prep(jr):
        # No point in downloading large dropdowns which we hide, so provide a smaller represent
        # the update forms are not ready. when they will - uncomment this and comment the next one
        #if jr.method in ("create", "update"):
        if jr.method == "create":
            # person_id mandatory for a staff!
            table.person_id.requires = IS_ONE_OF_EMPTY(db, "pr_person.id")
            table.organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_organisation.id"))
            table.office_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_office.id"))
        return True
    response.s3.prep = prep

    # Post-processor
    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False)
    
    return output

def donor():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # Post-processor
    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False)
    
    return output

# Component Resources need these settings to be visible where they are linked from
# - so we put them outside their controller function
tablename = "%s_%s" % (module, "donor")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_DONOR,
    title_display = T("Donor Details"),
    title_list = T("Donors Report"),
    title_update = T("Edit Donor"),
    title_search = T("Search Donors"),
    subtitle_create = T("Add New Donor"),
    subtitle_list = T("Donors"),
    label_list_button = T("List Donors"),
    label_create_button = ADD_DONOR,
    label_delete_button = T("Delete Donor"),
    msg_record_created = T("Donor added"),
    msg_record_modified = T("Donor updated"),
    msg_record_deleted = T("Donor deleted"),
    msg_list_empty = T("No Donors currently registered"))

def project():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    db.org_staff.person_id.comment[1] = DIV(DIV(_class="tooltip",
                              _title=Tstr("Person") + "|" + Tstr("Select the person assigned to this role for this project.")))

    # Post-processor
    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    rheader = lambda r: shn_project_rheader(r,
                                            tabs = [(T("Basic Details"), None),
                                                    (T("Staff"), "staff"),
                                                    (T("Tasks"), "task"),
                                                    #(T("Donors"), "organisation"),
                                                    #(T("Sites"), "site"),  # Ticket 195
                                                   ])
                                           
    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 listadd=False,
                                 main="code",
                                 rheader=rheader
                                )
    
    return output

def task():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # Post-processor
    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp
    
    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 listadd=False
                                )
    
    return output

def office_table_linkto(field):
    return URL(r=request, f = "office",  args=[field, "read"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
def office_table_linkto_update(field):
    return URL(r=request, f = "office", args=[field, "update"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def staff_table_linkto(field):
    return URL(r=request, f = "staff",  args=[field, "read"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
def staff_table_linkto_update(field):
    return URL(r=request, f = "staff", args=[field, "update"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def project_table_linkto(field):
    return URL(r=request, f = "project",  args=[field, "read"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
def project_table_linkto_update(field):
    return URL(r=request, f = "project", args=[field, "update"],
                vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

def org_sub_list(tablename, org_id):
    fields = []
    headers = {}
    table = db[tablename]
    
    for field in table:
        if field.readable and field.name <> "organisation_id" and field.name <> "admin":
            headers[str(field)] = str(field.label)
            fields.append(field)

    table_linkto_update = dict( \
        org_office = office_table_linkto_update,
        org_staff =  staff_table_linkto_update,
        org_project = project_table_linkto_update,
    )

    table_linkto = dict( \
        org_office = office_table_linkto,
        org_staff = staff_table_linkto,
        org_project = project_table_linkto,
    )

    authorised = shn_has_permission("update", tablename)
    if authorised:
        linkto = table_linkto_update[tablename]
    else:
        linkto = table_linkto[tablename]

    query = (table.organisation_id == org_id)

    list =  crud.select(table, query = table.organisation_id == org_id, fields = fields, headers = headers, linkto = linkto, truncate=48, _id = tablename + "_list", _class="display")

    # Required so that there is a table with an ID for the refresh after add
    if list == None:
        list = TABLE("None", _id = tablename + "_list")

    return list

def dashboard():
    " Deprecated function which was used before we had Component Tabs "

    INVALID_ORGANIZATION = T("Invalid Organization ID!")
    # Get Organization to display from Arg, Var, Session or Default
    if len(request.args) > 0:
        org_id = int(request.args[0])
        try:
            org_name = db(db.org_organisation.id == org_id).select(db.org_organisation.name, limitby=(0, 1)).first().name
        except:
            session.error = INVALID_ORGANIZATION
            redirect(URL(r=request, c="org", f="index"))
    elif "name" in request.vars:
        org_name = request.vars["name"]
        try:
            org_id = db(db.org_organisation.name == org_name).select(db.org_organisation.id, limitby=(0, 1)).first().id
        except:
            session.error = INVALID_ORGANIZATION
            redirect(URL(r=request, c="org", f="index"))
    else:
        table = db.org_organisation
        deleted  = ((table.deleted == False) | (table.deleted == None))
        org_id = s3xrc.get_session(session, "org", "organisation") or 0
        if org_id:
            query = (table.id == org_id) & deleted
        else:
            query = (table.id > 0) & deleted
        try:
            org_name = db(query).select(table.name, limitby=(0, 1)).first().name
        except:
            session.warning = T("No Organizations registered!")
            redirect(URL(r=request, c="org", f="index"))

    o_opts = []
    first_option = True;
    # if we keep the dropdown - it should be in alphabetic order
    # that way the user will find things easier
    for organisation in db(db.org_organisation.deleted == False).select(db.org_organisation.ALL, orderby = db.org_organisation.name):
        if (org_id == 0 and first_option) or organisation.id == org_id:
            first_option = False
            if org_id == 0:
                org_id = organisation.id
            o_opts += [OPTION(organisation.name, _value=organisation.id, _selected="")]
        else:
            o_opts += [OPTION(organisation.name, _value=organisation.id)]

    organisation_select = SELECT(_name="org", *o_opts, **dict(name="org", requires=IS_NULL_OR(IS_IN_DB(db, "org_organisation.id")), _id = "organisation_select"))

    org_details = crud.read("org_organisation", org_id)

    office_list = org_sub_list("org_office", org_id)
    staff_list = org_sub_list("org_staff", org_id)
    project_list = org_sub_list("org_project", org_id)

    but_add_org = A(ADD_ORGANIZATION,
                        _class="colorbox",
                        _href=URL(r=request,
                            c="org", f="organisation", args="create",
                            vars=dict(format="popup", KeepThis="true")) + "&TB_iframe=true&mode=new",
                            _target="top", _title=ADD_ORGANIZATION)

    but_edit_org = A(T("Edit Organization"),
                        _href=URL(r=request,
                            c="org", f="organisation", args=[org_id, "update"]))

    but_add_office = A(ADD_OFFICE,
                        _class="colorbox",
                        _href=URL(r=request,
                            c="org", f="office", args="create",
                            vars=dict(format="popup", KeepThis="true")) + "&TB_iframe=true&mode=new",
                            _target="top", _title=ADD_OFFICE)

    but_add_staff = A(ADD_STAFF,
                        _class="colorbox",
                        _href=URL(r=request,
                            c="org", f="staff", args="create",
                            vars=dict(format="popup", KeepThis="true")) + "&TB_iframe=true&mode=new",
                            _target="top", _title=ADD_STAFF)

    but_add_project = A(ADD_PROJECT,
                        _class="colorbox",
                        _href=URL(r=request,
                            c="org", f="project", args="create",
                            vars=dict(format="popup", KeepThis="true")) + "&TB_iframe=true&mode=new",
                            _target="top", _title=ADD_PROJECT)

    session.s3.organisation_id = org_id

    return dict(organisation_id=org_id, organisation_select=organisation_select, org_details=org_details, office_list=office_list, staff_list=staff_list, project_list=project_list, but_add_org=but_add_org, but_edit_org=but_edit_org, but_add_office=but_add_office, but_add_staff=but_add_staff, but_add_project=but_add_project)

def shn_org_rheader(r, tabs=[]):
    " Organisation Registry page headers "

    if r.representation == "html":
        
        rheader_tabs = shn_rheader_tabs(r, tabs)
        
        if r.name == "organisation":
        
            #_next = r.here()
            #_same = r.same()

            organisation = r.record

            if organisation.sector_id:
                sectors = re.split("\|", organisation.sector_id)[1:-1]
                _sectors = TABLE()
                for sector in sectors:
                    _sectors.append(TR(db(db.org_sector.id == sector).select(db.org_sector.name, limitby=(0, 1)).first().name))
            else:
                _sectors = None

            try:
                _type = org_organisation_type_opts[organisation.type]
            except KeyError:
                _type = None
            
            rheader = DIV(TABLE(
                TR(
                    TH(T("Organization: ")),
                    organisation.name,
                    TH(T("Sector(s): ")),
                    _sectors
                    ),
                TR(
                    #TH(A(T("Edit Organization"),
                    #    _href=URL(r=request, c="org", f="organisation", args=[r.id, "update"], vars={"_next": _next})))
                    TH(T("Type: ")),
                    _type,
                    )
            ), rheader_tabs)

            return rheader

        elif r.name == "office":
        
            #_next = r.here()
            #_same = r.same()

            office = r.record
            organisation = db(db.org_organisation.id == office.organisation_id).select(db.org_organisation.name, limitby=(0, 1)).first()
            if organisation:
                org_name = organisation.name
            else:
                org_name = None

            rheader = DIV(TABLE(
                    TR(
                        TH(T("Name: ")),
                        office.name,
                        TH(T("Type: ")),
                        org_office_type_opts.get(office.type, UNKNOWN_OPT),
                        ),
                    TR(
                        TH(T("Organization: ")),
                        org_name,
                        TH(T("Location: ")),
                        shn_gis_location_represent(office.location_id),
                        ),
                    TR(
                        #TH(A(T("Edit Office"),
                        #    _href=URL(r=request, c="org", f="office", args=[r.id, "update"], vars={"_next": _next})))
                        )
                ), rheader_tabs)

            return rheader

    return None
