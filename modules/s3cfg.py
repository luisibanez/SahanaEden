# -*- coding: utf-8 -*-

from gluon.http import HTTP
from gluon.storage import Storage

class S3Config(Storage):

    def __init__(self, T):
        self.auth = Storage()
        self.base = Storage()
        self.database = Storage()
        self.gis = Storage()
        self.mail = Storage()
        self.L10n = Storage()
        self.security = Storage()
        self.T = T

    # Auth settings
    def get_auth_hmac_key(self):
        return self.auth.get("hmac_key", "akeytochange")
    def get_auth_registration_requires_verification(self):
        return self.auth.get("registration_requires_verification", False)
    def get_auth_registration_requires_approval(self):
        return self.auth.get("registration_requires_approval", False)
    def get_auth_openid(self):
        return self.auth.get("openid", False)

    # Base settings
    def get_base_public_url(self):
        return self.base.get("public_url", "http://127.0.0.1:8000")
    def get_base_migrate(self):
        return self.base.get("migrate", True)
    def get_base_prepopulate(self):
        return self.base.get("prepopulate", True)

    # Database settings
    def get_database_string(self):
        db_type = self.database.get("db_type", "sqlite")
        pool_size = self.database.get("pool_size", 0)
        if (db_type == "sqlite"):
            db_string = "sqlite://storage.db"
        elif (db_type == "mysql"):
            db_string = "mysql://%s:%s@%s/%s" % \
                        (self.database.get("username", "sahana"),
                         self.database.get("password", "password"),
                         self.database.get("host", "localhost"),
                         self.database.get("database", "sahana"))
        elif (db_type == "postgres"):
            db_string = "postgres://%s:%s@%s/%s" % \
                        (self.database.get("username", "sahana"),
                         self.database.get("password", "password"),
                         self.database.get("host", "localhost"),
                         self.database.get("database", "sahana"))
        else:
            raise HTTP(501, body="Database type '%s' not recognised - please correct file models/000_config.py." % db_type)
        if pool_size:
            return (db_string, pool_size)
        else:
            return db_string

    # GIS (Map) Settings
    def get_gis_locations_hierarchy(self):
        T = self.T
        gis_location_hierarchy = {
            "L0":T("Country"),
            "L1":T("Province"),
            "L2":T("District"),
            "L3":T("Town"),
            "L4":T("Village")
        }
        return self.gis.get("locations_hierarchy", gis_location_hierarchy)
    def get_gis_map_selector(self):
        return self.gis.get("map_selector", True)
    def get_gis_display_l0(self):
        return self.gis.get("display_L0", False)
    def get_gis_display_l1(self):
        return self.gis.get("display_L1", True)
    def get_gis_edit_l0(self):
        return self.gis.get("edit_L0", True)
    def get_gis_edit_l1(self):
        return self.gis.get("edit_L1", True)
    def get_gis_edit_l2(self):
        return self.gis.get("edit_L2", True)
    def get_gis_edit_l3(self):
        return self.gis.get("edit_L3", True)
    def get_gis_edit_l4(self):
        return self.gis.get("edit_L4", True)
    def get_gis_edit_l5(self):
        return self.gis.get("edit_L5", True)
    def get_gis_geoserver_url(self):
        return self.gis.get("geoserver_url", "http://localhost/geoserver")
    def get_gis__username(self):
        return self.gis.get("geoserver_username", "admin")
    def get_gis_geoserver_password(self):
        return self.gis.get("geoserver_password", "password")
    def get_gis_spatialdb(self):
        return self.gis.get("spatialdb", False)
    
    # L10N Settings
    def get_L10n_countries(self):
        return self.L10n.get("countries", "")
    def get_L10n_default_language(self):
        return self.L10n.get("default_language", "en")
    def get_L10n_display_toolbar(self):
        return self.L10n.get("display_toolbar", True)
    def get_L10n_languages(self):
        return self.L10n.get("languages", { "en":self.T("English") })
    def get_L10n_utc_offset(self):
        return self.L10n.get("utc_offset", "UTC +0000")

    # Mail settings
    def get_mail_server(self):
        return self.mail.get("server", "127.0.0.1:25")
    def get_mail_server_login(self):
        return self.mail.get("login", False)
    def get_mail_sender(self):
        return self.mail.get("sender", "sahana@your.org")
    def get_mail_approver(self):
        return self.mail.get("approver", "useradmin@your.org")

    # Security Settings
    def get_security_policy(self):
        return self.security.get("policy", 1)
    def get_security_map(self):
        return self.security.get("map", False)

    # Active modules list
    def has_module(self, module_name):
        if not self.modules:
            _modules = [
                "admin",        # Admin
                "gis",          # GIS
                "doc",          # Document Library
                "pr",           # Person Registry
                "org",          # Organisation Registry
                "budget",       # Budgetting
                "cr",           # Camp Registry
                "delphi",       # Delphi Decision Maker
                "dvi",          # Disaster Victim Identification
                "dvr",          # Disaster Victim Registry
                "hms",          # Hospital Management
                #"lms",          # Logistics
                "mpr",          # Missing Person Registry
                "msg",          # Messaging
                #"nim",          # Nursing Information Manager
                "rms",          # Request Management
                "ticket",       # Ticketing
                "vol"           # Volunteer Management
            ]
        else:
            _modules = self.modules

        return module_name in _modules
