# -*- coding: utf-8 -*-

"""
    Messaging Module - Controllers
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
	[T("Compose"), False, URL(r=request, c="msg", f="compose")],
	[T("Outbox"), False, URL(r=request, f="outbox")],#TODO
	[T("Distribution groups"), False, URL(r=request, f="group"), [
		[T("List/Add"), False, URL(r=request, f="group")],
		[T("Group Memberships"), False, URL(r=request, f="group_membership")],
	]],
    #["CAP", False, URL(r=request, f="tbc")]
]

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

def tbc():
    """ Coming soon... """
    return dict()

def email_settings():
    """ RESTful CRUD controller for email settings - appears in the administration menu """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    
    table.inbound_mail_server.label = T("Server")
    table.inbound_mail_type.label = T("Type")
    table.inbound_mail_ssl.label = "SSL"
    table.inbound_mail_port.label = T("Port")
    table.inbound_mail_username.label = T("Username")
    table.inbound_mail_password.label = T("Password")
    table.inbound_mail_delete.label = T("Delete from Server?")
    table.inbound_mail_port.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Port") + "|" + Tstr("For POP-3 this is usually 110 (995 for SSL), for IMAP this is usually 143 (993 for IMAP).")))
    table.inbound_mail_delete.comment = DIV(DIV(_class="tooltip",
            _title=Tstr("Delete") + "|" + Tstr("If this is set to True then mails will be deleted from the server after downloading.")))

    if not auth.has_membership(auth.id_group("Administrator")):
		session.error = UNAUTHORISED
		redirect(URL(r=request, f="index"))
    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Email Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Email settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )
    
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, "email_settings", listadd=False, deletable=False)

#--------------------------------------------------------------------------------------------------

# The following 2 functions hook into the pr functions
# -----------------------------------------------------------------------------
def group():
    "RESTful CRUD controller"
    
    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
        vars={"_next":URL(r=request, c="msg", f="group")}))

    module = "pr"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Hide unnecessary fields
    table.description.readable = table.description.writable = False

    # Do not show system groups
    response.s3.filter = (table.system == False)

    response.s3.pagination = True

    return shn_rest_controller(module, resource,
                               main="name",
                               extra="description",
                               rheader=shn_pr_rheader,
                               deletable=False)
# -----------------------------------------------------------------------------
def group_membership():
    "RESTful CRUD controller"

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
        vars={"_next":URL(r=request, c="msg", f="group_membership")}))

    module = "pr"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Hide unnecessary fields
    table.description.readable = table.description.writable = False
    table.comment.readable = table.comment.writable = False
    table.group_head.readable = table.group_head.writable = False
    
    return shn_rest_controller(module, resource)

#-------------------------------------------------------------------------------

def pe_contact():
    """ Allows the user to add, update and delete their contacts"""
    
    if auth.is_logged_in() or auth.basic():
        person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        response.s3.filter = (db.pr_pe_contact.pe_id == person)
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
            vars={"_next":URL(r=request, c="msg", f="pe_contact")}))

    module = "pr"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # These fields will be populated automatically
    table.name.writable = table.name.readable = False
    table.pe_id.writable = table.pe_id.readable = False
    table.person_name.writable = table.person_name.readable = False
    table.id.writable = False
#   table.id.readable = False

    def msg_pe_contact_onvalidation(form):
        """ This onvalidation method adds the person id to the record """
        person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        form.vars.pe_id = person

    def msg_pe_contact_restrict_access(jr):
        """ The following restricts update and delete access to contacts not owned by the user """
        if jr.id :
            person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
            if person == db(db.pr_pe_contact.id == jr.id).select(db.pr_pe_contact.pe_id, limitby=(0, 1)).first().pe_id :
                return True
            else:
                session.error = T("Access denied")
                return dict(bypass = True, output = redirect(URL(r=request)))
        else:
            return True
    s3xrc.model.configure(table,
            onvalidation=lambda form: msg_pe_contact_onvalidation(form))
    response.s3.prep = msg_pe_contact_restrict_access
    response.menu_options = []
    return shn_rest_controller(module, resource, listadd=True)

#-------------------------------------------------------------------------------

def search():
    """
    Do a search of groups which match a type
    Used for auto-completion
    """
    if auth.is_logged_in() or auth.basic():
        pass
    else:
        return

    import gluon.contrib.simplejson as sj
    table1 = db.pr_group
    field1 = "name"
    table2 = db.pr_person
    field21 = "first_name"
    field22 = "middle_name"
    field23 = "last_name"
    # JQuery Autocomplete uses 'q' instead of 'value'
    value = request.vars.q
    if value:
		item = []
		query = db((table1[field1].like("%" + value + "%")) & (table1.deleted == False)).select(db.pr_group.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field21].like("%" + value + "%")) & (table2.deleted == False)).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field22].like("%" + value + "%")) & (table2.deleted == False)).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field23].like("%" + value + "%")) & (table2.deleted == False)).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		item = sj.dumps(item)
		response.view = "xml.html"
		return dict(item=item)
    return

def process_sms_via_api():
	"Controller for SMS api processing - to be called via cron"

	msg.process_outbox(contact_method = 2)
	return

def process_email_via_api():
	"Controller for Email api processing - to be called via cron"

	msg.process_outbox(contact_method = 1)
	return

#-------------------------------------------------------------------------------

@auth.shn_requires_membership(1)
def modem_settings():
    """ Modem settings """
    
    try:
        import serial
    except ImportError:
        session.error = T("Python Serial module not available within the running Python - this needs installing to activate the Modem")
        redirect(URL(r=request, c="admin", f="index"))

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    
    table.modem_port.label = T("Port")
    table.modem_baud.label = T("Baud")
    table.modem_port.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Port") + "|" + Tstr("The serial port at which the modem is connected - /dev/ttyUSB0, etc on linux and com1, com2, etc on Windows")))
    table.modem_baud.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Baud") + "|" + Tstr("Baud rate to use for your modem - The default is safe for most cases")))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Enabled") + "|" + Tstr("Unselect to disable the modem")))
    
    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Modem Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Modem settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    crud.settings.update_next = URL(r=request, args=[1, "update"])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False,
    listadd=False)

@auth.shn_requires_membership(1)
def gateway_settings():
    """ Gateway settings """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    
    table.url.label = "URL"
    table.to_variable.label = T("To variable")
    table.message_variable.label = T("Message variable")
    table.url.comment = DIV(DIV(_class="tooltip",
        _title="URL|" + Tstr("The URL of your web gateway without the post parameters")))
    table.parameters.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Parameters") + "|" + Tstr("The post variables other than the ones containing the message and the phone number")))
    table.message_variable.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Message Variable") + "|" + Tstr("The post variable on the URL used for sending messages")))
    table.to_variable.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("To variable") + "|" + Tstr("The post variable containing the phone number")))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title=Tstr("Enabled") + "|" + Tstr("Unselect to disable the modem")))

    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Gateway Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Gateway settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    crud.settings.update_next = URL(r=request, args=[1, "update"])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False, listadd=False)

@auth.shn_requires_membership(1)
def setting():
    """ Overall settings for the messaging framework """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    table.outgoing_sms_handler.label = T("Outgoing SMS handler")
    table.outgoing_sms_handler.comment = DIV(DIV(_class="tooltip",
    _title=Tstr("Outgoing SMS handler") + "|" + Tstr("Selects whether to use the gateway or the Modem for sending out SMS")))
    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Messaging Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        label_delete_button = T("Delete Setting"),
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Messaging settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    crud.settings.update_next = URL(r=request, args=[1, "update"])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def compose():

    return shn_msg_compose()

def outbox():
    "View the contents of the Outbox"

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    table.message_id.label = T("Message")
    table.message_id.writable = False
    table.pe_id.readable = True
    table.pe_id.label = T("Recipient")
    
    # Subject works for Email but not SMS
    table.message_id.represent = lambda id: db(db.msg_log.id == id).select(db.msg_log.message, limitby=(0, 1)).first().message

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_list = T("View Outbox"),
        title_update = T("Edit Message"),
        subtitle_list = T("Available Messages"),
        label_list_button = T("View Outbox"),
        label_delete_button = T("Delete Message"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No Messages currently in Outbox")
    )

    # Server-side Pagination
    response.s3.pagination = True

    return shn_rest_controller(module, resource, listadd=False)

# Enabled only for testing - the ticketing module should be the normal interface
# - although we should provide a menu item to that here...
@auth.shn_requires_membership(1)
def log():
    " RESTful CRUD controller "
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Model options
    table.message.comment = SPAN("*", _class="req")
    table.priority.represent = lambda id: (
        [id and
            DIV(IMG(_src="/%s/static/img/priority/priority_%d.gif" % (request.application,id,), _height=12)) or
            DIV(IMG(_src="/%s/static/img/priority/priority_4.gif" % request.application), _height=12)
        ][0].xml())
    table.priority.label = T("Priority")
    # Add Auth Restrictions

    # CRUD Strings
    ADD_MESSAGE = T("Add Message")
    LIST_MESSAGES = T("List Messages")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MESSAGE,
        title_display = T("Message Ddetails"),
        title_list = LIST_MESSAGES,
        title_update = T("Edit message"),
        title_search = T("Search messages"),
        subtitle_create = T("Send new message"),
        subtitle_list = T("Messages"),
        label_list_button = LIST_MESSAGES,
        label_create_button = ADD_MESSAGE,
        msg_record_created = T("Message added"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No messages in the system"))

    # Server-side Pagination
    response.s3.pagination = True

    return shn_rest_controller(module, resource, listadd=False)

# Enabled only for testing
@auth.shn_requires_membership(1)
def tag():
    " RESTful CRUD controller "
    resource = "tag"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    # Server-side Pagination
    response.s3.pagination = True
    
    return shn_rest_controller(module, resource, listadd=False)

