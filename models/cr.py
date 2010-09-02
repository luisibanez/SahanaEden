# -*- coding: utf-8 -*-

"""
    Camp Registry
"""

module = "cr"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = module + "_" + resource
    table = db.define_table(tablename,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)

    # -------------------------------------------------------------------------
    # Shelter types
    resource = "shelter_type"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field("name",
                          notnull=True,
                          comment = SPAN("*", _class="req")),
                    comments,
                    migrate=migrate)
    
    ADD_SHELTER_TYPE = T("Add Shelter Type")
    LIST_SHELTER_TYPES = T("List Shelter Types")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SHELTER_TYPE,
        title_display = T("Shelter Type Details"),
        title_list = LIST_SHELTER_TYPES,
        title_update = T("Edit Shelter Type"),
        title_search = T("Search Shelter Types"),
        subtitle_create = T("Add New Shelter Type"),
        subtitle_list = T("Shelter Types"),
        label_list_button = LIST_SHELTER_TYPES,
        label_create_button = ADD_SHELTER_TYPE,
        msg_record_created = T("Shelter Type added"),
        msg_record_modified = T("Shelter Type updated"),
        msg_record_deleted = T("Shelter Type deleted"),
        msg_list_empty = T("No Shelter Types currently registered"))

    shelter_type_id = db.Table(None, "shelter_type_id",
                               Field("shelter_type_id", db.cr_shelter_type,
                                     requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter_type.id", "%(name)s")),
                                     represent = lambda id: (id and [db.cr_shelter_type[id].name] or ["None"])[0],
                                     comment = A(ADD_SHELTER_TYPE, _class="colorbox", _href=URL(r=request, c="cr", f="shelter_type", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER_TYPE),
                                     ondelete = "RESTRICT",
                                     label = T("Shelter Type")
                                    )
                              )

    # -------------------------------------------------------------------------
    resource = "shelter_service"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field("name",
                          notnull=True,
                          comment = SPAN("*", _class="req")),
                    comments,
                    migrate=migrate)
    
    ADD_SHELTER_SERVICE = T("Add Shelter Service")
    LIST_SHELTER_SERVICES = T("List Shelter Services")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SHELTER_SERVICE,
        title_display = T("Shelter Service Details"),
        title_list = LIST_SHELTER_SERVICES,
        title_update = T("Edit Shelter Service"),
        title_search = T("Search Shelter Services"),
        subtitle_create = T("Add New Shelter Service"),
        subtitle_list = T("Shelter Services"),
        label_list_button = LIST_SHELTER_SERVICES,
        label_create_button = ADD_SHELTER_SERVICE,
        msg_record_created = T("Shelter Service added"),
        msg_record_modified = T("Shelter Service updated"),
        msg_record_deleted = T("Shelter Service deleted"),
        msg_list_empty = T("No Shelter Services currently registered"))

    def shn_shelter_service_represent(shelter_service_ids):
        if not shelter_service_ids:
            return "None"
        elif "|" in str(shelter_service_ids):
            shelter_services = [db(db.cr_shelter_service.id == id).select(db.cr_shelter_service.name, limitby=(0, 1)).first().name for id in shelter_service_ids.split("|") if id]
            return ", ".join(shelter_services)
        else:
            return db(db.cr_shelter_service.id == shelter_service_ids).select(db.cr_shelter_service.name, limitby=(0, 1)).first().name

    shelter_service_id = db.Table(None, "shelter_service_id",
                                  FieldS3("shelter_service_id", 
                                          requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter_service.id", "%(name)s", multiple=True)),
                                          represent = shn_shelter_service_represent,
                                          comment = A(ADD_SHELTER_SERVICE, _class="colorbox", _href=URL(r=request, c="cr", f="shelter_service", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER_SERVICE),
                                          ondelete = "RESTRICT",
                                          label = T("Shelter Service")
                                         )
                                 )

    # -------------------------------------------------------------------------
    resource = "shelter"
    tablename = module + "_" + resource

    # If the hms module is enabled, we include a hospital_id field, so if the
    # shelter is co-located with a hospital, the hospital can be identified.
    # To get the fields in the correct order in the table, get the fields
    # before and after where hospital_id should go.
    #
    # Caution (mainly for developers):  If you start with hms enabled, and
    # fill in hospital info, then disable hms, the hospital_id column will
    # get dropped.  If hms is re-enabled, the hospital_id links will be gone.
    # Moral is, if this is a production site, do not disable hms unless you
    # really mean it...

    fields_before_hospital = db.Table(None, None,
                    timestamp, uuidstamp, deletion_status,
                    site_id,
                    Field("name", notnull=True),
                    shelter_type_id,
                    shelter_service_id,
                    location_id,
                    Field("phone"),
                    person_id,
                    # Don't show this field -- it will be going away in favor of
                    # location -- but preserve it for converting to a location.
                    # @ToDo This address field is free format.  If we don't
                    # want to try to parse it, could let users convert it to a
                    # location by providing a special (temporary) update form.
                    Field("address", "text", readable=False, writable=False),
                    Field("capacity", "integer"),
                    Field("dwellings", "integer"),
                    Field("persons_per_dwelling", "integer"),
                    Field("area"),
                    document_id,
                    # @Temporary School-specific fields -- school code, PF --
                    # are for Pakistan flood response.  It is simpler
                    # to keep this info in the shelter table and hide it if
                    # the shelter is not a school.
                    Field("school_code", "integer",
                          comment = SPAN("*", _class="req")),
                    Field("school_pf", "integer"),
                    )

    fields_after_hospital = db.Table(None, None, comments)

    # Make a copy of reusable field hospital_id and change its comment to
    # include a *.  # We want it to look required whenever it's visible.
    cr_hospital_id = db.Table(None, "hospital_id", hospital_id)
    comment_with_star = DIV(SPAN("*", _class="req"), 
                            cr_hospital_id.hospital_id.comment)
    cr_hospital_id.hospital_id.comment = comment_with_star


    # Only include hospital_id if the hms module is enabled.
    if deployment_settings.has_module("hms"):
        table = db.define_table(tablename,
                                fields_before_hospital,
                                cr_hospital_id,
                                fields_after_hospital,
                                migrate=migrate)
    else:
        table = db.define_table(tablename,
                                fields_before_hospital,
                                fields_after_hospital,
                                migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    # Shelters don't have to have unique names
    # @ToDo If we want to filter incoming reports automatically to see if
    # they apply to shelters, then we may need to reconsider whether names
    # can be non-unique, *especially* since location is not required.
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Shelter Name")
    table.name.comment = SPAN("*", _class="req")
    table.person_id.label = T("Contact Person")
    table.address.label = T("Address")
    table.capacity.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))
    table.capacity.label = T("Capacity (Max Persons)")
    table.dwellings.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.dwellings.label = T("Dwellings")
    table.persons_per_dwelling.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999))
    table.persons_per_dwelling.label = T("Max Persons per Dwelling")
    table.area.label = T("Area")
    table.school_code.label = T("School Code")
    table.school_pf.label = T("PF Number")
    table.phone.label = T("Phone")
    table.phone.requires = shn_phone_requires

    ADD_SHELTER = T("Add Shelter")
    LIST_SHELTERS = T("List Shelters")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SHELTER,
        title_display = T("Shelter Details"),
        title_list = LIST_SHELTERS,
        title_update = T("Edit Shelter"),
        title_search = T("Search Shelters"),
        subtitle_create = T("Add New Shelter"),
        subtitle_list = T("Shelters"),
        label_list_button = LIST_SHELTERS,
        label_create_button = ADD_SHELTER,
        msg_record_created = T("Shelter added"),
        msg_record_modified = T("Shelter updated"),
        msg_record_deleted = T("Shelter deleted"),
        msg_list_empty = T("No Shelters currently registered"))

    # reusable field
    shelter_id = db.Table(None, "shelter_id",
                          Field("shelter_id", db.cr_shelter,
                                requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter.id", "%(name)s", sort=True)),
                                represent = lambda id: (id and [db.cr_shelter[id].name] or ["None"])[0],
                                ondelete = "RESTRICT",
                                comment = DIV(A(ADD_SHELTER, _class="colorbox", _href=URL(r=request, c="cr", f="shelter", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER),
                                          DIV( _class="tooltip", _title=Tstr("Shelter") + "|" + Tstr("The Shelter this Request is from (optional)."))),
                                label = T("Shelter")
                               )
                         )

    # Add Shelters as component of Services, Types, Locations as a simple way
    # to get reports showing shelters per type, etc.
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(cr_shelter_type="shelter_type_id", 
                                          cr_shelter_service="shelter_service_id", 
                                          gis_location="location_id",
                                          doc_document="document_id"),
                              deletable=True,
                              editable=True,
                              listadd=False)

    s3xrc.model.configure(table,
        onaccept=lambda form: shn_site_onaccept(form, table=db.cr_shelter),
        delete_onaccept=lambda form: shn_site_ondelete(form),
        list_fields=["id",
                     "name",
                     "shelter_type_id",
                     "shelter_service_id",
                     "location_id"])
