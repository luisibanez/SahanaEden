# -*- coding: utf-8 -*-

"""
    Admin module
"""

import cPickle as pickle

module = "admin"

# Settings
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)

# Import Jobs
resource = "import_job"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("module", "string",
                      default="org", notnull=True),
                Field("resource", "string",
                      widget=SQLFORM.widgets.options.widget,
                      default="organisation", notnull=True),
                Field("description", "string", notnull=True),
                Field("source_file", "upload", notnull=True),
                Field("status", "string", default="new", writable=False),
                Field("column_map", "blob", writable=False, readable=False),
                Field("failure_reason", "string", writable=False),
                timestamp,
                authorstamp,
                migrate=migrate)
table.status.requires = IS_IN_SET(["new", "failed", "processing", "completed"])
modules_list = []
for module in deployment_settings.modules:
    modules_list.append(module)
table.module.requires = IS_IN_SET(modules_list)
# TODO(mattb): These need to be pulled dynamically!!
table.resource.requires = IS_IN_SET(["organisation", "office", "staff"])


# Import lines
def display_dict_pickle_as_str(data):
    try:
        t = pickle.loads(data)
    except pickle.UnpicklingError:
        t = {}
    return ", ".join(["%s: %s" % (k, v) for k, v in t.iteritems() if v])


def display_status_select(data):
    if data in ["ignore", "imported"]:
        return data
    return SELECT("ignore", "import", value=data, _class="import_line_status")

resource = "import_line"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("import_job", db.admin_import_job, writable=False),
                Field("line_no", "integer"),
                Field("valid", "boolean", writable=False),
                Field("errors", "string", writable=False),
                Field("status", "string",
                      represent=display_status_select),
                Field("data", "blob", writable=False,
                      represent=display_dict_pickle_as_str),
                migrate=migrate)
table.import_job.requires = IS_IN_DB(db, "admin_import_job.id", "%(description)")
table.status.requires = IS_IN_SET(["ignore", "import", "imported"])

