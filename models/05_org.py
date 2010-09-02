# -*- coding: utf-8 -*-

"""
    Organisation Registry
"""

module = "org"

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
# Site
# 
# Site is a generic type for any facility (office, hospital, shelter,
# warehouse, etc.) and serves the same purpose as pentity does for person
# entity types:  It provides a common join key name across all types of
# sites, with a unique value for each sites.  This allows other types that
# are useful to any sort of site to have a common way to join to any of
# them.  It's especially useful for component types.
#
# This is currently being added so people can discuss it, and to get
# inventories quickly associated with shelters without adding shelter_id
# to inventory_store, or attempting to join on location_id.  It is in
# org because that's relatively generic and has one of the site types.
# You'll note that it is a slavish copy of pentity with the names changed.

org_site_types = Storage(
    cr_shelter = T("Shelter"),
    org_office = T("Office"),
    hms_hospital = T("Hospital"),
)

resource = "site"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, deletion_status,
                        Field("site_type"),
                        Field("uuid", length=128),
                        Field("site_id", "integer"),
                        migrate=migrate)

table.site_type.writable = False
table.site_type.represent = lambda opt: org_site_types.get(opt, opt)
table.uuid.writable = False

def shn_site_represent(id, default_label="[no label]"):

    """
        Represent a site in option fields or list views
    """

    site_str = T("None (no such record)")

    site_table = db.org_site
    site = db(site_table.id == id).select(site_table.site_type,
                                          limitby=(0, 1)).first()
    if not site:
        return site_str

    site_type = site.site_type
    site_type_nice = site_table.site_type.represent(site_type)

    table = db.get(site_type, None)
    if not table:
        return site_str

    # All the current types of sites have a required "name" field that can
    # serve as their representation.
    record = db(table.site_id == id).select(table.name, limitby=(0, 1)).first()

    if record:
        site_str = "%s (%s)" % (record.name, site_type_nice) 
    else:
        # Since name is notnull for all types so far, this won't be reached.
        site_str = "[site %d] (%s)" % (id, site_type_nice)

    return site_str

def shn_site_ondelete(record):

    uid = record.get("uuid", None)

    if uid:

        site_table = db.org_site
        db(site_table.uuid == uid).update(deleted=True)

    return True

def shn_site_onaccept(form, table=None):

    if "uuid" not in table.fields or "id" not in form.vars:
        return False

    id = form.vars.id

    fields = [table.id, table.uuid]
    record = db(table.id == id).select(limitby=(0, 1), *fields).first()

    if record:

        site_table = db.org_site
        uid = record.uuid

        site = db(site_table.uuid == uid).select(site_table.id, limitby=(0, 1)).first()
        if site:
            values = dict(site_id = site.id)
            db(site_table.uuid == uid).update(**values)
        else:
            site_type = table._tablename
            site_id = site_table.insert(uuid=uid, site_type=site_type)
            db(site_table.id == site_id).update(site_id=site_id, deleted=False)
            db(table.id == id).update(site_id=site_id)

        return True

    else:
        return False

site_id = db.Table(None, "site_id",
    Field("site_id", db.org_site,
          requires = IS_NULL_OR(IS_ONE_OF(db, "org_site.id", shn_site_represent)),
          represent = lambda id: (id and [shn_site_represent(id)] or [NONE])[0],
          readable = False,
          writable = False,
          ondelete = "RESTRICT"))

# -----------------------------------------------------------------------------
# Sectors (to be renamed as Clusters)
#
resource = "sector"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                migrate=migrate)

# Field settings
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")

# Functions
def shn_sector_represent(sector_ids):
    if not sector_ids:
        return NONE
    elif "|" in str(sector_ids):
        sectors = [db(db.org_sector.id == id).select(db.org_sector.name, limitby=(0, 1)).first().name for id in sector_ids.split("|") if id]
        return ", ".join(sectors)
    else:
        return db(db.org_sector.id == sector_ids).select(db.org_sector.name, limitby=(0, 1)).first().name

# Reusable field
ADD_SECTOR = T("Add Cluster")
sector_id = db.Table(None, "sector_id",
                     FieldS3("sector_id", sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "org_sector.id", "%(name)s", multiple=True)),
                           represent = shn_sector_represent,
                           label = T("Sector"),
                           comment = DIV(A(ADD_SECTOR, _class="colorbox", _href=URL(r=request, c="org", f="sector", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SECTOR),
                                     DIV( _class="tooltip", _title=Tstr("Add Sector") + "|" + Tstr("The Sector(s) this organization works in. Multiple values can be selected by holding down the 'Control' key."))),
                           ondelete = "RESTRICT",
                           # Doesn't re-populate on edit (FF 3.6.8)
                           #widget = SQLFORM.widgets.checkboxes.widget
                          ))

# -----------------------------------------------------------------------------
# Organizations
#
org_organisation_type_opts = {
    1:T("Government"),
    2:T("Embassy"),
    3:T("International NGO"),
    4:T("Donor"),               # Don't change this number without changing organisation_popup.html
    6:T("National NGO"),
    7:"UN",
    8:T("International Organization"),
    9:T("Military"),
    10:T("Private")
    #12:"MINUSTAH"   Haiti-specific
}

resource = "organisation"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                        pe_id,
                        #Field("privacy", "integer", default=0),
                        #Field("archived", "boolean", default=False),
                        Field("name", length=128, notnull=True, unique=True),
                        Field("acronym", length=8),
                        Field("type", "integer"),
                        sector_id,
                        #Field("registration", label=T("Registration")),    # Registration Number
                        Field("country", "string", length=2),
                        Field("website"),
                        Field("twitter"),   # deprecated by pe_contact component
                        Field("donation_phone"),
                        comments,
                        source_id,
                        migrate=migrate)

# Field settings
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_organisation_type_opts))
table.type.represent = lambda opt: org_organisation_type_opts.get(opt, UNKNOWN_OPT)
table.country.requires = IS_NULL_OR(IS_IN_SET(shn_list_of_nations, sort=True))
table.country.represent = lambda opt: shn_list_of_nations.get(opt, UNKNOWN_OPT)
table.website.requires = IS_NULL_OR(IS_URL())
table.donation_phone.requires = shn_phone_requires
table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")
table.acronym.label = T("Acronym")
table.type.label = T("Type")
table.donation_phone.label = T("Donation Phone #")
table.donation_phone.comment = DIV( _class="tooltip", _title=Tstr("Donation Phone #") + "|" + Tstr("Phone number to donate to this organization's relief efforts."))
table.country.label = T("Home Country")
table.website.label = T("Website")
# Should be visible to the Dashboard
table.website.represent = shn_url_represent
table.twitter.label = T("Twitter")
table.twitter.comment = DIV( _class="tooltip", _title=Tstr("Twitter") + "|" + Tstr("Twitter ID or #hashtag"))
# CRUD strings
ADD_ORGANIZATION = Tstr("Add Organization")
LIST_ORGANIZATIONS = T("List Organizations")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_ORGANIZATION,
    title_display = T("Organization Details"),
    title_list = LIST_ORGANIZATIONS,
    title_update = T("Edit Organization"),
    title_search = T("Search Organizations"),
    subtitle_create = T("Add New Organization"),
    subtitle_list = T("Organizations"),
    label_list_button = LIST_ORGANIZATIONS,
    label_create_button = ADD_ORGANIZATION,
    label_delete_button = T("Delete Organization"),
    msg_record_created = T("Organization added"),
    msg_record_modified = T("Organization updated"),
    msg_record_deleted = T("Organization deleted"),
    msg_list_empty = T("No Organizations currently registered"))

# Reusable field
def shn_organisation_represent(id):
    row = db(db.org_organisation.id == id).select(db.org_organisation.name,
                                                  db.org_organisation.acronym,
                                                  limitby = (0, 1)).first()
    if row:
        organisation_represent = row.name
        if row.acronym:
            organisation_represent = organisation_represent + " (" + row.acronym + ")"
    else:
        organisation_represent = "-"

    return organisation_represent

organisation_popup_url = URL(r=request, c="org", f="organisation", args="create", vars=dict(format="popup"))

shn_organisation_comment = DIV(A(ADD_ORGANIZATION,
                           _class="colorbox",
                           _href=organisation_popup_url,
                           _target="top",
                           _title=ADD_ORGANIZATION),
                         DIV(DIV(_class="tooltip",
                                 _title=ADD_ORGANIZATION + "|" + Tstr("The Organization this record is associated with."))))

organisation_id = db.Table(None, "organisation_id",
                           FieldS3("organisation_id", db.org_organisation, sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id", shn_organisation_represent, sort=True)),
                           represent = shn_organisation_represent,
                           label = T("Organization"),
                           comment = shn_organisation_comment,
                           ondelete = "RESTRICT"
                          ))

#@TODO Replace Function with Class
def get_organisation_id(name = "organisation_id",
                         label = T("Organization"),
                         add_label = ADD_ORGANIZATION,
                         help_str = Tstr("The Organization this record is associated with."),
                         ):
    return db.Table(None, 
                    name,
                    FieldS3(name, db.org_organisation, sortby="name",
                            requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id", shn_organisation_represent, sort=True)),
                            represent = shn_organisation_represent,
                            label = label,
                            comment = DIV(A(add_label,
                                            _class="colorbox",
                                            _href=organisation_popup_url,
                                            _target="top",
                                            _title=add_label),
                                          DIV(DIV(_class="tooltip",
                                                  _title=add_label + "|" + help_str
                                                  )
                                              )
                                          ),
                            ondelete = "RESTRICT"
                            )
                    )

# Orgs as component of Clusters
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_sector="sector_id"),
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
                      # Ensure that table is substituted when lambda defined not evaluated by using the default value
                      onaccept=lambda form, tab=table: shn_pentity_onaccept(form, table=tab),
                      delete_onaccept=lambda form: shn_pentity_ondelete(form),
                      list_fields = ["id",
                                     "name",
                                     "acronym",
                                     "type",
                                     "country",
                                     "website"])

# -----------------------------------------------------------------------------
# Offices
#
org_office_type_opts = {
    1:T("Satellite Office"),
    2:T("Country"),
    3:T("Regional"),
    4:T("Headquarters")
}

resource = "office"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                        pe_id,
                        site_id,
                        Field("name", notnull=True),
                        organisation_id,
                        Field("type", "integer"),
                        location_id,
                        Field("parent", "reference org_office"),   # This form of hierarchy may not work on all Databases
                        Field("address", "text"),
                        Field("postcode"),
                        Field("phone1"),
                        Field("phone2"),
                        Field("email"),
                        Field("fax"),
                        Field("national_staff", "integer"),
                        Field("international_staff", "integer"),
                        Field("number_of_vehicles", "integer"),
                        Field("vehicle_types"),
                        Field("equipment"),
                        source_id,
                        comments,
                        migrate=migrate)

# Field settings
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
#db[table].name.requires = IS_NOT_EMPTY()   # Office names don't have to be unique
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.type.requires = IS_NULL_OR(IS_IN_SET(org_office_type_opts))
table.type.represent = lambda opt: org_office_type_opts.get(opt, UNKNOWN_OPT)
table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s"))
table.parent.represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name, limitby=(0, 1)).first().name] or [NONE])[0]
table.phone1.requires = shn_phone_requires
table.phone2.requires = shn_phone_requires
table.fax.requires = shn_phone_requires
table.email.requires = IS_NULL_OR(IS_EMAIL())
table.national_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
table.international_staff.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
table.number_of_vehicles.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")
table.parent.label = T("Parent")
table.type.label = T("Type")
table.address.label = T("Address")
table.postcode.label = T("Postcode")
table.phone1.label = T("Phone 1")
table.phone2.label = T("Phone 2")
table.email.label = T("Email")
table.fax.label = T("Fax")
table.national_staff.label = T("National Staff")
table.international_staff.label = T("International Staff")
table.number_of_vehicles.label = T("Number of Vehicles")
table.vehicle_types.label = T("Vehicle Types")
table.equipment.label = T("Equipment")
# CRUD strings
ADD_OFFICE = Tstr("Add Office")
LIST_OFFICES = T("List Offices")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_OFFICE,
    title_display = T("Office Details"),
    title_list = LIST_OFFICES,
    title_update = T("Edit Office"),
    title_search = T("Search Offices"),
    subtitle_create = T("Add New Office"),
    subtitle_list = T("Offices"),
    label_list_button = LIST_OFFICES,
    label_create_button = ADD_OFFICE,
    label_delete_button = T("Delete Office"),
    msg_record_created = T("Office added"),
    msg_record_modified = T("Office updated"),
    msg_record_deleted = T("Office deleted"),
    msg_list_empty = T("No Offices currently registered"))

# Reusable field for other tables to reference
office_id = db.Table(None, "office_id",
            FieldS3("office_id", db.org_office, sortby="default/indexname",
                requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s")),
                represent = lambda id: (id and [db(db.org_office.id == id).select(db.org_office.name, limitby=(0, 1)).first().name] or [NONE])[0],
                label = T("Office"),
                comment = DIV(A(ADD_OFFICE, _class="colorbox", _href=URL(r=request, c="org", f="office", args="create", vars=dict(format="popup")), _target="top", _title=ADD_OFFICE),
                          DIV( _class="tooltip", _title=ADD_OFFICE + "|" + Tstr("The Office this record is associated with."))),
                ondelete = "RESTRICT"
                ))

# Offices as component of Orgs & Locations
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_organisation="organisation_id", gis_location="location_id"),
                          deletable=True,
                          editable=True)

# Office is a member of two superentities, so has to call both of their
# onaccept and ondelete methods.

def shn_office_onaccept(form, table=None):
    shn_pentity_onaccept(form, table=table)
    shn_site_onaccept(form, table=table)

def shn_office_ondelete(form):
    shn_pentity_ondelete(form)
    shn_site_ondelete(form)

s3xrc.model.configure(table,
                      # Ensure that table is substituted when lambda defined not evaluated by using the default value
                      onaccept=lambda form, tab=table: shn_office_onaccept(form, table=tab),
                      delete_onaccept=lambda form: shn_office_ondelete(form),
                      list_fields=["id",
                                   "name",
                                   "organisation_id",   # Filtered in Component views
                                   "location_id",
                                   "phone1",
                                   "email"])

# Donors are a type of Organisation
def shn_donor_represent(donor_ids):
    if not donor_ids:
        return NONE
    elif "|" in str(donor_ids):
        donors = [db(db.org_organisation.id == id).select(db.org_organisation.name, limitby=(0, 1)).first().name for id in donor_ids.split("|") if id]
        return ", ".join(donors)
    else:
        return db(db.org_organisation.id == donor_ids).select(db.org_organisation.name, limitby=(0, 1)).first().name

ADD_DONOR = Tstr("Add Donor")
donor_id = db.Table(None, "donor_id",
                    FieldS3("donor_id", sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id", "%(name)s", multiple=True, filterby="type", filter_opts=[4])),
                    represent = shn_donor_represent,
                    label = T("Donor"),
                    comment = DIV(A(ADD_DONOR, _class="colorbox", _href=URL(r=request, c="org", f="organisation", args="create", vars=dict(format="popup", child="donor_id")), _target="top", _title=ADD_DONOR),
                              DIV( _class="tooltip", _title=ADD_DONOR + "|" + Tstr("The Donor(s) for this project. Multiple values can be selected by holding down the 'Control' key."))),
                    ondelete = "RESTRICT"
                   ))

# -----------------------------------------------------------------------------
# Projects:
#   the projects which each organization is engaged in
#
org_project_status_opts = {
    1: T('active'),
    2: T('completed'),
    99: T('inactive')
    }
resource = "project"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                        Field("code"),
                        Field("name"),
                        organisation_id,
                        location_id,
                        sector_id,
                        Field('status', 'integer',
                                requires = IS_IN_SET(org_project_status_opts, zero=None),
                                # default = 99,
                                label = T('Project Status'),
                                represent = lambda opt: org_project_status_opts.get(opt, UNKNOWN_OPT)),
                        Field("description", "text"),
                        Field("beneficiaries", "integer"),
                        Field("start_date", "date"),
                        Field("end_date", "date"),
                        Field("funded", "boolean"),
                        donor_id,
                        Field("budgeted_cost", "double"),
                        migrate=migrate)

# Field settings
table.code.requires = [IS_NOT_EMPTY(error_message=T("Please fill this!")),
                         IS_NOT_IN_DB(db, "org_project.code")]
table.start_date.requires = IS_NULL_OR(IS_DATE())
table.end_date.requires = IS_NULL_OR(IS_DATE())
table.budgeted_cost.requires = IS_NULL_OR(IS_FLOAT_IN_RANGE(0, 999999999))

# Project Resource called from multiple controllers
# - so we define strings in the model
table.code.label = T("Code")
table.code.comment = SPAN("*", _class="req")
table.name.label = T("Title")
table.start_date.label = T("Start date")
table.end_date.label = T("End date")
table.description.label = T("Description")
#table.description.comment = SPAN("*", _class="req")
table.status.label = T("Status")
table.status.comment = SPAN("*", _class="req")

ADD_PROJECT = Tstr("Add Project")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_PROJECT,
    title_display = T("Project Details"),
    title_list = T("List Projects"),
    title_update = T("Edit Project"),
    title_search = T("Search Projects"),
    subtitle_create = T("Add New Project"),
    subtitle_list = T("Projects"),
    label_list_button = T("List Projects"),
    label_create_button = ADD_PROJECT,
    label_delete_button = T("Delete Project"),
    msg_record_created = T("Project added"),
    msg_record_modified = T("Project updated"),
    msg_record_deleted = T("Project deleted"),
    msg_list_empty = T("No Projects currently registered"))

# Reusable field
project_id = db.Table(None, "project_id",
                        FieldS3("project_id", db.org_project, sortby="name",
                        requires = IS_NULL_OR(IS_ONE_OF(db, "org_project.id", "%(code)s")),
                        represent = lambda id: (id and [db.org_project[id].code] or [NONE])[0],
                        comment = DIV(A(ADD_PROJECT, _class="colorbox", _href=URL(r=request, c="org", f="project", args="create", vars=dict(format="popup")), _target="top", _title=ADD_PROJECT),
                                  DIV( _class="tooltip", _title=ADD_PROJECT + "|" + Tstr("Add new project."))),
                        label = "Project",
                        ondelete = "RESTRICT"
                        ))

# Projects as component of Orgs & Locations
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_organisation="organisation_id", gis_location="location_id"),
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
                      list_fields=["id",
                                   "organisation_id",
                                   "location_id",
                                   "sector_id",
                                   "code",
                                   "name",
                                   "status",
                                   "start_date",
                                   "end_date",
                                   "budgeted_cost"])

# -----------------------------------------------------------------------------
# Staff
# Many-to-Many Persons to Offices & Projects with also the Title & Manager that the person has in this context
# ToDo: Build an Organigram out of this data?
#
resource = "staff"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                        person_id,
                        organisation_id,
                        office_id,
                        project_id,
                        Field("title"),
                        Field("manager_id", db.pr_person),
                        Field("focal_point", "boolean"),
                        #Field("slots", "integer", default=1),
                        #Field("payrate", "double", default=0.0), # Wait for Bugeting integration
                        comments,
                        migrate=migrate)

# Field settings
# Over-ride the default IS_NULL_OR as Staff doesn't make sense without an associated Organisation
table.organisation_id.requires = IS_ONE_OF(db, "org_organisation.id", "%(name)s")
table.manager_id.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent))
table.manager_id.represent = lambda id: (id and [shn_pr_person_represent(id)] or [NONE])[0]

# Staff Resource called from multiple controllers
# - so we define strings in the model
table.person_id.label = T("Person")
#table.person_id.comment = DIV(SPAN("*", _class="req"), shn_person_id_comment)
table.organisation_id.comment = DIV(SPAN("*", _class="req"), shn_organisation_comment)
table.title.label = T("Job Title")
table.title.comment = DIV( _class="tooltip", _title=Tstr("Title") + "|" + Tstr("The Role this person plays within this Office/Project."))
table.manager_id.label = T("Manager")
table.manager_id.comment = DIV( _class="tooltip", _title=Tstr("Manager") + "|" + Tstr("The person's manager within this Office/Project."))
table.focal_point.comment = DIV( _class="tooltip", _title=Tstr("Focal Point") + "|" + Tstr("The contact person for this organization."))
# CRUD strings
ADD_STAFF = Tstr("Add Staff")
LIST_STAFF = T("List Staff")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_STAFF,
    title_display = T("Staff Details"),
    title_list = LIST_STAFF,
    title_update = T("Edit Staff"),
    title_search = T("Search Staff"),
    subtitle_create = T("Add New Staff"),
    subtitle_list = T("Staff"),
    label_list_button = LIST_STAFF,
    label_create_button = ADD_STAFF,
    msg_record_created = T("Staff added"),
    msg_record_modified = T("Staff updated"),
    msg_record_deleted = T("Staff deleted"),
    msg_list_empty = T("No Staff currently registered"))

# Functions
def represent_focal_point(is_focal_point):
    if is_focal_point:
        return "Focal Point"
    else:
        return "-"

def shn_org_staff_represent(staff_id):
    person = db((db.org_staff.id == staff_id) &
                (db.pr_person.id == db.org_staff.person_id)).select(db.pr_person.first_name, db.pr_person.middle_name, db.pr_person.last_name)
    if person:
        return vita.fullname(person[0])
    else:
        return None

table.focal_point.represent = lambda focal_point: represent_focal_point(focal_point)

def shn_orgs_to_person(person_id):
    orgs = []
    if person_id:
        staff = db((db.org_staff.person_id == person_id) &
                      (db.org_staff.deleted == False)).select(db.org_staff.organisation_id)
        if staff:
            for s in staff:
                orgs.append(s.organisation_id)
    return orgs

# Reusable field
staff_id = db.Table(None, "staff_id",
                        FieldS3("staff_id", db.org_staff, sortby="name",
                        requires = IS_NULL_OR(IS_ONE_OF(db, "org_staff.id", shn_org_staff_represent)),
                        represent = lambda id: shn_org_staff_represent(id),
                        comment = DIV(A(ADD_STAFF, _class="colorbox", _href=URL(r=request, c="org", f="staff", args="create", vars=dict(format="popup")), _target="top", _title=ADD_STAFF),
                                  DIV( _class="tooltip", _title=ADD_STAFF + "|" + Tstr("Add new staff role."))),
                        label = T("Staff"),
                        ondelete = "RESTRICT"
                        ))

# Staff as component of Orgs, Offices & Projects
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(org_organisation="organisation_id", org_office="office_id", org_project="project_id"),
                          deletable=True,
                          editable=True)

# May wish to over-ride this in controllers
s3xrc.model.configure(table,
                      list_fields=["id",
                                   "person_id",
                                   "organisation_id",
                                   "office_id",
                                   "project_id",
                                   "title",
                                   "manager_id",
                                   "focal_point"
                                   #"description",
                                   #"slots",
                                   #"payrate"
                                   ])

# org_position (component of org_project)
#   describes a position in a project
#
# Deprecated - replaced by staff
#
#org_position_type_opts = {
#    1: T("Site Manager"),
#    2: T("Team Leader"),
#    3: T("Assistant"),
#    99: T("Other")
#}
#resource = "position"
#tablename = module + "_" + resource
#table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
#                project_id,
#                Field("type", "integer",
#                    requires = IS_IN_SET(org_position_type_opts, zero=None),
#                    # default = 99,
#                    label = T("Position type"),
#                    represent = lambda opt: org_position_type_opts.get(opt, UNKNOWN_OPT)),
#                Field("title", length=30),
#                Field("description", "text"),
#                Field("slots", "integer", default=1),
#                Field("payrate", "double", default=0.0),
#                #Field("status")?
#                migrate=migrate)

# CRUD Strings
#ADD_POSITION = Tstr("Add Position")
#POSITIONS = T("Positions")
#s3.crud_strings[tablename] = Storage(
#    title_create = ADD_POSITION,
#    title_display = T("Position Details"),
#    title_list = POSITIONS,
#    title_update = T("Edit Position"),
#    title_search = T("Search Positions"),
#    subtitle_create = T("Add New Position"),
#    subtitle_list = POSITIONS,
#    label_list_button = T("List Positions"),
#    label_create_button = ADD_POSITION,
#    msg_record_created = T("Position added"),
#    msg_record_modified = T("Position updated"),
#    msg_record_deleted = T("Position deleted"),
#    msg_list_empty = T("No positions currently registered"))

# Reusable field
#org_position_id = db.Table(None, "org_position_id",
#                        FieldS3("org_position_id", db.org_position, sortby="title",
#                        requires = IS_NULL_OR(IS_ONE_OF(db, "org_position.id", "%(title)s")),
#                        represent = lambda id: lambda id: (id and [db.org_position[id].title] or [NONE])[0],
#                        comment = DIV(A(ADD_POSITION, _class="colorbox", _href=URL(r=request, c="org", f="project", args="create", vars=dict(format="popup")), _target="top", _title=ADD_POSITION),
#                                  DIV( _class="tooltip", _title=ADD_POSITION + "|" + Tstr("Add new position."))),
#                        ondelete = "RESTRICT"
#                        ))

# -----------------------------------------------------------------------------
# org_task:
#   a task within a project
#
org_task_status_opts = {
    1: T("new"),
    2: T("assigned"),
    3: T("completed"),
    4: T("postponed"),
    5: T("feedback"),
    6: T("cancelled"),
    99: T("unspecified")
}

org_task_priority_opts = {
    4: T("normal"),
    1: T("immediately"),
    2: T("urgent"),
    3: T("high"),
    5: T("low")
}

resource = "task"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                        project_id,
                        office_id,
                        Field("priority", "integer",
                            requires = IS_IN_SET(org_task_priority_opts, zero=None),
                            # default = 4,
                            label = T("Priority"),
                            represent = lambda opt: org_task_priority_opts.get(opt, UNKNOWN_OPT)),
                        Field("subject", length=80),
                        Field("description", "text"),
                        person_id,
                        Field("status", "integer",
                            requires = IS_IN_SET(org_task_status_opts, zero=None),
                            # default = 1,
                            label = T("Status"),
                            represent = lambda opt: org_task_status_opts.get(opt, UNKNOWN_OPT)),
                        migrate=migrate)

# Task Resource called from multiple controllers
# - so we define strings in the model
table.person_id.label = T("Assigned to")


def shn_org_task_onvalidation(form):

    """ Task form validation """

    if str(form.vars.status) == "2" and not form.vars.person_id:
        form.errors.person_id = T("Select a person in charge for status 'assigned'")

    return False


# CRUD Strings
ADD_TASK = T("Add Task")
LIST_TASKS = T("List Tasks")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_TASK,
    title_display = T("Task Details"),
    title_list = LIST_TASKS,
    title_update = T("Edit Task"),
    title_search = T("Search Tasks"),
    subtitle_create = T("Add New Task"),
    subtitle_list = T("Tasks"),
    label_list_button = LIST_TASKS,
    label_create_button = ADD_TASK,
    msg_record_created = T("Task added"),
    msg_record_modified = T("Task updated"),
    msg_record_deleted = T("Task deleted"),
    msg_list_empty = T("No tasks currently registered"))

# Task as Component of Project, Office, (Organisation to come? via Project? Can't rely on that as multi-Org projects)
s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(org_project="project_id", org_office="office_id"),
    deletable=True,
    editable=True,
    main="subject", extra="description")

s3xrc.model.configure(table,
                      onvalidation = lambda form: shn_org_task_onvalidation(form),
                      list_fields=["id",
                                   "project_id",
                                   "office_id",
                                   "priority",
                                   "subject",
                                   "person_id",
                                   "status"])

# -----------------------------------------------------------------------------
# shn_project_search_location:
#   form function to search projects by location
#
def shn_project_search_location(xrequest, **attr):

    if attr is None:
        attr = {}

    if not shn_has_permission("read", db.org_project):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c="default", f="user", args="login", vars={"_next":URL(r=request, args="search_location", vars=request.vars)}))

    if xrequest.representation == "html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, c="org", f="project", args="[id]"))

        # Custom view
        response.view = "%s/project_search.html" % xrequest.prefix

        # Title and subtitle
        title = T("Search for a Project")
        subtitle = T("Matching Records")

        # Select form:
        l_opts = [OPTION(_value="")]
        l_opts += [OPTION(location.name, _value=location.id)
                for location in db(db.gis_location.deleted == False).select(db.gis_location.ALL, cache=(cache.ram, 3600))]
        form = FORM(TABLE(
                TR(T("Location: "),
                SELECT(_name="location", *l_opts, **dict(name="location", requires=IS_NULL_OR(IS_IN_DB(db, "gis_location.id"))))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            table = db.org_project
            query = (table.deleted == False)

            if form.vars.location is None:
                results = db(query).select(table.ALL)
            else:
                query = query & (table.location_id == form.vars.location)
                results = db(query).select(table.ALL)

            if results and len(results):
                records = []
                for result in results:
                    href = next.replace("%5bid%5d", "%s" % result.id)
                    records.append(TR(
                        A(result.name, _href=href),
                        result.start_date or NONE,
                        result.end_date or NONE,
                        result.description or NONE,
                        result.status and org_project_status_opts[result.status] or "unknown",
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("ID"),
                    TH("Organization"),
                    TH("Location"),
                    TH("Sector(s)"),
                    TH("Code"),
                    TH("Name"),
                    TH("Status"),
                    TH("Start date"),
                    TH("End date"),
                    TH("Budgeted Cost"))),
                    TBODY(records), _id="list", _class="display"))
            else:
                    items = T(NONE)

        try:
            label_create_button = s3.crud_strings["org_project"].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f="project", args="create"), _class="action-btn")

        output.update(dict(items=items, add_btn=add_btn))

        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, "project", method="search_location", action=shn_project_search_location )

# -----------------------------------------------------------------------------
def shn_project_rheader(jr, tabs=[]):

    if jr.representation == "html":

        rheader_tabs = shn_rheader_tabs(jr, tabs)

        if jr.name == "project":

            _next = jr.here()
            _same = jr.same()

            project = jr.record

            sectors = TABLE()
            if project.sector_id:
                _sectors = re.split("\|", project.sector_id)[1:-1]
                for sector in _sectors:
                    sectors.append(TR(db(db.org_sector.id == sector).select(db.org_sector.name, limitby=(0, 1)).first().name))

            if project:
                rheader = DIV(TABLE(
                    TR(
                        TH(T("Code: ")),
                        project.code,
                        TH(A(T("Clear Selection"),
                            _href=URL(r=request, f="project", args="clear", vars={"_next": _same})))
                        ),
                    TR(
                        TH(T("Name: ")),
                        project.name,
                        TH(T("Location: ")),
                        location_id.location_id.represent(project.location_id),
                        ),
                    TR(
                        TH(T("Status: ")),
                        "%s" % org_project_status_opts[project.status],
                        TH(T("Sector(s): ")),
                        sectors,
                        #TH(A(T("Edit Project"),
                        #    _href=URL(r=request, f="project", args=[jr.id, "update"], vars={"_next": _next})))
                        )
                ), rheader_tabs)
                return rheader

    return None

# -----------------------------------------------------------------------------

org_menu = [
    #[T("Dashboard"), False, URL(r=request, f="dashboard")],
    [T("Organizations"), False, URL(r=request, c="org", f="organisation"),[
        [T("List"), False, URL(r=request, c="org", f="organisation")],
        [T("Add"), False, URL(r=request, c="org", f="organisation", args="create")],
        #[T("Search"), False, URL(r=request, f="organisation", args="search")]
    ]],
    [T("Activities"), False, URL(r=request, c="project", f="activity"),[
        [T("List"), False, URL(r=request, c="project", f="activity")],
        [T("Add"), False, URL(r=request,  c="project", f="activity", args="create")],                                                                         
        #[T("Search"), False, URL(r=request, f="project", args="search")]
    ]],    
    [T("Offices"), False, URL(r=request, c="org", f="office"),[
        [T("List"), False, URL(r=request, c="org", f="office")],
        [T("Add"), False, URL(r=request,  c="org",f="office", args="create")],
        #[T("Search"), False, URL(r=request, f="office", args="search")]
    ]],
    [T("Staff"), False, URL(r=request,  c="org",f="staff"),[
        [T("List"), False, URL(r=request,  c="org",f="staff")],
        [T("Add"), False, URL(r=request,  c="org",f="staff", args="create")],
        #[T("Search"), False, URL(r=request, f="staff", args="search")]
    ]],
    #[T("Tasks"), False, URL(r=request,  c="org",f="task"),[
    #    [T("List"), False, URL(r=request,  c="org",f="task")],
    #    [T("Add"), False, URL(r=request,  c="org",f="task", args="create")],
        #[T("Search"), False, URL(r=request, f="task", args="search")]
    #]],
]
