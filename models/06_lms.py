# -*- coding: utf-8 -*-

"""
    LMS Logistics Management System

    @author: Ajay Kumar
"""

module = "lms"
if deployment_settings.has_module(module):

    # Settings
    resource = 'setting'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field('audit_read', 'boolean'),
                    Field('audit_write', 'boolean'),
                    migrate=migrate)


    # Unit Option fields for both Length and Weight used throughout LMS
    # Also an arbitrary measure of unit

    # This part defines the types of Units we deal here. Categories of Units.
    lms_unit_type_opts = {
        1:T('Length'),
        2:T('Weight'),
        3:T('Volume - Fluids'),
        4:T('Volume - Solids'),
            5:T('Real World Arbitrary Units')
        }

    opt_lms_unit_type = db.Table(None, 'opt_lms_unit_type',
                        Field('opt_lms_unit_type', 'integer',
                        requires = IS_IN_SET(lms_unit_type_opts, zero=None),
                        # default = 1,
                        label = T('Unit Set'),
                        represent = lambda opt: lms_unit_type_opts.get(opt, UNKNOWN_OPT)))

    resource = 'unit'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, deletion_status,
                    opt_lms_unit_type, #lms_unit_type_opts --> Type of Unit
                    Field('label'), #short code of Unit for e.g. "m" for "meter"
                    Field('name'),  #complete Unit - "meter" for "m"
                    Field('base_unit'), #links to which unit
                    Field('multiplicator', 'double', default=1.0), #by default 1 thisi s what links
                    migrate=migrate)

    if not db(table.id > 0).count():
        table.insert(
            opt_lms_unit_type=1,
            label="m",
            name="Meters"
        )
        table.insert(
            opt_lms_unit_type=2,
            label="kg",
            name="Kilograms"
        )
        table.insert(
            opt_lms_unit_type=3,
            label="l",
            name="Litres"
        )
        table.insert(
            opt_lms_unit_type=4,
            label="cbm",
            name="Cubic Meters"
        )
        table.insert(
            opt_lms_unit_type=5,
            label="ton",
            name="Tonne"
        )

    table.base_unit.requires = IS_NULL_OR(IS_ONE_OF(db, "lms_unit.label", "lms_unit.name"))
    table.label.requires=IS_NOT_IN_DB(db, '%s.label' % tablename)
    table.label.label = T('Unit')
    table.label.comment = SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Label") + "|" + Tstr("Unit Short Code for e.g. m for meter."))
    table.name.comment = SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Unit Name") + "|" + Tstr("Complete Unit Label for e.g. meter for m."))
    table.base_unit.comment = SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Base Unit") + "|" + Tstr("The entered unit links to this unit. For e.g. if you are entering m for meter then choose kilometer(if it exists) and enter the value 0.001 as multiplicator."))
    table.multiplicator.comment = SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Multiplicator") + "|" + Tstr("If Unit = m, Base Unit = Km, then multiplicator is 0.0001 since 1m = 0.001 km."))
    ADD_UNIT = T('Add Unit')
    LIST_UNITS = T('List Units')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_UNIT,
        title_display = T('Unit Details'),
        title_list = LIST_UNITS,
        title_update = T('Edit Unit'),
        title_search = T('Search Units'),
        subtitle_create = T('Add New Unit'),
        subtitle_list = T('Units of Measure'),
        label_list_button = LIST_UNITS,
        label_create_button = ADD_UNIT,
        msg_record_created = T('Unit added'),
        msg_record_modified = T('Unit updated'),
        msg_record_deleted = T('Unit deleted'),
        msg_list_empty = T('No Units currently registered'))

    # Sites
    site_category_opts = {
        1:T('Donor'),
        2:T('Miscellaneous'),
            3:T('Office'),
            4:T('Project'),
            5:T('Vendor'),
            6:T('Warehouse')
        }
    opt_site_category = db.Table(None, 'site_category_type',
                            Field('category', 'integer', notnull=True,
                                requires = IS_IN_SET(site_category_opts, zero=None),
                                # default = 1,
                                label = T('Category'),
                                represent = lambda opt: site_category_opts.get(opt, UNKNOWN_OPT)))
    resource = 'site'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('name', notnull=True),
                    Field('description'),
                    opt_site_category,
                    person_id,
                    organisation_id, #Field('organisation', db.org_organisation),
                    Field('address', 'text'),
                    Field('site_phone'),
                    Field('site_fax'),
                    location_id,
                    Field('attachment', 'upload', autodelete=True),
                    comments,
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.name.requires = IS_NOT_EMPTY()   # Sites don't have to have unique names
    table.name.label = T("Site Name")
    table.name.comment = SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Site Name") + "|" + Tstr("A Warehouse/Site is a physical location with an address and GIS data where Items are Stored. It can be a Building, a particular area in a city or anything similar."))
    table.description.comment = DIV( _class="tooltip", _title=Tstr("Site Description") + "|" + Tstr("Use this space to add a description about the warehouse/site."))
    table.person_id.label = T("Contact Person")
    table.address.comment = DIV( _class="tooltip", _title=Tstr("Site Address") + "|" + Tstr("Detailed address of the site for informational/logistics purpose. Please note that you can add GIS/Mapping data about this site in the 'Location' field mentioned below."))
    table.attachment.label = T("Image/Other Attachment")
    table.attachment.comment = DIV( _class="tooltip", _title=Tstr("Image/Attachment") + "|" + Tstr("A snapshot of the location or additional documents that contain supplementary information about the Site can be uploaded here."))
    table.comments.comment = DIV( _class="tooltip", _title=Tstr("Additional Comments") + "|" + Tstr("Use this space to add additional comments and notes about the Site/Warehouse."))
    ADD_SITE = T('Add Site')
    LIST_SITES = T('List Sites')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SITE,
        title_display = T('Site Details'),
        title_list = LIST_SITES,
        title_update = T('Edit Site'),
        title_search = T('Search Site(s)'),
        subtitle_create = T('Add New Site'),
        subtitle_list = T('Sites'),
        label_list_button = LIST_SITES,
        label_create_button = ADD_SITE,
        msg_record_created = T('Site added'),
        msg_record_modified = T('Site updated'),
        msg_record_deleted = T('Site deleted'),
        msg_list_empty = T('No Sites currently registered'))

    # Storage Locations
    resource = 'storage_loc'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('site_id', db.lms_site),
                    Field('name', notnull=True),
                    Field('description'),
                    location_id,
                    Field('capacity'),
                                    Field('capacity_unit'),
                    Field('max_weight'),
                                    Field('weight_unit'),
                                    Field('attachment', 'upload', autodelete=True),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.name.requires = IS_NOT_EMPTY()   # Storage Locations don't have to have unique names
    table.site_id.label = T("Site")
    table.site_id.requires = IS_IN_DB(db, 'lms_site.id', 'lms_storage_loc.name')
    table.capacity_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[1])
    table.capacity_unit.comment = DIV(A(T('Add Unit'), _class='colorbox', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Unit") + "|" + Tstr("Add the unit of measure if it doesnt exists already.")))
    table.weight_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[2])
    table.weight_unit.comment = DIV(A(T('Add Unit'), _class='colorbox', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Unit") + "|" + Tstr("Add the unit of measure if it doesnt exists already.")))
    table.site_id.comment = DIV(A(T('Add Site'), _class='colorbox', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Site") + "|" + Tstr("Add the main Warehouse/Site information where this Storage location is.")))
    table.name.label = T("Storage Location Name")
    table.name.comment = SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Site Location Name") + "|" + Tstr("A place within a Site like a Shelf, room, bin number etc."))
    table.description.comment = DIV( _class="tooltip", _title=Tstr("Site Location Description") + "|" + Tstr("Use this space to add a description about the site location."))
    table.capacity.label = T("Capacity (W x D X H)")
    table.capacity.comment = DIV( _class="tooltip", _title=Tstr("Volume Capacity") + "|" + Tstr("Dimensions of the storage location. Input in the following format 1 x 2 x 3 for width x depth x height followed by choosing the unit from the drop down list."))
    table.max_weight.comment = DIV( _class="tooltip", _title=Tstr("Maximum Weight") + "|" + Tstr("Maximum weight capacity of the Storage Location followed by choosing the unit from the drop down list."))
    table.attachment.label = T("Image/Other Attachment")
    table.attachment.comment = DIV( _class="tooltip", _title=Tstr("Image/Attachment") + "|" + Tstr("A snapshot of the location or additional documents that contain supplementary information about the Site Location can be uploaded here."))
    ADD_STORAGE_LOCATION = T('Add Storage Location ')
    LIST_STORAGE_LOCATIONS = T('List Storage Location')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_STORAGE_LOCATION,
        title_display = T('Storage Location Details'),
        title_list = LIST_STORAGE_LOCATIONS,
        title_update = T('Edit Storage Location'),
        title_search = T('Search Storage Location(s)'),
        subtitle_create = T('Add New Storage Location'),
        subtitle_list = T('Storage Locations'),
        label_list_button = LIST_STORAGE_LOCATIONS,
        label_create_button = ADD_STORAGE_LOCATION,
        msg_record_created = T('Storage Location added'),
        msg_record_modified = T('Storage Location updated'),
        msg_record_deleted = T('Storage Location deleted'),
        msg_list_empty = T('No Storage Locations currently registered'))

    # Storage Bin Type
    resource = 'storage_bin_type'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('name', notnull=True),
                    Field('description'),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.comment = SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Storage Bin Type") + "|" + Tstr("Name of Storage Bin Type."))
    table.description.comment = DIV( _class="tooltip", _title=Tstr("Description of Bin Type") + "|" + Tstr("Use this space to add a description about the Bin Type."))
    ADD_STORAGE_BIN_TYPE = T('Add Storage Bin Type')
    LIST_STORAGE_BIN_TYPES = T('List Storage Bin Type(s)')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_STORAGE_BIN_TYPE,
        title_display = T('Storage Bin Type Details'),
        title_list = LIST_STORAGE_BIN_TYPES,
        title_update = T('Edit Storage Bin Type(s)'),
        title_search = T('Search Storage Bin Type(s)'),
        subtitle_create = T('Add New Bin Type'),
        subtitle_list = T('Storage Bin Types'),
        label_list_button = LIST_STORAGE_BIN_TYPES,
        label_create_button = ADD_STORAGE_BIN_TYPE,
        msg_record_created = T('Storage Bin Type added'),
        msg_record_modified = T('Storage Bin Type updated'),
        msg_record_deleted = T('Storage Bin Type deleted'),
        msg_list_empty = T('No Storage Bin Type currently registered'))

    # Storage Bins
    resource = 'storage_bin'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('site_id', db.lms_site),
                                    Field('storage_id', db.lms_storage_loc),
                                    Field('number', notnull=True),
                    Field('bin_type', db.lms_storage_bin_type),
                    Field('capacity'),
                                    Field('capacity_unit'),
                                    Field('max_weight'),
                                    Field('weight_unit'),
                                    Field('attachment', 'upload', autodelete=True),
                                    comments,
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.site_id.requires = IS_IN_DB(db, 'lms_site.id', 'lms_storage_loc.name')
    table.site_id.label = T("Site/Warehouse")
    table.site_id.comment = DIV(A(T('Add Site'), _class='colorbox', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Site") + "|" + Tstr("Add the main Warehouse/Site information where this Bin belongs to.")))
    table.storage_id.label = T("Storage Location")
    table.storage_id.requires = IS_IN_DB(db, 'lms_storage_loc.id', 'lms_storage_loc.name')
    table.storage_id.comment = DIV(A(T('Add Storage Location'), _class='popup', _href=URL(r=request, c='lms', f='storage_loc', args='create', vars=dict(format='plain')), _target='top'), DIV( _class="tooltip", _title=Tstr("Storage Location") + "|" + Tstr("Add the Storage Location where this this Bin belongs to.")))
    table.number.requires = IS_NOT_EMPTY()   # Storage Bin Numbers don't have to have unique names
    table.capacity_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[1])
    table.capacity_unit.comment = DIV(A(T('Add Unit'), _class='colorbox', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Unit") + "|" + Tstr("Add the unit of measure if it doesnt exists already.")))
    table.weight_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[2])
    table.weight_unit.comment = DIV(A(T('Add Unit'), _class='colorbox', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Unit") + "|" + Tstr("Add the unit of measure if it doesnt exists already.")))
    table.bin_type.requires = IS_IN_DB(db, 'lms_storage_bin_type.id', 'lms_storage_bin_type.name')
    table.bin_type.comment = DIV(A(T('Add Storage Bin Type'), _class='colorbox', _href=URL(r=request, c='lms', f='storage_bin_type', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Storage Bin") + "|" + Tstr("Add the Storage Bin Type.")))
    table.storage_id.requires = IS_IN_DB(db, 'lms_storage_loc.id', 'lms_storage_loc.name')
    table.storage_id.comment = DIV(A(T('Add Storage Location'), _class='colorbox', _href=URL(r=request, c='lms', f='storage_loc', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Storage Location") + "|" + Tstr("Add the Storage Location where this bin is located.")))
    table.number.label = T("Storage Bin Number")
    table.number.comment = SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Storage Bin Number") + "|" + Tstr("Identification label of the Storage bin."))
    table.storage_id.label = T("Storage Location ID")
    table.attachment.label = T("Image/Other Attachment")
    table.capacity.label = T("Capacity (W x D X H)")
    table.capacity.comment = DIV( _class="tooltip", _title=Tstr("Volume Capacity") + "|" + Tstr("Dimensions of the storage bin. Input in the following format 1 x 2 x 3 for width x depth x height followed by choosing the unit from the drop down list."))
    table.max_weight.comment = DIV( _class="tooltip", _title=Tstr("Maximum Weight") + "|" + Tstr("Maximum weight capacity of the items the storage bin can contain. followed by choosing the unit from the drop down list."))
    table.attachment.comment = DIV( _class="tooltip", _title=Tstr("Image/Attachment") + "|" + Tstr("A snapshot of the bin or additional documents that contain supplementary information about it can be uploaded here."))
    ADD_STORAGE_BIN = T('Add Storage Bin ')
    LIST_STORAGE_BINS = T('List Storage Bins')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_STORAGE_BIN,
        title_display = T('Storage Bin Details'),
        title_list = LIST_STORAGE_BINS,
        title_update = T('Edit Storage Bins'),
        title_search = T('Search Storage Bin(s)'),
        subtitle_create = T('Add New Bin'),
        subtitle_list = T('Storage Bins'),
        label_list_button = LIST_STORAGE_BINS,
        label_create_button = ADD_STORAGE_BIN,
        msg_record_created = T('Storage Bin added'),
        msg_record_modified = T('Storage Bin updated'),
        msg_record_deleted = T('Storage Bin deleted'),
        msg_list_empty = T('No Storage Bins currently registered'))

    # Item Catalog Master
    resource = 'catalog'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    organisation_id,
                                    Field('name'),
                    Field('description'),
                                    comments,
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Catalog Name")
    table.name.comment = SPAN("*", _class="req")
    ADD_ITEM_CATALOG = T('Add Item Catalog ')
    LIST_ITEM_CATALOGS = T('List Item Catalogs')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM_CATALOG,
        title_display = T('Item Catalog Details'),
        title_list = LIST_ITEM_CATALOGS,
        title_update = T('Edit Item Catalog'),
        title_search = T('Search Item Catalog(s)'),
        subtitle_create = T('Add New Item Catalog'),
        subtitle_list = T('Item Catalogs'),
        label_list_button = LIST_ITEM_CATALOGS,
        label_create_button = ADD_ITEM_CATALOG,
        msg_record_created = T('Item Catalog added'),
        msg_record_modified = T('Item Catalog updated'),
        msg_record_deleted = T('Item Catalog deleted'),
        msg_list_empty = T('No Item Catalog currently registered'))

    # Item Catalog Category
    resource = 'catalog_cat'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('name'),
                    Field('description'),
                                    comments,
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Item Catalog Category")
    table.name.comment = SPAN("*", _class="req")
    ADD_ITEM_CATALOG_CATEGORY = T('Add Item Catalog Category ')
    LIST_ITEM_CATALOG_CATEGORIES = T('List Item Catalog Categories')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM_CATALOG_CATEGORY,
        title_display = T('Item Catalog Category Details'),
        title_list = LIST_ITEM_CATALOG_CATEGORIES,
        title_update = T('Edit Item Catalog Categories'),
        title_search = T('Search Item Catalog Category(s)'),
        subtitle_create = T('Add New Item Catalog Category'),
        subtitle_list = T('Item Catalog Categories'),
        label_list_button = LIST_ITEM_CATALOG_CATEGORIES,
        label_create_button = ADD_ITEM_CATALOG_CATEGORY,
        msg_record_created = T('Item Catalog Category added'),
        msg_record_modified = T('Item Catalog Category updated'),
        msg_record_deleted = T('Item Catalog Category deleted'),
        msg_list_empty = T('No Item Catalog Category currently registered'))

    # Item Catalog Sub-Category
    resource = 'catalog_subcat'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('parent_category', db.lms_catalog_cat),
                                    Field('name'),
                    Field('description'),
                                    comments,
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Item Sub-Category")
    table.name.comment = SPAN("*", _class="req")
    table.parent_category.requires = IS_IN_DB(db, 'lms_catalog_cat.id', 'lms_catalog_cat.name')
    table.parent_category.comment = DIV(A(T('Add Item Category'), _class='colorbox', _href=URL(r=request, c='lms', f='catalog_cat', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=T("Add main Item Category.")))
    ADD_ITEM_SUB_CATEGORY = T('Add Item Sub-Category ')
    LIST_ITEM_SUB_CATEGORIES = T('List Item Sub-Categories')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM_SUB_CATEGORY,
        title_display = T('Item Sub-Category Details'),
        title_list = LIST_ITEM_SUB_CATEGORIES,
        title_update = T('Edit Item Sub-Categories'),
        title_search = T('Search Item Sub-Category(s)'),
        subtitle_create = T('Add New Item Sub-Category'),
        subtitle_list = T('Item Sub-Categories'),
        label_list_button = LIST_ITEM_SUB_CATEGORIES,
        label_create_button = ADD_ITEM_SUB_CATEGORY,
        msg_record_created = T('Item Sub-Category added'),
        msg_record_modified = T('Item Sub-Category updated'),
        msg_record_deleted = T('Item Sub-Category deleted'),
        msg_list_empty = T('No Item Sub-Category currently registered'))

    # Category<>Sub-Category<>Catalog Relation between all three.

    resource = 'category_master'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('category_id', db.lms_catalog_cat),
                    Field('subcategory_id', db.lms_catalog_subcat),
                    Field('catalog_id', db.lms_catalog),
                    migrate=migrate)
    table.category_id.requires = IS_IN_DB(db, 'lms_catalog_cat.id', 'lms_catalog_cat.name')
    table.category_id.label = T('Category')
    table.category_id.represent = lambda category_id: db(db.lms_catalog_cat.id==category_id).select()[0].name
    table.category_id.comment = DIV(A(T('Add Item Category'), _class='colorbox', _href=URL(r=request, c='lms', f='catalog_cat', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=T("Add main Item Category.")))
    table.subcategory_id.requires = IS_IN_DB(db, 'lms_catalog_subcat.id', 'lms_catalog_subcat.name')
    table.subcategory_id.label = T('Sub Category')
    table.subcategory_id.represent = lambda subcategory_id: db(db.lms_catalog_subcat.id==subcategory_id).select()[0].name
    table.subcategory_id.comment = DIV(A(T('Add Item Sub-Category'), _class='colorbox', _href=URL(r=request, c='lms', f='catalog_subcat', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=T("Add main Item Sub-Category.")))
    table.catalog_id.requires = IS_IN_DB(db, 'lms_catalog.id', 'lms_catalog.name')
    table.catalog_id.label = T('Catalog')
    table.catalog_id.represent = lambda catalog_id: db(db.lms_catalog.id==catalog_id).select()[0].name
    table.catalog_id.comment = DIV(A(T('Add Item Catalog'), _class='colorbox', _href=URL(r=request, c='lms', f='catalog', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=T("Add Catalog.")))
    ADD_CATEGORY_RELATION = T('Add Category<>Sub-Category<>Catalog Relation ')
    LIST_CATEGORY_RELATIONS = T('List Category<>Sub-Category<>Catalog Relation')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_CATEGORY_RELATION,
        title_display = T('Category<>Sub-Category<>Catalog Relation'),
        title_list = LIST_CATEGORY_RELATIONS,
        title_update = T('Edit Category<>Sub-Category<>Catalog Relation'),
        title_search = T('Search Category<>Sub-Category<>Catalog Relation'),
        subtitle_create = ADD_CATEGORY_RELATION,
        subtitle_list = T('Category<>Sub-Category<>Catalog Relation'),
        label_list_button = LIST_CATEGORY_RELATIONS,
        label_create_button = ADD_CATEGORY_RELATION,
        msg_record_created = T('Category<>Sub-Category<>Catalog Relation added'),
        msg_record_modified = T('Category<>Sub-Category<>Catalog Relation updated'),
        msg_record_deleted = T('Category<>Sub-Category<>Catalog Relation deleted'),
        msg_list_empty = T('No Category<>Sub-Category<>Catalog Relation currently registered'))

    # Shipment
    resource = 'shipment'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                                    Field('way_bill', notnull=True),
                                    Field('sender_site', db.lms_site),
                                    Field('sender_person'),
                                    Field('sent_date', 'datetime'),
                                    Field('recipient_site', db.lms_site),
                                    Field('recieving_person'),
                                    Field('recieved_date', 'datetime'),
                                    Field('cost', 'double', default=0.00),
                                    Field('currency'),
                                    Field('track_status', readable='False'), #Linked to Shipment Transit Log table
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.way_bill.requires = IS_NOT_EMPTY()
    table.way_bill.label = T("Shipment/Way Bills")
    table.way_bill.comment = SPAN("*", _class="req")
    table.sender_site.requires = IS_IN_DB(db, 'lms_site.id', 'lms_site.name')
    table.sender_site.comment = DIV(A(T('Add Sender Site'), _class='colorbox', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Site") + "|" + Tstr("Add a new Site from where the Item is being sent.")))
    table.recipient_site.requires = IS_IN_DB(db, 'lms_site.id', 'lms_site.name')
    table.recipient_site.comment = DIV(A(T('Add Recipient Site'), _class='colorbox', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Recipient") + "|" + Tstr("Add a new Site where the Item is being sent to.")))
    ADD_SHIPMENT = T('Add Shipment/Way Bills')
    LIST_SHIPMENTS = T('List Shipment/Way Bills')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SHIPMENT,
        title_display = T('Shipment/Way Bills Details'),
        title_list = LIST_SHIPMENTS,
        title_update = T('Edit Shipment/Way Bills'),
        title_search = T('Search Shipment/Way Bills'),
        subtitle_create = ADD_SHIPMENT,
        subtitle_list = T('Shipment/Way Bills'),
        label_list_button = LIST_SHIPMENTS,
        label_create_button = ADD_SHIPMENT,
        msg_record_created = T('Shipment/Way Bill added'),
        msg_record_modified = T('Shipment/Way Bills updated'),
        msg_record_deleted = T('Shipment/Way Bills deleted'),
        msg_list_empty = T('No Shipment/Way Bills currently registered'))

    # Items
    resource = 'item'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('site_id', db.lms_site),
                                    Field('storage_id', db.lms_storage_loc, writable=False, default=0), #No storage location assigned
                                    Field('bin_id', db.lms_storage_bin, writable=False, default=0), #No Storage Bin assigned
                                    Field('catalog', db.lms_catalog, writable=False, default=1), #default catalog assigned
                                    #Shipment Details
                                    Field('way_bill'),
                                    Field('sender_site', db.lms_site),
                                    Field('sender_person'),
                                    Field('recipient_site', db.lms_site),
                                    Field('recieving_person'),
                                    #Item Details
                                    Field('name'), #Item Catalog
                    Field('description'), #Item Catalog
                                    Field('category', db.lms_catalog_cat), #Item Catalog
                                    Field('sub_category', db.lms_catalog_subcat), #Item Catalog
                                    Field('designated'), #More details to be added, maybe a new table.
                                    Field('quantity_sent', 'double', default=0.00),
                                    Field('quantity_received', 'double', default=0.00),
                                    Field('quantity_shortage', default=0.00),
                                    Field('quantity_unit'), #Item Catalog
                                    Field('specifications'), #Item Catalog
                                    Field('specifications_unit'), #Item Catalog
                                    Field('weight', 'double', default=0.00), #Item Catalog
                                    Field('weight_unit'), #Item Catalog
                                    Field('date_time', 'datetime'),
                                    comments,
                                    Field('attachment', 'upload', autodelete=True),
                    Field('unit_cost', 'double', default=0.00),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.site_id.requires = IS_IN_DB(db, 'lms_site.id', 'lms_storage_loc.name') #this should be automatically done. Using LMS User Preferences
    table.site_id.label = T("Site/Warehouse")
    table.site_id.comment = DIV(A(T('Add Site'), _class='colorbox', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Site") + "|" + Tstr("Add the main Warehouse/Site information where this Item is to be added.")))
    table.quantity_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[5])
    table.quantity_unit.comment = DIV(A(T('Add Unit'), _class='colorbox', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Unit") + "|" + Tstr("Add the unit of measure if it doesnt exists already.")))
    table.specifications_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[1])
    table.specifications_unit.comment = DIV(A(T('Add Unit'), _class='colorbox', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Unit") + "|" + Tstr("Add the unit of measure if it doesnt exists already.")))
    table.weight_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[2])
    table.weight_unit.comment = DIV(A(T('Add Unit'), _class='colorbox', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=Tstr("Add Unit") + "|" + Tstr("Add the unit of measure if it doesnt exists already.")))
    table.name.requires = IS_NOT_EMPTY()
    table.way_bill.comment = SPAN("*", _class="req")
    table.name.label = T("Product Name")
    table.name.comment = SPAN("*", _class="req")
    table.description.label = T("Product Description")
    table.category.requires = IS_IN_DB(db, 'lms_catalog_cat.id', 'lms_catalog_cat.name')
    table.category.comment = DIV(A(T('Add Item Category'), _class='colorbox', _href=URL(r=request, c='lms', f='catalog_cat', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=T("Add main Item Category.")))
    table.sub_category.requires = IS_IN_DB(db, 'lms_catalog_subcat.id', 'lms_catalog_subcat.name')
    table.sub_category.comment = DIV(A(T('Add Item Sub-Category'), _class='colorbox', _href=URL(r=request, c='lms', f='catalog_subcat', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=T("Add main Item Sub-Category.")))
    table.sender_site.requires = IS_IN_DB(db, 'lms_site.id', 'lms_site.name')
    table.sender_site.comment = DIV(A(T('Add Sender Organisation'), _class='colorbox', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=T("Add Sender Site.")))
    table.recipient_site.requires = IS_IN_DB(db, 'lms_site.id', 'lms_site.name')
    table.recipient_site.comment = DIV(A(T('Add Recipient Site'), _class='colorbox', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='popup')), _target='top'), DIV( _class="tooltip", _title=T("Add Recipient Site.")))
    table.designated.label = T("Designated for")
    table.specifications.label = T("Volume/Dimensions")
    table.designated.comment = DIV( _class="tooltip", _title=Tstr("Designated for") + "|" + Tstr("The item is designated to be sent for specific project, population, village or other earmarking of the donation such as a Grant Code."))
    table.specifications.comment = DIV( _class="tooltip", _title=Tstr("Volume/Dimensions") + "|" + Tstr("Additional quantity quantifier – i.e. “4x5”."))
    table.date_time.comment = DIV( _class="tooltip", _title=Tstr("Date/Time") + "|" + Tstr("Date and Time of Goods receipt. By default shows the current time but can be modified by editing in the drop down list."))
    table.unit_cost.label = T('Unit Cost')
    ADD_ITEM = T('Add Item')
    LIST_ITEMS = T('List Items')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ITEM,
        title_display = T('Item Details'),
        title_list = LIST_ITEMS,
        title_update = T('Edit Item'),
        title_search = T('Search Items'),
        subtitle_create = T('Add New Item'),
        subtitle_list = T('Items'),
        label_list_button = LIST_ITEMS,
        label_create_button = ADD_ITEM,
        msg_record_created = T('Item added'),
        msg_record_modified = T('Item updated'),
        msg_record_deleted = T('Item deleted'),
        msg_list_empty = T('No Item currently registered'))

    # Shipment<>Item - A shipment can have many items under it.
    # And an Item can have multiple shipment way bills, for e.g. during transit at multiple exchanges/transits

    resource = 'shipment_item'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                                    Field('shipment_id', db.lms_shipment),
                                    Field('item_id', db.lms_item),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.shipment_id.requires = IS_IN_DB(db, 'lms_shipment.id', 'lms_shipment.way_bill')
    table.item_id.requires = IS_IN_DB(db, 'lms_item.id', 'lms_item.name') #This needs to be represented as Name+Brand+Model+Description+Size
    s3.crud_strings[tablename] = Storage(
        title_create = T('Link Item & Shipment'),
        title_display = T('Shipment<>Item Relations Details'),
        title_list = T('List Shipment<>Item Relation'),
        title_update = T('Edit Shipment<>Item Relation'),
        title_search = T('Search Shipment<>Item Relation'),
        subtitle_create = T('Link Item & Shipment'),
        subtitle_list = T('Shipment<>Item Relations'),
        label_list_button = T('Shipment<>Item Relations'),
        label_create_button = T('Link an Item & Shipment'),
        msg_record_created = T('Shipment<>Item Relation added'),
        msg_record_modified = T('Shipment<>Item Relation updated'),
        msg_record_deleted = T('Shipment<>Item Relation deleted'),
        msg_list_empty = T('No Shipment<>Item Relation currently registered'))

    # Shipment<>Item - A shipment can have many items under it.
    # And an Item can have multiple shipment way bills, for e.g. during transit at multiple exchanges/transits

    resource = 'shipment_transit_logs'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                                    Field('shipment_id', db.lms_shipment),
                                    Field('item_id', db.lms_item),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % tablename)
    table.shipment_id.requires = IS_IN_DB(db, 'lms_shipment.id', 'lms_shipment.way_bill')
    table.item_id.requires = IS_IN_DB(db, 'lms_item.id', 'lms_item.name') #This needs to be represented as Name+Brand+Model+Description+Size
    ADD_SHIPMENT_TRANSIT_LOG = T('Add Shipment Transit Log')
    LIST_SHIPMENT_TRANSIT_LOGS = T('List Shipment Transit Logs')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SHIPMENT_TRANSIT_LOG,
        title_display = T('Shipment Transit Log Details'),
        title_list = LIST_SHIPMENT_TRANSIT_LOGS,
        title_update = T('Edit Shipment Transit Log'),
        title_search = T('Search Shipment Transit Logs'),
        subtitle_create = ADD_SHIPMENT_TRANSIT_LOG,
        subtitle_list = T('Shipment Transit Logs'),
        label_list_button = LIST_SHIPMENT_TRANSIT_LOGS,
        label_create_button = ADD_SHIPMENT_TRANSIT_LOG,
        msg_record_created = T('Shipment Transit Log added'),
        msg_record_modified = T('Shipment Transit Log updated'),
        msg_record_deleted = T('Shipment Transit Log deleted'),
        msg_list_empty = T('No Shipment Transit Logs currently registered'))

    # Kits
    resource = 'kit'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('code', length=128, notnull=True, unique=True),
                    Field('description'),
                    Field('total_unit_cost', 'double', writable=False),
                    Field('total_monthly_cost', 'double', writable=False),
                    Field('total_minute_cost', 'double', writable=False),
                    Field('total_megabyte_cost', 'double', writable=False),
                    comments,
                    migrate=migrate)
    table.code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % tablename)]
    table.code.label = T('Code')
    table.code.comment = SPAN("*", _class="req")
    table.description.label = T('Description')
    table.total_unit_cost.label = T('Total Unit Cost')
    table.total_monthly_cost.label = T('Total Monthly Cost')
    table.total_minute_cost.label = T('Total Cost per Minute')
    table.total_megabyte_cost.label = T('Total Cost per Megabyte')
    table.comments.label = T('Comments')
    ADD_KIT = T('Add Kit')
    LIST_KITS = T('List Kits')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_KIT,
        title_display = T('Kit Details'),
        title_list = LIST_KITS,
        title_update = T('Edit Kit'),
        title_search = T('Search Kits'),
        subtitle_create = T('Add New Kit'),
        subtitle_list = T('Kits'),
        label_list_button = LIST_KITS,
        label_create_button = ADD_KIT,
        msg_record_created = T('Kit added'),
        msg_record_modified = T('Kit updated'),
        msg_record_deleted = T('Kit deleted'),
        msg_list_empty = T('No Kits currently registered'))

    # Kit<>Item Many2Many
    resource = 'kit_item'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field('kit_id', db.lms_kit),
                    Field('item_id', db.lms_item, ondelete='RESTRICT'),
                    Field('quantity', 'integer', default=1, notnull=True),
                    migrate=migrate)
    table.kit_id.requires = IS_IN_DB(db, 'lms_kit.id', 'lms_kit.code')
    table.kit_id.label = T('Kit')
    table.kit_id.represent = lambda kit_id: db(db.budget_kit.id == kit_id).select(db.budget_kit.code, limitby=(0, 1)).first().code
    table.item_id.requires = IS_IN_DB(db, 'lms_item.id', 'lms_item.description')
    table.item_id.label = T('Item')
    table.item_id.represent = lambda item_id: db(db.lms_item.id == item_id).select(db.lms_item.description, limitby=(0, 1)).first().description
    table.quantity.requires = IS_NOT_EMPTY()
    table.quantity.label = T('Quantity')
    table.quantity.comment = SPAN("*", _class="req")
