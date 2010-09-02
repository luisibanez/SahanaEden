# -*- coding: utf-8 -*-

"""
    Document Library - Controllers

    @author: Fran Boon
    @author: Michael Howden
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [ [T("Documents"), False, URL(r=request, f="document")],
                          [T("Photos"), False, URL(r=request, f="image")],
                          #[T("Bulk Uploader"), False, URL(r=request, f="bulk_upload")]
                        ]

#==============================================================================
# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db)

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

#==============================================================================
# Used to display the number of Components in the tabs
def shn_document_tabs(jr):
    
    tab_opts = [{"tablename": "sitrep_assessment",
                 "resource": "assessment",
                 "one_title": T("1 Assessment"),
                 "num_title": " Assessments",
                 },
                 {"tablename": "irs_ireport",
                 "resource": "ireport",
                 "one_title": "1 Incident Report",
                 "num_title": " Incident Reports",
                 },
                 {"tablename": "inventory_store",
                 "resource": "store",
                 "one_title": "1 Inventory Store",
                 "num_title": " Inventory Stores",
                 },
                 {"tablename": "cr_shelter",
                 "resource": "shelter",
                 "one_title": "1 Shelter",
                 "num_title": " Shelters",
                 },
                 {"tablename": "flood_freport",
                 "resource": "freport",
                 "one_title": "1 Flood Report",
                 "num_title": " Flood Reports",
                 },
                 {"tablename": "rms_req",
                 "resource": "req",
                 "one_title": "1 Request",
                 "num_title": " Requests",
                 },
                ] 
    tabs = [(T("Details"), None)]
    for tab_opt in tab_opts:
        tablename = tab_opt["tablename"]
        tab_count = db( (db[tablename].deleted == False) & (db[tablename].document_id == jr.id) ).count()
        if tab_count == 0:
            label = shn_get_crud_string(tablename, "title_create")
        elif tab_count == 1:
            label = tab_opt["one_title"]
        else:
            label = T(str(tab_count) + tab_opt["num_title"] )
        tabs.append( (label, tab_opt["resource"] ) )
        
    return tabs
    
def shn_document_rheader(r):
    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, shn_document_tabs(r))
        doc_document = r.record
        table = db.doc_document
        rheader = DIV(B(Tstr("Name") + ": "),doc_document.name,
                      TABLE(TR(
                               TH(Tstr("File") + ": "), table.file.represent( doc_document.file ),
                               TH(Tstr("URL") + ": "), table.url.represent( doc_document.url ),
                               ),
                            TR(
                               TH(Tstr("Organisation") + ": "), table.organisation_id.represent( doc_document.organisation_id ),
                               TH(Tstr("Person") + ": "), table.person_id.represent( doc_document.organisation_id ),
                               ),
                           ),
                      rheader_tabs
                      )
        return rheader
    return None  

def document():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Model options
    # used in multiple controllers, so in the model
    
    #Disable legacy fields in components, unless updating, so the data can be manually transferred to new fields
    if "update" not in request.args:
        db.sitrep_assessment.source.readable = db.sitrep_assessment.source.writable = False   
        db.sitrep_school_district.document.readable = db.sitrep_school_district.document.writable = False 
        db.irs_ireport.source.readable = db.irs_ireport.source.writable = False        
        db.irs_ireport.source_id.readable = db.irs_ireport.source_id.writable = False  
        #db.flood_freport.document.readable = db.flood_freport.document.writable = False   
   
    def postp(jr, output):                          
        shn_action_buttons(jr)
        return output
    response.s3.postp = postp
    
    rheader = lambda r: shn_document_rheader(r)

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 rheader=rheader)

    return output
#==============================================================================
def image():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # Model options
    # used in multiple controllers, so in the model
    
    def postp(jr, output):                          
        shn_action_buttons(jr)
        return output
    response.s3.postp = postp    

    response.s3.pagination = True
    output = shn_rest_controller(module, resource)
    
    return output
#==============================================================================
# END - Following code is not utilised

def metadata():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.description.label = T("Description")
    table.person_id.label = T("Contact")
    table.source.label = T("Source")
    table.sensitivity.label = T("Sensitivity")
    table.event_time.label = T("Event Time")
    table.expiry_time.label = T("Expiry Time")
    table.url.label = "URL"

    # CRUD Strings
    LIST_METADATA = T("List Metadata")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_METADATA,
        title_display = T("Metadata Details"),
        title_list = LIST_METADATA,
        title_update = T("Edit Metadata"),
        title_search = T("Search Metadata"),
        subtitle_create = T("Add New Metadata"),
        subtitle_list = T("Metadata"),
        label_list_button = LIST_METADATA,
        label_create_button = ADD_METADATA,
        label_delete_button = T("Delete Metadata"),
        msg_record_created = T("Metadata added"),
        msg_record_modified = T("Metadata updated"),
        msg_record_deleted = T("Metadata deleted"),
        msg_list_empty = T("No Metadata currently defined"))

    return shn_rest_controller(module, resource)
#==============================================================================
def bulk_upload():
    """
    Custom view to allow bulk uploading of photos which are made into GIS Features.
    Lat/Lon can be pulled from an associated GPX track with timestamp correlation.
    """

    crud.messages.submit_button = T("Upload")

    form = crud.create(db.doc_metadata)

    gpx_tracks = OptionsWidget()
    gpx_widget = gpx_tracks.widget(track_id.track_id, track_id.track_id.default, _id="gis_layer_gpx_track_id")
    gpx_label = track_id.track_id.label
    gpx_comment = track_id.track_id.comment

    feature_group = OptionsWidget()
    fg_widget = feature_group.widget(feature_group_id.feature_group_id, feature_group_id.feature_group_id.default, _id="gis_location_to_feature_group_feature_group_id")
    fg_label = feature_group_id.feature_group_id.label
    fg_comment = feature_group_id.feature_group_id.comment

    response.title = T("Bulk Uploader")

    return dict(form=form, gpx_widget=gpx_widget, gpx_label=gpx_label, gpx_comment=gpx_comment, fg_widget=fg_widget, fg_label=fg_label, fg_comment=fg_comment, IMAGE_EXTENSIONS=IMAGE_EXTENSIONS)

def upload_bulk():
    "Receive the Uploaded data from bulk_upload()"
    # Is there a GPX track to correlate timestamps with?
    #track_id = form.vars.track_id
    # Is there a Feature Group to add Features to?
    #feature_group_id = form.vars.feature_group_id
    # Collect default metadata
    #description = form.vars.description
    #person_id = form.vars.person_id
    #source = form.vars.source
    #sensitivity = form.vars.sensitivity
    #event_time = form.vars.event_time
    #expiry_time = form.vars.expiry_time
    #url = form.vars.url

    # Insert initial metadata
    #metadata_id = db.media_metadata.insert(description=description, person_id=person_id, source=source, sensitivity=sensitivity, event_time=event_time, expiry_time=expiry_time)

    # Extract timestamps from GPX file
    # ToDo: Parse using lxml?

    # Receive file
    #location_id
    #image

    #image_filename = db.insert()

    # Read EXIF Info from file
    #exec("import applications.%s.modules.EXIF as EXIF" % request.application)
    # Faster for Production (where app-name won't change):
    #import applications.sahana.modules.EXIF as EXIF

    #f = open(file_image, "rb")
    #tags = EXIF.process_file(f, details=False)
    #for key in tags.keys():
        # Timestamp
    #    if key[tag] == "":
    #        timestamp = key[tag]
        # ToDo: LatLon
        # ToDo: Metadata

    # Add image to database
    image_id = db.media_image.insert()

    return s3xrc.xml.json_message(True, "200", "Files Processed.")

def upload(module, resource, table, tablename, onvalidation=None, onaccept=None):
    # Receive file ( from import_url() )
    record = Storage()

    for var in request.vars:

        # Skip the Representation
        if var == "format":
            continue
        elif var == "uuid":
            uuid = request.vars[var]
        elif table[var].type == "upload":
            # Handle file uploads (copied from gluon/sqlhtml.py)
            field = table[var]
            fieldname = var
            f = request.vars[fieldname]
            fd = fieldname + "__delete"
            if f == "" or f == None:
                #if request.vars.get(fd, False) or not self.record:
                if request.vars.get(fd, False):
                    record[fieldname] = ""
                else:
                    #record[fieldname] = self.record[fieldname]
                    pass
            elif hasattr(f, "file"):
                (source_file, original_filename) = (f.file, f.filename)
            elif isinstance(f, (str, unicode)):
                ### do not know why this happens, it should not
                (source_file, original_filename) = \
                    (cStringIO.StringIO(f), "file.txt")
            newfilename = field.store(source_file, original_filename)
            request.vars["%s_newfilename" % fieldname] = record[fieldname] = newfilename
            if field.uploadfield and not field.uploadfield==True:
                record[field.uploadfield] = source_file.read()
        else:
            record[var] = request.vars[var]

    # Validate record
    for var in record:
        if var in table.fields:
            value = record[var]
            (value, error) = s3xrc.xml.validate(table, original, var, value)
        else:
            # Shall we just ignore non-existent fields?
            # del record[var]
            error = "Invalid field name."
        if error:
            raise HTTP(400, body=s3xrc.xml.json_message(False, 400, var + " invalid: " + error))
        else:
            record[var] = value

    form = Storage()
    form.method = method
    form.vars = record

    # Onvalidation callback
    if onvalidation:
        onvalidation(form)

    # Create/update record
    try:
        if jr.component:
            record[jr.fkey]=jr.record[jr.pkey]
        if method == "create":
            id = table.insert(**dict(record))
            if id:
                error = 201
                item = s3xrc.xml.json_message(True, error, "Created as " + str(jr.other(method=None, record_id=id)))
                form.vars.id = id
                if onaccept:
                    onaccept(form)
            else:
                error = 403
                item = s3xrc.xml.json_message(False, error, "Could not create record!")

        elif method == "update":
            result = db(table.uuid==uuid).update(**dict(record))
            if result:
                error = 200
                item = s3xrc.xml.json_message(True, error, "Record updated.")
                form.vars.id = original.id
                if onaccept:
                    onaccept(form)
            else:
                error = 403
                item = s3xrc.xml.json_message(False, error, "Could not update record!")

        else:
            error = 501
            item = s3xrc.xml.json_message(False, error, "Unsupported Method!")
    except:
        error = 400
        item = s3xrc.xml.json_message(False, error, "Invalid request!")

    raise HTTP(error, body=item)
