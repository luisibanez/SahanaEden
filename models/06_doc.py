# -*- coding: utf-8 -*-

"""
    Document Library
"""

module = "doc"
#==============================================================================
# Settings
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)
#==============================================================================
resource = "document"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("file", "upload", autodelete = True,),
                        Field("url"),                        
                        person_id,
                        organisation_id,
                        location_id,
                        Field("date", "date"),
                        comments,
                        Field("entered", "boolean"),
                        migrate=migrate
                        )

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
#table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")

def shn_file_represent( file, table):
    if file:        
        return A(table.file.retrieve(file)[0], 
                 _href=URL(r=request, f="download", args=[file]))
    else:
        return NONE
    
table.file.represent = lambda file, table=table: shn_file_represent(file, table)
table.url.label = T("URL")
table.url.represent = lambda url: url and A(url,_href=url) or NONE

table.url.requires = [IS_NULL_OR(IS_URL()),IS_NULL_OR(IS_NOT_IN_DB(db, "%s.url" % tablename))]

table.person_id.label = T("Author")
table.person_id.comment = shn_person_comment(T("Author"), T("The Author of this Document (optional)"))

table.location_id.readable = table.location_id.writable = False 

table.entered.comment = DIV( _class="tooltip", 
                             _title="Entered" + "|" + Tstr("Has data from this Reference Document been entered into Sahana?")
                             )
# -----------------------------------------------------------------------------
def document_represent(id):
    if not id:
        return NONE
    represent = shn_get_db_field_value(db = db,
                                       table = "doc_document", 
                                       field = "name", 
                                       look_up = id)    
    #File
    #Website
    #Person
    return A ( represent,
               _href = URL(r=request, c="doc", f="document", args = [id], extension = ""),
               _target = "blank"
               )

DOCUMENT = Tstr("Reference Document")
ADD_DOCUMENT = Tstr("Add Reference Document")

document_comment = DIV( A( ADD_DOCUMENT, 
                           _class="colorbox", 
                           _href=URL(r=request, c="doc", f="document", args="create", vars=dict(format="popup")), 
                           _target="top", 
                           _title=Tstr("If you need to add a new document then you can click here to attach one."),
                           ),
                        DIV( _class="tooltip", 
                             _title=DOCUMENT + "|" + \
                             Tstr("A Reference Document such as a file, URL or contact person to verify this data. You can type the 1st few characters of the document name to link to an existing document."),
                             #Tstr("Add a Reference Document such as a file, URL or contact person to verify this data. If you do not enter a Reference Document, your email will be displayed instead."),
                             ),
                        #SPAN( I( T("If you do not enter a Reference Document, your email will be displayed to allow this data to be verified.") ),
                        #     _style = "color:red"
                        #     )
                        )

# CRUD Strings
LIST_DOCUMENTS = T("List Documents")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_DOCUMENT,
    title_display = T("Document Details"),
    title_list = LIST_DOCUMENTS,
    title_update = T("Edit Document"),
    title_search = T("Search Documents"),
    subtitle_create = T("Add New Document"),
    subtitle_list = DOCUMENT,
    label_list_button = LIST_DOCUMENTS,
    label_create_button = ADD_DOCUMENT,
    label_delete_button = T("Delete Document"),
    msg_record_created = T("Document added"),
    msg_record_modified = T("Document updated"),
    msg_record_deleted = T("Document deleted"),
    msg_list_empty = T("No Documents found"))

document_id = db.Table(None, 
                       "document_id",
                       Field("document_id", 
                             db.doc_document,
                             requires = IS_NULL_OR(IS_ONE_OF(db, "doc_document.id", document_represent)),
                             represent = document_represent,
                             label = DOCUMENT,
                             comment = document_comment,
                             ondelete = "RESTRICT",
                             )
                       )
#==============================================================================
resource = "image"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("image", "upload"),                        
                        #metadata_id,
                        Field("url"),                        
                        person_id,
                        organisation_id,
                        location_id,
                        Field("date", "date"),
                        comments,                
                        migrate=migrate)

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
#table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")
table.url.label = "URL"
table.person_id.label = T("Person")

# upload folder needs to be visible to the download() function as well as the upload
table.image.uploadfolder = os.path.join(request.folder, "uploads/images")
IMAGE_EXTENSIONS = ["png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "gif", "GIF", "tif", "TIF", "tiff", "TIFF", "bmp", "BMP", "raw", "RAW"]
table.image.requires = IS_IMAGE(extensions=(IMAGE_EXTENSIONS))

ADD_IMAGE = Tstr("Add Photo")
image_id = db.Table(None, "image_id",
            Field("image_id", db.doc_image,
                requires = IS_NULL_OR(IS_ONE_OF(db, "doc_image.id", "%(name)s")),
                represent = lambda id: (id and [DIV(A(IMG(_src=URL(r=request, c="default", f="download", args=db(db.doc_image.id == id).select(db.doc_image.image, limitby=(0, 1)).first().image), _height=40), _class="zoom", _href="#zoom-media_image-%s" % id), DIV(IMG(_src=URL(r=request, c="default", f="download", args=db(db.doc_image.id == id).select(db.doc_image.image, limitby=(0, 1)).first().image),_width=600), _id="zoom-media_image-%s" % id, _class="hidden"))] or [""])[0],
                label = T("Image"),
                comment = DIV(A(ADD_IMAGE, _class="colorbox", _href=URL(r=request, c="doc", f="image", args="create", vars=dict(format="popup")), _target="top", _title=ADD_IMAGE),
                          DIV( _class="tooltip", _title=ADD_IMAGE + "|" + Tstr("Add an Photo."))),
                ondelete = "RESTRICT"
                ))

# CRUD Strings
LIST_IMAGES = T("List Photos")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_IMAGE,
    title_display = T("Photo Details"),
    title_list = LIST_IMAGES,
    title_update = T("Edit Photo"),
    title_search = T("Search Photos"),
    subtitle_create = T("Add New Photo"),
    subtitle_list = T("Photo"),
    label_list_button = LIST_IMAGES,
    label_create_button = ADD_IMAGE,
    label_delete_button = T("Delete Photo"),
    msg_record_created = T("Photo added"),
    msg_record_modified = T("Photo updated"),
    msg_record_deleted = T("Photo deleted"),
    msg_list_empty = T("No Photos found"))

#==============================================================================
# END - Following code is not utilised
resource = "metadata"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                location_id,
                Field("description"),
                person_id,
                #Field("organisation.id", "reference org_organisation"),
                Field("source"),
                Field("sensitivity"),    # Should be turned into a drop-down by referring to AAA's sensitivity table
                Field("event_time", "datetime"),
                Field("expiry_time", "datetime"),
                Field("url"),
                migrate=migrate)
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.event_time.requires = IS_NULL_OR(IS_DATETIME())
table.expiry_time.requires = IS_NULL_OR(IS_DATETIME())
table.url.requires = IS_NULL_OR(IS_URL())
ADD_METADATA = Tstr("Add Metadata")
metadata_id = db.Table(None, "metadata_id",
            Field("metadata_id", db.doc_metadata,
                requires = IS_NULL_OR(IS_ONE_OF(db, "doc_metadata.id", "%(id)s")),
                represent = lambda id: (id and [db(db.doc_metadata.id==id).select()[0].name] or [NONE])[0],
                label = T("Metadata"),
                comment = DIV(A(ADD_METADATA, _class="colorbox", _href=URL(r=request, c="doc", f="metadata", args="create", vars=dict(format="popup")), _target="top", _title=ADD_METADATA),
                          DIV( _class="tooltip", _title=ADD_METADATA + "|" + "Add some metadata for the file, such as Soure, Sensitivity, Event Time.")),
                ondelete = "RESTRICT"
                ))