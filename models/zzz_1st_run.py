# -*- coding: utf-8 -*-

# 1st-run initialisation
# designed to be called from Crontab's @reboot
# however this isn't reliable (doesn't work on Win32 Service) so still in models for now...

# Deployments can change settings live via appadmin

# Set to False in Production (to save 1x DAL hit every page)
if db(db["s3_setting"].id > 0).count() or \
   not deployment_settings.get_base_prepopulate():
    empty = False
else:
    empty = True

if empty:

    # Themes
    tablename = "admin_theme"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            name = T("Sahana Blue"),
            logo = "img/sahanapy_logo.png",
            #header_background = "img/header_bg.png",
            #footer = "footer.html",
            text_direction = "ltr",
            col_background = "336699",
            col_menu = "0066cc",
            col_highlight = "0077aa",
            col_txt_background = "f3f6ff",
            col_txt_border = "c6d1f5",
            col_txt_underline = "003366",
            col_txt = "006699",
            col_input = "ffffcc",
            col_border_btn_out = "6699cc",
            col_border_btn_in = "4589ce",
            col_btn_hover = "3377bb",
        )
        table.insert(
            name = T("Sahana Green"),
            logo = "img/sahanapy_logo_green.png",
            #header_background = "img/header_bg.png",
            #footer = "footer.html",
            text_direction = "ltr",
            col_background = "337733",
            col_menu = "cc7722",
            col_highlight = "338833",
            col_txt_background = "f3f6ff",
            col_txt_border = "c6d1f5",
            col_txt_underline = "003366",
            col_txt = "006699",
            col_input = "ffffcc",
            col_border_btn_out = "6699cc",
            col_border_btn_in = "4589ce",
            col_btn_hover = "3377bb",
        )
        table.insert(
            # Needs work
            # - some colours need changing independently of each other
            # - logo size needs storing
            name = T("Sahana Steel"),
            logo = "img/sahanapy_logo_ideamonk.png",
            #header_background = "img/header_bg.png",
            #footer = "footer.html",
            text_direction = "ltr",
            col_background = "dbdbdb",
            col_menu = "0066cc",
            col_highlight = "0077aa",
            col_txt_background = "f3f6ff",
            col_txt_border = "c6d1f5",
            col_txt_underline = "003366",
            col_txt = "eeeeee",
            col_input = "ffffcc",
            col_border_btn_out = "c6d1f5",
            col_border_btn_in = "4589ce",
            col_btn_hover = "3377bb",
        )

    # Global Settings
    tablename = "s3_setting"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            admin_name = T("Sahana Administrator"),
            admin_email = "support@Not Set",
            admin_tel = T("Not Set"),
            theme = 1
        )

    tablename = "admin_setting"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    tablename = "appadmin_setting"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    tablename = "gis_setting"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Person Registry
    tablename = "pr_setting"
    table = db[tablename]
    if not db(table.id > 0).count():
       table.insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Organisation Registry
    tablename = "org_setting"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    tablename = "org_sector"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert( name = "Agriculture" )
        table.insert( name = "Shelter and Non-Food Items" )
        table.insert( name = "Coordination and Support Services" )
        table.insert( name = "Food" )
        table.insert( name = "Infrastructure and Rehabilitation" )
        table.insert( name = "Security" )
        table.insert( name = "Water and Sanitation" )
        table.insert( name = "Education" )
        table.insert( name = "Health" )
        table.insert( name = "Protection and Human Rights and Rule of Law" )
        table.insert( name = "Urban Search and Rescue" )

    # Synchronisation
    tablename = "sync_setting"
    table = db[tablename]
    if not db(table.id > 0).count():
       table.insert(
            uuid = uuid.uuid4()
        )

    # Logistics
    if "lms" in deployment_settings.modules:
        tablename = "lms_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

        tablename = "lms_catalog"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                name="Default",
                description="Default Catalog",
                comments="All items are by default added to this Catalog"
            )

    # Budget Module
    if "budget" in deployment_settings.modules:
        tablename = "budget_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

        tablename = "budget_parameter"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
            )

    # Shelter Registry
    if "cr" in deployment_settings.modules:
        tablename = "cr_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

    # Disaster Victim Identification
    if "dvi" in deployment_settings.modules:
        tablename = "dvi_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

    # Disaster Victim Registration
    if "dvr" in deployment_settings.modules:
        tablename = "dvr_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

    # Human Remains Management
    if "hrm" in deployment_settings.modules:
        tablename = "hrm_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

    # Incident Reporting System
    if "irs" in deployment_settings.modules:
        tablename = "irs_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )
        # Categories visible to ends-users by default
        tablename = "irs_icategory"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(code = "flood")
            table.insert(code = "geophysical.landslide")
            table.insert(code = "roadway.bridgeClosure")
            table.insert(code = "roadway.roadwayClosure")
            table.insert(code = "other.buildingCollapsed")
            table.insert(code = "other.peopleTrapped")
            table.insert(code = "other.powerFailure")

    # Messaging Module
    if "msg" in deployment_settings.modules:
        tablename = "msg_email_settings"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                inbound_mail_server = "imap.gmail.com",
                inbound_mail_type = "imap",
                inbound_mail_ssl = True,
                inbound_mail_port = 993,
                inbound_mail_username = "username",
                inbound_mail_password = "password",
                inbound_mail_delete = False,
                #outbound_mail_server = "mail:25",
                #outbound_mail_from = "demo@sahanafoundation.org",
            )
        tablename = "msg_modem_settings"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(modem_baud=115200)
        tablename = "msg_gateway_settings"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(to_variable = "to")
        tablename = "msg_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                audit_read = False,
                audit_write = False,
                outgoing_sms_handler = "Gateway"
                )


    # Missing Person Registry
    if "mpr" in deployment_settings.modules:
        tablename = "mpr_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

    # Request Management System
    if "rms" in deployment_settings.modules:
        tablename = "rms_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

    # Ticketing System
    if "ticket" in deployment_settings.modules:
        tablename = "ticket_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )
        tablename = "ticket_category"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( name = "Report Missing Person" )
            table.insert( name = "Report Security Incident" )
            table.insert( name = "Report Information" )
            table.insert( name = "Request for Assistance" )
            table.insert( name = "Offer of Help" )


    # Volunteer Management
    if "vol" in deployment_settings.modules:
        tablename = "vol_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                # If Disabled at the Global Level then can still Enable just for this Module here
                audit_read = False,
                audit_write = False
            )

    # GIS Module
    tablename = "gis_marker"
    table = db[tablename]
    # Can't do sub-folders :/
    # need a script to read in the list of default markers from the filesystem, copy/rename & populate the DB 1 by 1
    if not db(table.id > 0).count():
        # We want to start at ID 1
        table.truncate()
        table.insert(
            name = "marker_red",
            image = "gis_marker.image.marker_red.png"
        )
        table.insert(
            name = "marker_yellow",
            image = "gis_marker.image.marker_yellow.png"
        )
        table.insert(
            name = "marker_amber",
            image = "gis_marker.image.marker_amber.png"
        )
        table.insert(
            name = "marker_green",
            image = "gis_marker.image.marker_green.png"
        )
        table.insert(
            name = "person",
            image = "gis_marker.image.Civil_Disturbance_Theme.png"
        )
        table.insert(
            name = "school",
            image = "gis_marker.image.Edu_Schools_S1.png"
        )
        table.insert(
            name = "food",
            image = "gis_marker.image.Emergency_Food_Distribution_Centers_S1.png"
        )
        table.insert(
            name = "shelter",
            image = "gis_marker.image.Emergency_Shelters_S1.png"
        )
        table.insert(
            name = "office",
            image = "gis_marker.image.Emergency_Operations_Center_S1.png"
        )
        table.insert(
            name = "activity",
            image = "gis_marker.image.Emergency_Teams_S1.png"
        )
        table.insert(
            name = "hospital",
            image = "gis_marker.image.E_Med_Hospital_S1.png"
        )
        table.insert(
            name = "earthquake",
            image = "gis_marker.image.Geo_Earth_Quake_Epicenter.png"
        )
        table.insert(
            name = "volcano",
            image = "gis_marker.image.Geo_Volcanic_Threat.png"
        )
        table.insert(
            name = "tsunami",
            image = "gis_marker.image.Hydro_Meteor_Tsunami_ch.png"
        )
        table.insert(
            name = "church",
            image = "gis_marker.image.Public_Venue_Church_S1.png"
        )
        table.insert(
            name = "temple",
            image = "gis_marker.image.Public_Venue_Temple_S1.png"
        )
        table.insert(
            name = "mosque",
            image = "gis_marker.image.Public_Venue_Mosque_S1.png"
        )
        table.insert(
            name = "phone",
            image = "gis_marker.image.SMS_Message_Phone.png"
        )
        table.insert(
            name = "orphanage",
            image = "gis_marker.image.Special_Needs_Child_Day_Care_S1.png"
        )
        table.insert(
            name = "airport",
            image = "gis_marker.image.Trans_Airport_S1.png"
        )
        table.insert(
            name = "bridge",
            image = "gis_marker.image.Trans_Bridge_S1.png"
        )
        table.insert(
            name = "helicopter",
            image = "gis_marker.image.Trans_Helicopter_Landing_Site_S1.png"
        )
        table.insert(
            name = "port",
            image = "gis_marker.image.Trans_Port_S1.png"
        )
        table.insert(
            name = "rail_station",
            image = "gis_marker.image.Trans_Rail_Station_S1.png"
        )
        table.insert(
            name = "vehicle",
            image = "gis_marker.image.Transport_Vehicle_Theme.png"
        )
        table.insert(
            name = "water",
            image = "gis_marker.image.Water_Supply_Infrastructure_Theme_S1.png"
        )
        table.insert(
            name = "volunteer",
            image = "gis_marker.image.Volunteer.png"
        )
    tablename = "gis_symbology"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            name = "Australasia"
        )
        table.insert(
            name = "Canada"
        )
        table.insert(
            name = "US"
        )
    tablename = "gis_projection"
    table = db[tablename]
    if not db(table.id > 0).count():
       # We want to start at ID 1
       table.truncate()
       table.insert(
            uuid = "www.sahanafoundation.org/GIS-PROJECTION-900913",
            name = "Spherical Mercator",
            epsg = 900913,
            maxExtent = "-20037508, -20037508, 20037508, 20037508.34",
            maxResolution = 156543.0339,
            units = "m"
        )
       table.insert(
            uuid = "www.sahanafoundation.org/GIS-PROJECTION-4326",
            name = "WGS84",
            epsg = 4326,
            maxExtent = "-180,-90,180,90",
            maxResolution = 1.40625,
            units = "degrees"
            # OSM use these:
            #maxResolution = 156543.0339,
            #units = "m"
        )

    tablename = "gis_config"
    table = db[tablename]
    if not db(table.id > 0).count():
       # We want to start at ID 1
       table.truncate()
       table.insert(
            lat = "51.8",
            lon = "-1.3",
            zoom = 7,
            # Doesn't work on Postgres! (db.commit() the previous step?)
            projection_id = 1,
            marker_id = 1,
            map_height = 600,
            map_width = 800,
            symbology_id = db(db.gis_symbology.name == "US").select(limitby=(0, 1)).first().id,
        )

    tablename = "gis_feature_class"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-TRACK",
            name = "Track",
            gps_marker = "TracBack Point",
            module = "gis",
            resource = "track"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L0",
            name = "Country",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L1",
            name = "Province",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L2",
            name = "District",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L3",
            name = "Town",
            gps_marker = "City (Medium)",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L4",
            name = "Village",
            gps_marker = "City (Small)",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-AIRPORT",
            name = "Airport",
            marker_id = db(db.gis_marker.name == "airport").select(limitby=(0, 1)).first().id,
            gps_marker = "Airport",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-BRIDGE",
            name = "Bridge",
            marker_id = db(db.gis_marker.name == "bridge").select(limitby=(0, 1)).first().id,
            gps_marker = "Bridge",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-CHURCH",
            name = "Church",
            marker_id = db(db.gis_marker.name == "church").select(limitby=(0, 1)).first().id,
            gps_marker = "Church",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-FOOD",
            name = "Food",
            marker_id = db(db.gis_marker.name == "food").select(limitby=(0, 1)).first().id,
            gps_marker = "Restaurant",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-HOSPITAL",
            name = "Hospital",
            marker_id = db(db.gis_marker.name == "hospital").select(limitby=(0, 1)).first().id,
            gps_marker = "Medical Facility",
            module = "hms",
            resource = "hospital"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-INCIDENT",
            name = "Incident",
            gps_marker = "Danger Area",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-OFFICE",
            name = "Office",
            marker_id = db(db.gis_marker.name == "office").select(limitby=(0, 1)).first().id,
            gps_marker = "Building",
            module = "or",
            resource = "office"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PERSON",
            name = "Person",
            marker_id = db(db.gis_marker.name == "person").select(limitby=(0, 1)).first().id,
            gps_marker = "Contact, Dreadlocks",
            module = "pr",
            resource = "person"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PORT",
            name = "Port",
            marker_id = db(db.gis_marker.name == "port").select(limitby=(0, 1)).first().id,
            gps_marker = "Marina",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PROJECT",
            name = "Project",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SCHOOL",
            name = "School",
            marker_id = db(db.gis_marker.name == "school").select(limitby=(0, 1)).first().id,
            gps_marker = "School",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SHELTER",
            name = "Shelter",
            marker_id = db(db.gis_marker.name == "shelter").select(limitby=(0, 1)).first().id,
            gps_marker = "Campground",
            module = "cr",
            resource = "shelter"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SMS",
            name = "SMS",
            marker_id = db(db.gis_marker.name == "phone").select(limitby=(0, 1)).first().id,
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-VEHICLE",
            name = "Vehicle",
            marker_id = db(db.gis_marker.name == "vehicle").select(limitby=(0, 1)).first().id,
            gps_marker = "Car",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-VOLUNTEER",
            name = "Volunteer",
            marker_id = db(db.gis_marker.name == "volunteer").select(limitby=(0, 1)).first().id,
            gps_marker = "Contact, Dreadlocks",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-WAREHOUSE",
            name = "Warehouse",
            gps_marker = "Building",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-WATER",
            name = "Water",
            marker_id = db(db.gis_marker.name == "water").select(limitby=(0, 1)).first().id,
            gps_marker = "Drinking Water",
        )
    tablename = "gis_apikey"
    table = db[tablename]
    if not db(table.id > 0).count():
       table.insert(
            name = "google",
            apikey = "ABQIAAAAgB-1pyZu7pKAZrMGv3nksRRi_j0U6kJrkFvY4-OX2XYmEAa76BSH6SJQ1KrBv-RzS5vygeQosHsnNw",
            description = "localhost"
        )
       table.insert(
            name = "yahoo",
            apikey = "euzuro-openlayers",
            description = "trial - replace for Production use"
        )
       table.insert(
            name = "multimap",
            apikey = "metacarta_04",
            description = "trial - replace for Production use"
        )
    tablename = "gis_layer_openstreetmap"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        for subtype in gis_layer_openstreetmap_subtypes:
            if subtype in ["Taiwan"]:
                # Local OSM layers should be disabled by default in default builds
                table.insert(
                        name = "OSM " + subtype,
                        subtype = subtype,
                        enabled = False
                    )
            else:
                table.insert(
                        name = "OSM " + subtype,
                        subtype = subtype
                    )
    tablename = "gis_layer_google"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        for subtype in gis_layer_google_subtypes:
            table.insert(
                    name = "Google " + subtype,
                    subtype = subtype,
                    enabled = False
                )
    tablename = "gis_layer_yahoo"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        for subtype in gis_layer_yahoo_subtypes:
            table.insert(
                    name = "Yahoo " + subtype,
                    subtype = subtype,
                    enabled = False
                )
    #tablename = "gis_layer_bing"
    #table = db[tablename]
    #if not db(table.id > 0).count():
        # Populate table
    #    for subtype in gis_layer_bing_subtypes:
    #        table.insert(
    #                name = "Bing " + subtype,
    #                subtype = subtype,
    #                enabled = False
    #            )
    tablename = "gis_layer_mgrs"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        table.insert(
                name = "MGRS Atlas PDFs",
                description = "http://en.wikipedia.org/wiki/Military_grid_reference_system",
                url = "http://www.sharedgeo.org/datasets/shared/maps/usng/pdf.map?VERSION=1.0.0&SERVICE=WFS&request=GetFeature&typename=wfs_all_maps",
                enabled = False
            )
    tablename = "gis_layer_wms"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        table.insert(
                name = "VMap0",
                description = "A Free low-resolution Vector Map of the whole world",
                url = "http://labs.metacarta.com/wms/vmap0",
                #projection_id = db(db.gis_projection.epsg == 4326).select(limitby=(0, 1)).first().id,
                layers = "basic",
                enabled = False
            )
        table.insert(
                name = "Blue Marble",
                description = "A composite of four months of MODIS observations with a spatial resolution (level of detail) of 1 square kilometer per pixel.",
                url = "http://maps.opengeo.org/geowebcache/service/wms",
                #projection_id = db(db.gis_projection.epsg == 4326).select(limitby=(0, 1)).first().id,
                layers = "bluemarble",
                enabled = False
            )
    tablename = "gis_layer_georss"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        table.insert(
                name = "Earthquakes",
                description = "USGS: Global 7-day",
                url = "http://earthquake.usgs.gov/eqcenter/catalogs/eqs7day-M2.5.xml",
                projection_id = db(db.gis_projection.epsg == 4326).select(limitby=(0, 1)).first().id,
                marker_id = db(db.gis_marker.name == "earthquake").select(limitby=(0, 1)).first().id,
                enabled = False
            )
        table.insert(
                name = "Volcanoes",
                description = "USGS: US recent",
                url = "http://volcano.wr.usgs.gov/rss/vhpcaprss.xml",
                projection_id = db(db.gis_projection.epsg == 4326).select(limitby=(0, 1)).first().id,
                marker_id = db(db.gis_marker.name == "volcano").select(limitby=(0, 1)).first().id,
                enabled = False
            )

    tablename = "gis_location"
    table = db[tablename]
    if not db(table.id > 0).count():
        # L0 Countries
        import_file = os.path.join(request.folder,
                                   "private", "import",
                                   "countries.csv")
        table.import_from_csv_file(open(import_file,"r"))

    # Authorization
    # User Roles (uses native Web2Py Auth Groups)
    table = auth.settings.table_group_name
    if not db(db[table].id > 0).count():
        # The 1st 4 permissions are hard-coded for performance reasons
        # This must stay as id=1
        auth.add_group("Administrator", description = "System Administrator - can access & make changes to any data")
        # This must stay as id=2
        auth.add_group("Authenticated", description = "Authenticated - all logged-in users")
        # This must stay as id=3
        auth.add_group("Creator", description = "Creator - dummy role which isn't meant to have users added to it. Used to restrict records to just those created by the user")
        # Optional roles for delegating access
        # This must stay as id=4
        auth.add_group("Editor", description = "Editor - can access & make changes to any unprotected data")
        auth.add_group("UserAdmin", description = "UserAdmin - allowed to manage the membership of the Editor role")
        #auth.add_group("Restricted", description = "Restricted - is given a simplified full-screen view so as to minimise the possibility of errors")
        # GIS
        auth.add_group("MapAdmin", description = "MapAdmin - allowed access to edit the MapService Catalogue")
        # DVI
        auth.add_group("DVI", description = "DVI - allowed access to the DVI module")
        # HMS
        auth.add_group("HMSAdmin", description = "HMSAdmin - full access to HMS")
        auth.add_group("HMSOfficer", description = "HMSOfficer - permission to edit requests and pledges")
        auth.add_group("HMSFacility", description = "HMSFacility - permission to submit status and requests")
        auth.add_group("HMSOrg", description = "HMSOrg - permission to submit pledges")
        auth.add_group("HMSViewer", description = "HMSViewer - permission to access HMS")
        # Ticketing
        auth.add_group("TicketAdmin", description = "TicketAdmin - full access to Ticketing")

    # Supply / Inventory
    tablename = "supply_item_category"
    table = db[tablename]
    if not db(table.id > 0).count():
        shn_import_table("supply_item_category")
    tablename = "supply_item"
    table = db[tablename]
    if not db(table.id > 0).count():
        shn_import_table("supply_item")


    # Security Defaults for all tables (if using 'full' security policy)
    if session.s3.security_policy != 1:
        table = auth.settings.table_permission_name
        if not db(db[table].id>0).count():
            # For performance we only populate this once (at system startup)
            # => need to populate manually when adding new tables to the database! (less RAD)
            authenticated = auth.id_group("Authenticated")
            #editors = auth.id_group("Editor")
            for tablename in db.tables:
                table = db[tablename]
                # allow all registered users the ability to Read all records
                auth.add_permission(authenticated, "read", table)
                # allow anonymous users the ability to Read all records
                #auth.add_permission(anonymous, "read", table)
                # Editors can make changes
                auth.add_permission(editors, "create", table)
                auth.add_permission(editors, "update", table)
                auth.add_permission(editors, "delete", table)

            # Module-specific defaults can be set here
            #table = pr_person
            # Clear out defaults
            #auth.del_permission(authenticated, "read", table)
            #auth.del_permission(editors, "create", table)
            #auth.del_permission(editors, "update", table)
            #auth.del_permission(editors, "delete", table)
            # Add specific Role(s)
            #id = auth.id_group("myrole")
            #auth.add_permission(id, "read", table)
            #auth.add_permission(id, "create", table)
            #auth.add_permission(id, "update", table)
            #auth.add_permission(id, "delete", table)

