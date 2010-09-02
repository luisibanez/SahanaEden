# -*- coding: utf-8 -*-

"""
    Volunteer Management System
"""

from gluon.sql import Rows

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions)
def shn_menu():
    menu = [
        [T("Projects"), False, URL(r=request, f="project"),[
            [T("Search"), False, URL(r=request, f="project", args="search_location")],
            [T("Add Project"), False, URL(r=request, f="project", args="create")],
        ]],
    ]
    if session.rcvars and "org_project" in session.rcvars:
        project_id = session.rcvars["org_project"]
        selection = db.org_project[project_id]
        if selection:
            menu_project = [
                    ["%s %s" % (T("Project:"), selection.code), False, URL(r=request, f="project", args=[project_id]),[
                        [T("Tasks"), False, URL(r=request, f="project", args=[project_id, "task"])],
                        [T("Staff"), False, URL(r=request, f="project", args=[project_id, "staff"])],
                    ]]
            ]
            menu.extend(menu_project)

    menu_teams = [
        [T("Teams"), False, URL(r=request, f="group"),[
            [T("List"), False, URL(r=request, f="group")],
            [T("Add"), False, URL(r=request, f="group", args="create")],
        ]]
    ]
    menu.extend(menu_teams)
    if session.rcvars and "pr_group" in session.rcvars:
        group_id = session.rcvars["pr_group"]
        selection = db.pr_group[group_id]
        if selection:
            team_name = shn_pr_group_represent(group_id)
            menu_teams = [
                ["%s %s" % (T("Team:"), team_name), False, URL(r=request, f="group", args=[group_id, "read"]),[
                    [T("View On Map"), False, URL(r=request, f="view_team_map", args=[group_id])],
                    [T("Send Mail"), False, URL(r=request, f="compose_group", vars={"group_id":group_id})],
                ]],
            ]
            menu.extend(menu_teams)

    menu_persons = [
        [T("Persons"), False, URL(r=request, f="person", args=["search_simple"]),[
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
        ]]
    ]
    menu.extend(menu_persons)
    if session.rcvars and "pr_person" in session.rcvars:
        person_id = session.rcvars["pr_person"]
        selection = db.pr_person[person_id]
        if selection:
            person_name = shn_pr_person_represent(person_id)
            # ?vol_tabs=person and ?vol_tabs=volunteer are used by the person
            # controller to select which set of tabs to display.
            menu_person = [
                ["%s %s" % (T("Person:"), person_name), False, URL(r=request, f="person", args=[person_id, "read"]),[
                    # The arg "volunteer" causes this to display the
                    # vol_volunteer tab initially.
                    [T("Volunteer Data"), False, URL(r=request, f="person", args=[person_id, "volunteer"], vars={"vol_tabs":"volunteer"})],
                    # The default tab is pr_person, which is fine here.
                    [T("Person Data"), False, URL(r=request, f="person", args=[person_id], vars={"vol_tabs":"person"})],
                    [T("View On Map"), False, URL(r=request, f="view_map", args=[person_id])],
                    [T("Send Mail"), False, URL(r=request, f="compose_person", vars={"person_id":person_id})],
                ]],
            ]
            menu.extend(menu_person)
    menu_skills = [
        [T("Skill Types"), False, URL(r=request, f="skill_types")],
    ]
    menu.extend(menu_skills)
    if auth.user is not None:
        menu_user = [
            [T("My Tasks"), False, URL(r=request, f="task", args="")],
        ]
        menu.extend(menu_user)
    response.menu_options = menu

shn_menu()


def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
def person():

    """
    This controller produces either generic person component tabs or
    volunteer-specific person component tabs, depending on whether "vol_tabs"
    in the URL's vars is "person" or "volunteer".
    """

    response.s3.pagination = True

    def person_postp(jr, output):
        if jr.representation in ("html", "popup"):
            if not jr.component:
                label = READ
            else:
                label = UPDATE
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        return output
    response.s3.postp = person_postp

    tab_set = "person"
    if "vol_tabs" in request.vars:
        tab_set = request.vars["vol_tabs"]
    if tab_set == "person":
        db.pr_person.missing.default = False
        tabs = [(T("Basic Details"), None),
                (T("Images"), "image"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "pe_contact"),
                (T("Presence Log"), "presence")]
    else:
        # TODO: These files are for the multiselect widget used for skills.
        # Check if we still need them if we switch to a different widget.
        response.files.append(URL(r=request,c='static/scripts/S3',f='jquery.multiSelect.js'))
        response.files.append(URL(r=request,c='static/styles/S3',f='jquery.multiSelect.css'))
        db.pr_group_membership.group_id.label = T("Team Id")
        db.pr_group_membership.group_head.label = T("Team Head")
        s3xrc.model.configure(db.pr_group_membership,
                              list_fields=["id",
                                           "group_id",
                                           "group_head",
                                           "description"])
        # TODO: If we don't know what a "status report" is supposed to be,
        # take it out.  Take out resources til they're modernized.
        tabs = [
                #(T("Status Report"), None),
                (T("Availablity"), "volunteer"),
                (T("Teams"), "group_membership"),
                (T("Skills"), "skill"),
                #(T("Resources"), "resource"),
               ]

    resource = request.function
    output = shn_rest_controller("pr", resource,
        main="first_name",
        extra="last_name",
        rheader=lambda r: shn_pr_rheader(r, tabs),
        listadd=False)

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def project():
    "Project controller"

    resource = request.function

    def org_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = org_postp

    # ServerSidePagination
    response.s3.pagination = True

    tabs = [
            (T("Basic Details"), None),
            (T("Staff"), "staff"),
            (T("Tasks"), "task"),
            #(T("Donors"), "organisation"),
            #(T("Sites"), "site"),  # Ticket 195
           ]

    rheader = lambda r: shn_project_rheader(r, tabs)

    output = shn_rest_controller("org", resource,
                                 listadd=False,
                                 main="code",
                                 rheader=rheader)

    return output


# -----------------------------------------------------------------------------
def task():
    """ Manage current user's tasks """

    resource = request.function
    tablename = "org_%s" % (resource)
    table = db[tablename]

    my_person_id = None

    if auth.user is not None and auth.user.person_uuid:
        my_person_id = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.id, limitby=(0,1)).first()

    if not my_person_id:
        session.error = T("No person record found for current user.")
        redirect(URL(r=request, f="index"))

    table.person_id.default = my_person_id
    #table.person_id.writable = False

    response.s3.filter = (db.org_task.person_id == my_person_id)

    s3.crud_strings[tablename].title_list = T("My Tasks")
    s3.crud_strings[tablename].subtitle_list = T("Task List")

    response.s3.pagination = True

    return shn_rest_controller("org", resource, listadd=False)


# -----------------------------------------------------------------------------
def skill_types():
    "Allow user to define new skill types."
    return shn_rest_controller(module, "skill_types")


# -----------------------------------------------------------------------------
def view_map():
    """
    Map Location of Volunteer.
    Use most recent presence if available, else any address that's available.
    """

    person_id = request.args(0)

    presence_query = (db.pr_person.id == person_id) & (db.pr_presence.pe_id == db.pr_person.pe_id) & (db.gis_location.id == db.pr_presence.location_id)

    # Need sql.Rows object for show_map, so don't extract individual row.
    location = db(presence_query).select(db.gis_location.ALL, orderby=~db.pr_presence.datetime, limitby=(0, 1))

    if not location:
        address_query = (db.pr_person.id == person_id) & (db.pr_address.pe_id == db.pr_person.pe_id) & (db.gis_location.id == db.pr_address.location_id)
        # TODO: If there are multiple addresses, which should we choose?
        # For now, take whichever address is supplied first.
        location = db(address_query).select(db.gis_location.ALL, limitby=(0, 1))

    if location:
        # Center and zoom the map.
        location_row = location.first()  # location is a sql.Rows
        lat = location_row.lat
        lon = location_row.lon
        bounds = gis.get_bounds(features=location)

        volunteer = {"feature_group" : "People"}
        html = gis.show_map(
            feature_queries = [{"name" : "Volunteer", "query" : location, "active" : True, "marker" : db(db.gis_marker.name == "volunteer").select().first().id}],
            feature_groups = [volunteer],
            wms_browser = {"name" : "Risk Maps", "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
            catalogue_overlays = True,
            catalogue_toolbar = True,
            toolbar = True,
            search = True,
            lat = lat,
            lon = lon,
            bbox = bounds,
            window = True,
        )
        return dict(map=html)

    # TODO: What is an appropriate response if no location is available?
    return None


# -----------------------------------------------------------------------------
def group():

    """
    Team controller -- teams use the group table from pr.
    """

    tablename = "pr_group"
    table = db[tablename]

    table.group_type.label = T("Team Type")
    table.description.label = T("Team Description")
    table.name.label = T("Team Name")
    db.pr_group_membership.group_id.label = T("Team Id")
    db.pr_group_membership.group_head.label = T("Team Head")

    # CRUD Strings
    ADD_TEAM = T("Add Team")
    LIST_TEAMS = T("List Teams")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TEAM,
        title_display = T("Team Details"),
        title_list = LIST_TEAMS,
        title_update = T("Edit Team"),
        title_search = T("Search Teams"),
        subtitle_create = T("Add New Team"),
        subtitle_list = T("Teams"),
        label_list_button = LIST_TEAMS,
        label_create_button = ADD_TEAM,
        label_search_button = T("Search Teams"),
        msg_record_created = T("Team added"),
        msg_record_modified = T("Team updated"),
        msg_record_deleted = T("Team deleted"),
        msg_list_empty = T("No Items currently registered"))

    s3.crud_strings["pr_group_membership"] = Storage(
        title_create = T("Add Member"),
        title_display = T("Membership Details"),
        title_list = T("Team Members"),
        title_update = T("Edit Membership"),
        title_search = T("Search Member"),
        subtitle_create = T("Add New Member"),
        subtitle_list = T("Current Team Members"),
        label_list_button = T("List Members"),
        label_create_button = T("Add Group Member"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Team Member added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Members currently registered"))

    response.s3.filter = (db.pr_group.system == False) # do not show system groups
    response.s3.pagination = True

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "person_id",
                                       "group_head",
                                       "description"])

    def group_postp(jr, output):
        if jr.representation in ("html", "popup"):
            if not jr.component:
                label = READ
            else:
                label = UPDATE
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        return output
    response.s3.postp = group_postp

    output = shn_rest_controller("pr", "group",
                                 main="name",
                                 extra="description",
                                 rheader=lambda jr: shn_pr_rheader(jr,
                                        tabs = [(T("Team Details"), None),
                                                (T("Address"), "address"),
                                                (T("Contact Data"), "pe_contact"),
                                                (T("Members"), "group_membership")]),
                                 listadd=False,
                                 deletable=False)

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def skill():
    "Select skills a volunteer has."
    return shn_rest_controller(module, "skill")


# -----------------------------------------------------------------------------
def view_team_map():
    """
    Map Location of Volunteer in a Team.
    Use most recent presence if available, else any address that's available.
    """

    group_id = request.args(0)

    members_query = (db.pr_group_membership.group_id == group_id)
    members = db(members_query).select(db.pr_group_membership.person_id) #members of a team aka group
    member_person_ids = [ x.person_id for x in members ] #list of members

    #Presence Data of the members with Presence Logs
    presence_rows = db(db.pr_person.id.belongs(member_person_ids) & (db.pr_presence.pe_id == db.pr_person.pe_id) & (db.gis_location.id ==  db.pr_presence.location_id)).select(db.gis_location.ALL, db.pr_person.id, orderby=~db.pr_presence.datetime)
    #Get Latest Presence Data
    person_location_sort = presence_rows.sort(lambda row:row.pr_person.id)
    previous_person_id = None
    locations_list = []
    for row in person_location_sort:
        if row.pr_person.id != previous_person_id:
            locations_list.append(row["gis_location"])
            member_person_ids.remove(row.pr_person.id)
            previous_person_id = row.pr_person.id

    #Address of those members without Presence data
    address = db(db.pr_person.id.belongs(member_person_ids) & (db.pr_address.pe_id == db.pr_person.pe_id) & (db.gis_location.id ==  db.pr_address.location_id)).select(db.gis_location.ALL)

    locations_list.extend(address)

    if locations_list:

        bounds = gis.get_bounds(features=locations_list)

        volunteer = {"feature_group" : "People"}
        html = gis.show_map(
            feature_queries = [{"name" : "Volunteer", "query" : locations_list, "active" : True, "marker" : db(db.gis_marker.name == "volunteer").select().first().id}],
            feature_groups = [volunteer],
            wms_browser = {"name" : "Risk Maps", "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
            catalogue_overlays = True,
            catalogue_toolbar = True,
            toolbar = True,
            search = True,
            bbox = bounds,
            window = True,
        )
        return dict(map=html)

    # TODO: What is an appropriate response if no location is available?
    return None


# -----------------------------------------------------------------------------
def compose_person():
    "Send message to volunteer"

    person_pe_id_query = (db.pr_person.id == request.vars.person_id)
    pe_id_row = db(person_pe_id_query).select(db.pr_person.pe_id).first()
    request.vars.pe_id = pe_id_row["pe_id"]

    return shn_msg_compose( redirect_module=module,
                            redirect_function="compose_person",
                            redirect_vars={"person_id":request.vars.person_id},
                            title_name="Send a message to a volunteer" )


# -----------------------------------------------------------------------------
def compose_group():
    "Send message to members of a team"

    group_pe_id_query = (db.pr_group.id == request.vars.group_id)
    pe_id_row = db(group_pe_id_query).select(db.pr_group.pe_id).first()
    request.vars.pe_id = pe_id_row["pe_id"]

    return shn_msg_compose( redirect_module=module,
                            redirect_function="compose_group",
                            redirect_vars={"group_id":request.vars.group_id},
                            title_name="Send a message to a team of volunteers" )


# -----------------------------------------------------------------------------
# TODO: Is resource a bad name, due to possible confusion with other usage?
def resource():
    "Select resources a volunteer has."
    return shn_rest_controller(module, "resource")
