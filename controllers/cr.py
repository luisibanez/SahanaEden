# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers
"""
# @ToDo Search shelters by type, services, location, available space
# @ToDo Tie in assessments from RAT and requests from RMS.
# @ToDo Associate persons with shelters (via presence loc == shelter loc?)

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
def shn_menu():
    menu = [
        [T("Shelters"), False, URL(r=request, f="shelter"), [
            [T("List"), False, URL(r=request, f="shelter")],
            [T("Add"), False, URL(r=request, f="shelter", args="create")],
            # @ToDo Search by type, services, location, available space
            #[T("Search"), False, URL(r=request, f="shelter", args="search")],
        ]],
    ]
    if not deployment_settings.get_security_map() or shn_has_role("Editor"):
        menu_editor = [
            [T("Shelter Types and Services"), False, URL(r=request, f="#"), [
                [T("List / Add Services"), False, URL(r=request, f="shelter_service")],
                [T("List / Add Types"), False, URL(r=request, f="shelter_type")],
            ]],
        ]
        menu.extend(menu_editor)
    response.menu_options = menu

shn_menu()

# S3 framework functions
# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice

    shn_menu()
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def shelter_type():

    """
    RESTful CRUD controller
    List / add shelter types (e.g. NGO-operated, Government evacuation center,
    School, Hospital -- see Agasti opt_camp_type.)
    """

    resource = request.function

    # Don't provide delete button in list view
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp
    
    rheader = lambda r: shn_shelter_rheader(r,
                                            tabs = [(T("Basic Details"), None),
                                                    (T("Shelters"), "shelter")
                                                   ])

    # @ToDo Shelters per type display is broken -- always returns none.
    output = shn_rest_controller(module, resource,
                                 listadd=False,
                                 rheader=rheader)
    shn_menu()
    return output

# -----------------------------------------------------------------------------
def shelter_service():

    """
    RESTful CRUD controller
    List / add shelter services (e.g. medical, housing, food,...)
    """

    resource = request.function

    # Don't provide delete button in list view
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    rheader = lambda r: shn_shelter_rheader(r,
                                            tabs = [(T("Basic Details"), None),
                                                    (T("Shelters"), "shelter")])
                                                    
    output = shn_rest_controller(module, resource,
                                 listadd=False,
                                 rheader=rheader)
    shn_menu()
    return output

# -----------------------------------------------------------------------------
def shelter():

    """ RESTful CRUD controller

    >>> resource="shelter"
    >>> from applications.sahana.modules.s3_test import WSGI_Test
    >>> test=WSGI_Test(db)
    >>> "200 OK" in test.getPage("/sahana/%s/%s" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody("List Shelters")
    >>> "200 OK" in test.getPage("/sahana/%s/%s/create" % (module,resource))    #doctest: +SKIP
    True
    >>> test.assertHeader("Content-Type", "text/html")                          #doctest: +SKIP
    >>> test.assertInBody("Add Shelter")                                        #doctest: +SKIP
    >>> "200 OK" in test.getPage("/sahana/%s/%s?format=json" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody("[")
    >>> "200 OK" in test.getPage("/sahana/%s/%s?format=csv" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/csv")

    """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    response.s3.prep = shelter_prep

    crud.settings.create_onvalidation = shelter_onvalidation
    crud.settings.update_onvalidation = shelter_onvalidation

    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    response.s3.pagination = True

    shelter_tabs = [(T("Basic Details"), None),
                    (T("Assessments"), "assessment"),
                    (T("Requests"), "req"),
                    (T("Inventory"), "store"),  # table is inventory_store
                   ]

    rheader = lambda r: shn_shelter_rheader(r, tabs=shelter_tabs)

    output = shn_rest_controller(module, resource,
                                 listadd=False,
                                 rheader=rheader)

    shn_menu()
    return output

"""
The school- and hospital-specific fields are guarded by checkboxes in
the form.  If the "is_school" or "is_hospital" checkbox was checked,
we use the corresponding field values, else we discard them.  Presence
of a non-empty value for school_code or hospital_id is what determines
later whether a shelter record is a school or hospital, as the is_school
and is_hospital values are not in the table.

Note we clear the unused hospital value *before* validation, because
there is a (small) possibility that someone deleted the chosen hospital 
record while this request was in flight.  If the user doesn't want the
hospital they selected, there's no reason to make sure it's in the database.

On the other hand, we don't check for a missing school code or hospital id
value until after other fields have been validated, as that allows the
user to get all the user to see al the errors in one go.

We don't just clear the fields in the form if the user unchecks the
checkbox because they might do that accidentally, and it would not be
nice to make them re-enter the info.
"""

def shelter_prep(r):
    """
    If the "is_school" or "is_hospital" checkbox was checked, we use the
    corresponding field values, else we clear them so no attempt is made
    to validate them.
    """

    # Note the checkbox inputs that guard the optional data are inserted in
    # the view and are not database fields, so are not in request.post_vars
    # (or, after validation, in form.vars), only in request.vars.

    # Likewise, these controls won't be present for, e.g., xml import, so
    # restrict to html and popup.  The hospital_id field won't be present
    # at all if the hms module is not enabled.  When we later get to
    # onvalidation, we need to know if this was html or popup, so save that
    # in request.vars in a variable that won't be used to carry any real
    # form data.

    if r.representation in ("popup", "html"):
        # Remember this is html or popup.
        response.cr_shelter_request_was_html_or_popup = True

        if r.http == "POST":

            if not "is_school" in request.vars:
                request.post_vars.school_code = None
                request.post_vars.school_pf = None
    
            if not "is_hospital" in request.vars and "hospital_id" in request.post_vars:
                request.post_vars.hospital_id = None

    return True

def shelter_onvalidation(form):
    """
    If the user checked is_school, but there is no school_code, add a
    form.error for that field, to fail the submission and get an error
    message into the page.  Likewise for is_hospital and hospital_id.
    """

    if response.cr_shelter_request_was_html_or_popup:
        # Get rid of that before anyone else sees it...
        response.cr_shelter_request_was_html_or_popup = None

        if "is_school" in request.vars and not form.vars.school_code:
            form.errors.school_code = T(
                "Please enter a school code or don't check 'Is this a school?'")

        # Note the form is defective if there's an is_hospital checkbox
        # but no hospital_id field...
        if "is_hospital" in request.vars and not form.vars.hospital_id:
            form.errors.hospital_id = T(
                "Please select a hospital or don't check 'Is this a hospital?'")

    return


# -----------------------------------------------------------------------------
def shn_shelter_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)

        record = r.record
        rheader = DIV(TABLE(
                        TR(
                            TH(Tstr("Name") + ": "), record.name
                          ),
                        ),
                      rheader_tabs)

        return rheader

    else:
        return None

# -----------------------------------------------------------------------------
# This code provides urls of the form:
# http://.../eden/cr/call/<service>/rpc/<method>/<id>
# e.g.:
# http://.../eden/cr/call/jsonrpc/rpc/list/2
# It is not currently in use but left in as an example, and because it may
# be used in future for interoperating with or transferring data from Agasti
# which uses xml-rpc.  See:
# http://www.web2py.com/examples/default/tools#services
# http://groups.google.com/group/web2py/browse_thread/thread/53086d5f89ac3ae2
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    return service()

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def rpc(method,id=0):
    if method == "list":
        return db().select(db.cr_shelter.ALL).as_list()
    if method == "read":
        return db(db.cr_shelter.id==id).select().as_list()
    if method == "delete":
        status=db(db.cr_shelter.id==id).delete()
        if status:
            return "Success - record %d deleted!" % id
        else:
            return "Failed - no record %d!" % id
    else:
        return "Method not implemented!"

@service.xmlrpc
def create(name):
    # Need to do validation manually!
    id = db.cr_shelter.insert(name=name)
    return id

@service.xmlrpc
def update(id, name):
    # Need to do validation manually!
    status = db(db.cr_shelter.id == id).update(name=name)
    if status:
        return "Success - record %d updated!" % id
    else:
        return "Failed - no record %d!" % id
