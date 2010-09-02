# -*- coding: utf-8 -*-

"""
    GIS Controllers

    @author: Fran Boon <fran@aidiq.com>
"""

from operator import __and__

module = request.controller

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Locations"), False, URL(r=request, f="location"), [
        #[T("List"), False, URL(r=request, f="location")],
        [T("Search"), False, URL(r=request, f="location", args="search_simple")],
        [T("Add"), False, URL(r=request, f="location", args="create")],
    ]],
    [T("Fullscreen Map"), False, URL(r=request, f="map_viewing_client")],
    # Currently broken
    #[T("Bulk Uploader"), False, URL(r=request, c="doc", f="bulk_upload")]
]
if not deployment_settings.get_security_map() or shn_has_role("MapAdmin"):
    response.menu_options.append([T("Service Catalogue"), False, URL(r=request, f="map_service_catalogue")])
    response.menu_options.append([T("De-duplicator"), False, URL(r=request, f="location_duplicates")])
 
# -----------------------------------------------------------------------------
# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db)

# S3 framework functions
def index():
    """
       Module's Home Page
    """

    module_name = deployment_settings.modules[module].name_nice
    
    # Include an embedded Overview Map on the index page
    window = False
    toolbar = False
    
    map = define_map(window=window, toolbar=toolbar)

    return dict(module_name=module_name, map=map)

# -----------------------------------------------------------------------------
def define_map(window=False, toolbar=False):
    """
        Define the main Situation Map
        This can then be called from both the Index page (embedded) & the Map_Viewing_Client (fullscreen)
    """
    
    # @ToDo: Make these configurable
    #config = gis.get_config()
    if not deployment_settings.get_security_map() or shn_has_role("MapAdmin"):
        catalogue_toolbar = True
    else:
        catalogue_toolbar = False
    search = True
    catalogue_overlays = True

    # Custom Feature Layers
    # @ToDo: Move these layer definitions into the DB, removing Feature Groups
    # Feature Classes to be removed from Locations, although we still want the symbology mappings
    # Incidents
    module = "irs"
    resource = "ireport"
    layername = Tstr("Incident Reports")
    popup_label = Tstr("Incident")
    # Default (but still better to define here as otherwise each feature needs to check it's feature_class)
    marker = "marker_red"
    incidents = gis.get_feature_layer(module, resource, layername, popup_label, marker, active=False)
    
    # Shelters
    module = "cr"
    resource = "shelter"
    layername = Tstr("Shelters")
    popup_label = Tstr("Shelter")
    marker = "shelter"
    shelters = gis.get_feature_layer(module, resource, layername, popup_label, marker, active=True)
    
    # Schools
    module = "sitrep"
    resource = "school_report"
    layername = Tstr("Schools")
    popup_label = Tstr("School")
    marker = "school"
    schools = gis.get_feature_layer(module, resource, layername, popup_label, marker, active=True)
    
    # Requests
    module = "rms"
    resource = "req"
    layername = Tstr("Requests")
    popup_label = Tstr("Request")
    marker = "marker_yellow"
    requests = gis.get_feature_layer(module, resource, layername, popup_label, marker, active=True)
    
    # Assessments
    module = "sitrep"
    resource = "assessment"
    layername = Tstr("Assessments")
    popup_label = Tstr("Assessment")
    marker = "marker_green"
    assessments = gis.get_feature_layer(module, resource, layername, popup_label, marker, active=True)
    
    # Activities
    module = "project"
    resource = "activity"
    layername = Tstr("Activities")
    popup_label = Tstr("Activity")
    marker = "activity"
    activities = gis.get_feature_layer(module, resource, layername, popup_label, marker, active=True)
    
    feature_queries = [
                       incidents,
                       shelters,
                       schools,
                       requests,
                       assessments,
                       activities
                       ]
    
    map = gis.show_map(
                       window=window,
                       catalogue_toolbar=catalogue_toolbar,
                       #wms_browser = {"name" : "Sahana ", "url" : "http://geo.eden.sahanafoundation.org/geoserver/ows?service=WMS&request=GetCapabilities"},
                       toolbar=toolbar,
                       search=search,
                       catalogue_overlays=catalogue_overlays,
                       feature_queries=feature_queries
                      )

    return map
    
# -----------------------------------------------------------------------------
def location():

    """ RESTful CRUD controller for Locations """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Allow prep to pass vars back to the controller
    vars = {}
    
    # Pre-processor
    def prep(r, vars):

        # Restrict access to Polygons to just MapAdmins
        if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
            table.code.writable = False
            if r.method == "create":
                table.code.readable = False
            table.gis_feature_type.writable = table.gis_feature_type.readable = False
            table.wkt.writable = table.wkt.readable = False
            table.marker_id.comment = ""
        else:
            table.code.comment = DIV( _class="tooltip", _title=Tstr("Code") + "|" + Tstr("For a country this would be the ISO2 code, for a Town, it would be the Airport Locode."))
            table.wkt.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title="WKT" + "|" + Tstr("The <a href='http://en.wikipedia.org/wiki/Well-known_text' target=_blank>Well-Known Text</a> representation of the Polygon/Line.")))

        if r.http == "GET" and r.representation in ("html", "popup"):
            # Options which are only required in interactive HTML views
            table.level.comment = DIV( _class="tooltip", _title=Tstr("Level") + "|" + Tstr("If the location is a geographic area, then state at what level here."))
            table.parent.comment = DIV(A(ADD_LOCATION,
                                           _class="colorbox",
                                           _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", child="parent")),
                                           _target="top",
                                           _title=ADD_LOCATION),
                                         DIV(
                                           _class="tooltip",
                                           _title=Tstr("Parent") + "|" + Tstr("The Area which this Site is located within."))),
            table.name.comment = SPAN("*", _class="req")
            table.osm_id.comment = DIV( _class="tooltip", _title="OSM ID" + "|" + Tstr("The <a href='http://openstreetmap.org' target=_blank>OpenStreetMap</a> ID. If you don't know the ID, you can just say 'Yes' if it has been added to OSM."))

            # CRUD Strings
            LIST_LOCATIONS = T("List Locations")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_LOCATION,
                title_display = T("Location Details"),
                title_list = T("Locations"),
                title_update = T("Edit Location"),
                title_search = T("Search Locations"),
                subtitle_create = T("Add New Location"),
                subtitle_list = LIST_LOCATIONS,
                label_list_button = LIST_LOCATIONS,
                label_create_button = ADD_LOCATION,
                label_delete_button = T("Delete Location"),
                msg_record_created = T("Location added"),
                msg_record_modified = T("Location updated"),
                msg_record_deleted = T("Location deleted"),
                msg_list_empty = T("No Locations currently available"))

            if r.method in (None, "list") and r.record == None:
                # List
                pass
            elif r.method in ("delete", "search_simple"):
                pass
            else:
                # Add Map to allow locations to be found this way
                config = gis.get_config()
                lat = config.lat
                lon = config.lon
                zoom = config.zoom
                feature_queries = []

                if r.method == "create":
                    add_feature = True
                    add_feature_active = True
                else:
                    if r.method == "update":
                        add_feature = True
                        add_feature_active = False
                    else:
                        # Read
                        add_feature = False
                        add_feature_active = False
                    
                    location = db(db.gis_location.id == r.id).select(db.gis_location.lat, db.gis_location.lon, limitby=(0, 1)).first()
                    if location and location.lat is not None and location.lon is not None:
                        lat = location.lat
                        lon = location.lon
                    # Same as a single zoom on a cluster
                    zoom = zoom + 2
                    
                _map = gis.show_map(lat = lat,
                                    lon = lon,
                                    zoom = zoom,
                                    feature_queries = feature_queries,
                                    add_feature = add_feature,
                                    add_feature_active = add_feature_active,
                                    toolbar = True,
                                    collapsed = True)

                # Pass the map back to the main controller
                vars.update(_map=_map)
        return True
    response.s3.prep = lambda r, vars=vars: prep(r, vars)
    
    # Options
    _vars = request.vars
    filters = []
    # Deprecate!
    #fclass = _vars.get("feature_class", None)
    #if fclass:
    #    filters.append((db.gis_location.feature_class_id == db.gis_feature_class.id) &
    #                          (db.gis_feature_class.name.like(fclass)))

    parent = _vars.get("parent_", None)
    # Don't use 'parent' as the var name as otherwise it conflicts with the form's var of the same name & hence this will be triggered during form submission
    if parent:
        # Can't do this using a JOIN in DAL syntax
        # .belongs() not GAE-compatible!
        filters.append((db.gis_location.parent.belongs(db(db.gis_location.name.like(parent)).select(db.gis_location.id))))
        # ToDo: Make this recursive - want descendants not just direct children!
        # Use new gis.get_children() function

    # ToDo
    # bbox = _vars.get("bbox", None):

    if filters:
        response.s3.filter = reduce(__and__, filters)

    caller = _vars.get("caller", None)
    if caller:
        # We've been called as a Popup
        if "gis_location_parent" in caller:
            # Populate defaults & hide unnecessary rows
            # Use default Marker for Admin Locations
            table.marker_id.readable = table.marker_id.writable = False
            table.addr_street.readable = table.addr_street.writable = False
            #table.osm_id.readable = table.osm_id.writable = False
            #table.source.readable = table.source.writable = False
        else:
            parent = _vars.get("parent_", None)
            # Don't use 'parent' as the var name as otherwise it conflicts with the form's var of the same name & hence this will be triggered during form submission
            if parent:
                table.parent.default = parent
            
            #fc = None
            # Populate defaults & hide unnecessary rows
            if "cr_shelter" in caller:
                #fc = db(db.gis_feature_class.name == "Shelter").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "hms_hospital" in caller:
                #fc = db(db.gis_feature_class.name == "Hospital").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "irs_ireport" in caller:
                #fc = db(db.gis_feature_class.name == "Incident").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "org_office" in caller:
                #fc = db(db.gis_feature_class.name == "Office").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "pr_presence" in caller:
                #fc = db(db.gis_feature_class.name == "Person").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "assessment_location" in caller:
                table.level.default = "L4"
                #table.feature_class_id.readable = table.feature_class_id.writable = False
                table.marker_id.readable = table.marker_id.writable = False
                table.addr_street.readable = table.addr_street.writable = False
            elif "school_district" in caller:
                table.level.default = "L2"
                #table.feature_class_id.readable = table.feature_class_id.writable = False
                table.marker_id.readable = table.marker_id.writable = False
                table.addr_street.readable = table.addr_street.writable = False
            elif "school_report_location" in caller:
                table.level.default = "L2"
                #table.feature_class_id.readable = table.feature_class_id.writable = False
                table.marker_id.readable = table.marker_id.writable = False
                table.addr_street.readable = table.addr_street.writable = False
            elif "school_report_union" in caller:
                table.level.default = "L4"
                #table.feature_class_id.readable = table.feature_class_id.writable = False
                table.marker_id.readable = table.marker_id.writable = False
                table.addr_street.readable = table.addr_street.writable = False
            
            #try:
                # If we have a pre-assigned Feature Class
                #table.feature_class_id.default = fc.id
                #table.feature_class_id.readable = table.feature_class_id.writable = False
                # Use default Marker for Class
                #table.marker_id.readable = table.marker_id.writable = False
            #except:
                #pass

            table.osm_id.readable = table.osm_id.writable = False
            table.source.readable = table.source.writable = False

    level = _vars.get("level", None)
    if level:
        # We've been called from the Location Selector widget
        table.marker_id.readable = table.marker_id.writable = False
        table.addr_street.readable = table.addr_street.writable = False
    
    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False)

    _map = vars.get("_map", None)
    if _map and isinstance(output, dict):
        output.update(_map=_map)

    return output

def location_duplicates():

    """ Handle De-duplication of Locations """

    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    def delete_location(old, new):
        # Find all tables which link to the Locations table
        tables = []
        for table in db.tables:
            # @ToDo: Catch all fields through
            #for field in db[table].fields:
            #    if type(field) == "reference gis_location":
            #        tables[table] = field
            if "location_id" in db[table]:
                tables.append(table)

        for table in tables:
            query = db[table].location_id == old
            db(query).update(location_id=new)
        db(db.gis_location.id == old).update(deleted=True)

    def open_btn(field):
        return A(T("Open in New Tab"), _id=field, _href=URL(r=request, f="location"), _class="action-btn", _target="_blank")

    form = SQLFORM.factory(
                           Field("old", db.gis_location, requires=IS_ONE_OF(db, "gis_location.id", "%(name)s"), label = B(T("Old")), comment=open_btn("btn_old")),
                           Field("new", db.gis_location, requires=IS_ONE_OF(db, "gis_location.id", "%(name)s"), label = B(T("New")), comment=open_btn("btn_new")),
                          )
    
    if form.accepts(request.vars, session):
        _vars = form.vars
        
        if not _vars.old == _vars.new:
            # Take Action
            delete_location(_vars.old, _vars.new)
            response.confirmation = T("Location De-duplicated")
        else:
            response.error = T("Locations should be different!")

    elif form.errors:
        response.error = T("Need to select 2 Locations")

    return dict(form=form)
    
# -----------------------------------------------------------------------------
def map_service_catalogue():
    """
        Map Service Catalogue.
        Allows selection of which Layers are active.
    """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    subtitle = T("List Layers")
    # Start building the Return with the common items
    output = dict(subtitle=subtitle)

    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = shn_has_permission("update", table)
    item_list = []
    even = True
    if authorised:
        # List View with checkboxes to Enable/Disable layers
        for type in gis_layer_types:
            table = db["gis_layer_%s" % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ""
                label = type + "_" + str(row.id)
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value=True, _name=label)
                else:
                    enabled = INPUT(_type="checkbox", _name=label)
                item_list.append(TR(TD(row.name), TD(description), TD(enabled), _class=theclass))

        table_header = THEAD(TR(TH("Layer"), TH("Description"), TH("Enabled?")))
        table_footer = TFOOT(TR(TD(INPUT(_id="submit_button", _type="submit", _value=T("Update")), _colspan=3)), _align="right")
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(r=request, f="layers_enable")))

    else:
        # Simple List View
        for type in gis_layer_types:
            table = db["gis_layer_%s" % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ""
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value="on", _disabled="disabled")
                else:
                    enabled = INPUT(_type="checkbox", _disabled="disabled")
                item_list.append(TR(TD(row.name), TD(description), TD(enabled), _class=theclass))

        table_header = THEAD(TR(TH("Layer"), TH("Description"), TH("Enabled?")))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))

    output.update(dict(items=items))
    return output

def layers_enable():
    """
        Enable/Disable Layers
    """

    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = shn_has_permission("update", table)
    if authorised:
        for type in gis_layer_types:
            resource = "gis_layer_%s" % type
            table = db[resource]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                query_inner = (table.id == row.id)
                var = "%s_%i" % (type, row.id)
                # Read current state
                if db(query_inner).select(table.enabled, limitby=(0, 1)).first().enabled:
                    # Old state: Enabled
                    if var in request.vars:
                        # Do nothing
                        pass
                    else:
                        # Disable
                        db(query_inner).update(enabled=False)
                        # Audit
                        #shn_audit_update_m2m(resource=resource, record=row.id, representation="html")
                        shn_audit_update_m2m(resource, row.id, "html")
                else:
                    # Old state: Disabled
                    if var in request.vars:
                        # Enable
                        db(query_inner).update(enabled=True)
                        # Audit
                        shn_audit_update_m2m(resource, row.id, "html")
                    else:
                        # Do nothing
                        pass
        session.flash = T("Layers updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f="map_service_catalogue"))

# -----------------------------------------------------------------------------
def apikey():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.writable = False
    table.apikey.comment = SPAN("*", _class="req")

    # CRUD Strings
    ADD_KEY = T("Add Key")
    LIST_KEYS = T("List Keys")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_KEY,
        title_display = T("Key Details"),
        title_list = T("Keys"),
        title_update = T("Edit Key"),
        title_search = T("Search Keys"),
        subtitle_create = T("Add New Key"),
        subtitle_list = LIST_KEYS,
        label_list_button = LIST_KEYS,
        label_create_button = ADD_KEY,
        label_delete_button = T("Delete Key"),
        msg_record_created = T("Key added"),
        msg_record_modified = T("Key updated"),
        msg_record_deleted = T("Key deleted"),
        msg_list_empty = T("No Keys currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def config():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Pre-processor
    def prep(r):
        if r.representation in ("html", "popup"):
            # Model options
            # In Model so that they're visible to person() as component
            # CRUD Strings (over-ride)
            s3.crud_strings[tablename].title_display = T("Defaults")
            s3.crud_strings[tablename].title_update = T("Edit Defaults")
            s3.crud_strings[tablename].msg_record_modified = T("Defaults updated")
        if deployment_settings.get_security_map() and r.id == 1 and r.method in ["create", "update"] and not shn_has_role("MapAdmin"):
            unauthorised()
        return True
    response.s3.prep = prep

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    output["list_btn"] = ""

    if auth.is_logged_in():
        personalised = db((db.pr_person.uuid == auth.user.person_uuid) & (table.pe_id == db.pr_person.pe_id)).select(table.id, limitby=(0, 1)).first()
        if personalised:
            output["rheader"] = P(T("You have personalised settings, so changes made here won't be visible to you. To change your personalised settings, click "), A(T("here"), _href=URL(r=request, c="pr", f="person", args=["config"], vars={"person.uid":auth.user.person_uuid})))
        else:
            output["rheader"] = P(T("These are the default settings for all users. To change settings just for you, click "), A(T("here"), _href=URL(r=request, c="pr", f="person", args=["config"], vars={"person.uid":auth.user.person_uuid})))

    return output

def feature_class():
    """
        RESTful CRUD controller
        Deprecated? (How to link Symbology with Feature Queries?)
    """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")
    table.gps_marker.comment = DIV( _class="tooltip", _title=Tstr("GPS Marker") + "|" + Tstr("Defines the icon used for display of features on handheld GPS."))

    # CRUD Strings
    LIST_FEATURE_CLASS = T("List Feature Classes")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_FEATURE_CLASS,
        title_display = T("Feature Class Details"),
        title_list = T("Feature Classes"),
        title_update = T("Edit Feature Class"),
        title_search = T("Search Feature Class"),
        subtitle_create = T("Add New Feature Class"),
        subtitle_list = LIST_FEATURE_CLASS,
        label_list_button = LIST_FEATURE_CLASS,
        label_create_button = ADD_FEATURE_CLASS,
        label_delete_button = T("Delete Feature Class"),
        msg_record_created = T("Feature Class added"),
        msg_record_modified = T("Feature Class updated"),
        msg_record_deleted = T("Feature Class deleted"),
        msg_list_empty = T("No Feature Classes currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view and response.view != "popup.html":
        response.view = "gis/" + response.view

    return output

def feature_layer():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")
    table.query.comment = SPAN("*", _class="req")

    # CRUD Strings
    ADD_FEATURE_LAYER = T("Add Feature Layer")
    LIST_FEATURE_LAYERS = T("List Feature Layers")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_FEATURE_LAYER,
        title_display = T("Feature Layer Details"),
        title_list = T("Feature Layers"),
        title_update = T("Edit Feature Layer"),
        title_search = T("Search Feature Layers"),
        subtitle_create = T("Add New Feature Layer"),
        subtitle_list = LIST_FEATURE_LAYERS,
        label_list_button = LIST_FEATURE_LAYERS,
        label_create_button = ADD_FEATURE_LAYER,
        label_delete_button = T("Delete Feature Layer"),
        msg_record_created = T("Feature Layer added"),
        msg_record_modified = T("Feature Layer updated"),
        msg_record_deleted = T("Feature Layer deleted"),
        msg_list_empty = T("No Feature Layers currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    crud.settings.create_onvalidation = lambda form: feature_layer_query(form)
    crud.settings.update_onvalidation = lambda form: feature_layer_query(form)

    output = shn_rest_controller(module, resource)

    return output

def feature_layer_query(form):
    """ OnValidation callback to build the simple Query from helpers """

    if "advanced" in form.vars:
        # We should use the query field as-is
        pass
    elif "resource" in form.vars:
        # We build query from helpers
        if "filter_field" in form.vars and "filter_value" in form.vars:
            if "deleted" in db[resource]:
                form.vars.query = "(db[%s].deleted == False) & (db[%s][%s] == '%s')" % (resource, resource, filter_field, filter_value)
            else:
                form.vars.query = "(db[%s][%s] == '%s')" % (resource, filter_field, filter_value)
        else:
            if "deleted" in db[resource]:
                # All undeleted members of the resource
                form.vars.query = "(db[%s].deleted == False)" % (resource)
            else:
                # All members of the resource
                form.vars.query = "(db[%s].id > 0)" % (resource)
    else:
        # Resource is mandatory if not in advanced mode
        session.error = T("Need to specify a Resource!")

    return

def marker():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")

    # CRUD Strings
    LIST_MARKERS = T("List Markers")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MARKER,
        title_display = T("Marker Details"),
        title_list = T("Markers"),
        title_update = T("Edit Marker"),
        title_search = T("Search Markers"),
        subtitle_create = T("Add New Marker"),
        subtitle_list = LIST_MARKERS,
        label_list_button = LIST_MARKERS,
        label_create_button = ADD_MARKER,
        label_delete_button = T("Delete Marker"),
        msg_record_created = T("Marker added"),
        msg_record_modified = T("Marker updated"),
        msg_record_deleted = T("Marker deleted"),
        msg_list_empty = T("No Markers currently available"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource)

    if not "gis" in response.view and response.view != "popup.html":
        response.view = "gis/" + response.view

    return output

def projection():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")
    table.epsg.comment = SPAN("*", _class="req")
    table.maxExtent.comment = SPAN("*", _class="req")
    table.maxResolution.comment = SPAN("*", _class="req")

    # CRUD Strings
    ADD_PROJECTION = T("Add Projections")
    LIST_PROJECTIONS = T("List Projections")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_PROJECTION,
        title_display = T("Projection Details"),
        title_list = T("Projections"),
        title_update = T("Edit Projection"),
        title_search = T("Search Projections"),
        subtitle_create = T("Add New Projection"),
        subtitle_list = LIST_PROJECTIONS,
        label_list_button = LIST_PROJECTIONS,
        label_create_button = ADD_PROJECTION,
        label_delete_button = T("Delete Projection"),
        msg_record_created = T("Projection added"),
        msg_record_modified = T("Projection updated"),
        msg_record_deleted = T("Projection deleted"),
        msg_list_empty = T("No Projections currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def track():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    table = module + "_" + resource

    # Model options
    # used in multiple controllers, so defined in model

    # CRUD Strings
    # used in multiple controllers, so defined in model

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False)
    return output

# Common CRUD strings for all layers
ADD_LAYER = T("Add Layer")
LAYER_DETAILS = T("Layer Details")
LAYERS = T("Layers")
EDIT_LAYER = T("Edit Layer")
SEARCH_LAYERS = T("Search Layers")
ADD_NEW_LAYER = T("Add New Layer")
LIST_LAYERS = T("List Layers")
DELETE_LAYER = T("Delete Layer")
LAYER_ADDED = T("Layer added")
LAYER_UPDATED = T("Layer updated")
LAYER_DELETED = T("Layer deleted")
# These may be differentiated per type of layer.
TYPE_LAYERS_FMT = "%s Layers"
ADD_NEW_TYPE_LAYER_FMT = "Add New %s Layer"
EDIT_TYPE_LAYER_FMT = "Edit %s Layer"
LIST_TYPE_LAYERS_FMT = "List %s Layers"
NO_TYPE_LAYERS_FMT = "No %s Layers currently defined"

def layer_openstreetmap():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "OpenStreetMap"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_google():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "Google"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_yahoo():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "Yahoo"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_mgrs():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "MGRS"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_bing():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "Bing"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_georss():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "GeoRSS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_gpx():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    table = module + "_" + resource

    # Model options
    # Needed in multiple controllers, so defined in Model

    # CRUD Strings
    type = "GPX"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_kml():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "KML"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, copyable=True)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_tms():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")
    table.layers.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "TMS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_wfs():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "WFS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_wms():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")
    table.layers.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "WMS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

@auth.shn_requires_membership("MapAdmin")
def layer_js():
    """ RESTful CRUD controller """
    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "JS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_xyz():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not shn_has_role("MapAdmin"):
        unauthorised()

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "XYZ"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

# -----------------------------------------------------------------------------
def map_viewing_client():
    """
        Map Viewing Client.
        UI for a user to view the overall Maps with associated Features
    """

    # Read configuration settings
    config = gis.get_config()
    if config.opt_gis_layout == 1:
        window = True
    else:
        window = False

    # @ToDo Make Configurable
    toolbar = True
    
    map = define_map(window=window, toolbar=toolbar)

    return dict(map=map)

# -----------------------------------------------------------------------------
def display_feature():
    """
        Cut-down version of the Map Viewing Client.
        Used by shn_gis_location_represent() to show just this feature on the map.
        Called by the s3_viewMap() JavaScript
    """

    # The Feature
    feature_id = request.args(0)

    # Check user is authorised to access record
    if not shn_has_permission("read", db.gis_location, feature_id):
        session.error = str(T("No access to this record!"))
        raise HTTP(401, body=s3xrc.xml.json_message(False, 401, session.error))

    query = db(db.gis_location.id == feature_id).select(limitby=(0, 1))
    feature = query.first()

    config = gis.get_config()
    
    try:
        # Centre on Feature
        lat = feature.lat
        lon = feature.lon
        if (lat is None) or (lon is None):
            if feature.get("parent"):
                # Skip the current record if we can
                latlon = gis.get_latlon(feature.parent)
            elif feature.get("id"):
                latlon = gis.get_latlon(feature.id)
            else:
                # nothing we can do!
                raise
            if latlon:
                lat = latlon["lat"]
                lon = latlon["lon"]
            else:
                # nothing we can do!
                raise
    except:
        lat = config.lat
        lon = config.lon

    # Calculate an appropriate BBox
    #bounds = gis.get_bounds(features=query)
    
    # Default zoom +2 (same as a single zoom on a cluster)
    zoom = config.zoom + 2

    map = gis.show_map(
        feature_queries = [{"name" : "Feature", "query" : query, "active" : True}],
        lat = lat,
        lon = lon,
        #bbox = bounds,
        zoom = zoom,
        window = True,
        collapsed = True
    )

    return dict(map=map)

def display_features():
    """
        Cut-down version of the Map Viewing Client.
        Used as a link from the RHeader.
            URL generated server-side
        Shows all locations matching a query.
        ToDo: Most recent location is marked using a bigger Marker.
    """

    # Parse the URL, check for implicit resources, extract the primary record
    # http://127.0.0.1:8000/eden/gis/display_features&module=pr&resource=person&instance=1&jresource=presence
    ok = 0
    if "module" in request.vars:
        res_module = request.vars.module
        ok +=1
    if "resource" in request.vars:
        resource = request.vars.resource
        ok +=1
    if "instance" in request.vars:
        instance = int(request.vars.instance)
        ok +=1
    if "jresource" in request.vars:
        jresource = request.vars.jresource
        ok +=1
    if ok != 4:
        session.error = str(T("Insufficient vars: Need module, resource, jresource, instance"))
        raise HTTP(400, body=s3xrc.xml.json_message(False, 400, session.error))

    component, pkey, fkey = s3xrc.model.get_component(res_module, resource, jresource)
    table = db["%s_%s" % (res_module, resource)]
    jtable = db[str(component.table)]
    query = (jtable[fkey] == table[pkey]) & (table.id == instance)
    # Filter out deleted
    deleted = (table.deleted == False)
    query = query & deleted
    # Filter out inaccessible
    query2 = db.gis_location.id == jtable.location_id
    accessible = shn_accessible_query("read", db.gis_location)
    query2 = query2 & accessible

    features = db(query).select(db.gis_location.ALL, left = [db.gis_location.on(query2)])

    # Calculate an appropriate BBox
    bounds = gis.get_bounds(features=features)

    map = gis.show_map(
        feature_queries = [{"name" : "Features", "query" : features, "active" : True}],
        bbox = bounds,
        window = True,
        collapsed = True
    )

    return dict(map=map)

# -----------------------------------------------------------------------------
def geolocate():

    """
        Call a Geocoder service
    """
    
    if "location" in request.vars:
        location = request.vars.location
    else:
        session.error = T("Need to specify a location to search for.")
        redirect(URL(r=request, f="index"))

    if "service" in request.vars:
        service = request.vars.service
    else:
        # ToDo service=all should be default
        service = "google"

    if service == "google":
        return s3gis.GoogleGeocoder(location, db).get_kml()

    if service == "yahoo":
        return s3gis.YahooGeocoder(location, db).get_xml()

# -----------------------------------------------------------------------------
def proxy():
    """
    Based on http://trac.openlayers.org/browser/trunk/openlayers/examples/proxy.cgi
    This is a blind proxy that we use to get around browser
    restrictions that prevent the Javascript from loading pages not on the
    same server as the Javascript. This has several problems: it's less
    efficient, it might break some sites, and it's a security risk because
    people can use this proxy to browse the web and possibly do bad stuff
    with it. It only loads pages via http and https, but it can load any
    content type. It supports GET and POST requests.
    """

    import urllib2
    import cgi
    import sys, os

    # ToDo - need to link to map_service_catalogue
    # prevent Open Proxy abuse
    allowedHosts = []
    #allowedHosts = ["www.openlayers.org", "openlayers.org",
    #                "labs.metacarta.com", "world.freemap.in",
    #                "prototype.openmnnd.org", "geo.openplans.org",
    #                "sigma.openplans.org", "demo.opengeo.org",
    #                "www.openstreetmap.org", "sample.avencia.com",
    #                "v-swe.uni-muenster.de:8080"]

    method = request["wsgi"].environ["REQUEST_METHOD"]

    if method == "POST":
        # This can probably use same call as GET in web2py
        qs = request["wsgi"].environ["QUERY_STRING"]

        d = cgi.parse_qs(qs)
        if d.has_key("url"):
            url = d["url"][0]
        else:
            url = "http://www.openlayers.org"
    else:
        # GET
        #fs = cgi.FieldStorage()
        #url = fs.getvalue("url", "http://www.openlayers.org")
        if "url" in request.vars:
            url = request.vars.url
        else:
            session.error = str(T("Need a 'url' argument!"))
            raise HTTP(400, body=s3xrc.xml.json_message(False, 400, session.error))

    try:
        host = url.split("/")[2]
        if allowedHosts and not host in allowedHosts:
            msg = "Status: 502 Bad Gateway\n"
            msg += "Content-Type: text/plain\n\n"
            msg += "This proxy does not allow you to access that location (%s).\n\n" % (host,)

            msg += os.environ
            return msg

        elif url.startswith("http://") or url.startswith("https://"):
            if method == "POST":
                length = int(request["wsgi"].environ["CONTENT_LENGTH"])
                headers = {"Content-Type": request["wsgi"].environ["CONTENT_TYPE"]}
                body = request.body.read(length)
                r = urllib2.Request(url, body, headers)
                y = urllib2.urlopen(r)
            else:
                y = urllib2.urlopen(url)

            # print content type header
            # TODO: this doesn't work in web2py, need to figure out how that happens?
            #i = y.info()
            #if i.has_key("Content-Type"):
            # msg = "Content-Type: %s" % (i["Content-Type"])
            #else:
            # msg = "Content-Type: text/plain"

            #msg += "\n" + y.read()

            msg = y.read()
            y.close()
            return msg
        else:
            msg = "Content-Type: text/plain\n\n"

            msg += "Illegal request."
            return msg

    except Exception, E:
        msg = "Status: 500 Unexpected Error\n"
        msg += "Content-Type: text/plain\n\n"
        msg += "Some unexpected error occurred. Error text was: %s" % str(E)
        return msg

# -----------------------------------------------------------------------------
# Tests - not Production
def test():
    """
       Test Mapping API
    """

    # Will use default popup_url
    hospitals = {"feature_group" : "Hospitals"}

    if auth.is_logged_in():
        offices = {"feature_group" : "Offices", "popup_url" : URL(r=request, c="gis", f="location", args="update.popup")}
    else:
        offices = {"feature_group" : "Offices", "popup_url" : URL(r=request, c="gis", f="location", args="read.popup")}

    query = db((db.gis_feature_class.name == "Town") & (db.gis_location.feature_class_id == db.gis_feature_class.id)).select()

    html = gis.show_map(
                add_feature = True,
                collapsed = True,
                #feature_groups = [offices, hospitals],
                #feature_queries = [{"name" : "Towns", "query" : query, "active" : True}],
                #wms_browser = {"name" : "OpenGeo Demo WMS", "url" : "http://demo.opengeo.org/geoserver/ows?service=WMS&request=GetCapabilities"},
                ##wms_browser = {"name" : "Risk Maps", "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
                ##wms_browser = {"name" : "Risk Maps", "url" : "http://www.pdc.org/wms/wmservlet/PDC_Active_Hazards?request=getcapabilities&service=WMS&version=1.1.1"},
                #catalogue_overlays = True,
                #catalogue_toolbar = True,
                #legend = True, # Stops Feature Layers from Printing
                #toolbar = True,
                #search = True,
                #print_tool = {
                #        #"url" : "http://localhost:8080/geoserver/pdf/",                    # Local GeoServer
                #        "url" : "http://localhost:8080/print-servlet-1.2-SNAPSHOT/pdf/",    # Local Windows Tomcat
                #        #"url" : "http://host.domain:8180/print-servlet-1.2-SNAPSHOT/pdf/", # Linux Tomcat
                #        "mapTitle" : "Title",
                #        "subTitle" : "SubTitle"
                #    },
                ##mgrs = {"name" : "MGRS Atlas PDFs", "url" : "http://www.sharedgeo.org/datasets/shared/maps/usng/pdf.map?VERSION=1.0.0&SERVICE=WFS&request=GetFeature&typename=wfs_all_maps"},
                #window = True,
                )

    return dict(map=html)

def test2():
    " Test new OpenLayers functionality in a RAD environment "
    return dict()
