# -*- coding: utf-8 -*-

""" MPR Missing Persons Registry

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

module = "mpr"

if deployment_settings.has_module(module):

    #
    # Settings --------------------------------------------------------------------
    #
    resource = 'setting'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field('audit_read', 'boolean'),
                            Field('audit_write', 'boolean'),
                            migrate=migrate)

    # *************************************************************************
    # Missing report
    #
    shn_mpr_reporter_comment = \
        DIV(A(ADD_PERSON,
            _class="colorbox",
            _href=URL(r=request, c="pr", f="person", args="create", vars=dict(format="popup")),
            _target="top",
            _title=ADD_PERSON),
        DIV(DIV(_class="tooltip",
            _title=Tstr("Reporter") + "|" + Tstr("The person reporting about the missing person."))))

    reporter = db.Table(None, "reporter",
                        FieldS3("reporter",
                                db.pr_person,
                                sortby=["first_name", "middle_name", "last_name"],
                                requires = IS_NULL_OR(IS_ONE_OF(db,
                                                "pr_person.id",
                                                shn_pr_person_represent)),
                                represent = lambda id: \
                                            (id and
                                            [shn_pr_person_represent(id)] or
                                            ["None"])[0],
                                comment = shn_mpr_reporter_comment,
                                ondelete = "RESTRICT"))

    # -------------------------------------------------------------------------
    resource = 'missing_report'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            person_id,
                            Field("found", "boolean"),
                            Field("since", "datetime"),
                            Field("details", "text"),
                            #Field("found_date", "datetime"),
                            location_id,
                            Field("location_details"),
                            reporter,
                            Field("contact", "text"),
                            migrate=migrate)

    table.person_id.label = T("Person missing")
    table.reporter.label = T("Person reporting")

    table.found.label = T("Person found")
    table.found.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Person found") + "|" + Tstr("Use this to indicate that the person has been found.")))

    table.since.label = T("Date/Time of disappearence")
    table.since.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)
    table.since.represent = lambda value: shn_as_local_time(value)

    table.location_id.label = T("Last known location")
    table.location_id.comment = DIV(A(ADD_LOCATION,
            _class="colorbox",
            _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup")),
            _target="top",
            _title=ADD_LOCATION),
        DIV( _class="tooltip",
            _title=Tstr("Last known location") + "|" + Tstr("The last known location of the missing person before disappearance."))),
    table.location_details.label = T("Location details")

    table.details.label = T("Details")
    table.details.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Details") + "|" + Tstr("Circumstances of disappearance, other victims/witnesses who last saw the missing person alive.")))

    table.contact.label = T("Contact")
    table.contact.comment =  DIV(DIV(_class="tooltip",
        _title=Tstr("Contact") + "|" + Tstr("Contact person in case of news or further questions (if different from reporting person). Include telephone number, address and email as available.")))

    s3xrc.model.add_component(module, resource,
                              multiple=False,
                              joinby=dict(pr_person="person_id"),
                              deletable=False,
                              editable=True)


    def shn_mpr_report_onaccept(form):

        table = db.pr_person

        if form.vars.person_id:
            if form.vars.found:
                db(table.id == form.vars.person_id).update(missing=False)
            else:
                db(table.id == form.vars.person_id).update(missing=True)


    s3xrc.model.configure(table,
        onaccept = lambda form: shn_mpr_report_onaccept(form),
        list_fields = [
            "id",
            "reporter"
        ])

# -----------------------------------------------------------------------------
ADD_REPORT = T("Add Report")
LIST_REPORTS = T("List Reports")
s3.crud_strings[tablename] = Storage(
title_create = ADD_REPORT,
title_display = T("Missing Persons Report"),
title_list = LIST_REPORTS,
title_update = T("Edit Report"),
title_search = T("Search Reports"),
subtitle_create = ADD_PERSON,
subtitle_list = T("Missing Person Reports"),
label_list_button = LIST_REPORTS,
label_create_button = ADD_REPORT,
label_delete_button = T("Delete Report"),
msg_record_created = T("Report added"),
msg_record_modified = T("Report updated"),
msg_record_deleted = T("Report deleted"),
msg_list_empty = T("No Reports currently registered"))

