# -*- coding: utf-8 -*-

"""
    HMS Hospital Status Assessment and Request Management System

    @author: nursix
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# -----------------------------------------------------------------------------
def shn_menu():
    menu = [
        [T("Home"), False, URL(r=request, f="index")],
        [T("Hospitals"), False, URL(r=request, f="hospital"), [
            [T("List All"), False, URL(r=request, f="hospital")],
            [T("Find by Name"), False, URL(r=request, f="hospital", args="search_simple")],
            [T("Add Hospital"), False, URL(r=request, f="hospital", args="create")]
        ]],
    ]
    if session.rcvars and "hms_hospital" in session.rcvars:
        hospital = db.hms_hospital
        query = (hospital.id == session.rcvars["hms_hospital"])
        selection = db(query).select(hospital.id, hospital.name, limitby=(0, 1)).first()
        if selection:
            menu_hospital = [
                    [selection.name, False, URL(r=request, f="hospital", args=[selection.id])]
            ]
            menu.extend(menu_hospital)
    menu2 = [
        [T("Add Request"), False, URL(r=request, f="hrequest", args="create")],
        [T("Requests"), False, URL(r=request, f="hrequest")],
        [T("Pledges"), False, URL(r=request, f="hpledge")],
    ]
    menu.extend(menu2)
    response.menu_options = menu

shn_menu()

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name, public_url=deployment_settings.base.public_url)

# -----------------------------------------------------------------------------
def hospital():

    """ Main controller for hospital data entry """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    table.gov_uuid.label = T("Government UID")
    table.name.label = T("Name")
    table.name.comment = SPAN("*", _class="req")
    table.aka1.label = T("Other Name")
    table.aka2.label = T("Other Name")
    table.address.label = T("Address")
    table.postcode.label = T("Postcode")
    table.phone_exchange.label = T("Phone/Exchange")
    table.phone_business.label = T("Phone/Business")
    table.phone_emergency.label = T("Phone/Emergency")
    table.email.label = T("Email")
    table.fax.label = T("Fax")
    table.website.represent = shn_url_represent

    table.total_beds.label = T("Total Beds")
    table.total_beds.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Total Beds") + "|" + Tstr("Total number of beds in this hospital. Automatically updated from daily reports.")))

    table.available_beds.label = T("Available Beds")
    table.available_beds.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Available Beds") + "|" + Tstr("Number of vacant/available beds in this hospital. Automatically updated from daily reports.")))

    table.ems_status.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("EMS Status") + "|" + Tstr("Status of operations of the emergency department of this hospital.")))
    table.ems_reason.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("EMS Reason") + "|" + Tstr("Report the contributing factors for the current EMS status.")))

    table.or_status.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("OR Status") + "|" + Tstr("Status of the operating rooms of this hospital.")))
    table.or_reason.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("OR Reason") + "|" + Tstr("Report the contributing factors for the current OR status.")))

    table.facility_status.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Facility Status") + "|" + Tstr("Status of general operation of the facility.")))

    table.clinical_status.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Clinical Status") + "|" + Tstr("Status of clinical operation of the facility.")))

    table.morgue_status.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Morgue Status") + "|" + Tstr("Status of morgue capacity.")))

    table.security_status.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Security Status") + "|" + Tstr("Status of security procedures/access restrictions in the hospital.")))

    table.morgue_units.label = T("Morgue Units Available")
    table.morgue_units.comment =  DIV(DIV(_class="tooltip",
        _title=Tstr("Morgue Units Available") + "|" + Tstr("Number of vacant/available units to which victims can be transported immediately.")))

    table.doctors.label = T("Number of doctors")
    table.nurses.label = T("Number of nurses")
    table.non_medical_staff.label = T("Number of non-medical staff")

    table.access_status.label = T("Road Conditions")
    table.access_status.comment =  DIV(DIV(_class="tooltip",
        _title=Tstr("Road Conditions") + "|" + Tstr("Describe the condition of the roads to your hospital.")))

    table.info_source.label = "Source of Information"
    table.info_source.comment =  DIV(DIV(_class="tooltip",
        _title=Tstr("Source of Information") + "|" + Tstr("Specify the source of the information in this report.")))

    # CRUD Strings
    LIST_HOSPITALS = T("List Hospitals")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_HOSPITAL,
        title_display = T("Hospital Details"),
        title_list = LIST_HOSPITALS,
        title_update = T("Edit Hospital"),
        title_search = T("Search Hospitals"),
        subtitle_create = T("Add New Hospital"),
        subtitle_list = T("Hospitals"),
        label_list_button = LIST_HOSPITALS,
        label_create_button = ADD_HOSPITAL,
        label_delete_button = T("Delete Hospital"),
        msg_record_created = T("Hospital information added"),
        msg_record_modified = T("Hospital information updated"),
        msg_record_deleted = T("Hospital information deleted"),
        msg_list_empty = T("No Hospitals currently registered"))

    #s3xrc.sync_resolve = shn_hospital_resolver

    def hospital_postp(jr, output):
        if jr.representation in ("html", "popup"):
            if jr.component and jr.component.name == "bed_capacity":
                label = UPDATE
            else:
                label = READ
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        return output
    response.s3.postp = hospital_postp

    rheader = lambda r: shn_hms_hospital_rheader(r,
                                                 tabs=[(T("Status Report"), ""),
                                                       (T("Bed Capacity"), "bed_capacity"),
                                                       (T("Activity Report"), "hactivity"),
                                                       (T("Requests"), "hrequest"),
                                                       (T("Images"), "himage"),
                                                       (T("Services"), "services"),
                                                       (T("Contacts"), "hcontact")
                                                      ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 rheader=rheader,
                                 rss=dict(title="%(name)s",
                                          description=shn_hms_hospital_rss),
                                 listadd=False)

    shn_menu()

    return output


def shn_hospital_resolver(vector):

    """ Example for a simple Sync resolver - not for production use """

    # Default resolution: import data from peer if newer
    vector.default_resolution = vector.RESOLUTION.NEWER

    if vector.tablename == "hms_hospital":
        # Do not update hospital Gov-UUIDs or names
        vector.resolution = dict(
            gov_uuid = vector.RESOLUTION.THIS,
            name = vector.RESOLUTION.THIS
        )
    else:
        vector.resolution = vector.RESOLUTION.NEWER

    # Allow both, update of existing and create of new records:
    vector.strategy = [vector.METHOD.UPDATE, vector.METHOD.CREATE]

# -----------------------------------------------------------------------------
def hrequest():

    """ Hospital Requests Controller """

    resource = request.function

    if auth.user is not None:
        person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.id)
        if person:
            db.hms_hpledge.person_id.default = person[0].id

    def hrequest_postp(jr, output):
        if jr.representation in ("html", "popup") and not jr.component:
            response.s3.actions = [
                dict(label=str(T("Pledge")), _class="action-btn", url=str(URL(r=request, args=["[id]", "hpledge"])))
            ]
        return output
    response.s3.postp = hrequest_postp


    response.s3.pagination = True
    output = shn_rest_controller(module , resource,
                                 listadd=False,
                                 deletable=False,
                                 rheader=shn_hms_hrequest_rheader)

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def hpledge():

    """ Pledges Controller """

    resource = request.function

    pledges = db(db.hms_hpledge.status == 3).select()
    for pledge in pledges:
        db(db.hms_hrequest.id == pledge.hms_hrequest_id).update(status = 6)

    db.commit()

    if auth.user is not None:
        person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.id)
        if person:
            db.hms_hpledge.person_id.default = person[0].id

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, editable = True, listadd=False)

    shn_menu()
    return output

# -----------------------------------------------------------------------------
#
def shn_hms_hospital_rheader(jr, tabs=[]):

    """ Page header for component resources """

    if jr.name == "hospital":
        if jr.representation == "html":

            _next = jr.here()
            _same = jr.same()

            rheader_tabs = shn_rheader_tabs(jr, tabs)

            hospital = jr.record
            if hospital:
                rheader = DIV(TABLE(

                    TR(TH(T("Name: ")),
                        hospital.name,
                        TH(T("EMS Status: ")),
                        "%s" % db.hms_hospital.ems_status.represent(hospital.ems_status)),

                    TR(TH(T("Location: ")),
                        db.gis_location[hospital.location_id] and db.gis_location[hospital.location_id].name or "unknown",
                        TH(T("Facility Status: ")),
                        "%s" % db.hms_hospital.facility_status.represent(hospital.facility_status)),

                    TR(TH(T("Total Beds: ")),
                        hospital.total_beds,
                        TH(T("Clinical Status: ")),
                        "%s" % db.hms_hospital.clinical_status.represent(hospital.clinical_status)),

                    TR(TH(T("Available Beds: ")),
                        hospital.available_beds,
                        TH(T("Security Status: ")),
                        "%s" % db.hms_hospital.security_status.represent(hospital.security_status))

                        ), rheader_tabs)

                return rheader

    return None

# -----------------------------------------------------------------------------
def shn_hms_hrequest_rheader(jr):

    """ Request RHeader """

    if jr.representation == "html":

        _next = jr.here()
        _same = jr.same()

        aid_request = jr.record
        if aid_request:
            try:
                hospital_represent = hospital_id.hospital_id.represent(aid_request.hospital.id)
            except:
                hospital_represent = None

            rheader = TABLE(
                        TR(
                            TH(T("Message: ")),
                            TD(aid_request.message, _colspan=3),
                            ),
                        TR(
                            TH(T("Hospital: ")),
                            db.hms_hospital[aid_request.hospital_id] and \
                            db.hms_hospital[aid_request.hospital_id].name or "unknown",
                            TH(T("Source Type: ")),
                            hms_hrequest_source_type.get(aid_request.source_type, "unknown"),
                            TH(""),
                            ""
                            ),
                        TR(
                            TH(T("Time of Request: ")),
                            aid_request.timestmp,
                            TH(T("Priority: ")),
                            hms_hrequest_priority_opts.get(aid_request.priority, "unknown"),
                            TH(T("Status: ")),
                            hms_hrequest_status_opts.get(aid_request.status, "unknown")
                        ),
                    )
            return rheader

    return None

#
# -----------------------------------------------------------------------------
