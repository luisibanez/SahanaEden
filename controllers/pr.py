# -*- coding: utf-8 -*-

""" S3 Person Registry, controllers

    @author: nursix

"""

module = request.controller

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions" Views)
def shn_menu():
    response.menu_options = [
        [T("Search for a Person"), False, URL(r=request, f="person", args="search_simple")],
        [T("Persons"), False, URL(r=request, f="person"), [
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
        ]],
        [T("Groups"), False, URL(r=request, f="group"), [
            [T("List"), False, URL(r=request, f="group")],
            [T("Add"), False, URL(r=request, f="group", args="create")],
        ]]]
    menu_selected = []
    if session.rcvars and "pr_group" in session.rcvars:
        group = db.pr_group
        query = (group.id == session.rcvars["pr_group"])
        record = db(query).select(group.id, group.name, limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Group"), name), False,
                                 URL(r=request, f="group", args=[record.id])])
    if session.rcvars and "pr_person" in session.rcvars:
        person = db.pr_person
        query = (person.id == session.rcvars["pr_person"])
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = shn_pr_person_represent(record.id)
            menu_selected.append(["%s: %s" % (T("Person"), name), False,
                                 URL(r=request, f="person", args=[record.id])])
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

shn_menu()

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    try:
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Person Registry")

    def prep(jr):
        if jr.representation == "html":
            if not jr.id:
                jr.method = "search_simple"
                jr.custom_action = shn_pr_person_search_simple
            else:
               redirect(URL(r=request, f="person", args=[jr.id]))
        return True
    response.s3.prep = prep

    def postp(jr, output):
        if isinstance(output, dict):
            gender = []
            for g_opt in pr_gender_opts:
                count = db((db.pr_person.deleted == False) & \
                        (db.pr_person.gender == g_opt)).count()
                gender.append([str(pr_gender_opts[g_opt]), int(count)])

            age = []
            for a_opt in pr_age_group_opts:
                count = db((db.pr_person.deleted == False) & \
                        (db.pr_person.age_group == a_opt)).count()
                age.append([str(pr_age_group_opts[a_opt]), int(count)])

            total = int(db(db.pr_person.deleted == False).count())
            output.update(module_name=module_name, gender=gender, age=age, total=total)
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
    response.s3.postp = postp

    response.s3.pagination = True
    output = shn_rest_controller("pr", "person")
    response.view = "pr/index.html"

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

    resource = request.function

    def prep(r):
        if r.component_name == "config":
            _config = db.gis_config
            defaults = db(_config.id == 1).select(limitby=(0, 1)).first()
            for key in defaults.keys():
                if key not in ["id", "uuid", "mci", "update_record", "delete_record"]:
                    _config[key].default = defaults[key]
        if r.representation == "popup":
            # Hide "pe_label" and "missing" fields in person popups
            r.table.pe_label.readable = False
            r.table.pe_label.writable = False
            r.table.missing.readable = False
            r.table.missing.writable = False
        return True
    response.s3.prep = prep

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "group_id",
                                       "group_head",
                                       "description"])

    def postp(r, output):
        if r.representation in ("html", "popup"):
            if not r.component:
                label = READ
            else:
                label = UPDATE
            linkto = shn_linkto(r, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        return output
    response.s3.postp = postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 listadd = False,
                                 main="first_name",
                                 extra="last_name",
                                 rheader=lambda r: shn_pr_rheader(r,
                                    tabs = [(T("Basic Details"), None),
                                            (T("Images"), "image"),
                                            (T("Identity"), "identity"),
                                            (T("Address"), "address"),
                                            (T("Contact Data"), "pe_contact"),
                                            (T("Memberships"), "group_membership"),
                                            (T("Presence Log"), "presence"),
                                            (T("Subscriptions"), "pe_subscription"),
                                            (T("Map Settings"), "config")
                                            ]))

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def group():

    """ RESTful CRUD controller """

    resource = request.function

    response.s3.filter = (db.pr_group.system == False) # do not show system groups

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
                dict(label=str(label), _class="action-btn", url=linkto)
            ]
        return output
    response.s3.postp = group_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                main="name",
                extra="description",
                rheader=lambda jr: shn_pr_rheader(jr,
                    tabs = [(T("Group Details"), None),
                            (T("Address"), "address"),
                            (T("Contact Data"), "pe_contact"),
                            (T("Members"), "group_membership")]),
                deletable=False)

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def image():

    """ RESTful CRUD controller """

    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def pe_contact():

    """ RESTful CRUD controller """

    resource = request.function
    return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
#def group_membership():

    #""" RESTful CRUD controller """

    #resource = request.function
    #return shn_rest_controller(module, resource)

# -----------------------------------------------------------------------------
def pentity():

    """ RESTful CRUD controller """

    resource = request.function
    response.s3.pagination = True
    return shn_rest_controller(module, resource,
                               editable=False,
                               deletable=False,
                               listadd=False)

# -----------------------------------------------------------------------------
def download():

    """ Download a file. """

    return response.download(request, db)

# -----------------------------------------------------------------------------
def tooltip():

    """ Ajax tooltips """

    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return dict()

# -----------------------------------------------------------------------------
