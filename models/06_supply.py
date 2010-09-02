# -*- coding: utf-8 -*-

"""
    Supply 
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16    
    
    Generic Supply functionality such as catalogs and items that will be used across multiple modules
"""

module = "supply"
if deployment_settings.has_module("logs"):
    #==============================================================================
    # Settings
    #
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("audit_read", "boolean"),
                            Field("audit_write", "boolean"),
                            migrate=migrate)

    #==============================================================================
    # Item Category
    #
    resource = "item_category"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, 
                            timestamp, 
                            uuidstamp, 
                            authorstamp, 
                            deletion_status,
                            Field("name", length=128, notnull=True, unique=True),
                            comments,
                            migrate=migrate)

    table.name.comment = SPAN("*", _class="req")

    s3.crud_strings[tablename] = shn_crud_strings("Item Category", "Item Categories")

    # -----------------------------------------------------------------------------
    # @ToDo Replace Function with Class
    def get_item_category_id (field_name = "item_category_id", 
                              label = T("Category"),
                              ):
        requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item_category.id", "%(name)s", sort=True))
        
        represent = lambda id: shn_get_db_field_value(db = db,
                                                      table = "supply_item_category", 
                                                      field = "name", 
                                                      look_up = id)    

        return db.Table(None, 
                        field_name,
                        FieldS3(field_name, 
                                db.supply_item_category, sortby="name",
                                requires = requires,
                                represent = represent,
                                label = label,
                                comment = SPAN("*", _class="req"),
                                ondelete = "RESTRICT"
                                )
                        )
    # -----------------------------------------------------------------------------

    #==============================================================================
    # Item
    #
    resource = "item"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, 
                            timestamp, 
                            uuidstamp, 
                            authorstamp, 
                            deletion_status,                        
                            # @ToDo Replace Function with Class
                            get_item_category_id(),
                            Field("name", length=128, notnull=True, unique=True),
                            comments,
                            migrate=migrate)

    table.name.comment = SPAN("*", _class="req")

    s3.crud_strings[tablename] = shn_crud_strings("Relief Item")

    # -----------------------------------------------------------------------------
    # @ToDo Replace Function with Class
    def get_item_id ( field_name = "item_id", 
                      label = T("Item"),
                      ):
        requires = IS_NULL_OR(IS_ONE_OF(db, "supply_item.id", "%(name)s", sort=True))
        
        represent = lambda id: shn_get_db_field_value(db = db,
                                                      table = "supply_item", 
                                                      field = "name", 
                                                      look_up = id) 
        
        comment = DIV( A( T("Add Relief Item"),
                          _class="colorbox",
                          _href=URL(r=request, 
                                    c="supply", 
                                    f="item", 
                                    args="create", 
                                    vars=dict(format="popup")
                                    ),
                          _target="top",
                          _title=T("Add Relief Item")
                          ),
                       DIV( _class="tooltip",
                            _title=Tstr("Relief Item") + "|" + Tstr("Add a New Relief Item")
                            )
                       )

        return db.Table(None, 
                        field_name,
                        FieldS3(field_name, 
                                db.supply_item, sortby="name",
                                requires = requires,
                                represent = represent,
                                label = label,
                                comment = comment,
                                ondelete = "RESTRICT"
                                )
                        )
