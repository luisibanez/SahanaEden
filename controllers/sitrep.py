# -*- coding: utf-8 -*-

""" Assessments Module - Controllers

    @author: Fran Boon
    @see: http://eden.sahanafoundation.org/wiki/Pakistan
    @ToDo: Rename as 'assessment' (Deprioritised due to Data Migration issues being distracting for us currently)

"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Assessments"), False, URL(r=request, f="assessment"),[
        [T("List"), False, URL(r=request, f="assessment")],
        [T("Add"), False, URL(r=request, f="assessment", args="create")],
        #[T("Search"), False, URL(r=request, f="assessment", args="search")]
    ]],
    [T("Schools"), False, URL(r=request, f="school_district"),[
        [T("List"), False, URL(r=request, f="school_district")],
        [T("Add"), False, URL(r=request, f="school_district", args="create")],
        #[T("Search"), False, URL(r=request, f="school_district", args="search")]
    ]],
    #[T("Map"), False, URL(r=request, f="maps")],
]

def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)


def maps():

    """ Show a Map of all Assessments """

    freports = db(db.gis_location.id == db.sitrep_freport.location_id).select()
    freport_popup_url = URL(r=request, f="freport", args="read.popup?freport.location_id=")
    map = gis.show_map(feature_queries = [{"name":Tstr("Flood Reports"), "query":freports, "active":True, "popup_url": freport_popup_url}], window=True)

    return dict(map=map)


def assessment():

    """ Assessments, RESTful controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Villages only
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF(db(db.gis_location.level == "L5"), "gis_location.id", repr_select, sort=True))

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Pre-processor
    def prep(r):
        if r.method == "update":
            # Disable legacy fields, unless updating, so the data can be manually transferred to new fields
            table.source.readable = table.source.writable = False        
        return True
    response.s3.prep = prep

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource)
    return output


def school_district():

    """
        REST Controller
        @ToDo: Move to CR
    """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Districts only
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF(db(db.gis_location.level == "L2"), "gis_location.id", repr_select, sort=True))
    table.location_id.comment = DIV(A(ADD_LOCATION,
                                       _class="colorbox",
                                       _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup")),
                                       _target="top",
                                       _title=ADD_LOCATION),
                                     DIV( _class="tooltip",
                                       _title=Tstr("District") + "|" + Tstr("The District for this Report."))),

    # Pre-processor
    def prep(r):
        if r.method == "update":
            # Disable legacy fields, unless updating, so the data can be manually transferred to new fields
            table.document.readable = table.document.writable = False        
        return True
    response.s3.prep = prep

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    rheader = lambda r: shn_sitrep_rheader(r,
                                           tabs = [(T("Basic Details"), None),
                                                   (T("School Reports"), "school_report")
                                                  ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def school_report():
    
    """
        REST Controller
        Needed for Map Popups
        @ToDo: Move to CR
    """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource)
    return output

# -----------------------------------------------------------------------------
def download():

    """ Download a file """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def shn_sitrep_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)

        if r.name == "school_district":

            report = r.record
            doc_url = URL(r=request, f="download", args=[report.document])
            try:
                doc_name, file = r.table.document.retrieve(report.document)
                if hasattr(file, "close"):
                    file.close()
            except:
                doc_name = report.document

            rheader = DIV(TABLE(
                            TR(
                                TH(Tstr("Date") + ": "), report.date
                              ),
                            TR(
                                TH(Tstr("Document") + ": "), A(doc_name, _href=doc_url)
                              )
                            ),
                          rheader_tabs)

            return rheader
        else:
            return None
