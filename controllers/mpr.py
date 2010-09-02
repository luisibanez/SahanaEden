# -*- coding: utf-8 -*-

""" MPR Missing Person Registry - Controllers

    @author: nursix

"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

module = request.controller

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions" Views)
def shn_menu():
    response.menu_options = [
        [T("Search for a Person"), False, URL(r=request, f="person", args="search_simple")],
        [T("Missing Persons"), False, URL(r=request, f="person"), [
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
        ]]]
    menu_selected = []
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

    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

    resource = request.function

    def person_prep(jr):
        if jr.component_name == "config":
            _config = db.gis_config
            defaults = db(_config.id == 1).select(limitby=(0, 1)).first()
            for key in defaults.keys():
                if key not in ["id", "uuid", "mci", "update_record", "delete_record"]:
                    _config[key].default = defaults[key]
        if jr.http == "POST" and jr.method == "create" and not jr.component:
            # Don't know why web2py always adds that,
            # remove it here as we want to manually redirect
            jr.request.post_vars.update(_next=None)
        return True

    response.s3.prep = person_prep

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "group_id",
                                       "group_head",
                                       "description"])

    def person_postp(jr, output):
        if jr.representation in ("html", "popup"):
            if not jr.component:
                label = READ
            else:
                label = UPDATE
            linkto = shn_linkto(jr, sticky=True)("[id]")
            report = URL(r=request, f="person", args=("[id]", "missing_report"))
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto)),
                dict(label=str(T("Report")), _class="action-btn", url=str(report))
            ]
        if jr.http == "POST" and jr.method == "create" and not jr.component:
            # If a new person gets added, redirect to mpr_next
            if response.s3.mpr_next:
                jr.next = response.s3.mpr_next
                response.s3.mpr_next = None
        return output
    response.s3.postp = person_postp

    db.pr_person.missing.readable = False
    db.pr_person.missing.writable = False
    db.pr_person.missing.default = True

    db.mpr_missing_report.person_id.readable = False
    db.mpr_missing_report.person_id.writable = False

    # Show only missing persons in list views
    if len(request.args) == 0:
        response.s3.filter = (db.pr_person.missing == True)

    mpr_tabs = [
                (T("Person Details"), None),
                (T("Missing Report"), "missing_report"),
                (T("Physical Description"), "physical_description"),
                (T("Images"), "image"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "pe_contact"),
                (T("Presence Log"), "presence"),
               ]
    
    rheader = lambda r: shn_pr_rheader(r, tabs=mpr_tabs)

    response.s3.pagination = True
    output = shn_rest_controller("pr", resource,
                                 main="first_name",
                                 extra="last_name",
                                 listadd=False,
                                 rheader=rheader)

    shn_menu()
    return output

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
def shn_mpr_person_onvalidate(form):

    pass
#
# -----------------------------------------------------------------------------
