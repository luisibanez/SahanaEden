# -*- coding: utf-8 -*-
"""
    Template for a Model

    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-05-23

    This model introduces some of the basic features of Sahana
    it can be used as a template to build a model for your own modules
"""

module = "template"
if deployment_settings.has_module(module):

    # -----------------------------------------------------------------------------
    # Settings
    #
    resource = "setting"
    table_name = "%s_%s" % (module, resource)
    table = table = db.define_table(table_name,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)

    # -----------------------------------------------------------------------------
    # Hazard
    # Example Table

    resource = "hazard"
    table_name = module + "_" + resource
    table = db.define_table(table_name, timestamp, uuidstamp, deletion_status,
                    #fields for table >>>
                    Field("name",
                          length=128,
                          notnull=True,
                          unique=True),
                    #<<<
                    comments,
                    migrate=migrate)

    # Field settings
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]

    # CRUD strings
    s3.crud_strings[table_name] = shn_crud_strings("Hazard")

    field_settings = S3CheckboxesWidget(db = db,
                                        lookup_table_name = "template_hazard",
                                        lookup_field_name = "name",
                                        multiple = True,
                                        num_column = 3,
                                        help_lookup_field_name = "comment",
                                        help_footer = P(I("source: PreventionWeb"))
                                        )

    # Reusable field
    hazard_ids = db.Table(None, "hazard_ids",
                         Field("hazard_ids",
                               requires = field_settings.requires,
                               widget = field_settings.widget,
                               represent = field_settings.represent,
                               label = T("Hazard"),
                               ondelete = "RESTRICT"
                              ))

    # Import Data
    shn_import_table(table_name)

    # -----------------------------------------------------------------------------
    # Disaster
    # Example table
    # According to Disaster Management Theory: Disaster = Hazard * Vulnerability

    resource = "disaster"
    table_name = "%s_%s" % (module, resource)
    table = db.define_table( table_name, timestamp, uuidstamp, deletion_status,
                             #fields for table >>>
                             Field("name"),
                             hazard_ids,
                             Field("vulnerability", "integer"),
                             Field("update_dummy"), # This field is mainly used as a place holder
                             #<<<
                             migrate=migrate)

    s3.crud_strings[tablename] = shn_crud_strings("Disaster") #creates heading for the table (see /models/00_utils.py)

    table.name.requires = IS_NOT_EMPTY()

    opt_vulnerability = {1:T("Low"),
                    2:T("Medium"),
                    3:T("High")
                    }

    #Will be displayed as a select
    table.vulnerability.requires = IS_IN_SET(opt_vulnerability, zero=None)

    # -----------------------------------------------------------------------------
    # Update:
    #  Example table

    resource = "update"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field("disaster_id"),
                    Field("date", "date"),
                    comments,
                    migrate=migrate)

    # Field settings
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

    db.template_disaster.update_dummy.label = T("Update")

    update_dummy_element = S3MultiSelectWidget(db = db,
                                               link_table_name = tablename,
                                               link_field_name = "disaster_id"
                                               )

    db.template_disaster.update_dummy.widget = update_dummy_element.widget
    db.template_disaster.update_dummy.represent = update_dummy_element.represent

    # -----------------------------------------------------------------------------
    # template_disaster_onaccept

    def template_disaster_onaccept(form):
        template_disaster_id = session.rcvars.template_disaster

        #The widget is finished processing here,
        #so that records can be linked to new table  (id=template_disaster_id
        update_dummy_element.onaccept( db, template_disaster_id, request)

    s3xrc.model.configure(db.template_disaster, onaccept=lambda form: template_disaster_onaccept(form))
