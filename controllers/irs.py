# -*- coding: utf-8 -*-

""" Incident Reporting System - Controllers

    @author: Sahana Taiwan Team

"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Incident Reports"), False, URL(r=request, f="ireport"),[
        [T("List"), False, URL(r=request, f="ireport")],
        [T("Add"), False, URL(r=request, f="ireport", args="create")],
        #[T("Ushahidi"), False, URL(r=request, f="ireport", args="ushahidi")],
        #[T("Search"), False, URL(r=request, f="ireport", args="search")]
    ]],
    #[T("Assessments"), False, URL(r=request, f="iassessment"),[
    #    [T("List"), False, URL(r=request, f="iassessment")],
    #    [T("Add"), False, URL(r=request, f="iassessment", args="create")],
        #[T("Search"), False, URL(r=request, f="iassessment", args="search")]
    #]],
    #[T("Map"), False, URL(r=request, f="maps")],
]

if shn_has_role("Editor"):
    response.menu_options.append(
        [T("Confirmed Incidents"), False, URL(r=request, f="incident"),[
            [T("List"), False, URL(r=request, f="incident")],
            [T("Add"), False, URL(r=request, f="incident", args="create")],
            #[T("Search"), False, URL(r=request, f="incident", args="search")]
        ]]
    )
if shn_has_role(1):
    response.menu_options.append(
        [T("Incident Categories"), False, URL(r=request, f="icategory"),[
            [T("List"), False, URL(r=request, f="icategory")],
            [T("Add"), False, URL(r=request, f="icategory", args="create")]
        ]]
    )
    response.menu_options.append(
        [T("Ushahidi Import"), False, URL(r=request, f="ireport", args="ushahidi")],
    )

# -----------------------------------------------------------------------------
def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
def maps():

    """ Show a Map of all Incident Reports """

    reports = db(db.gis_location.id == db.irs_ireport.location_id).select()
    popup_url = URL(r=request, f="ireport", args="read.popup?ireport.location_id=")
    incidents = {"name":Tstr("Incident Reports"), "query":reports, "active":True, "popup_url": popup_url}
    feature_queries = [incidents]
    
    map = gis.show_map(feature_queries=feature_queries, window=True)

    return dict(map=map)


# -----------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def icategory():

    """
        Incident Categories, RESTful controller
        Note: This just defines which categories are visible to end-users
        The full list of hard-coded categories are visible to admins & should remain unchanged for sync
    """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)
    return output

# -----------------------------------------------------------------------------
def incident():

    """ Incidents, RESTful controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    db.irs_iimage.assessment_id.readable = \
    db.irs_iimage.assessment_id.writable = False

    db.irs_iimage.incident_id.readable = \
    db.irs_iimage.incident_id.writable = False

    db.irs_iimage.report_id.readable = \
    db.irs_iimage.report_id.writable = False

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    rheader = lambda r: shn_irs_rheader(r, tabs = [(T("Incident Details"), None),
                                                   (T("Reports"), "ireport"),
                                                   (T("Images"), "iimage"),
                                                   #(T("Assessments"), "iassessment"),
                                                   (T("Response"), "iresponse")
                                                  ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False, rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def ireport():

    """ Incident Reports, RESTful controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Non-Editors should only see a limited set of options
    if not shn_has_role("Editor"):
        allowed_opts = [irs_incident_type_opts.get(opt.code, opt.code) for opt in db().select(db.irs_icategory.code)]
        table.category.requires = IS_NULL_OR(IS_IN_SET(allowed_opts))
    
    # Pre-processor
    def prep(r):
        if r.method == "ushahidi":
            auth.settings.on_failed_authorization = r.other(method="", vars=None)
        elif r.method == "update":
            # Disable legacy fields, unless updating, so the data can be manually transferred to new fields
            table.source.readable = table.source.writable = False        
            table.source_id.readable = table.source_id.writable = False         
        elif r.representation in ("html", "popup") and r.method == "create":
            table.datetime.default = request.utcnow
            person = session.auth.user.id if auth.is_logged_in() else None
            if person:
                person_uuid = db(db.auth_user.id == person).select(db.auth_user.person_uuid, limitby=(0, 1)).first().person_uuid
                person = db(db.pr_person.uuid == person_uuid).select(db.pr_person.id, limitby=(0, 1)).first().id
            table.person_id.default = person

        return True
    response.s3.prep = prep

    if not shn_has_role("Editor"):
        table.incident_id.readable = table.incident_id.writable = False
    
    db.irs_iimage.assessment_id.readable = \
    db.irs_iimage.assessment_id.writable = False

    db.irs_iimage.report_id.readable = \
    db.irs_iimage.report_id.writable = False

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False, copyable=True)
        return output
    response.s3.postp = user_postp

    rheader = lambda r: shn_irs_rheader(r, tabs = [(T("Report Details"), None),
                                                   (T("Images"), "iimage")
                                                  ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False, rheader=rheader)
    return output

# -----------------------------------------------------------------------------
# Currently unused - Assessment module (in 'sitrep' currently) is used instead
def iassessment():

    """ Incident Assessment, RESTful controller """

    resource = request.function

    db.irs_iimage.assessment_id.readable = \
    db.irs_iimage.assessment_id.writable = False

    db.irs_iimage.report_id.readable = \
    db.irs_iimage.report_id.writable = False

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    rheader = lambda r: shn_irs_rheader(r, tabs = [(T("Assessment Details"), None),
                                                   (T("Images"), "iimage")
                                                  ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, rheader=rheader)
    return output


# -----------------------------------------------------------------------------
def shn_irs_rheader(r, tabs=[]):

    """ Resource Headers for IRS """

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)

        if r.name == "ireport":
            report = r.record
            reporter = report.person_id
            if reporter:
                reporter = shn_pr_person_represent(reporter)
            location = report.location_id
            if location:
                location = shn_gis_location_represent(location)
            create_request = DIV(P(), A(T("Create Request"), _class="action-btn colorbox", _href=URL(r=request, c="rms", f="req", args="create", vars={"format":"popup", "caller":"irs_ireport"}), _title=T("Add Request")), P())
            rheader = DIV(TABLE(
                            TR(
                                TH(T("Short Description: ")), report.name,
                                TH(T("Reporter: ")), reporter),
                            TR(
                                TH(T("Contacts: ")), report.contact,
                                TH(T("Location: ")), location)
                            ),
                          create_request,
                          rheader_tabs)

        elif r.name == "incident":
            incident = r.record
            location = incident.location_id
            if location:
                location = shn_gis_location_represent(location)
            category = irs_incident_type_opts.get(incident.category, incident.category)
            rheader = DIV(TABLE(
                            TR(
                                TH(T("Short Description: ")), incident.name,
                                TH(T("Category: ")), category),
                            TR(
                                TH(T("Contacts: ")), incident.contact,
                                TH(T("Location: ")), location)
                            ),
                      rheader_tabs)

        elif r.name == "iassessment":
            assessment = r.record
            author = shn_pr_person_represent(assessment.created_by)
            itype = irs_assessment_type_opts.get(assessment.itype, UNKNOWN_OPT)
            etype = irs_event_type_opts.get(assessment.event_type, UNKNOWN_OPT)
            rheader = DIV(TABLE(
                            TR(
                                TH(T("Assessment Type: ")), itype,
                                TH(T("Author: ")), author),
                            TR(
                                TH("Event type: "), etype,
                                TH(T("Date: ")), assessment.datetime)
                            ),
                      rheader_tabs)

        return rheader

    else:
        return None


# -----------------------------------------------------------------------------
