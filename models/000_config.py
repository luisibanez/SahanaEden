# -*- coding: utf-8 -*-

"""
    Deployment settings
    All settings which are typically edited for a deployment should be done here
    Deployers shouldn't typically need to edit any other files.
"""

def Tstr(text):
    """
       Convenience function for non-Web2Py modules
       (latest web2py no longer needs this)
    """
    return str(T(text))

s3cfg = local_import("s3cfg")
deployment_settings = s3cfg.S3Config(T)

# Database settings
deployment_settings.database.db_type = "sqlite"
deployment_settings.database.host = "localhost"
deployment_settings.database.port = "" # use default
deployment_settings.database.database = "sahana"
deployment_settings.database.username = "sahana"
deployment_settings.database.password = "password"
deployment_settings.database.pool_size = 30

# Authentication settings
# This setting should be changed _before_ registering the 1st user
deployment_settings.auth.hmac_key = "akeytochange"
# These settings should be changed _after_ the 1st (admin) user is
# registered in order to secure the deployment
deployment_settings.auth.registration_requires_verification = False
deployment_settings.auth.registration_requires_approval = False
deployment_settings.auth.openid = False

# Base settings
# Set this to the Public URL of the instance
deployment_settings.base.public_url = "http://127.0.0.1:8000"

# Switch to "False" in Production for a Performance gain
# (need to set to "True" again when Table definitions are changed)
deployment_settings.base.migrate = True

# Enable/disable pre-population of the database.
# Set to False during first run for manual DB migration in case this
# is explicitly required for a code upgrade, otherwise leave at True
# NOTE: the web UI will not be accessible while the DB is empty,
# instead run:
#   python web2py.py -S eden -M
# to create the db structure, then exit and re-import the data.
deployment_settings.base.prepopulate = True

# Email settings
# Outbound server
deployment_settings.mail.server = "127.0.0.1:25"
# Useful for Windows Laptops:
#deployment_settings.mail.server = "smtp.gmail.com:587"
#deployment_settings.mail.login = "username:password"
# From Address
deployment_settings.mail.sender = "'Sahana' <sahana@your.org>"
# Address to which mails get sent to approve new users
deployment_settings.mail.approver = "useradmin@your.org"

# L10n settings
# Uncomment this if the deployment is just in a few countries
# (used in the GIS Location Selector & maybe in future: Messaging)
#deployment_settings.L10n.countries = ["PK"]
# Languages used in the deployment (used for Language Toolbar & GIS Locations)
# http://www.loc.gov/standards/iso639-2/php/code_list.php
deployment_settings.L10n.languages = {
    "en":T("English"),
    "es":T("Spanish"),
    "pa":T("Punjabi"),
    "ps":T("Pashto"),
    "sd":T("Sindhi"),
    "ur":T("Urdu"),
    "zh-tw":T("Chinese (Taiwan)"),
    "seraiki":T("Seraiki"),
    "balochi":T("Balochi"),
}
# Default language for Language Toolbar (& GIS Locations in future)
deployment_settings.L10n.default_language = "en"
# Display the language toolbar
deployment_settings.L10n.display_toolbar = True
# Default timezone for users
deployment_settings.L10n.utc_offset = "UTC +0000"

# GIS (Map) settings
# Provide a tool to select locations via a map on all forms with location_id
deployment_settings.gis.map_selector = True
# Display Resources recorded to Admin-Level Locations on the map
deployment_settings.gis.display_L0 = False
# Currently unused
#deployment_settings.gis.display_L1 = True
# Allow non-MapAdmins to edit Admin locations?
# (defaults to True, if not set)
deployment_settings.gis.edit_L0 = False
deployment_settings.gis.edit_L1 = True
#deployment_settings.gis.edit_L2 = True
deployment_settings.gis.locations_hierarchy = {
    "L0":T("Country"),
    "L1":T("Province"),
    "L2":T("District"),
    "L3":T("Town"),
    "L4":T("Village")
}
# Do we have a spatial DB available? (currently unused. Will support PostGIS & Spatialite.)
deployment_settings.gis.spatialdb = False
# GeoServer (currently unused. Will allow REST control of GeoServer.)
deployment_settings.gis.geoserver_url = "http://localhost/geoserver"
deployment_settings.gis.geoserver_username = "admin"
deployment_settings.gis.geoserver_password = "password"


# Security Policy settings
# Lock-down access to Map Editing
#deployment_settings.security.map = True
# Currently unused
#deployment_settings.security.policy = 2 # Editor

# Comment/uncomment modules here to disable/enable them
# Modules menu is defined in 01_menu.py
from gluon.storage import Storage
deployment_settings.modules = Storage(
    default = Storage(
            name_nice = Tstr("Home"),
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = 0     # This item is always 1st in the menu
        ),
    admin = Storage(
            name_nice = Tstr("Administration"),
            description = Tstr("Site Administration"),
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = 0     # This item is handled separately in the menu
        ),
    gis = Storage(
            name_nice = Tstr("Map"),
            description = Tstr("Situation Awareness & Geospatial Analysis"),
            module_type = 1,     # 1st item in the menu
            resources = Storage(
                gis_location = {'importer' : True}
             )
        ),
    mpr = Storage(
            name_nice = Tstr("Missing Persons"),
            description = Tstr("Helps to report and search for Missing Persons"),
            module_type = 2,
        ),
    rms = Storage(
            name_nice = Tstr("Requests"),
            description = Tstr("Tracks requests for aid and matches them against donors who have pledged aid"),
            module_type = 3,
            resources = Storage(
                rms_req = {'importer' : True},
            )
        ),
    hms = Storage(
            name_nice = Tstr("Hospitals"),
            description = Tstr("Helps to monitor status of hospitals"),
            module_type = 4,
            resources = Storage(
                hms_hospital = {'importer' : True}
            )
        ),
    vol = Storage(
            name_nice = Tstr("Volunteers"),
            description = Tstr("Manage volunteers by capturing their skills, availability and allocation"),
            module_type = 5,
        ),
    logs = Storage(
            name_nice = Tstr("Logistics Management"),
            description = Tstr("Managing, Storing and Distributing Relief Items"),
            module_type = 10
        ),
    project = Storage(
            name_nice = Tstr("Project Management"),
            description = Tstr("Project Activities"),
            module_type = 10
        ),
    msg = Storage(
            name_nice = Tstr("Messaging"),
            description = Tstr("Sends & Receives Alerts via Email & SMS"),
            module_type = 10,
        ),
    flood = Storage(
            name_nice = Tstr("Flood Alerts"),
            description = Tstr("Flood Alerts show water levels in various parts of the country"),
            module_type = 10
        ),
    sitrep = Storage(
            name_nice = Tstr("Assessments"),
            description = Tstr("Assessments are structured reports done by Professional Organisations - data includes WFP Assessments (Rapid Assessment Tool to come)"),
            module_type = 10
        ),
    rat = Storage(
            name_nice = Tstr("Rapid Assessments"),
            description = Tstr("Assessments are structured reports done by Professional Organisations"),
            module_type = 10
        ),
    pr = Storage(
            name_nice = Tstr("Person Registry"),
            description = Tstr("Central point to record details on People"),
            module_type = 10,
            resources = Storage(
                pr_address = {'importer' : True},
                pr_pe_contact = {'importer' : True},
                pr_presence = {'importer' : True},
	 	        pr_identity = {'importer' : True},
                pr_person = {'importer' : True},
                pr_group = {'importer' : True},
                pr_group_membership = {'importer' : True},
            )
        ),
    dvi = Storage(
            name_nice = Tstr("Disaster Victim Identification"),
            description = Tstr("Disaster Victim Identification"),
            module_type = 10,
            resources = Storage(
                dvi_recreq = {'importer' : True},
            )
        ),
    #dvr = Storage(
    #        name_nice = Tstr("Disaster Victim Registry"),
    #        description = Tstr("Traces internally displaced people (IDPs) and their needs"),
    #        module_type = 10
    #    ),
    budget = Storage(
            name_nice = Tstr("Budgeting Module"),
            description = Tstr("Allows a Budget to be drawn up"),
            module_type = 10,
            resources = Storage(
                budget_item = {'importer' : True},
                budget_kit = {'importer' : True},
                budget_bundle = {'importer' : True},
            )
        ),
    cr = Storage(
            name_nice = Tstr("Shelter Registry"),
            description = Tstr("Tracks the location, distibution, capacity and breakdown of victims in Shelters"),
            module_type = 10,
            resources = Storage(
                cr_shelter = {'importer' : True }
            )
        ),
    delphi = Storage(
         name_nice = Tstr("Delphi Decision Maker"),
            description = Tstr("Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list."),
            module_type = 10,
        ),
    doc = Storage(
            name_nice = Tstr("Documents and Photos"),
            description = Tstr("A library of digital resources, such as photos, documents and reports"),
            module_type = 10,
        ),
    irs = Storage(
        name_nice = Tstr("Incident Reporting"),
        description = Tstr("Incident Reporting System"),
        module_type = 10
    ),
    org = Storage(
         name_nice = Tstr("Organization Registry"),
            description = Tstr('Lists "who is doing what & where". Allows relief agencies to coordinate their activities'),
            module_type = 10,
            resources = Storage(
                org_organisation = {'importer' : True},
                org_office = {'importer' : True},
                org_project = {'importer' : True},
                org_staff = {'importer' : True},
                org_task = {'importer' : True}
            )
        ),
    ticket = Storage(
            name_nice = Tstr("Ticketing Module"),
            description = Tstr("Master Message Log to process incoming reports & requests"),
            module_type = 10,
        ),
    importer = Storage(
    	     name_nice = "Spreadsheet Importer",
    	     description = "Used to import data from spreadsheets into the database",
    	     module_type = 10,
    )
    #lms = Storage(
    #        name_nice = Tstr("Logistics Management System"),
    #        description = Tstr("An intake system, a warehouse management system, commodity tracking, supply chain management, procurement and other asset and resource management capabilities."),
    #        module_type = 10
    #    ),
)