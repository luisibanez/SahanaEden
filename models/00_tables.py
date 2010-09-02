# -*- coding: utf-8 -*-

"""
    Global tables and re-usable fields
"""

# Reusable timestamp fields to include in other table definitions
timestamp = db.Table(None, "timestamp",
            Field("created_on", "datetime",
                          readable=False,
                          writable=False,
                          default=request.utcnow),
            Field("modified_on", "datetime",
                          readable=False,
                          writable=False,
                          default=request.utcnow,
                          update=request.utcnow)
            )

# Reusable Author fields to include in other table definitions
# TODO: make a better represent!
def shn_user_represent(id):
    def user_represent(id):
        table = db.auth_user
        user = db(table.id == id).select(table.email, limitby=(0, 1))
        if user:
            user = user.first()
            return user.email
        return None
    return cache.ram("repr_user_%s" % id,
                     lambda: user_represent(id), time_expire=10)

authorstamp = db.Table(None, "authorstamp",
            Field("created_by", db.auth_user,
                          readable=False, # Enable when needed, not by default
                          writable=False,
                          default=session.auth.user.id if auth.is_logged_in() else None,
                          represent = lambda id: id and shn_user_represent(id) or UNKNOWN_OPT,
                          ondelete="RESTRICT"),
            Field("modified_by", db.auth_user,
                          readable=False, # Enable when needed, not by default
                          writable=False,
                          default=session.auth.user.id if auth.is_logged_in() else None,
                          update=session.auth.user.id if auth.is_logged_in() else None,
                          represent = lambda id: id and shn_user_represent(id) or UNKNOWN_OPT,
                          ondelete="RESTRICT")
            )

comments = db.Table(None, "comments",
                    Field("comments", "text",
                          comment = DIV(_class="tooltip",
                                        _title=Tstr("Comments") + "|" +Tstr("Please use this field to record any additional information, including a history of the record if it is updated."))))

# Reusable UUID field to include in other table definitions
s3uuid = SQLCustomType(
                type = "string",
                native = "VARCHAR(128)",
                encoder = (lambda x: "'%s'" % (uuid.uuid4() if x == "" else str(x).replace("'", "''"))),
                decoder = (lambda x: x)
            )

uuidstamp = db.Table(None, "uuidstamp",
            Field("uuid",
                  type=s3uuid,
                  length=128,
                  notnull=True,
                  unique=True,
                  readable=False,
                  writable=False,
                  default=""),
            Field("mci", "integer", # Master-Copy-Index
                  default=0,
                  readable=False,
                  writable=False))
# Reusable Deletion_Status field to include in other table definitions
deletion_status = db.Table(None, "deletion_status",
                    Field("deleted", "boolean",
                          readable=False,
                          writable=False,
                          default=False))

# Reusable Admin field to include in other table definitions
# Deprecated: http://eden.sahanafoundation.org/wiki/BluePrintAuthorization#Recordrestriction
#admin_id = db.Table(None, "admin_id",
#            FieldS3("admin", db.auth_group, sortby="role",
#                requires = IS_NULL_OR(IS_ONE_OF(db, "auth_group.id", "%(role)s")),
#                represent = lambda id: (id and [db(db.auth_group.id == id).select(db.auth_group.role, limitby=(0, 1)).first().role] or ["None"])[0],
#                comment = DIV(A(T("Add Role"), _class="colorbox", _href=URL(r=request, c="admin", f="group", args="create", vars=dict(format="popup")), _target="top", _title=T("Add Role")), DIV( _class="tooltip", _title=str(T("Admin")) + "|" + str(T("The Group whose members can edit data in this record.")))),
#                ondelete="RESTRICT"
#                ))

# Reusable Document field to include in other table definitions
document = db.Table(None, "document",
            Field("document", "upload", autodelete = True,
                label=T("Scanned File"),
                #comment = DIV( _class="tooltip", _title=str(T("Scanned File")) + "|" + str(T("The scanned copy of this document."))),
                ))

# Reusable Currency field to include in other table definitions
currency_type_opts = {
    1:T("Dollars"),
    2:T("Euros"),
    3:T("Pounds")
}
opt_currency_type = db.Table(None, "currency_type",
                    Field("currency_type", "integer", notnull=True,
                    requires = IS_IN_SET(currency_type_opts, zero=None),
                    # default = 1,
                    label = T("Currency"),
                    represent = lambda opt: currency_type_opts.get(opt, UNKNOWN_OPT)))

# Default CRUD strings
ADD_RECORD = T("Add Record")
LIST_RECORDS = T("List Records")
s3.crud_strings = Storage(
    title_create = ADD_RECORD,
    title_display = T("Record Details"),
    title_list = LIST_RECORDS,
    title_update = T("Edit Record"),
    title_search = T("Search Records"),
    subtitle_create = T("Add New Record"),
    subtitle_list = T("Available Records"),
    label_list_button = LIST_RECORDS,
    label_create_button = ADD_RECORD,
    label_delete_button = T("Delete Record"),
    msg_record_created = T("Record added"),
    msg_record_modified = T("Record updated"),
    msg_record_deleted = T("Record deleted"),
    msg_list_empty = T("No Records currently available"))

module = "admin"
resource = "theme"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("name"),
                Field("logo"),
                Field("header_background"),
                Field("text_direction"),
                Field("col_background"),
                Field("col_txt"),
                Field("col_txt_background"),
                Field("col_txt_border"),
                Field("col_txt_underline"),
                Field("col_menu"),
                Field("col_highlight"),
                Field("col_input"),
                Field("col_border_btn_out"),
                Field("col_border_btn_in"),
                Field("col_btn_hover"),
                migrate=migrate)

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.text_direction.requires = IS_IN_SET({"ltr":T("Left-to-Right"), "rtl":T("Right-to-Left")}, zero=None)
table.col_background.requires = IS_HTML_COLOUR()
table.col_txt.requires = IS_HTML_COLOUR()
table.col_txt_background.requires = IS_HTML_COLOUR()
table.col_txt_border.requires = IS_HTML_COLOUR()
table.col_txt_underline.requires = IS_HTML_COLOUR()
table.col_menu.requires = IS_HTML_COLOUR()
table.col_highlight.requires = IS_HTML_COLOUR()
table.col_input.requires = IS_HTML_COLOUR()
table.col_border_btn_out.requires = IS_HTML_COLOUR()
table.col_border_btn_in.requires = IS_HTML_COLOUR()
table.col_btn_hover.requires = IS_HTML_COLOUR()

module = "s3"
# Auditing
# ToDo: consider using native Web2Py log to auth_events
resource = "audit"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,timestamp,
                Field("person", db.auth_user, ondelete="RESTRICT"),
                Field("operation"),
                Field("representation"),
                Field("module"),
                Field("resource"),
                Field("record", "integer"),
                Field("old_value"),
                Field("new_value"),
                migrate=migrate)
table.operation.requires = IS_IN_SET(["create", "read", "update", "delete", "list", "search"])

# Settings - systemwide
s3_setting_security_policy_opts = {
    1:T("simple"),
    2:T("editor"),
    3:T("full")
    }
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp,
                Field("admin_name"),
                Field("admin_email"),
                Field("admin_tel"),
                Field("utc_offset", length=16, default=deployment_settings.get_L10n_utc_offset()), # default UTC offset of the instance
                Field("theme", db.admin_theme),
                Field("debug", "boolean", default=False),
                Field("self_registration", "boolean", default=True),
                Field("security_policy", "integer", default=1),
                Field("archive_not_delete", "boolean", default=True),
                Field("audit_read", "boolean", default=False),
                Field("audit_write", "boolean", default=False),
                migrate=migrate)
table.security_policy.requires = IS_IN_SET(s3_setting_security_policy_opts, zero=None)
table.security_policy.represent = lambda opt: s3_setting_security_policy_opts.get(opt, UNKNOWN_OPT)
table.theme.requires = IS_IN_DB(db, "admin_theme.id", "admin_theme.name", zero=None)
table.theme.represent = lambda name: db(db.admin_theme.id == name).select(db.admin_theme.name, limitby=(0, 1)).first().name
# Define CRUD strings (NB These apply to all Modules' "settings" too)
ADD_SETTING = T("Add Setting")
LIST_SETTINGS = T("List Settings")
s3.crud_strings[resource] = Storage(
    title_create = ADD_SETTING,
    title_display = T("Setting Details"),
    title_list = LIST_SETTINGS,
    title_update = T("Edit Setting"),
    title_search = T("Search Settings"),
    subtitle_create = T("Add New Setting"),
    subtitle_list = T("Settings"),
    label_list_button = LIST_SETTINGS,
    label_create_button = ADD_SETTING,
    msg_record_created = T("Setting added"),
    msg_record_modified = T("Setting updated"),
    msg_record_deleted = T("Setting deleted"),
    msg_list_empty = T("No Settings currently defined"))

# Common Source table
resource = "source"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp,
            Field("name"),
            Field("description"),
            Field("url"),
            migrate=migrate)
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Source of Information")
table.name.comment = SPAN("*", _class="req")
table.url.requires = IS_NULL_OR(IS_URL())
table.url.label = T("URL")
ADD_SOURCE = T("Add Source")
LIST_SOURCES = T("List Sources")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_SOURCE,
    title_display = T("Source Details"),
    title_list = LIST_SOURCES,
    title_update = T("Edit Source"),
    title_search = T("Search Sources"),
    subtitle_create = T("Add New Source"),
    subtitle_list = T("Sources"),
    label_list_button = LIST_SOURCES,
    label_create_button = ADD_SOURCE,
    msg_record_created = T("Source added"),
    msg_record_modified = T("Source updated"),
    msg_record_deleted = T("Source deleted"),
    msg_list_empty = T("No Sources currently registered"))
# Reusable field to include in other table definitions
source_id = db.Table(None, "source_id",
            FieldS3("source_id", db.s3_source, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "s3_source.id", "%(name)s")),
                represent = lambda id: (id and [db(db.s3_source.id == id).select(db.s3_source.name, limitby=(0, 1)).first().name] or [NONE])[0],
                label = T("Source of Information"),
                comment = DIV(A(ADD_SOURCE, _class="colorbox", _href=URL(r=request, c="default", f="source", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SOURCE), DIV( _class="tooltip", _title=str(T("Add Source")) + "|" + str(T("The Source this information came from.")))),
                ondelete = "RESTRICT"
                ))

# Settings - appadmin
module = "appadmin"
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)

