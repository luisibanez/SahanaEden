# -*- coding: utf-8 -*-

"""
    CRUD+LS Method Handlers (Frontend for S3REST)

    @author: Fran Boon
    @author: nursix

    @see: U{http://eden.sahanafoundation.org/wiki/RESTController}

    HTTP Status Codes: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
"""

# *****************************************************************************
# Constants to ensure consistency

# XSLT Settings
XSLT_FILE_EXTENSION = "xsl" #: File extension of XSLT templates
XSLT_IMPORT_TEMPLATES = "static/xslt/import" #: Path to XSLT templates for data import
XSLT_EXPORT_TEMPLATES = "static/xslt/export" #: Path to XSLT templates for data export

# XSLT available formats
shn_xml_import_formats = ["xml", "lmx", "osm", "pfif", "ushahidi", "odk", "agasti"] #: Supported XML import formats
shn_xml_export_formats = dict(
    xml = "application/xml",
    gpx = "application/xml",
    lmx = "application/xml",
    pfif = "application/xml",
    have = "application/xml",
    osm = "application/xml",
    rss = "application/rss+xml",
    georss = "application/rss+xml",
    kml = "application/vnd.google-earth.kml+xml",
    #geojson = "application/xml"
) #: Supported XML output formats and corresponding response headers

shn_json_import_formats = ["json"] #: Supported JSON import formats
shn_json_export_formats = dict(
    json = "text/x-json",
    geojson = "text/x-json"
) #: Supported JSON output formats and corresponding response headers

# Error messages
UNAUTHORISED = T("Not authorised!")
BADFORMAT = T("Unsupported data format!")
BADMETHOD = T("Unsupported method!")
BADRECORD = T("Record not found!")
INVALIDREQUEST = T("Invalid request!")
XLWT_ERROR = T("xlwt module not available within the running Python - this needs installing for XLS output!")
GERALDO_ERROR = T("Geraldo module not available within the running Python - this needs installing for PDF output!")
REPORTLAB_ERROR = T("ReportLab module not available within the running Python - this needs installing for PDF output!")

# How many rows to show per page in list outputs
ROWSPERPAGE = 20
PRETTY_PRINT = True

# *****************************************************************************
# Resource Controller
_s3xrc = local_import("s3xrc")

s3xrc = _s3xrc.S3ResourceController(db,
            domain=request.env.server_name,
            base_url="%s/%s" % (deployment_settings.get_base_public_url(),
                                request.application),
            cache=cache,
            auth=auth,
            gis=gis,
            rpp=ROWSPERPAGE,
            xml_import_formats = shn_xml_import_formats,
            xml_export_formats = shn_xml_export_formats,
            json_import_formats = shn_json_import_formats,
            json_export_formats = shn_json_export_formats,
            debug = False)

# *****************************************************************************
def shn_field_represent(field, row, col):

    """
        Representation of a field
        Used by:
         * export_xls()
         * shn_list()
           .aaData representation for dataTables' Server-side pagination
    """

    # TODO: put this function into XRequest

    try:
        represent = str(field.represent(row[col]))
    except:
        if row[col] is None:
            represent = NONE
        else:
            represent = row[col]
            if col == "comments":
                ur = unicode(represent, "utf8")
                if len(ur) > 48:
                    represent = ur[:48 - 3].encode("utf8") + "..."
    return represent

def shn_field_represent_sspage(field, row, col, linkto=None):

    """ Represent columns in SSPage responses """

    # TODO: put this function into XRequest

    if col == "id":
        id = str(row[col])
        # Remove SSPag variables, but keep "next":
        next = request.vars.next
        request.vars = Storage(next=next)
        # use linkto to produce ID column links:
        try:
            href = linkto(id)
        except TypeError:
            href = linkto % id
        # strip away ".aaData" extension => dangerous!
        href = str(href).replace(".aaData", "")
        href = str(href).replace(".aadata", "")
        return A( shn_field_represent(field, row, col), _href=href).xml()
    else:
        return shn_field_represent(field, row, col)

# *****************************************************************************
# Exports

#
# export_csv ------------------------------------------------------------------
#
def export_csv(resource, query, record=None):

    """ Export record(s) as CSV """

    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".csv")
    if record:
        filename = "%s_%s_%d.csv" % (request.env.server_name, resource, record)
    else:
        # List
        filename = "%s_%s_list.csv" % (request.env.server_name, resource)
    response.headers["Content-disposition"] = "attachment; filename=%s" % filename
    return str(db(query).select())

#
# export_pdf ------------------------------------------------------------------
#
def export_pdf(table, query, list_fields=None):

    """ Export record(s) as Adobe PDF """

    try:
        from reportlab.lib.units import cm
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        session.error = REPORTLAB_ERROR
        redirect(URL(r=request))
    try:
        from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = GERALDO_ERROR
        redirect(URL(r=request))

    records = db(query).select(table.ALL)
    if not records:
        session.warning = T("No data in this table - cannot create PDF!")
        redirect(URL(r=request))

    import StringIO
    output = StringIO.StringIO()

    fields = None
    if list_fields:
        fields = [table[f] for f in list_fields if table[f].readable]
    if fields and len(fields) == 0:
        fields.append(table.id)
    if not fields:
        fields = [table[f] for f in table.fields if table[f].readable]
    _elements = [ SystemField(
                        expression="%(report_title)s",
                        top=0.1*cm,
                        left=0,
                        width=BAND_WIDTH,
                        style={
                            "fontName": "Helvetica-Bold",
                            "fontSize": 14,
                            "alignment": TA_CENTER
                            }
                        )]
    detailElements = []
    COLWIDTH = 2.5
    LEFTMARGIN = 0.2

    def _represent(field, data):
        if data == None:
            return ""
        represent = table[field].represent
        if not represent:
            represent = lambda v: str(v)
        text = str(represent(data)).decode("utf-8")
        # Filter out markup from text
        if "<" in text:
            try:
                markup = etree.XML(text)
                text = markup.xpath(".//text()")
                if text:
                    text = " ".join(text)
            except etree.XMLSyntaxError:
                pass
        return text

    for field in fields:
        _elements.append(Label(text=str(field.label)[:16], top=0.8*cm, left=LEFTMARGIN*cm))
        tab, col = str(field).split(".")
        detailElements.append(ObjectValue(
            attribute_name=col,
            left=LEFTMARGIN * cm,
            width=COLWIDTH * cm,
            # Ensure that col is substituted when lambda defined not evaluated by using the default value
            get_value=lambda instance, column=col: _represent(column, instance[column])))
        LEFTMARGIN += COLWIDTH

    mod, res = str(table).split("_", 1)
    try:
        mod_nice = deployment_settings.modules[mod]["name_nice"]
    except:
        mod_nice = mod
    _title = mod_nice + ": " + res.capitalize()

    class MyReport(Report):
        title = _title
        page_size = landscape(A4)
        class band_page_header(ReportBand):
            height = 1.3*cm
            auto_expand_height = True
            elements = _elements
            borders = {"bottom": True}
        class band_page_footer(ReportBand):
            height = 0.5*cm
            elements = [
                Label(text="%s" % request.utcnow.date(), top=0.1*cm, left=0),
                SystemField(expression="Page # %(page_number)d of %(page_count)d", top=0.1*cm,
                    width=BAND_WIDTH, style={"alignment": TA_RIGHT}),
            ]
            borders = {"top": True}
        class band_detail(ReportBand):
            height = 0.5*cm
            auto_expand_height = True
            elements = tuple(detailElements)
    report = MyReport(queryset=records)
    report.generate_by(PDFGenerator, filename=output)

    output.seek(0)
    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".pdf")
    filename = "%s_%s.pdf" % (request.env.server_name, str(table))
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

#
# export_xls ------------------------------------------------------------------
#
def export_xls(table, query, list_fields=None):

    """ Export record(s) as XLS """

    # TODO: make this function XRequest-aware

    try:
        import xlwt
    except ImportError:
        session.error = XLWT_ERROR
        redirect(URL(r=request))

    import StringIO
    output = StringIO.StringIO()

    items = db(query).select(table.ALL)

    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet(str(table))
    # Header row
    row0 = sheet1.row(0)
    cell = 0

    fields = None
    if list_fields:
        fields = [table[f] for f in list_fields if table[f].readable]
    if fields and len(fields) == 0:
        fields.append(table.id)
    if not fields:
        fields = [table[f] for f in table.fields if table[f].readable]

    for field in fields:
        row0.write(cell, str(field.label), xlwt.easyxf("font: bold True;"))
        cell += 1
    row = 1
    style = xlwt.XFStyle()
    for item in items:
        # Item details
        rowx = sheet1.row(row)
        row += 1
        cell1 = 0
        for field in fields:
            tab, col = str(field).split(".")
            # Check for Date formats
            coltype = db[tab][col].type
            if coltype == "date":
                style.num_format_str = "D-MMM-YY"
            elif coltype == "datetime":
                style.num_format_str = "M/D/YY h:mm"
            elif coltype == "time":
                style.num_format_str = "h:mm:ss"

            # Check for a custom.represent (e.g. for ref fields)
            represent = shn_field_represent(field, item, col)
            # Filter out markup from text
            if isinstance(represent, basestring) and "<" in represent:
                try:
                    markup = etree.XML(represent)
                    represent = markup.xpath(".//text()")
                    if represent:
                        represent = " ".join(represent)
                except etree.XMLSyntaxError:
                    pass

            rowx.write(cell1, str(represent), style)
            cell1 += 1
    book.save(output)
    output.seek(0)
    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".xls")
    filename = "%s_%s.xls" % (request.env.server_name, str(table))
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()


# *****************************************************************************
# Imports

#
# import_csv ------------------------------------------------------------------
#
def import_csv(file, table=None):

    """ Import CSV file into Database """

    if table:
        table.import_from_csv_file(file)
    else:
        # This is the preferred method as it updates reference fields
        db.import_from_csv_file(file)
        db.commit()
#
# import_url ------------------------------------------------------------------
#
def import_url(r):

    """ Import data from URL query

        Restriction: can only update single records (no mass-update)

    """

    xml = s3xrc.xml

    prefix, name, table, tablename = r.target()

    record = r.record
    resource = r.resource

    # Handle components
    if record and r.component:
        component = resource.components[r.component_name]
        resource = component.resource
        resource.load()
        if len(resource) == 1:
            record = resource.records()[0]
        else:
            record = None
        r.request.vars.update({component.fkey:r.record[component.pkey]})
    elif not record and r.component:
        item = xml.json_message(False, 400, "Invalid Request!")
        return dict(item=item)

    # Check for update
    if record and xml.UID in table.fields:
        r.request.vars.update({xml.UID:record[xml.UID]})

    # Build tree
    element = etree.Element(xml.TAG.resource)
    element.set(xml.ATTRIBUTE.name, resource.tablename)
    for var in r.request.vars:
        if var.find(".") != -1:
            continue
        elif var in table.fields:
            field = table[var]
            value = xml.xml_encode(str(r.request.vars[var]).decode("utf-8"))
            if var in xml.FIELDS_TO_ATTRIBUTES:
                element.set(var, value)
            else:
                data = etree.Element(xml.TAG.data)
                data.set(xml.ATTRIBUTE.field, var)
                if field.type == "upload":
                    data.set(xml.ATTRIBUTE.filename, value)
                else:
                    data.text = value
                element.append(data)
    tree = xml.tree([element], domain=s3xrc.domain)

    # Import data
    result = Storage(committed=False)
    s3xrc.sync_resolve = lambda vector, result=result: result.update(vector=vector)
    try:
        success = resource.import_xml(tree)
    except SyntaxError:
        pass

    # Check result
    if result.vector:
        result = result.vector

    # Build response
    if success and result.committed:
        id = result.id
        method = result.method
        if method == result.METHOD.CREATE:
            item = xml.json_message(True, 201, "Created as %s?%s.id=%s" %
                                    (str(r.there(representation="html", vars=dict())),
                                     result.name, result.id))
        else:
            item = xml.json_message(True, 200, "Record updated")
    else:
        item = xml.json_message(False, 403, "Could not create/update record: %s" %
                                s3xrc.error or xml.error,
                                tree=xml.tree2json(tree))

    return dict(item=item)


# *****************************************************************************
# Audit
#
# These functions should always return True in order to be chainable
# by "and" for lambda's as onaccept-callbacks. -- nursix --

#
# shn_audit -------------------------------------------------------------------
#
def shn_audit(operation, prefix, name,
              form=None,
              record=None,
              representation=None):

    #print "Audit: %s on %s_%s #%s" % (operation, prefix, name, record or 0)

    if operation in ("list", "read"):
        return shn_audit_read(operation, prefix, name,
                              record=record, representation=representation)

    elif operation == "create":
        return shn_audit_create(form, prefix, name,
                                representation=representation)

    elif operation == "update":
        return shn_audit_update(form, prefix, name,
                                representation=representation)

    elif operation == "delete":
        return shn_audit_delete(prefix, name, record,
                                representation=representation)

    return True

# Set shn_audit as audit function for the resource controller
s3xrc.audit = shn_audit

#
# shn_audit_read --------------------------------------------------------------
#
def shn_audit_read(operation, module, resource, record=None, representation=None):

    """ Called during Read operations to enable optional Auditing """

    if session.s3.audit_read:
        db.s3_audit.insert(
                person = auth.user_id,
                operation = operation,
                module = module,
                resource = resource,
                record = record,
                representation = representation,
            )
    return True

#
# shn_audit_create ------------------------------------------------------------
#
def shn_audit_create(form, module, resource, representation=None):

    """
        Called during Create operations to enable optional Auditing

        Called as an onaccept so that it only takes effect when
        saved & can read the new values in::
            onaccept = lambda form: shn_audit_create(form, module, resource, representation)

    """

    if session.s3.audit_write:
        record =  form.vars.id
        new_value = []
        for var in form.vars:
            new_value.append(var + ":" + str(form.vars[var]))
        db.s3_audit.insert(
                person = auth.user_id,
                operation = "create",
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                new_value = new_value
            )
    return True

#
# shn_audit_update ------------------------------------------------------------
#
def shn_audit_update(form, module, resource, representation=None):

    """
        Called during Create operations to enable optional Auditing

        Called as an onaccept so that it only takes effect when
        saved & can read the new values in::
            onaccept = lambda form: shn_audit_update(form, module, resource, representation)

    """

    if session.s3.audit_write:
        record =  form.vars.id
        new_value = []
        for var in form.vars:
            new_value.append(var + ":" + str(form.vars[var]))
        db.s3_audit.insert(
                person = auth.user_id,
                operation = "update",
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                #old_value = old_value, # Need to store these beforehand if we want them
                new_value = new_value
            )
    return True

#
# shn_audit_update_m2m --------------------------------------------------------
#
def shn_audit_update_m2m(module, resource, record, representation=None):

    """
        Called during Update operations to enable optional Auditing
        Designed for use in M2M "Update Qty/Delete" (which can't use crud.settings.update_onaccept)
        shn_audit_update_m2m(resource, record, representation)
    """

    if session.s3.audit_write:
        db.s3_audit.insert(
                person = auth.user_id,
                operation = "update",
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                #old_value = old_value, # Need to store these beforehand if we want them
                #new_value = new_value  # Various changes can happen, so would need to store dict of {item_id: qty}
            )
    return True

#
# shn_audit_delete ------------------------------------------------------------
#
def shn_audit_delete(module, resource, record, representation=None):

    """ Called during Delete operations to enable optional Auditing """

    if session.s3.audit_write:
        module = module
        table = "%s_%s" % (module, resource)
        old_value = []
        _old_value = db(db[table].id == record).select(limitby=(0, 1)).first()
        for field in _old_value:
            old_value.append(field + ":" + str(_old_value[field]))
        db.s3_audit.insert(
                person = auth.user_id,
                operation = "delete",
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                old_value = old_value
            )
    return True

# *****************************************************************************
# Display Representations

# t2.itemize now deprecated
# but still used for t2.search

#
# shn_represent ---------------------------------------------------------------
#
def shn_represent(table, module, resource, deletable=True, main="name", extra=None):

    """ Designed to be called via table.represent to make t2.search() output useful """

    db[table].represent = lambda table: \
                          shn_list_item(table, resource,
                                        action="display",
                                        main=main,
                                        extra=shn_represent_extra(table,
                                                                  module,
                                                                  resource,
                                                                  deletable,
                                                                  extra))
    return

#
# shn_represent_extra ---------------------------------------------------------
#
def shn_represent_extra(table, module, resource, deletable=True, extra=None):

    """ Display more than one extra field (separated by spaces)"""

    authorised = shn_has_permission("delete", table._tablename)
    item_list = []
    if extra:
        extra_list = extra.split()
        for any_item in extra_list:
            item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % \
                             (module, resource, table.id, any_item))
    if authorised and deletable:
        item_list.append("TD(INPUT(_type='checkbox', _class='delete_row', _name='%s', _id='%i'))" % \
                         (resource, table.id))
    return ",".join( item_list )

#
# shn_list_item ---------------------------------------------------------------
#
def shn_list_item(table, resource, action, main="name", extra=None):

    """ Display nice names with clickable links & optional extra info """

    item_list = [TD(A(table[main], _href=URL(r=request, f=resource, args=[table.id, action])))]
    if extra:
        item_list.extend(eval(extra))
    items = DIV(TABLE(TR(item_list)))
    return DIV(*items)

#
# shn_custom_view -------------------------------------------------------------
#
def shn_custom_view(r, default_name, format=None):

    """ Check for custom view """

    prefix = r.request.controller

    if r.component:

        custom_view = "%s_%s_%s" % (r.name, r.component_name, default_name)

        _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

        if not os.path.exists(_custom_view):
            custom_view = "%s_%s" % (r.name, default_name)
            _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

    else:
        if format:
            custom_view = "%s_%s_%s" % (r.name, default_name, format)
        else:
            custom_view = "%s_%s" % (r.name, default_name)
        _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

    if os.path.exists(_custom_view):
        response.view = prefix + "/" + custom_view
    else:
        if format:
            response.view = default_name.replace(".html", "_%s.html" % format)
        else:
            response.view = default_name

#
# shn_convert_orderby ----------------------------------------------------------
#
def shn_get_columns(table):
    return [f for f in table.fields if table[f].readable]

def shn_convert_orderby(table, request, fields=None):
    cols = fields or shn_get_columns(table)

    def colname(i):
        return table._tablename + "." + cols[int(request.vars["iSortCol_" + str(i)])]

    def rng():
        return xrange(0, int(request.vars["iSortingCols"]))

    def direction(i):
        dir = "sSortDir_" + str(i)
        if request.vars.get(dir, None):
            return " " + request.vars[dir]
        return ""

    return ", ".join([colname(i) + direction(i) for i in rng()])

#
# shn_build_ssp_filter --------------------------------------------------------
#
def shn_build_ssp_filter(table, request, fields=None):

    cols = fields or shn_get_columns(table)
    searchq = None

    # TODO: use FieldS3 (with representation_field)
    for i in xrange(0, int(request.vars.iColumns)):
        field = table[cols[i]]
        query = None
        if str(field.type) == "integer":
            context = str(request.vars.sSearch).lower()
            requires = field.requires
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            if requires:
                r = requires[0]
                options = []
                if isinstance(r, (IS_NULL_OR, IS_EMPTY_OR)) and hasattr(r.other, "options"):
                    options = r.other.options()
                elif hasattr(r, "options"):
                    options = r.options()
                vlist = []
                for (value, text) in options:
                    if str(text).lower().find(context.lower()) != -1:
                        vlist.append(value)
                if vlist:
                    query = field.belongs(vlist)
            else:
                continue
        elif str(field.type) in ("string", "text"):
            context = "%" + request.vars.sSearch + "%"
            context = context.lower()
            query = table[cols[i]].lower().like(context)

        if searchq is None and query:
            searchq = query
        elif query:
            searchq = searchq | query

    return searchq

# *****************************************************************************
# REST Method Handlers
#
# These functions are to handle REST methods.
# Currently implemented methods are:
#
#   - list
#   - read
#   - create
#   - update
#   - delete
#   - search
#
# Handlers must be implemented as:
#
#   def method_handler(r, **attr)
#
# where:
#
#   r - is the S3Request
#   attr - attributes of the call, passed through
#

#
# shn_read --------------------------------------------------------------------
#
def shn_read(r, **attr):

    """ Read a single record. """

    prefix, name, table, tablename = r.target()
    representation = r.representation.lower()

    # Get the callbacks of the target table
    onvalidation = s3xrc.model.get_config(table, "onvalidation")
    onaccept = s3xrc.model.get_config(table, "onaccept")

    # Get the controller attributes
    rheader = attr.get("rheader", None)
    sticky = attr.get("sticky", rheader is not None)

    # Get the table-specific attributes
    _attr = r.component and r.component.attr or attr
    main = _attr.get("main", None)
    extra = _attr.get("extra", None)
    caller = _attr.get("caller", None)
    editable = _attr.get("editable", True)
    deletable = _attr.get("deletable", True)

    # Delete & Update links
    href_delete = r.other(method="delete", representation=representation)
    href_edit = r.other(method="update", representation=representation)

    # Get the correct record ID
    if r.component:
        resource = r.resource.components.get(r.component_name).resource
        resource.load(start=0, limit=1)
        if not len(resource):
            if not r.multiple:
                r.component_id = None
                if shn_has_permission("create", tablename):
                    redirect(r.other(method="create", representation=representation))
                else:
                    record_id = None
            else:
                session.error = BADRECORD
                redirect(r.there())
        else:
            record_id = resource.records().first().id
    else:
        record_id = r.id

    # Redirect to update if user has permission unless URL method specified
    if not r.method:
        authorised = shn_has_permission("update", tablename, record_id)
        if authorised and representation == "html" and editable:
            return shn_update(r, **attr)

    # Check for read permission
    authorised = shn_has_permission("read", tablename, record_id)
    if not authorised:
        r.unauthorised()

    # Audit
    s3xrc.audit("read", prefix, name,
                record=record_id, representation=representation)

    if r.representation in ("html", "popup"):

        # Title and subtitle
        title = shn_get_crud_string(r.tablename, "title_display")
        output = dict(title=title)
        if r.component:
            subtitle = shn_get_crud_string(tablename, "title_display")
            output.update(subtitle=subtitle)

        # Resource header
        if rheader and r.id and (r.component or sticky):
            try:
                rh = rheader(r)
            except TypeError:
                rh = rheader
            output.update(rheader=rh)

        # Item
        if record_id:
            item = crud.read(table, record_id)
            subheadings = attr.get("subheadings", None)
            if subheadings:
                shn_insert_subheadings(item, tablename, subheadings)
        else:
            item = shn_get_crud_string(tablename, "msg_list_empty")

        # Put into view
        if representation == "html":
            shn_custom_view(r, "display.html")
            output.update(item=item)
        elif representation == "popup":
            shn_custom_view(r, "popup.html")
            output.update(form=item, main=main, extra=extra, caller=caller)

        # Add edit and delete buttons as appropriate
        authorised = shn_has_permission("update", tablename, record_id)
        if authorised and href_edit and editable and r.method <> "update":
            edit = A(T("Edit"), _href=href_edit, _class="action-btn")
            output.update(edit=edit)
        authorised = shn_has_permission("delete", tablename)
        if authorised and href_delete and deletable:
            delete = A(T("Delete"), _href=href_delete, _id="delete-btn", _class="action-btn")
            output.update(delete=delete)

        # Add a list button if appropriate
        if not r.component or r.multiple:
            label_list_button = shn_get_crud_string(tablename, "label_list_button")
            list_btn = A(label_list_button, _href=r.there(), _class="action-btn")
            output.update(list_btn=list_btn)

        return output

    elif representation == "plain":
        item = crud.read(table, record_id)
        response.view = "plain.html"
        return dict(item=item)

    elif representation == "csv":
        query = db[table].id == record_id
        return export_csv(tablename, query)

    elif representation == "pdf":
        query = db[table].id == record_id
        return export_pdf(table, query, list_fields)

    elif representation == "xls":
        query = db[table].id == record_id
        return export_xls(table, query, list_fields)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f="index"))

#
# shn_linkto ------------------------------------------------------------------
#
def shn_linkto(r, sticky=False):

    """ Helper function to generate links in list views """

    def shn_list_linkto(field, r=r, sticky=sticky):
        if r.component:
            authorised = shn_has_permission("update", r.component.tablename)
            if authorised:
                return r.component.attr.linkto_update or \
                       URL(r=request, args=[r.id, r.component_name, field, "update"],
                           vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
            else:
                return r.component.attr.linkto or \
                       URL(r=request, args=[r.id, r.component_name, field],
                           vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
        else:
            authorised = shn_has_permission("update", r.tablename)
            if authorised:
                if sticky:
                    # Render "sticky" update form (returns to itself)
                    _next = str(URL(r=request, args=[field], vars=request.vars))
                     # need to avoid double URL-encoding if "[id]"
                    _next = str(_next).replace("%5Bid%5D", "[id]")
                else:
                    _next = URL(r=request, args=request.args, vars=request.vars)
                return response.s3.linkto_update or \
                       URL(r=request, args=[field, "update"])
            else:
                return response.s3.linkto or \
                       URL(r=request, args=[field],
                           vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

    return shn_list_linkto

#
# shn_list --------------------------------------------------------------------
#
def shn_list(r, **attr):

    """ List records matching the request """

    prefix, name, table, tablename = r.target()
    vars = r.request.get_vars
    representation = r.representation.lower()

    # Get callbacks and list fields
    onvalidation = s3xrc.model.get_config(table, "onvalidation")
    onaccept = s3xrc.model.get_config(table, "onaccept")
    list_fields = s3xrc.model.get_config(table, "list_fields")

    # Get controller attributes
    rheader = attr.get("rheader", None)
    sticky = attr.get("sticky", rheader is not None)

    # Table-specific controller attributes
    _attr = r.component and r.component.attr or attr
    editable = _attr.get("editable", True)
    deletable = _attr.get("deletable", True)
    listadd = _attr.get("listadd", True)
    main = _attr.get("main", None)
    extra = _attr.get("extra", None)
    orderby = _attr.get("orderby", None)
    sortby = _attr.get("sortby", None)

    # Provide the ability to get a subset of records
    start = vars.get("start", 0)
    limit = vars.get("limit", None)
    if limit is not None:
        try:
            start = int(start)
            limit = int(limit)
        except ValueError:
            limitby = None
        else:
            # disable Server-Side Pagination
            response.s3.pagination = False
            limitby = (start, start + limit)
    else:
        limitby = None

    # Get the initial query
    if r.component:
        resource = r.resource.components.get(r.component_name).resource
        href_add = URL(r=r.request, f=r.name, args=[r.id, name, "create"])
    else:
        resource = r.resource
        href_add = URL(r=r.request, f=r.name, args=["create"])
    query = resource.get_query()

    # SSPag filter handling
    if r.representation == "html":
        session.s3.filter = query
    elif r.representation.lower() == "aadata":
        if session.s3.filter is not None:
            query = session.s3.filter

    s3xrc.audit("list", prefix, name, representation=r.representation)

    # Which fields do we display?
    fields = None
    if list_fields:
        fkey = r.fkey or None
        fields = [f for f in list_fields if table[f].readable and f != fkey]
    if fields and len(fields) == 0:
        fields.append("id")
    if not fields:
        fields = [f for f in table.fields if table[f].readable]

    # Where to link the ID column?
    linkto = shn_linkto(r, sticky)

    if representation == "aadata":

        iDisplayStart = vars.get("iDisplayStart", 0)
        iDisplayLength = vars.get("iDisplayLength", None)

        if iDisplayLength is not None:
            try:
                start = int(iDisplayStart)
                limit = int(iDisplayLength)
            except ValueError:
                start = 0
                limit = None

        iSortingCols = vars.get("iSortingCols", None)
        if iSortingCols and orderby is None:
            orderby = shn_convert_orderby(table, request, fields=fields)

        if vars.sSearch:
            squery = shn_build_ssp_filter(table, request, fields=fields)
            if squery is not None:
                query = squery & query

        sEcho = int(vars.sEcho or 0)
        totalrows = resource.count()
        if limit:
            rows = db(query).select(table.ALL,
                                    limitby = (start, start + limit),
                                    orderby = orderby)
        else:
            rows = db(query).select(table.ALL,
                                    orderby = orderby)

        result = dict(sEcho = sEcho,
                      iTotalRecords = len(rows),
                      iTotalDisplayRecords = totalrows,
                      aaData = [[shn_field_represent_sspage(table[f], row, f, linkto=linkto)
                                for f in fields] for row in rows])

        from gluon.serializers import json
        return json(result)

    elif representation in ("html", "popup"):

        output = dict(main=main, extra=extra, sortby=sortby)

        if r.component:
            title = shn_get_crud_string(r.tablename, "title_display")
            if rheader:
                try:
                    rh = rheader(r)
                except TypeError:
                    rh = rheader
                output.update(rheader=rh)
        else:
            title = shn_get_crud_string(tablename, "title_list")

        subtitle = shn_get_crud_string(tablename, "subtitle_list")
        output.update(title=title, subtitle=subtitle)

        # Column labels: use custom or prettified label
        fields = [table[f] for f in fields]
        headers = dict(map(lambda f: (str(f), f.label), fields))

        # SSPag: only download 1 record initially & let
        # the view request what it wants via AJAX
        if response.s3.pagination and not limitby:
            limitby = (0, 1)

        # Get the items
        items = crud.select(table,
                            query=query,
                            fields=fields,
                            orderby=orderby,
                            limitby=limitby,
                            headers=headers,
                            linkto=linkto,
                            truncate=48, _id="list", _class="display")

        if not items:
            items = shn_get_crud_string(tablename, "msg_list_empty")
        output.update(items=items)

        authorised = shn_has_permission("create", tablename)
        if authorised and listadd:

            # Block join field
            if r.component:
                _comment = table[r.fkey].comment
                table[r.fkey].comment = None
                table[r.fkey].default = r.record[r.pkey]

                # Fix for #447:
                if r.http == "POST":
                    table[r.fkey].writable = True
                    request.post_vars.update({r.fkey: str(r.record[r.pkey])})
                else:
                    table[r.fkey].writable = False

            if onaccept:
                _onaccept = lambda form: \
                            s3xrc.audit("create", prefix, name, form=form,
                                        representation=representation) and \
                            s3xrc.store_session(session, prefix, name, 0) and \
                            onaccept(form)
            else:
                _onaccept = lambda form: \
                            s3xrc.audit("create", prefix, name, form=form,
                                        representation=representation) and \
                            s3xrc.store_session(session, prefix, name, 0)

            message = shn_get_crud_string(tablename, "msg_record_created")

            # Display the Add form above List
            form = crud.create(table,
                               onvalidation=onvalidation,
                               onaccept=_onaccept,
                               message=message,
                               next=r.there())

            # Cancel button?
            #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))
            if response.s3.cancel:
                form[0][-1][1].append(INPUT(_type="button",
                                            _value="Cancel",
                                            _onclick="window.location='%s';" %
                                                     response.s3.cancel))

            if "location_id" in db[tablename].fields:
                # Allow the Location Selector to take effect
                _gis.location_id = True
                if response.s3.gis.map_selector:
                    # Include a map
                    _map = shn_map(r, method="create")
                    output.update(_map=_map)

            if r.component:
                table[r.fkey].comment = _comment

            addtitle = shn_get_crud_string(tablename, "subtitle_create")

            label_create_button = shn_get_crud_string(tablename, "label_create_button")
            showaddbtn = A(label_create_button,
                           _id = "show-add-btn",
                           _class="action-btn")

            shn_custom_view(r, "list_create.html")
            output.update(form=form, addtitle=addtitle, showaddbtn=showaddbtn)

        else:
            # List only
            if authorised:
                label_create_button = shn_get_crud_string(tablename, "label_create_button")
                add_btn = A(label_create_button, _href=href_add, _class="action-btn")
            else:
                add_btn = ""

            shn_custom_view(r, "list.html")
            output.update(add_btn=add_btn)

        return output

    elif representation == "plain":
        items = crud.select(table, query, truncate=24)
        response.view = "plain.html"
        return dict(item=items)

    elif representation == "csv":
        return export_csv(tablename, query)

    elif representation == "pdf":
        return export_pdf(table, query, list_fields)

    elif representation == "xls":
        return export_xls(table, query, list_fields)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f="index"))

#
# shn_create ------------------------------------------------------------------
#
def shn_create(r, **attr):

    """ Create new records """

    prefix, name, table, tablename = r.target()
    representation = r.representation.lower()

    # Callbacks
    onvalidation = s3xrc.model.get_config(table, "onvalidation")
    onaccept = s3xrc.model.get_config(table, "onaccept")

    # Controller attributes
    rheader = attr.get("rheader", None)
    sticky = attr.get("sticky", rheader is not None)

    # Table-specific controller attributes
    _attr = r.component and r.component.attr or attr
    main = _attr.get("main", None)
    extra = _attr.get("extra", None)
    create_next = _attr.get("create_next")

    if representation in ("html", "popup"):

        # Copy from a previous record?
        from_record = r.request.get_vars.get("from_record", None)
        from_fields = r.request.get_vars.get("from_fields", None)
        original = None
        if from_record:
            del r.request.get_vars["from_record"] # forget it
            if from_record.find(".") != -1:
                source_name, from_record = from_record.split(".", 1)
                source = db.get(source_name, None)
            else:
                source = table
            if from_fields:
                del r.request.get_vars["from_fields"] # forget it
                from_fields = from_fields.split(",")
            else:
                from_fields = [f for f in table.fields if f in source.fields and f!="id"]
            if source and from_record:
                copy_fields = [source[f] for f in from_fields if
                                    f in source.fields and
                                    f in table.fields and
                                    table[f].type == source[f].type and
                                    table[f].readable and table[f].writable]
                if shn_has_permission("read", source._tablename, from_record):
                    original = db(source.id == from_record).select(limitby=(0, 1), *copy_fields).first()
                if original:
                    missing_fields = Storage()
                    for f in table.fields:
                        if f not in original and \
                           table[f].readable and table[f].writable:
                            missing_fields[f] = table[f].default
                    original.update(missing_fields)

        # Default components
        output = dict(module=prefix, resource=name, main=main, extra=extra)

        if "location_id" in db[tablename].fields:
            # Allow the Location Selector to take effect
            _gis.location_id = True
            if response.s3.gis.map_selector:
                # Include a map
                _map = shn_map(r, method="create")
                output.update(_map=_map)

        # Title, subtitle and resource header
        if r.component:
            title = shn_get_crud_string(r.tablename, "title_display")
            subtitle = shn_get_crud_string(tablename, "subtitle_create")
            output.update(subtitle=subtitle)
            if rheader and r.id:
                try:
                    rh = rheader(r)
                except TypeError:
                    rh = rheader
                output.update(rheader=rh)
        else:
            title = shn_get_crud_string(tablename, "title_create")
        output.update(title=title)

        if r.component:
            # Block join field
            _comment = table[r.fkey].comment
            table[r.fkey].comment = None
            table[r.fkey].default = r.record[r.pkey]
            if r.http == "POST":
                table[r.fkey].writable = True
                request.post_vars.update({r.fkey: str(r.record[r.pkey])})
            else:
                table[r.fkey].writable = False
            # Neutralize callbacks
            crud.settings.create_onvalidation = None
            crud.settings.create_onaccept = None
            crud.settings.create_next = None
            r.next = create_next or r.there()
        else:
            r.next = crud.settings.create_next or r.there()
            crud.settings.create_next = None
            if not onvalidation:
                onvalidation = crud.settings.create_onvalidation
            if not onaccept:
                onaccept = crud.settings.create_onaccept

        if onaccept:
            _onaccept = lambda form: \
                        s3xrc.audit("create", prefix, name, form=form,
                                    representation=representation) and \
                        s3xrc.store_session(session,
                                            prefix, name, form.vars.id) and \
                        onaccept(form)

        else:
            _onaccept = lambda form: \
                        s3xrc.audit("create", prefix, name, form=form,
                                    representation=representation) and \
                        s3xrc.store_session(session,
                                            prefix, name, form.vars.id)

        # Get the form
        message = shn_get_crud_string(tablename, "msg_record_created")
        if original:
            original.id = None
            form = crud.update(table,
                               original,
                               message=message,
                               next=crud.settings.create_next,
                               deletable=False,
                               onvalidation=onvalidation,
                               onaccept=_onaccept)
        else:
            form = crud.create(table,
                               message=message,
                               onvalidation=onvalidation,
                               onaccept=_onaccept)

        subheadings = attr.get("subheadings", None)
        if subheadings:
            shn_insert_subheadings(form, tablename, subheadings)

        # Cancel button?
        #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))
        if response.s3.cancel:
            form[0][-1][1].append(INPUT(_type="button",
                                        _value="Cancel",
                                        _onclick="window.location='%s';" %
                                                 response.s3.cancel))

        # Put the form into output
        output.update(form=form)

        # Restore comment
        if r.component:
            table[r.fkey].comment = _comment

        # Add a list button if appropriate
        if not r.component or r.multiple:
            label_list_button = shn_get_crud_string(tablename, "label_list_button")
            list_btn = A(label_list_button, _href=r.there(), _class="action-btn")
            output.update(list_btn=list_btn)

        # Custom view
        if representation == "popup":
            shn_custom_view(r, "popup.html")
            output.update(caller=r.request.vars.caller)
            r.next = None
        else:
            shn_custom_view(r, "create.html")

        return output

    elif representation == "plain":
        if onaccept:
            _onaccept = lambda form: \
                        s3xrc.audit("create", prefix, name, form=form,
                                    representation=representation) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        s3xrc.audit("create", prefix, name, form=form,
                                    representation=representation)

        form = crud.create(table,
                           onvalidation=onvalidation, onaccept=_onaccept)
        response.view = "plain.html"
        return dict(item=form)

    elif representation == "url":
        return import_url(r)

    elif representation == "csv":
        # Read in POST
        import csv
        csv.field_size_limit(1000000000)
        #infile = open(request.vars.filename, "rb")
        infile = r.request.vars.filename.file
        try:
            import_csv(infile, table)
            session.flash = T("Data uploaded")
        except:
            session.error = T("Unable to parse CSV file!")
        redirect(r.there())

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f="index"))

#
# shn_update ------------------------------------------------------------------
#
def shn_update(r, **attr):

    """ Update an existing record """

    prefix, name, table, tablename = r.target()
    representation = r.representation.lower()

    # Get callbacks
    onvalidation = s3xrc.model.get_config(table, "onvalidation")
    onaccept = s3xrc.model.get_config(table, "onaccept")

    # Get controller attributes
    rheader = attr.get("rheader", None)
    sticky = attr.get("sticky", rheader is not None)

    # Table-specific controller attributes
    _attr = r.component and r.component.attr or attr
    editable = _attr.get("editable", True)
    deletable = _attr.get("deletable", True)
    update_next = _attr.get("update_next", None)

    # Find the correct record ID
    if r.component:
        resource = r.resource.components.get(r.component_name).resource
        resource.load(start=0, limit=1)
        if not len(resource):
            if not r.multiple:
                r.component_id = None
                redirect(r.other(method="create", representation=representation))
            else:
                session.error = BADRECORD
                redirect(r.there())
        else:
            record_id = resource.records().first().id
    else:
        record_id = r.id

    # Redirect to read view if not editable
    if not editable and representation == "html":
        return shn_read(r, **attr)

    # Check authorisation
    authorised = shn_has_permission("update", tablename, record_id)
    if not authorised:
        r.unauthorised()

    # Audit read
    s3xrc.audit("read", prefix, name,
                record=record_id, representation=representation)

    if r.representation == "html" or r.representation == "popup":

        # Custom view
        if r.representation == "html":
            shn_custom_view(r, "update.html")
        elif r.representation == "popup":
            shn_custom_view(r, "popup.html")

        # Title and subtitle
        if r.component:
            title = shn_get_crud_string(r.tablename, "title_display")
            subtitle = shn_get_crud_string(tablename, "title_update")
            output = dict(title=title, subtitle=subtitle)
        else:
            title = shn_get_crud_string(tablename, "title_update")
            output = dict(title=title)

        # Resource header
        if rheader and r.id and (r.component or sticky):
            try:
                rh = rheader(r)
            except TypeError:
                rh = rheader
            output.update(rheader=rh)

        # Add delete button
        if deletable:
            href_delete = r.other(method="delete", representation=representation)
            label_del_button = shn_get_crud_string(tablename, "label_delete_button")
            del_btn = A(label_del_button,
                        _href=href_delete,
                        _id="delete-btn",
                        _class="action-btn")
            output.update(del_btn=del_btn)

        if r.component:
            _comment = table[r.fkey].comment
            table[r.fkey].comment = None
            table[r.fkey].default = r.record[r.pkey]
            # Fix for #447:
            if r.http == "POST":
                table[r.fkey].writable = True
                request.post_vars.update({r.fkey: str(r.record[r.pkey])})
            else:
                table[r.fkey].writable = False
            crud.settings.update_onvalidation = None
            crud.settings.update_onaccept = None
            if not representation == "popup":
                crud.settings.update_next = update_next or r.there()
        else:
            if not representation == "popup" and \
               not crud.settings.update_next:
                crud.settings.update_next = update_next or r.here()
            if not onvalidation:
                onvalidation = crud.settings.update_onvalidation
            if not onaccept:
                onaccept = crud.settings.update_onaccept

        if onaccept:
            _onaccept = lambda form: \
                        s3xrc.audit("update", prefix, name, form=form,
                                    representation=representation) and \
                        s3xrc.store_session(session, prefix, name, form.vars.id) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        s3xrc.audit("update", prefix, name, form=form,
                                    representation=representation) and \
                        s3xrc.store_session(session, prefix, name, form.vars.id)

        crud.settings.update_deletable = deletable
        message = shn_get_crud_string(tablename, "msg_record_modified")

        form = crud.update(table, record_id,
                            message=message,
                            onvalidation=onvalidation,
                            onaccept=_onaccept,
                            deletable=False) # TODO: add extra delete button to form

        subheadings = attr.get("subheadings", None)
        if subheadings:
            shn_insert_subheadings(form, tablename, subheadings)

        # Cancel button?
        #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))
        if response.s3.cancel:
            form[0][-1][1].append(INPUT(_type="button",
                                        _value="Cancel",
                                        _onclick="window.location='%s';" %
                                                 response.s3.cancel))

        output.update(form=form)

        # Restore comment
        if r.component:
            table[r.fkey].comment = _comment

        # Add a list button if appropriate
        if not r.component or r.multiple:
            label_list_button = shn_get_crud_string(tablename, "label_list_button")
            list_btn = A(label_list_button, _href=r.there(), _class="action-btn")
            output.update(list_btn=list_btn)

        if "location_id" in db[tablename].fields:
            # Allow the Location Selector to take effect
            _gis.location_id = True
            if response.s3.gis.map_selector:
                # Include a map
                _map = shn_map(r, method="update", tablename=tablename, prefix=prefix, name=name)
                oldlocation = _map["oldlocation"]
                _map = _map["_map"]
                output.update(_map=_map, oldlocation=oldlocation)

        return output

    elif representation == "plain":
        if onaccept:
            _onaccept = lambda form: \
                        s3xrc.audit("update", prefix, name, form=form,
                                    representation=representation) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        s3xrc.audit("update", prefix, name, form=form,
                                    representation=representation)

        form = crud.update(table, record_id,
                           onvalidation=onvalidation,
                           onaccept=_onaccept,
                           deletable=False)

        response.view = "plain.html"
        return dict(item=form)

    elif r.representation == "url":
        return import_url(r)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f="index"))


#
# shn_delete ------------------------------------------------------------------
#
def shn_delete(r, **attr):

    """ Delete record(s) """

    prefix, name, table, tablename = r.target()
    representation = r.representation.lower()

    # Get callbacks
    onvalidation = s3xrc.model.get_config(table, "delete_onvalidation")
    onaccept = s3xrc.model.get_config(table, "delete_onaccept")

    # Table-specific controller attributes
    _attr = r.component and r.component.attr or attr
    deletable = _attr.get("deletable", True)

    # custom delete_next?
    delete_next = _attr.get("delete_next", None)
    if delete_next:
        r.next = delete_next

    if r.component:
        query = ((table[r.fkey] == r.table[r.pkey]) & \
                 (table[r.fkey] == r.record[r.pkey]))
        if r.component_id:
            query = (table.id == r.component_id) & query
    else:
        query = (table.id == r.id)

    if "deleted" in table:
        query = (table.deleted == False) & query

    # Get target records
    rows = db(query).select(table.ALL)

    # Nothing to do? Return here!
    if not rows:
        session.confirmation = T("No records to delete")
        return {}

    message = shn_get_crud_string(tablename, "msg_record_deleted")

    # Delete all accessible records
    numrows = 0
    for row in rows:
        if shn_has_permission("delete", tablename, row.id):
            numrows += 1
            if s3xrc.get_session(session, prefix=prefix, name=name) == row.id:
                s3xrc.clear_session(session, prefix=prefix, name=name)
            try:
                shn_audit("delete", prefix, name, record=row.id, representation=representation)
                # Reset session vars if necessary
                if "deleted" in db[table] and \
                   db(db.s3_setting.id == 1).select(db.s3_setting.archive_not_delete, limitby=(0, 1)).first().archive_not_delete:
                    if onvalidation:
                        onvalidation(row)
                    # Avoid collisions of values in unique fields between deleted records and
                    # later new records => better solution could be: move the deleted data to
                    # a separate table (e.g. in JSON) and delete from this table (that would
                    # also eliminate the need for special deletion status awareness throughout
                    # the system). Should at best be solved in the DAL.
                    deleted = dict(deleted=True)
                    for f in table.fields:
                        if f not in ("id", "uuid") and table[f].unique:
                            deleted.update({f:None}) # not good => data loss!
                    db(db[table].id == row.id).update(**deleted)
                    if onaccept:
                        onaccept(row)
                else:
                    # Do not CRUD.delete! (it never returns, but redirects)
                    if onvalidation:
                        onvalidation(row)
                    del db[table][row.id]
                    if onaccept:
                        onaccept(row)

            # Would prefer to import sqlite3 & catch specific error, but
            # this isn't generalisable to other DBs...we need a DB config to pull in.
            #except sqlite3.IntegrityError:
            except:
                session.error = T("Cannot delete whilst there are linked records. Please delete linked records first.")
        else:
            continue

    if not session.error:
        if numrows > 1:
            session.confirmation = "%s %s" % ( numrows, T("records deleted"))
        else:
            session.confirmation = message

    item = s3xrc.xml.json_message()
    response.view = "plain.html"
    output = dict(item=item)

    return output

#
# shn_copy ------------------------------------------------------------------
#
def shn_copy(r, **attr):
    redirect(URL(r=request, args="create", vars={"from_record":r.id}))

#
# shn_map ------------------------------------------------------------------
#
def shn_map(r, method="create", tablename=None, prefix=None, name=None):
    """ Prepare a Map to include in forms"""
    
    if method == "create":
        _map = gis.show_map(add_feature = True,
                            add_feature_active = True,
                            toolbar = True,
                            collapsed = True,
                            window = True,
                            window_hide = True)
        return _map

    elif method == "update" and tablename and prefix and name:
        config = gis.get_config()
        zoom = config.zoom
        _locations = db.gis_location
        fields = [_locations.id, _locations.uuid, _locations.name, _locations.lat, _locations.lon, _locations.level, _locations.parent, _locations.addr_street]
        location = db((db[tablename].id == r.id) & (_locations.id == db[tablename].location_id)).select(limitby=(0, 1), *fields).first()
        if location and location.lat is not None and location.lon is not None:
            lat = location.lat
            lon = location.lon
        else:
            lat = config.lat
            lon = config.lon
        layername = Tstr("Location")
        popup_label = ""
        filter = Storage(tablename = tablename,
                         id = r.id
                        )
        layer = gis.get_feature_layer(prefix, name, layername, popup_label, filter=filter)
        feature_queries = [layer]
        _map = gis.show_map(lat = lat,
                            lon = lon,
                            # Same as a single zoom on a cluster
                            zoom = zoom + 2,
                            feature_queries = feature_queries,
                            add_feature = True,
                            add_feature_active = False,
                            toolbar = True,
                            collapsed = True,
                            window = True,
                            window_hide = True)
        if location and location.id:
            _location = Storage(id = location.id,
                                uuid = location.uuid,
                                name = location.name,
                                lat = location.lat,
                                lon = location.lon,
                                level = location.level,
                                parent = location.parent,
                                addr_street = location.addr_street
                                )
        else:
            _location = None
        return dict(_map=_map, oldlocation=_location)

    return dict(None, None)

#
# shn_search ------------------------------------------------------------------
#
def shn_search(r, **attr):

    """ Search function responding in JSON """

    deletable = attr.get("deletable", True)
    main = attr.get("main", None)
    extra = attr.get("extra", None)

    request = r.request

    # Filter Search list to just those records which user can read
    query = shn_accessible_query("read", r.table)

    # Filter search to items which aren't deleted
    if "deleted" in r.table:
        query = (r.table.deleted == False) & query

    # Respect response.s3.filter
    if response.s3.filter:
        query = response.s3.filter & query

    if r.representation in ("html", "popup"):

        shn_represent(r.table, r.prefix, r.name, deletable, main, extra)
        search = t2.search(r.table, query=query)
        #search = crud.search(r.table, query=query)[0]

        # Check for presence of Custom View
        shn_custom_view(r, "search.html")

        # CRUD Strings
        title = s3.crud_strings.title_search

        output = dict(search=search, title=title)

    elif r.representation == "json":

        _vars = request.vars
        _table = r.table

        # JQuery Autocomplete uses "q" instead of "value"
        value = _vars.value or _vars.q or None

        if _vars.field and _vars.filter and value:
            field = str.lower(_vars.field)
            _field = _table[field]

            # Optional fields
            if "field2" in _vars:
                field2 = str.lower(_vars.field2)
            else:
                field2 = None
            if "field3" in _vars:
                field3 = str.lower(_vars.field3)
            else:
                field3 = None
            if "parent" in _vars and _vars.parent:
                if _vars.parent == "null":
                    parent = None
                else:
                    parent = int(_vars.parent)
            else:
                parent = None

            limit = int(_vars.limit or 0)

            filter = _vars.filter
            if filter == "~":
                if field2 and field3:
                    # pr_person name search
                    if " " in value:
                        value1, value2 = value.split(" ", 1)
                        query = query & ((_field.like("%" + value1 + "%")) & \
                                        (_table[field2].like("%" + value2 + "%")) | \
                                        (_table[field3].like("%" + value2 + "%")))
                    else:
                        query = query & ((_field.like("%" + value + "%")) | \
                                        (_table[field2].like("%" + value + "%")) | \
                                        (_table[field3].like("%" + value + "%")))

                elif parent:
                    # gis_location hierarchical search
                    # Immediate children only
                    #query = query & (_table.parent == parent) & \
                    #                (_field.like("%" + value + "%"))
                    # Nice if we could filter in SQL but this breaks the recursion
                    children = gis.get_children(parent)
                    children = children.find(lambda row: value in str.lower(row.name))
                    item = children.json()
                    query = None

                else:
                    # Normal single-field
                    query = query & (_field.like("%" + value + "%"))

                if query:
                    if limit:
                        item = db(query).select(limitby=(0, limit)).json()
                    else:
                        item = db(query).select().json()

            elif filter == "=":
                query = query & (_field == value)
                if parent:
                    # e.g. gis_location hierarchical search
                    query = query & (_table.parent == parent)

                if _table == db.gis_location:
                    # Don't return unnecessary fields (WKT is large!)
                    item = db(query).select(_table.id, _table.uuid, _table.parent, _table.name, _table.level, _table.lat, _table.lon, _table.addr_street).json()
                else:
                    item = db(query).select().json()

            elif filter == "<":
                query = query & (_field < value)
                item = db(query).select().json()

            elif filter == ">":
                query = query & (_field > value)
                item = db(query).select().json()

            else:
                item = s3xrc.xml.json_message(False, 400, "Unsupported filter! Supported filters: ~, =, <, >")
                raise HTTP(400, body=item)
        else:
            item = s3xrc.xml.json_message(False, 400, "Search requires specifying Field, Filter & Value!")
            raise HTTP(400, body=item)

        response.view = "xml.html"
        output = dict(item=item)

    else:
        raise HTTP(501, body=BADFORMAT)

    return output

# *****************************************************************************
# Main controller function

#
# shn_rest_controller ---------------------------------------------------------
#
def shn_rest_controller(module, resource, **attr):

    """
        RESTlike controller function
        ============================

        Provides CRUD operations for the given module/resource.

        Supported Representations:
        ==========================

        Representation is recognized from the extension of the target resource.
        You can still pass a "?format=" to override this.

            - B{html}: is the default (including full layout)
            - B{plain}: is HTML with no layout
                - can be inserted into DIVs via AJAX calls
                - can be useful for clients on low-bandwidth or small screen sizes
            - B{ext}: is Ext layouts (experimental)
            - B{json}: JSON export/import using XSLT
            - B{xml}: XML export/import using XSLT
            - B{csv}: useful for synchronization/database migration
                - List/Display/Create for now
            - B{pdf}: list/read only
            - B{rss}: list only
            - B{xls}: list/read only
            - B{ajax}: designed to be run asynchronously to refresh page elements
            - B{url}: designed to be accessed via JavaScript
                - responses in JSON format
                - create/update/delete done via simple GET vars (no form displayed)
            - B{popup}: designed to be used inside popups
            - B{aaData}: used by dataTables for server-side pagination

        Request options:
        ================

            - B{response.s3.filter}: contains custom query to filter list views (primary resources)
            - B{response.s3.jfilter}: contains custom query to filter list views (joined resources)
            - B{response.s3.cancel}: adds a cancel button to forms & provides a location to direct to upon pressing
            - B{response.s3.pagination}: enables server-side pagination (detected by view which then calls REST via AJAX)

        Description:
        ============

        @param deletable: provide visible options for deletion (optional, default=True)
        @param editable: provide visible options for editing (optional, default=True)
        @param listadd: provide an add form in the list view (optional, default=True)

        @param main:
            the field used for the title in RSS output (optional, default="name")
        @param extra:
            the field used for the description in RSS output & in Search AutoComplete
            (optional, default=None)

        @param orderby:
            the sort order for server-side paginated list views (optional, default=None), e.g.::
                db.mytable.myfield1|db.mytable.myfield2

        @param sortby:
            the sort order for client-side paginated list views (optional, default=None), e.g.::
                [[1, "asc"], [2, "desc"]]

            see: U{http://datatables.net/examples/basic_init/table_sorting.html}

        @param rheader: function to produce a page header for the primary resource
        @type rheader:
            function(resource, record_id, representation, next=None, same=None)

        @author: Fran Boon
        @author: nursix

        @todo:
            - Alternate Representations
            - CSV update
            - SMS, LDIF

    """

    s3xrc.set_handler("list", shn_list)
    s3xrc.set_handler("read", shn_read)
    s3xrc.set_handler("create", shn_create)
    s3xrc.set_handler("update", shn_update)
    s3xrc.set_handler("delete", shn_delete)
    s3xrc.set_handler("search", shn_search)
    s3xrc.set_handler("copy", shn_copy)

    res, req = s3xrc.parse_request(module, resource, session, request, response)
    output = res.execute_request(req, **attr)

    return output

# END
# *****************************************************************************
