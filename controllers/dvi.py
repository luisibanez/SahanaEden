# -*- coding: utf-8 -*-

"""
    DVI Module - Controllers
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Only people with the DVI role should be able to access this module
#if not shn_has_role("DVI"):
#    unauthorised()

# Options Menu (available in all Functions" Views)
def shn_menu():
    response.menu_options = [
        [T("Recovery Requests"), False, URL(r=request, f="recreq"),[
            [T("List Requests"), False, URL(r=request, f="recreq")],
            [T("New Request"), False, URL(r=request, f="recreq", args="create")],
        ]],
        [T("Recovery Reports"), False, URL(r=request, f="body"),[
            [T("List Reports"), False, URL(r=request, f="body")],
            [T("New Report"), False, URL(r=request, f="body", args="create")],
        ]],
        [T("Search by ID Tag"), False, URL(r=request, f="body", args="search_simple")]
    ]
    menu_selected = []
    if session.rcvars and "dvi_body" in session.rcvars:
        body = db.dvi_body
        query = (body.id == session.rcvars["dvi_body"])
        record = db(query).select(body.id, body.pe_label, limitby=(0,1)).first()
        if record:
            label = record.pe_label
            menu_selected.append(["%s: %s" % (T("Body"), label), False,
                                 URL(r=request, f="body", args=[record.id])])
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

shn_menu()

# S3 framework functions
def index():

    """ Module's Home Page """

    try:
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Disaster Victim Identification")

    return dict(module_name=module_name)

def recreq():

    """ RESTful CRUD controller """

    resource = request.function

    def recreq_postp(jr, output):
        if jr.representation in ("html", "popup"):
            label = UPDATE
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        return output
    response.s3.postp = recreq_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False)

    shn_menu()
    return output

def body():

    """ RESTful CRUD controller """

    resource = request.function

    def body_postp(jr, output):
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
    response.s3.postp = body_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 main="pe_label",
                                 extra="gender",
                                 rheader=lambda r: \
                                         shn_dvi_rheader(r, tabs=[
                                            (T("Recovery"), ""),
                                            (T("Checklist"), "checklist"),
                                            (T("Images"), "image"),
                                            (T("Physical Description"), "physical_description"),
                                            (T("Effects Inventory"), "effects"),
                                            (T("Tracing"), "presence"),
                                            (T("Identity"), "identification"),
                                         ]),
                                 listadd=False)
    shn_menu()
    return output

# -----------------------------------------------------------------------------
def download():

    """ Download a file. """

    return response.download(request, db)

# -----------------------------------------------------------------------------
def tooltip():

    """ Ajax tooltips """

    formfield = request.vars.get("formfield", None)
    if formfield:
        response.view = "pr/ajaxtips/%s.html" % formfield
    return dict()

#
# -----------------------------------------------------------------------------
