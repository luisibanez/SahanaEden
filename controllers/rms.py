# -*- coding: utf-8 -*-

"""
    Request Management System - Controllers
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Home"), False, URL(r=request, f="index")],
    [T("Requests"), False, URL(r=request, f="req")],
#    [T("Requests"), False, URL(r=request, f="req"),
#     [T("Add"), False, URL(r=request, f="req", args="create")],
#     ],
    [T("All Requested Items"), False, URL(r=request, f="ritem")],
    [T("All Pledges"),False, URL(r=request, f="pledge")]
]

# S3 framework functions
def index():
    "Module's Home Page"

    """ Default to the rms_req list view - TODO does not work with paginate!!!"""

    request.function = "req"
    request.args = []
    return req()

    #module_name = deployment_settings.modules[module].name_nice

    #return dict(module_name=module_name, a=1)

def req():
    """ RESTful CRUD controller """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Pre-processor
    def prep(r):
        if r.representation in ("html", "popup"):
            if r.method == "create":
                table.timestmp.default = request.utcnow
                person = session.auth.user.id if auth.is_logged_in() else None
                if person:
                    person_uuid = db(db.auth_user.id == person).select(db.auth_user.person_uuid, limitby=(0, 1)).first().person_uuid
                    person = db(db.pr_person.uuid == person_uuid).select(db.pr_person.id, limitby=(0, 1)).first().id
                table.person_id.default = person
                table.pledge_status.readable = False
            elif r.method == "update":
                table.pledge_status.readable = False
            shn_action_buttons(r)
        return True
    response.s3.prep = prep

    # Filter out non-actionable SMS requests:
    #response.s3.filter = (db.rms_req.actionable == True) | (db.rms_req.source_type != 2) # disabled b/c Ushahidi no longer updating actionaable fielde

    # Post-processor
    def req_postp(jr, output):
        if jr.representation in ("html", "popup"):
            if not jr.component:
                response.s3.actions = [
                    dict(label=str(T("Open")), _class="action-btn", url=str(URL(r=request, args=["update", "[id]"]))),
                    dict(label=str(T("Items")), _class="action-btn", url=str(URL(r=request, args=["[id]", "ritem"]))),
                    dict(label=str(T("Pledge")), _class="action-btn", url=str(URL(r=request, args=["[id]", "pledge"])))
                ]
            elif jr.component_name == "pledge":
                response.s3.actions = [
                    dict(label=str(T("Details")), _class="action-btn", url=str(URL(r=request, args=["pledge", "[id]"])))
                ]
        return output
    response.s3.postp = req_postp

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 editable=True,
                                 #listadd=False,
                                 rheader=shn_rms_rheader)

    return output

def ritem():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    def postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = postp

    #rheader = lambda jr: shn_item_rheader(jr,
    #                                      tabs = [(T("Requests for Item"), None),
    #                                              (T("Inventories with Item"), "location_item"),
    #                                              (T("Requests for Item"), "req"),
    #                                             ]
    #                                     )

    return shn_rest_controller(module,
                               resource,
                               #rheader=rheader
                               )

def pledge():
    """ RESTful CRUD controller """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Pre-processor
    def prep(r):
        if r.representation in ("html", "popup"):
            if r.method == "create":
                # auto fill posted_on field and make it readonly
                table.submitted_on.default = request.now
                table.submitted_on.writable = False

                person = session.auth.user.id if auth.is_logged_in() else None
                if person:
                    person_uuid = db(db.auth_user.id == person).select(db.auth_user.person_uuid, limitby=(0, 1)).first().person_uuid
                    person = db(db.pr_person.uuid == person_uuid).select(db.pr_person.id, limitby=(0, 1)).first().id
                table.person_id.default = person
        return True
    response.s3.prep = prep

    # Change the request status to completed when pledge delivered
    # (this is necessary to close the loop)
    #pledges = db(db.rms_pledge.status == 3).select()
    #for pledge in pledges:
    #    req = db(db.rms_req.id == pledge.req_id).update(completion_status = True)
    #db.commit()

    def pledge_postp(jr, output):
        if jr.representation in ("html", "popup"):
            if not jr.component:
                response.s3.actions = [
                    dict(label=str(READ), _class="action-btn", url=str(URL(r=request, args=["[id]", "read"])))
                ]
        return output
    response.s3.postp = pledge_postp

    response.s3.pagination = True
    return shn_rest_controller(module,
                               resource,
                               editable = True,
                               #listadd=False
                               )


def shn_rms_rheader(jr):

    if jr.representation == "html":

        _next = jr.here()
        _same = jr.same()

        if jr.name == "req":
            aid_request = jr.record
            if aid_request:
                try:
                    location = db(db.gis_location.id == aid_request.location_id).select(limitby=(0, 1)).first()
                    location_represent = shn_gis_location_represent(location.id)
                except:
                    location_represent = None

                rheader_tabs = shn_rheader_tabs( jr,
                                                 [(T("Edit Details"), None),
                                                  (T("Items"), "ritem"),
                                                  (T("Pledge"), "pledge"),
                                                  ]
                                                 )

                rheader = DIV( TABLE(TR(TH(T("Message: ")),
                                TD(aid_request.message, _colspan=3)),
                                TR(TH(T("Priority: ")),
                                aid_request.priority,
                                #TH(T("Source Type: ")),
                                #rms_req_source_type.get(aid_request.source_type, T("unknown"))),
                                TH(T("Document: ")),
                                document_represent(aid_request.document_id)),
                                TR(TH(T("Time of Request: ")),
                                aid_request.timestmp,
                                TH(T("Verified: ")),
                                aid_request.verified),
                                TR(TH(T("Location: ")),
                                location_represent,
                                TH(T("Actionable: ")),
                                aid_request.actionable)),
                                rheader_tabs
                                )

                return rheader

    return None


# Unused: Was done for Haiti
def sms_complete(): #contributes to RSS feed for closing the loop with Ushahidi

    def t(record):
        return "Sahana Record Number: " + str(record.id)

    def d(record):
        ush_id = db(db.rms_sms_request.id == record.id).select("ush_id")[0]["ush_id"]
        smsrec = db(db.rms_sms_request.id == record.id).select("smsrec")[0]["smsrec"]

        return \
            "Ushahidi Link: " + A(ush_id, _href=ush_id).xml() + "<br>" + \
            "SMS Record: " + str(smsrec)

    rss = { "title" : t , "description" : d }
    response.s3.filter = (db.rms_req.completion_status == True) & (db.rms_req.source_type == 2)
    return shn_rest_controller(module, "req", editable=False, listadd=False, rss=rss)

# Unused: Was done for Haiti
def tweet_complete(): #contributes to RSS feed for closing the loop with TtT

    def t(record):
        return "Sahana Record Number: " + str(record.id)

    def d(record):
        ttt_id = db(db.rms_tweet_request.id == record.id).select("ttt_id")[0]["ttt_id"]
        return "Twitter: " + ttt_id

    rss = { "title" : t , "description" : d }
    response.s3.filter = (db.rms_req.completion_status == True) & (db.rms_req.source_type == 3)
    return shn_rest_controller(module, "req", editable=False, listadd=False, rss = rss)
