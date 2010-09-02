# -*- coding: utf-8 -*-

"""
    HMS Hospital Status Assessment and Request Management System

    @author: nursix
"""

module = "hms"
if deployment_settings.has_module(module):

    # -----------------------------------------------------------------------------
    # Settings
    #
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("audit_read", "boolean"),
                            Field("audit_write", "boolean"),
                            migrate=migrate)

    # -----------------------------------------------------------------------------
    # Hospitals
    #

    # Use government-assigned UUIDs instead of internal UUIDs
    HMS_HOSPITAL_USE_GOVUUID = True

    hms_facility_type_opts = {
        1: T("Hospital"),
        2: T("Field Hospital"),
        3: T("Specialized Hospital"),
        11: T("Health center"),
        12: T("Health center with beds"),
        13: T("Health center without beds"),
        21: T("Dispensary"),
        98: T("Other"),
        99: T("Unknown type of facility"),
    } #: Facility Type Options

    hms_facility_status_opts = {
        1: T("Normal"),
        2: T("Compromised"),
        3: T("Evacuating"),
        4: T("Closed")
    } #: Facility Status Options

    hms_clinical_status_opts = {
        1: T("Normal"),
        2: T("Full"),
        3: T("Closed")
    } #: Clinical Status Options

    hms_morgue_status_opts = {
        1: T("Open"),
        2: T("Full"),
        3: T("Exceeded"),
        4: T("Closed")
    } #: Morgue Status Options

    hms_security_status_opts = {
        1: T("Normal"),
        2: T("Elevated"),
        3: T("Restricted Access"),
        4: T("Lockdown"),
        5: T("Quarantine"),
        6: T("Closed")
    } #: Security Status Options

    hms_resource_status_opts = {
        1: T("Adequate"),
        2: T("Insufficient")
    } #: Resource Status Options

    hms_ems_traffic_opts = {
        1: T("Normal"),
        2: T("Advisory"),
        3: T("Closed"),
        4: T("Not Applicable")
    } #: EMS Traffic Options

    hms_or_status_opts = {
        1: T("Normal"),
        #2: T("Advisory"),
        3: T("Closed"),
        4: T("Not Applicable")
    } #: Operating Room Status Options

    resource = "hospital"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                    site_id,
                    Field("gov_uuid", unique=True, length=128), # UUID assigned by Local Government
                    Field("name", notnull=True),                # Name of the facility
                    Field("aka1"),                              # Alternate name, or name in local language
                    Field("aka2"),                              # Alternate name, or name in local language
                    Field("facility_type", "integer",           # Type of facility
                        requires = IS_NULL_OR(IS_IN_SET(hms_facility_type_opts)),
                        label = T("Facility Type"),
                        represent = lambda opt: hms_facility_type_opts.get(opt, T("not specified"))),
                    organisation_id,
                    location_id,
                    Field("address"),
                    Field("postcode"),
                    Field("city"),
                    Field("phone_exchange", requires = shn_phone_requires), # Switchboard
                    Field("phone_business", requires = shn_phone_requires),
                    Field("phone_emergency", requires = shn_phone_requires),
                    Field("website", requires = IS_NULL_OR(IS_URL())),
                    Field("email"),
                    Field("fax", requires = shn_phone_requires),
                    Field("total_beds", "integer"),             # Total Beds
                    Field("available_beds", "integer"),         # Available Beds
                    Field("ems_status", "integer",              # Emergency Room Status
                        requires = IS_NULL_OR(IS_IN_SET(hms_ems_traffic_opts)),
                        label = T("EMS Traffic Status"),
                        represent = lambda opt: hms_ems_traffic_opts.get(opt, UNKNOWN_OPT)),
                    Field("ems_reason", length=128,             # Reason for EMS Status
                        label = T("EMS Status Reason")),
                    Field("or_status", "integer",               # Operating Room Status
                        requires = IS_NULL_OR(IS_IN_SET(hms_or_status_opts)),
                        label = T("OR Status"),
                        represent = lambda opt: hms_or_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("or_reason", length=128,              # Reason for OR Status
                        label = T("OR Status Reason")),
                    Field("facility_status", "integer",         # Facility Status
                        requires = IS_NULL_OR(IS_IN_SET(hms_facility_status_opts)),
                        label = T("Facility Status"),
                        represent = lambda opt: hms_facility_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("clinical_status", "integer",         # Clinical Status
                        requires = IS_NULL_OR(IS_IN_SET(hms_clinical_status_opts)),
                        label = T("Clinical Status"),
                        represent = lambda opt: hms_clinical_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("morgue_status", "integer",           # Morgue Status
                        requires = IS_NULL_OR(IS_IN_SET(hms_morgue_status_opts)),
                        label = T("Morgue Status"),
                        represent = lambda opt: hms_clinical_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("morgue_units", "integer"),           # Number of available/vacant morgue units
                    Field("security_status", "integer",         # Security status
                        requires = IS_NULL_OR(IS_IN_SET(hms_security_status_opts)),
                        label = T("Security Status"),
                        represent = lambda opt: hms_security_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("doctors", "integer"),                # Number of Doctors
                    Field("nurses", "integer"),                 # Number of Nurses
                    Field("non_medical_staff", "integer"),      # Number of Non-Medical Staff
                    Field("staffing", "integer",                # Staffing status
                        requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                        label = T("Staffing"),
                        represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("facility_operations", "integer",     # Facility Operations Status
                        requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                        label = T("Facility Operations"),
                        represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("clinical_operations", "integer",     # Clinical Operations Status
                        requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                        label = T("Clinical Operations"),
                        represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("access_status"),                     # Access Status
                    Field("info_source"),                       # Source of Information
                    comments,                         # Comments field
                    migrate=migrate)


    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

    table.organisation_id.represent = lambda id: \
        (id and [db(db.org_organisation.id == id).select(db.org_organisation.acronym, limitby=(0, 1)).first().acronym] or ["None"])[0]

    table.gov_uuid.requires = IS_NULL_OR(IS_NOT_IN_DB(db, "%s.gov_uuid" % tablename))
    table.gov_uuid.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Government UID") + "|" + Tstr("The Unique Identifier (UUID) as assigned to this facility by the government.")))

    table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
    table.email.requires = IS_NULL_OR(IS_EMAIL())
    table.total_beds.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.total_beds.readable = False
    table.total_beds.writable = False
    table.available_beds.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.available_beds.readable = False
    table.available_beds.writable = False
    table.morgue_units.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.doctors.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.nurses.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.non_medical_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))

    # Reusable field for other tables to reference
    ADD_HOSPITAL = T("Add Hospital")
    hospital_id = db.Table(None, "hospital_id",
                        FieldS3("hospital_id", db.hms_hospital, sortby="name",
                                requires = IS_NULL_OR(IS_ONE_OF(db, "hms_hospital.id", "%(name)s")),
                                represent = lambda id: (id and
                                            [db(db.hms_hospital.id == id).select(db.hms_hospital.name, limitby=(0, 1)).first().name] or
                                            ["None"])[0],
                                label = T("Hospital"),
                                comment = DIV(A(ADD_HOSPITAL,
                                               _class="colorbox",
                                               _href=URL(r=request,
                                                         c="hms",
                                                         f="hospital",
                                                         args="create",
                                                         vars=dict(format="popup")),
                                               _target="top", _title=ADD_HOSPITAL),
                                              DIV(DIV(_class="tooltip",
                                                      _title=Tstr("Hospital") + "|" + Tstr("The hospital this record is associated with.")))),
                                ondelete = "RESTRICT"))

    # -----------------------------------------------------------------------------
    def shn_hms_hospital_rss(record):

        """ Hospital RSS Feed """

        if record:
            lat = lon = T("unknown")
            location_name = T("unknown")
            if record.location_id:
                location = db.gis_location[record.location_id]
                if location:
                    lat = "%.6f" % location.lat
                    lon = "%.6f" % location.lon
                    location_name = location.name
            return "<b>%s</b>: <br/>Location: %s [Lat: %s Lon: %s]<br/>Facility Status: %s<br/>Clinical Status: %s<br/>Morgue Status: %s<br/>Security Status: %s<br/>Beds available: %s" % (
                record.name,
                location_name,
                lat,
                lon,
                db.hms_hospital.facility_status.represent(record.facility_status),
                db.hms_hospital.clinical_status.represent(record.clinical_status),
                db.hms_hospital.morgue_status.represent(record.morgue_status),
                db.hms_hospital.security_status.represent(record.security_status),
                (record.available_beds is not None) and record.available_beds or T("unknown"))
        else:
            return None

    # -----------------------------------------------------------------------------
    def shn_hms_hospital_onvalidation(form):

        if "gov_uuid" in db.hms_hospital.fields and HMS_HOSPITAL_USE_GOVUUID:
            if form.vars.gov_uuid is not None and not str(form.vars.gov_uuid).isspace():
                form.vars.uuid = form.vars.gov_uuid
            else:
                form.vars.gov_uuid = None


    def shn_hms_hospital_onaccept(form, table=None):

        # Update requests
        hospital = db.hms_hospital[form.vars.id]
        if hospital:
            db(db.hms_hrequest.hospital_id == hospital.id).update(city=hospital.city)

        shn_site_onaccept(form, table=table)


    s3xrc.model.configure(table,
                          onvalidation=lambda form: \
                          shn_hms_hospital_onvalidation(form),
                          onaccept=lambda form, tab=table: \
                          shn_hms_hospital_onaccept(form, table=tab),
                          list_fields=["id",
                                       "gov_uuid",
                                       "name",
                                       "organisation_id",
                                       "location_id",
                                       "phone_business",
                                       "ems_status",
                                       "facility_status",
                                       "clinical_status",
                                       "security_status",
                                       "total_beds",
                                       "available_beds"])

    # -----------------------------------------------------------------------------
    # Contacts
    #
    resource = "hcontact"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, deletion_status,
                    hospital_id,
                    person_id,
                    Field("title"),
                    Field("phone"),
                    Field("mobile"),
                    Field("email"),
                    Field("fax"),
                    Field("skype"),
                    Field("website"),
                    migrate=migrate)

    table.person_id.label = T("Contact")
    table.title.label = T("Job Title")
    table.title.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Title") + "|" + Tstr("The Role this person plays within this hospital.")))

    table.phone.label = T("Phone")
    table.phone.requires = shn_phone_requires
    table.mobile.label = T("Mobile")
    table.mobile.requires = shn_phone_requires
    table.email.requires = IS_NULL_OR(IS_EMAIL())
    table.email.label = T("Email")
    table.fax.label = T("Fax")
    table.fax.requires = shn_phone_requires
    table.skype.label = T("Skype ID")

    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"),
                              deletable=True,
                              editable=True,
                              main="person_id", extra="title")

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "person_id",
                                       "title",
                                       "phone",
                                       "mobile",
                                       "email",
                                       "fax",
                                       "skype"])

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Contact"),
        title_display = T("Contact Details"),
        title_list = T("Contacts"),
        title_update = T("Edit Contact"),
        title_search = T("Search Contacts"),
        subtitle_create = T("Add New Contact"),
        subtitle_list = T("Contacts"),
        label_list_button = T("List Contacts"),
        label_create_button = T("Add Contact"),
        msg_record_created = T("Contact information added"),
        msg_record_modified = T("Contact information updated"),
        msg_record_deleted = T("Contact information deleted"),
        msg_list_empty = T("No contacts currently registered"))

    # -----------------------------------------------------------------------------
    # Activity
    #
    resource = "hactivity"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                    hospital_id,
                    Field("date", "datetime"),              # Date&Time the entry applies to
                    Field("patients", "integer"),           # Current Number of Patients
                    Field("admissions24", "integer"),       # Admissions in the past 24 hours
                    Field("discharges24", "integer"),       # Discharges in the past 24 hours
                    Field("deaths24", "integer"),           # Deaths in the past 24 hours
                    Field("comment", length=128),
                    migrate=migrate)

    table.date.label = T("Date & Time")
    table.date.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(),
                                          allow_future=False)
    table.date.represent = lambda value: shn_as_local_time(value)
    table.date.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Date & Time") + "|" + Tstr("Date and time this report relates to.")))

    table.patients.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.patients.default = 0
    table.patients.label = T("Number of Patients")
    table.patients.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Patients") + "|" + Tstr("Number of in-patients at the time of reporting.")))

    table.admissions24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.admissions24.default = 0
    table.admissions24.label = T("Admissions/24hrs")
    table.admissions24.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Admissions/24hrs") + "|" + Tstr("Number of newly admitted patients during the past 24 hours.")))

    table.discharges24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.discharges24.default = 0
    table.discharges24.label = T("Discharges/24hrs")
    table.discharges24.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Discharges/24hrs") + "|" + Tstr("Number of discharged patients during the past 24 hours.")))

    table.deaths24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.deaths24.default = 0
    table.deaths24.label = T("Deaths/24hrs")
    table.deaths24.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Deaths/24hrs") + "|" + Tstr("Number of deaths during the past 24 hours.")))

    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"),
                              deletable=True,
                              editable=False,
                              main="hospital_id", extra="id")

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "date",
                                       "patients",
                                       "admissions24",
                                       "discharges24",
                                       "deaths24",
                                       "comment"])

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Activity Report"),
        title_display = T("Activity Report"),
        title_list = T("Activity Reports"),
        title_update = T("Update Activity Report"),
        title_search = T("Search Activity Report"),
        subtitle_create = T("Add Activity Report"),
        subtitle_list = T("Activity Reports"),
        label_list_button = T("List Reports"),
        label_create_button = T("Add Report"),
        label_delete_button = T("Delete Report"),
        msg_record_created = T("Report added"),
        msg_record_modified = T("Report updated"),
        msg_record_deleted = T("Report deleted"),
        msg_list_empty = T("No reports currently available"))

    # -----------------------------------------------------------------------------
    # Bed Capacity (multiple)
    #
    hms_bed_type_opts = {
        1: T("Adult ICU"),
        2: T("Pediatric ICU"),
        3: T("Neonatal ICU"),
        4: T("Emergency Department"),
        5: T("Nursery Beds"),
        6: T("General Medical/Surgical"),
        7: T("Rehabilitation/Long Term Care"),
        8: T("Burn ICU"),
        9: T("Pediatrics"),
        10: T("Adult Psychiatric"),
        11: T("Pediatric Psychiatric"),
        12: T("Negative Flow Isolation"),
        13: T("Other Isolation"),
        14: T("Operating Rooms"),
        99: T("Other")
    }

    resource = "bed_capacity"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                    hospital_id,
                    Field("unit_name", length=64),
                    Field("bed_type", "integer",
                        requires = IS_IN_SET(hms_bed_type_opts, zero=None),
                        default = 6,
                        label = T("Bed Type"),
                        represent = lambda opt: hms_bed_type_opts.get(opt, UNKNOWN_OPT)),
                    Field("date", "datetime"),
                    Field("beds_baseline", "integer"),
                    Field("beds_available", "integer"),
                    Field("beds_add24", "integer"),
                    Field("comment", length=128),
                    migrate=migrate)

    table.unit_name.label = T("Department/Unit Name")
    table.unit_name.requires = IS_NULL_OR(IS_NOT_IN_DB(db(table.deleted==False), table.unit_name))
    table.unit_name.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Unit Name") + "|" + Tstr("Name of the unit or department this report refers to. Leave empty if your hospital has no subdivisions.")))

    table.bed_type.comment =  DIV(DIV(_class="tooltip",
        _title=Tstr("Bed Type") + "|" + Tstr("Specify the bed type of this unit.")))

    table.date.label = T("Date of Report")
    table.date.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(),
                                          allow_future=False)
    table.date.represent = lambda value: shn_as_local_time(value)

    table.beds_baseline.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.beds_baseline.default = 0
    table.beds_baseline.label = T("Baseline Number of Beds")
    table.beds_available.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.beds_available.default = 0
    table.beds_available.label = T("Available Beds")
    table.beds_add24.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
    table.beds_add24.default = 0
    table.beds_add24.label = T("Additional Beds / 24hrs")

    table.beds_baseline.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Baseline Number of Beds") + "|" + Tstr("Baseline number of beds of that type in this unit.")))
    table.beds_available.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Available Beds") + "|" + Tstr("Number of available/vacant beds of that type in this unit at the time of reporting.")))
    table.beds_add24.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Additional Beds / 24hrs") + "|" + Tstr("Number of additional beds of that type expected to become available in this unit within the next 24 hours.")))

    # -----------------------------------------------------------------------------
    #
    def shn_hms_bedcount_update(form):

        """ updates the number of total/available beds of a hospital """

        if isinstance(form, Row):
            formvars = form
        else:
            formvars = form.vars

        table = db.hms_bed_capacity
        query = ((table.id == formvars.id) &
                 (db.hms_hospital.id == table.hospital_id))
        hospital = db(query).select(db.hms_hospital.id, limitby=(0, 1))

        if hospital:
            hospital = hospital.first()

            a_beds = table.beds_available.sum()
            t_beds = table.beds_baseline.sum()
            query = (table.hospital_id == hospital.id) & (table.deleted == False)
            count = db(query).select(a_beds, t_beds)
            if count:
               a_beds = count[0]._extra[a_beds]
               t_beds = count[0]._extra[t_beds]

            db(db.hms_hospital.id == hospital.id).update(
                total_beds=t_beds,
                available_beds=a_beds)

    # add as component
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"),
                              deletable=True,
                              editable=True,
                              main="hospital_id", extra="id")

    s3xrc.model.configure(table,
                          onaccept = lambda form: \
                                     shn_hms_bedcount_update(form),
                          delete_onaccept = lambda row: \
                                            shn_hms_bedcount_update(row),
                          list_fields=["id",
                                       "unit_name",
                                       "bed_type",
                                       "date",
                                       "beds_baseline",
                                       "beds_available",
                                       "beds_add24"])

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Unit"),
        title_display = T("Unit Bed Capacity"),
        title_list = T("List Units"),
        title_update = T("Update Unit"),
        title_search = T("Search Units"),
        subtitle_create = T("Add Unit"),
        subtitle_list = T("Bed Capacity per Unit"),
        label_list_button = T("List Units"),
        label_create_button = T("Add Unit"),
        label_delete_button = T("Delete Unit"),
        msg_record_created = T("Unit added"),
        msg_record_modified = T("Unit updated"),
        msg_record_deleted = T("Unit deleted"),
        msg_list_empty = T("No units currently registered"))

    # -----------------------------------------------------------------------------
    # Services
    #
    resource = "services"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                    hospital_id,
                    Field("burn", "boolean", default=False),
                    Field("card", "boolean", default=False),
                    Field("dial", "boolean", default=False),
                    Field("emsd", "boolean", default=False),
                    Field("infd", "boolean", default=False),
                    Field("neon", "boolean", default=False),
                    Field("neur", "boolean", default=False),
                    Field("pedi", "boolean", default=False),
                    Field("surg", "boolean", default=False),
                    Field("labs", "boolean", default=False),
                    Field("tran", "boolean", default=False),
                    Field("tair", "boolean", default=False),
                    Field("trac", "boolean", default=False),
                    Field("psya", "boolean", default=False),
                    Field("psyp", "boolean", default=False),
                    Field("obgy", "boolean", default=False),
                    migrate=migrate)

    table.burn.label = T("Burn")
    table.card.label = T("Cardiology")
    table.dial.label = T("Dialysis")
    table.emsd.label = T("Emergency Department")
    table.infd.label = T("Infectious Diseases")
    table.neon.label = T("Neonatology")
    table.neur.label = T("Neurology")
    table.pedi.label = T("Pediatrics")
    table.surg.label = T("Surgery")
    table.labs.label = T("Clinical Laboratory")
    table.tran.label = T("Ambulance Service")
    table.tair.label = T("Air Transport Service")
    table.trac.label = T("Trauma Center")
    table.psya.label = T("Psychiatrics/Adult")
    table.psyp.label = T("Psychiatrics/Pediatric")
    table.obgy.label = T("Obstetrics/Gynecology")

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Service Profile"),
        title_display = T("Services Available"),
        title_list = T("Services Available"),
        title_update = T("Update Service Profile"),
        title_search = T("Search Service Profiles"),
        subtitle_create = T("Add Service Profile"),
        subtitle_list = T("Services Available"),
        label_list_button = T("List Service Profiles"),
        label_create_button = T("Add Service Profile"),
        label_delete_button = T("Delete Service Profile"),
        msg_record_created = T("Service profile added"),
        msg_record_modified = T("Service profile updated"),
        msg_record_deleted = T("Service profile deleted"),
        msg_list_empty = T("No service profile available"))

    s3xrc.model.add_component(module, resource,
                              multiple=False,
                              joinby=dict(hms_hospital="hospital_id"),
                              deletable=True,
                              editable=True,
                              main="hospital_id", extra="id")

    s3xrc.model.configure(table, list_fields = ["id"])

    # -----------------------------------------------------------------------------
    # Images
    #
    hms_image_type_opts = {
        1:T("Photograph"),
        2:T("Map"),
        3:T("Document Scan"),
        99:T("other")
    }

    resource = "himage"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                    hospital_id,
                    #Field("title"),
                    Field("type", "integer",
                        requires = IS_IN_SET(hms_image_type_opts, zero=None),
                        default = 1,
                        label = T("Image Type"),
                        represent = lambda opt: hms_image_type_opts.get(opt, T("not specified"))),
                    Field("image", "upload", autodelete=True),
                    Field("url"),
                    Field("description"),
                    Field("tags"),
                    migrate=migrate)

    # Field validation
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

    table.image.label = T("Image Upload")
    table.image.represent = lambda image: image and \
            DIV(A(IMG(_src=URL(r=request, c="default", f="download", args=image),_height=60, _alt=T("View Image")),
                _href=URL(r=request, c="default", f="download", args=image))) or \
            T("No Image")

    table.url.label = T("URL")
    table.url.represent = lambda url: len(url) and DIV(A(IMG(_src=url, _height=60), _href=url)) or T("None")

    table.tags.label = T("Tags")
    table.tags.comment = DIV(DIV(_class="tooltip",
                            _title=Tstr("Image Tags") + "|" + Tstr("Enter tags separated by commas.")))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Image"),
        title_display = T("Image Details"),
        title_list = T("List Images"),
        title_update = T("Edit Image Details"),
        title_search = T("Search Images"),
        subtitle_create = T("Add New Image"),
        subtitle_list = T("Images"),
        label_list_button = T("List Images"),
        label_create_button = T("Add Image"),
        label_delete_button = T("Delete Image"),
        msg_record_created = T("Image added"),
        msg_record_modified = T("Image updated"),
        msg_record_deleted = T("Image deleted"),
        msg_list_empty = T("No Images currently registered")
    )

    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"),
                              deletable=True,
                              editable=True)

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "type",
                                       "image",
                                       "url",
                                       "description",
                                       "tags"])

    # -----------------------------------------------------------------------------
    # Resources (multiple) - TODO: to be completed!
    #
    resource = "resources"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                    hospital_id,
                    Field("type"),
                    Field("description"),
                    Field("quantity"),
                    Field("comment"),
                    migrate=migrate)

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Report Resource"),
        title_display = T("Resource Details"),
        title_list = T("Resources"),
        title_update = T("Edit Resource"),
        title_search = T("Search Resources"),
        subtitle_create = T("Add New Resource"),
        subtitle_list = T("Resources"),
        label_list_button = T("List Resources"),
        label_create_button = T("Add Resource"),
        label_delete_button = T("Delete Resource"),
        msg_record_created = T("Resource added"),
        msg_record_modified = T("Resource updated"),
        msg_record_deleted = T("Resource deleted"),
        msg_list_empty = T("No resources currently reported"))

    # Add as component
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(hms_hospital="hospital_id"),
                              deletable=True,
                              editable=True,
                              main="hospital_id", extra="id")

    s3xrc.model.configure(table, list_fields = ["id"])

    # -----------------------------------------------------------------------------
    # Hospital Search by Name
    #
    def shn_hms_hospital_search_simple(r, **attr):

        """ Simple search form for hospitals """

        resource = r.resource
        table = resource.table

        r.id = None

        # Check permission
        if not shn_has_permission("read", table):
            r.unauthorised()

        if r.representation == "html":

            # Check for redirection
            next = r.request.vars.get("_next", None)
            if not next:
                next = URL(r=request, f="hospital", args="[id]")

            # Select form
            form = FORM(TABLE(
                    TR(Tstr("Name and/or ID Label" + ": "),
                    INPUT(_type="text", _name="label", _size="40"),
                    DIV(DIV(_class="tooltip",
                            _title=Tstr("Name") + "|" + Tstr("To search for a hospital, enter any part of the name or ID. You may use % as wildcard. Press 'Search' without input to list all hospitals.")))),
                    TR("", INPUT(_type="submit", _value="Search"))))

            output = dict(form=form, vars=form.vars)

            # Accept action
            items = None
            if form.accepts(request.vars, session, keepvalues=True):

                if form.vars.label == "":
                    form.vars.label = "%"

                # Search
                results = s3xrc.search_simple(table,
                            fields = ["gov_uuid", "name", "aka1", "aka2"],
                            label = form.vars.label)

                # Get the results
                if results:
                    resource.build_query(id=results)
                    report = shn_list(r, listadd=False)
                else:
                    report = dict(items=T("No matching records found."))

                output.update(dict(report))

            # Title and subtitle
            title = T("Search for a Hospital")
            subtitle = T("Matching Records")

            # Add-button
            label_create_button = shn_get_crud_string("hms_hospital", "label_create_button")
            add_btn = A(label_create_button, _class="action-btn",
                        _href=URL(r=request, f="hospital", args="create"))

            output.update(title=title, subtitle=subtitle, add_btn=add_btn)
            response.view = "search_simple.html"
            return output

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Plug into REST controller
    s3xrc.model.set_method(module, "hospital", method="search_simple", action=shn_hms_hospital_search_simple )


    # -----------------------------------------------------------------------------
    # Hospital Requests for Support
    #
    hms_hrequest_priority_opts = {
        5: T("immediately"),
        4: T("urgent"),
        3: T("high"),
        2: T("normal"),
        1: T("low")
    }

    hms_hrequest_impact_opts = {
        5: T("highly critical"),
        4: T("critical"),
        3: T("non-critical"),
        2: T("improvement"),
        1: T("wish")
    }

    hms_hrequest_status_opts = {
        6: T("completed"),              # Completed
        5: T("invalid"),                # Invalid request
        4: T("accepted"),               # Accepted request
        3: T("deferred"),               # Deferred
        2: T("review"),                 # For further review
        1: T("new")                     # New
    }

    hms_hrequest_type_opts = {
        1: T("Water"),
        2: T("Electricity"),
        3: T("Food"),
        4: T("Medical Supplies"),
        5: T("Medical Staff"),
        6: T("Non-medical Staff"),
        7: T("Security"),
        8: T("Transport"),
        9: T("Fuel"),
        10:T("Shelter"),
        11:T("Find"),
        12:T("Report"),
        99: T("Other")
    }

    hms_hrequest_source_type = {
        1 : "Manual",
        2 : "Voice",
        3 : "E-Mail",
        4 : "SMS",
        99: "Other"
    }

    resource = "hrequest"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                hospital_id,
                Field("subject"),
                Field("message", "text"),
                Field("timestmp", "datetime"),  # 'timestamp' is a reserved word in Postgres
                Field("type", "integer",
                    requires = IS_NULL_OR(IS_IN_SET(hms_hrequest_type_opts)),
                    represent = lambda type: hms_hrequest_type_opts.get(type, T("not specified")),
                    label = T("Type")),
                Field("priority", "integer",
                    requires = IS_NULL_OR(IS_IN_SET(hms_hrequest_priority_opts)),
                    default = 2,
                    represent = lambda opt: hms_hrequest_priority_opts.get(opt, T("not specified")),
                    #represent = lambda id: (id and
                    #  [DIV(IMG(_src="/%s/static/img/priority/hms_priority_%d.gif" % \
                    #      (request.application, id), _height=12))] or
                    #  [DIV(IMG(_src="/%s/static/img/priority/hms_priority_1.gif" % \
                    #      request.application, _height=12))]),
                    label = T("Priority")),
                Field("city", "string"),
                Field("status", "integer",
                    requires = IS_NULL_OR(IS_IN_SET(hms_hrequest_status_opts)),
                    represent = lambda type: hms_hrequest_status_opts.get(type, T("not specified")),
                    label = T("Status")),
                Field("source_type", "integer",
                    requires = IS_NULL_OR(IS_IN_SET(hms_hrequest_source_type)),
                    represent = lambda stype: stype and hms_hrequest_source_type[stype],
                    label = T("Source Type")),
                Field("actionable", "boolean", default=False),
                migrate=migrate)

    #label the fields for the view
    table.timestmp.label = T("Date & Time")

    #Hide fields from user:
    table.actionable.writable = table.actionable.readable = False
    table.source_type.writable = table.source_type.readable = False

    #set default values
    table.actionable.default = 1
    table.source_type.default = 1

    table.message.requires = IS_NOT_EMPTY()
    table.message.comment = SPAN("*", _class="req")

    s3.crud_strings[tablename] = Storage(
        title_create        = "Add Aid Request",
        title_display       = "Aid Request Details",
        title_list          = "List Aid Requests",
        title_update        = "Edit Aid Request",
        title_search        = "Search Aid Requests",
        subtitle_create     = "Add New Aid Request",
        subtitle_list       = "Aid Requests",
        label_list_button   = "List Aid Requests",
        label_create_button = "Add Aid Request",
        msg_record_created  = "Aid request added",
        msg_record_modified = "Aid request updated",
        msg_record_deleted  = "Aid request deleted",
        msg_list_empty      = "No aid requests currently available")

    # Reusable field for other tables to reference
    hms_hrequest_id = db.Table(None, "hms_hrequest_id",
                        Field("hms_hrequest_id", db.hms_hrequest,
                                requires = IS_NULL_OR(IS_ONE_OF(db, "hms_hrequest.id", "%(id)s")),
                                represent = lambda id: (id and [db(db.hms_hrequest.id==id).select()[0].id] or ["None"])[0],
                                label = T("Request"),
                                comment = DIV(A(s3.crud_strings[tablename].title_create,
                                               _class="colorbox",
                                               _href=URL(r=request, c="hms", f="hrequest", args="create", vars=dict(format="popup")),
                                               _target="top",
                                               _title=s3.crud_strings[tablename].title_create),
                                              DIV(DIV(_class="tooltip",
                                                      _title=Tstr("Request") + "|" + Tstr("The request this record is associated with.")))),
                                ondelete = "RESTRICT"))

    s3xrc.model.add_component(module, resource,
        multiple=True,
        joinby=dict(hms_hospital = "hospital_id"),
        deletable=True,
        editable=True)

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "timestmp",
                                       "hospital_id",
                                       "city",
                                       "type",
                                       "subject",
                                       "priority",
                                       "status"])

    # -----------------------------------------------------------------------------
    # Request Representation
    #
    def shn_hms_hrequest_onaccept(form):

        hrequest = db.hms_hrequest[form.vars.id]
        if hrequest:
            hospital = db.hms_hospital[hrequest.hospital_id]
            if hospital:
                db(db.hms_hrequest.id == hrequest.id).update(city=hospital.city)

    s3xrc.model.configure(db.hms_hrequest,
                          onaccept=lambda form: shn_hms_hrequest_onaccept(form))

    # -----------------------------------------------------------------------------
    # Request Search by Message Text
    #
    def shn_hms_get_hrequest(label, fields=None, filterby=None):

        """ Finds a request by Message string """

        if fields and isinstance(fields, (list,tuple)):
            search_fields = []
            for f in fields:
                if db.hms_hrequest.has_key(f):     # TODO: check for field type?
                    search_fields.append(f)
            if not len(search_fields):
                # Error: none of the specified search fields exists
                return None
        else:
            # No search fields specified at all => fallback
            search_fields = ["message"]

        if label and isinstance(label, str):
            labels = label.split()
            results = []
            query = None
            # TODO: make a more sophisticated search function (levenshtein?)
            for l in labels:

                # append wildcards
                wc = "%"
                _l = "%s%s%s" % (wc, l, wc)

                # build query
                for f in search_fields:
                    if query:
                        query = (db.hms_hrequest[f].like(_l)) | query
                    else:
                        query = (db.hms_hrequest[f].like(_l))

                # undeleted records only
                query = (db.hms_hrequest.deleted==False) & (query)
                # restrict to prior results (AND)
                if len(results):
                    query = (db.hms_hrequest.id.belongs(results)) & query
                if filterby:
                    query = (filterby) & (query)
                records = db(query).select(db.hms_hrequest.id)
                # rebuild result list
                results = [r.id for r in records]
                # any results left?
                if not len(results):
                    return None
            return results
        else:
            # no label given or wrong parameter type
            return None

    # -----------------------------------------------------------------------------
    # Request Search Form
    #
    def shn_hms_hrequest_search_simple(xrequest, **attr):

        """ Simple search form for requests """

        if attr is None:
            attr = {}

        if not shn_has_permission("read", db.hms_hrequest):
            session.error = UNAUTHORISED
            redirect(URL(r=request, c="default", f="user", args="login", vars={"_next":URL(r=request, args="search_simple", vars=request.vars)}))

        if xrequest.representation=="html":
            # Check for redirection
            if request.vars._next:
                next = str.lower(request.vars._next)
            else:
                next = str.lower(URL(r=request, f="req", args="[id]"))

            # Custom view
            response.view = "%s/hrequest_search.html" % xrequest.prefix

            # Title and subtitle
            title = T("Search for a Request")
            subtitle = T("Matching Records")

            # Select form
            form = FORM(TABLE(
                    TR(T("Text in Message: "),
                    INPUT(_type="text", _name="label", _size="40"),
                    DIV(DIV(_class="tooltip",
                            _title=Tstr("Text in Message") + "|" + Tstr("To search for a request, enter some of the text that you are looking for. You may use % as wildcard. Press 'Search' without input to list all requests.")))),
                    TR("", INPUT(_type="submit", _value="Search"))))

            output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

            # Accept action
            items = None
            if form.accepts(request.vars, session):

                if form.vars.label == "":
                    form.vars.label = "%"

                results = shn_hms_get_hrequest(form.vars.label)

                if results and len(results):
                    rows = db(db.hms_hrequest.id.belongs(results)).select()
                else:
                    rows = None

                # Build table rows from matching records
                if rows:
                    records = []
                    for row in rows:
                        href = next.replace("%5bid%5d", "%s" % row.id)
                        records.append(TR(
                            row.completion_status,
                            row.message,
                            row.timestmp,
                            row.hospital_id and hospital_id.hospital_id.represent(row.hospital_id) or "unknown",
                            ))
                    items=DIV(TABLE(THEAD(TR(
                        TH("Completion Status"),
                        TH("Message"),
                        TH("Time"),
                        TH("Hospital"),
                        )),
                        TBODY(records), _id="list", _class="display"))
                else:
                    items = T("None")

            try:
                label_create_button = s3.crud_strings["hms_hrequest"].label_create_button
            except:
                label_create_button = s3.crud_strings.label_create_button

            add_btn = A(label_create_button, _href=URL(r=request, f="req", args="create"), _class="action-btn")

            output.update(dict(items=items, add_btn=add_btn))
            return output

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Plug into REST controller
    s3xrc.model.set_method(module, resource,
                        method="search_simple",
                        action=shn_hms_hrequest_search_simple)

    # -----------------------------------------------------------------------------
    # Pledges
    #
    hms_pledge_status_opts = {
        1:T("Pledged"),
        2:T("In Transit"),
        3:T("Delivered"),
    }

    resource = "hpledge"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                    Field("submitted_on", "datetime"),
                    hms_hrequest_id,
                    Field("status", "integer"),
                    organisation_id,
                    person_id,
                    Field("description"),
                    migrate=migrate)

    # hide unnecessary fields
    table.hms_hrequest_id.writable = False

    # set pledge default
    table.status.default = 1

    # auto fill posted_on field and make it readonly
    table.submitted_on.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(),
                                                  allow_future=False)
    table.submitted_on.represent = lambda value: shn_as_local_time(value)
    table.submitted_on.default = request.utcnow
    table.submitted_on.writable = False

    table.status.requires = IS_IN_SET(hms_pledge_status_opts, zero=None)
    table.status.represent = lambda status: status and hms_pledge_status_opts[status]
    table.status.label = T("Status")

    # Pledges as a component of requests
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(hms_hrequest = "hms_hrequest_id"),
                              deletable=True,
                              editable=True)

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       #"organisation_id",
                                       #"person_id",
                                       "submitted_on",
                                       "description",
                                       "status"])

    s3.crud_strings[tablename] = Storage(
        title_create = "Add Pledge",
        title_display = "Pledge Details",
        title_list = "List Pledges",
        title_update = "Edit Pledge",
        title_search = "Search Pledges",
        subtitle_create = "Add New Pledge",
        subtitle_list = "Pledges",
        label_list_button = "List Pledges",
        label_create_button = "Add Pledge",
        label_delete_button = "Delete Pledge",
        msg_record_created = "Pledge added",
        msg_record_modified = "Pledge updated",
        msg_record_deleted = "Pledge deleted",
        msg_list_empty = "No Pledges currently available")

    # -----------------------------------------------------------------------------
