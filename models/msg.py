# -*- coding: utf-8 -*-

"""
    Messaging module
"""

module = "msg"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("audit_read", "boolean"),
                            Field("audit_write", "boolean"),
                            Field("outgoing_sms_handler"),
                            Field("default_country_code", "integer", default = 44),
                            migrate=migrate)
    table.outgoing_sms_handler.requires = IS_IN_SET(["Modem", "Gateway"], zero=None)

    resource = "email_settings"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field("inbound_mail_server"),
                    Field("inbound_mail_type"),
                    Field("inbound_mail_ssl", "boolean"),
                    Field("inbound_mail_port", "integer"),
                    Field("inbound_mail_username"),
                    Field("inbound_mail_password"),
                    Field("inbound_mail_delete", "boolean"),
                    # Also needs to be used by Auth (order issues), DB calls are overheads
                    # - as easy for admin to edit source in 000_config.py as to edit DB (although an admin panel can be nice)
                    #Field("outbound_mail_server"),
                    #Field("outbound_mail_from"),
                    migrate=migrate)
    table.inbound_mail_type.requires = IS_IN_SET(["imap", "pop3"], zero=None)

    # Status
    resource = "email_inbound_status"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    Field("status"),
                    migrate=migrate)


    # Valid message outbox statuses
    msg_status_type_opts = {
        1:T("Unsent"),
        2:T("Sent"),
        3:T("Draft"),
        4:T("Invalid")
        }

    opt_msg_status = db.Table(None, "opt_msg_status",
                        Field("status", "integer", notnull=True,
                        requires = IS_IN_SET(msg_status_type_opts, zero=None),
                        default = 1,
                        label = T("Status"),
                        represent = lambda opt: msg_status_type_opts.get(opt, UNKNOWN_OPT)))

    # SMS store for persistence and scratch pad for combining incoming xform chunks
    resource = "xforms_store"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                Field("sender", "string", length = 20),
                Field("fileno", "integer"),
                Field("totalno", "integer"),
                Field("partno", "integer"),
                Field("message", "string", length = 160),
            migrate=migrate)

    # Settings for modem.
    resource = "modem_settings"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                #Field("account_name"), # Nametag to remember account - To be used later
                Field("modem_port"),
                Field("modem_baud", "integer", default = 115200),
                Field("enabled", "boolean", default = False),
                #Field("preference", "integer", default = 5), To be used later
                migrate=migrate)


    # Settings for modem.
    resource = "gateway_settings"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                Field("url", default = "https://api.clickatell.com/http/sendmsg"),
                Field("parameters", default = "user=yourusername&password=yourpassword&api_id=yourapiid"),
                Field("message_variable", "string", default = "text"),
                Field("to_variable", "string", default = "to"),
                Field("enabled", "boolean", default = False),
                #Field("preference", "integer", default = 5), To be used later
                migrate=migrate)
    # Message priority
    msg_priority_opts = {
        3:T("High"),
        2:T("Medium"),
        1:T("Low")
    }

    # Message Log - This is where all the messages / logs go into
    resource = "log"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        pe_id,#Sender
        Field("sender"), #The name to go out incase of the email, if set used
        Field("fromaddress"), #From address if set changes sender to this
        Field("subject", length=78),
        Field("message", "text"),
   #     Field("attachment", "upload", autodelete = True), #TODO
        Field("verified", "boolean", default = False),
        Field("verified_comments", "text"),
        Field("actionable", "boolean", default = True),
        Field("actioned", "boolean", default = False),
        Field("actioned_comments", "text"),
        Field("priority", "integer", default = 1),
        Field("inbound", "boolean", default = False),
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    table.priority.requires = IS_NULL_OR(IS_IN_SET(msg_priority_opts))
    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "pe_id",
                                       "subject",
                                       "verified",
                                       "verified_comments",
                                       "actionable",
                                       "actioned",
                                       "actioned_comments",
                                       "priority"])

    # Reusable Message ID
    message_id = db.Table(None, "message_id",
                FieldS3("message_id", db.msg_log,
                    requires = IS_NULL_OR(IS_ONE_OF(db, "msg_log.id")),
                    # FIXME: Subject works for Email but not SMS
                    represent = lambda id: db(db.msg_log.id == id).select(db.msg_log.subject, limitby=(0, 1)).first().subject,
                    ondelete = "RESTRICT"
                ))

    # Message Tag - Used to tag a message to a resource
    resource = "tag"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        Field("resource"),
        Field("record_uuid", # null in this field implies subscription to the entire resource
            type=s3uuid,
            length=128),
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "record_uuid",
                                        "resource",
                                       ])

    # The following was added to show only the supported messaging methods
    msg_contact_method_opts = { # pr_contact_method dependency
        1:T("E-Mail"),
        2:T("Mobile Phone"),
    }


    # Channel - For inbound messages this tells which channel the message came in from.
    resource = "channel"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                            message_id,
                            Field("pr_message_method", "integer",
                                    requires = IS_IN_SET(msg_contact_method_opts, zero=None),
                                    default = 1),
                            Field("log"),
                            migrate=migrate)


    # Outbox - needs to be separate to Log since a single message sent needs different outbox entries for each recipient
    resource = "outbox"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        pe_id, # Person/Group to send the message out to
        Field("address"), # If set used instead of picking up from pe_id
        Field("pr_message_method", "integer",
              requires = IS_IN_SET(msg_contact_method_opts, zero=None),
              default = 1,
              label = T("Contact Method"),
              represent = lambda opt: msg_contact_method_opts.get(opt, UNKNOWN_OPT)),
        opt_msg_status,
        Field("system_generated", "boolean", default = False),
        Field("log"),
        migrate=migrate)

    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(msg_log="message_id"),
                              deletable=True,
                              editable=True)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "pe_id",
                                        "status",
                                        "log",
                                       ])

    # Message Read Status - To replace Message Outbox #TODO
    resource = "read_status"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
        message_id,
        person_id,
        migrate=migrate)

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "person_id",
                                       ])

    # CAP: Common Alerting Protocol
    # http://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html
    # CAP alert Status Code (status)
    cap_alert_status_code_opts = {
        "Actual":T("Actionable by all targeted recipients"),
        "Exercise":T("Actionable only by designated exercise participants; exercise identifier SHOULD appear in <note>"),
        "System":T("For messages that support alert network internal functions"),
        "Test":T("Technical testing only, all recipients disregard"),
        "Draft":T("preliminary template or draft, not actionable in its current form"),
    }
    # CAP info Event Category (category)
    cap_info_category_opts = {
        "Geo":T("Geophysical (inc. landslide)"),
        "Met":T("Meteorological (inc. flood)"),
        "Safety":T("General emergency and public safety"),
        "Security":T("Law enforcement, military, homeland and local/private security"),
        "Rescue":T("Rescue and recovery"),
        "Fire":T("Fire suppression and rescue"),
        "Health":T("Medical and public health"),
        "Env":T("Pollution and other environmental"),
        "Transport":T("Public and private transportation"),
        "Infra":T("Utility, telecommunication, other non-transport infrastructure"),
        "CBRNE":T("Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack"),
        "Other":T("Other events"),
    }
    # CAP info Response Type (responseType)
    cap_info_responseType_opts = {
        "Shelter":T("Take shelter in place or per <instruction>"),
        "Evacuate":T("Relocate as instructed in the <instruction>"),
        "Prepare":T("Make preparations per the <instruction>"),
        "Execute":T("Execute a pre-planned activity identified in <instruction>"),
        "Avoid":T("Avoid the subject event as per the <instruction>"),
        "Monitor":T("Attend to information sources as described in <instruction>"),
        "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
        "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
        "None":T("No action recommended"),
    }

    # Reports
    # Verified reports ready to be sent out as alerts or displayed on a map
    msg_report_type_opts = {
        "Shelter":T("Take shelter in place or per <instruction>"),
        "Evacuate":T("Relocate as instructed in the <instruction>"),
        "Prepare":T("Make preparations per the <instruction>"),
        "Execute":T("Execute a pre-planned activity identified in <instruction>"),
        "Avoid":T("Avoid the subject event as per the <instruction>"),
        "Monitor":T("Attend to information sources as described in <instruction>"),
        "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
        "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
        "None":T("No action recommended"),
    }
    resource = "report"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    message_id,
                    location_id,
                    Field("image", "upload", autodelete = True),
                    Field("url", requires=IS_NULL_OR(IS_URL())),
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

def shn_msg_compose( redirect_module = "msg", 
                     redirect_function = "compose", 
                     redirect_vars = None,
                     title_name = "Send Message" ):
    """ 
        Form to Compose a Message 

        @param redirect_module: Redirect to the specified module's url after login.
        @param redirect_function: Redirect to the specified function
        @param redirect_vars:  Dict with vars to include in redirects
        @param title_name: Title of the page
    """

    resource1 = "log"
    tablename1 = "msg" + "_" + resource1
    table1 = db[tablename1]
    resource2 = "outbox"
    tablename2 = "msg" + "_" + resource2
    table2 = db[tablename2]

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
            vars={"_next":URL(r=request, c=redirect_module, f=redirect_function, vars=redirect_vars)}))

    # Model options
    table1.sender.writable = table1.sender.readable = False
    table1.fromaddress.writable = table1.fromaddress.readable = False
    table1.pe_id.writable = table1.pe_id.readable = False
    table1.verified.writable = table1.verified.readable = False
    table1.verified_comments.writable = table1.verified_comments.readable = False
    table1.actioned.writable = table1.actioned.readable = False
    table1.actionable.writable = table1.actionable.readable = False
    table1.actioned_comments.writable = table1.actioned_comments.readable = False
    
    table1.subject.label = T("Subject")
    table1.message.label = T("Message")
    table1.priority.label = T("Priority")
    
    table2.pe_id.writable = table2.pe_id.readable = True
    table2.pe_id.label = T("Recipients")

    def compose_onvalidation(form):
        """ Set the sender and use msg.send_by_pe_id to route the message """
        if not request.vars.pe_id:
            session.error = T("Please enter the recipient")
            redirect(URL(r=request,c=redirect_module, f=redirect_function, vars=redirect_vars))
        sender_pe_id = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        if msg.send_by_pe_id(request.vars.pe_id,
                             request.vars.subject,
                             request.vars.message,
                             sender_pe_id,
                             request.vars.pr_message_method):
            session.flash = T("Message sent to outbox")
            redirect(URL(r=request, c=redirect_module, f=redirect_function, vars=redirect_vars))
        else:
            session.error = T("Error in message")
            redirect(URL(r=request,c=redirect_module, f=redirect_function, vars=redirect_vars))

    logform = crud.create(table1,
                          onvalidation = compose_onvalidation)
    outboxform = crud.create(table2)
    
    return dict(logform = logform, outboxform = outboxform, title = T(title_name))
