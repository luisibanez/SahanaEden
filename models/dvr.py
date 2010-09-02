# -*- coding: utf-8 -*-

"""
    DVR Disaster Victim Registry (Sahana Legacy)

    @author nursix
"""

module = "dvr"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    table = module + "_" + resource
    db.define_table(table,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)
