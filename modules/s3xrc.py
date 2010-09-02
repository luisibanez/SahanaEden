# -*- coding: utf-8 -*-

"""
    S3XRC Resource Framework

    @version: 2.1
    @see: U{B{I{S3XRC-2}} <http://eden.sahanafoundation.org/wiki/S3XRC>} on Eden wiki

    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: nursix
    @contact: dominic AT nursix DOT org
    @copyright: 2009-2010 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

__name__ = "S3XRC"
__all__ = ["S3Resource",
           "S3Request",
           "S3MethodHandler",
           "S3ResourceController"]

import os, sys, cgi, uuid, datetime, time, urllib, StringIO
import gluon.contrib.simplejson as json

from gluon.storage import Storage
from gluon.sql import Set, Row
from gluon.html import URL
from gluon.http import HTTP, redirect
from gluon.validators import IS_NULL_OR, IS_EMPTY_OR, IS_DATE, IS_TIME
try:
    from xml.etree.cElementTree import ElementTree
except ImportError:
    from xml.etree.ElementTree import ElementTree

from lxml import etree


# *****************************************************************************
class S3Resource(object):

    """ API for resources """

    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name,
                 id=None,
                 uid=None,
                 filter=None,
                 url_vars=None,
                 parent=None,
                 components=None,
                 storage=None,
                 debug=None):

        """ Constructor

            @param manager: the resource controller
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (without prefix)
            @param id: record ID (or list of record IDs)
            @param uid: record UID (or list of record UIDs)
            @param filter: filter query (DAL resources only)
            @param url_vars: dictionary of URL query variables
            @param parent: the parent resource
            @param components: component name (or list of component names)
            @param storage: URL of the data store, None for DAL
            @param debug: whether to write debug messages to stderr or not
            @type debug: bool

        """

        assert manager is not None, "Undefined Resource Manager"
        self.__manager = manager

        self.ERROR = self.__manager.ERROR

        if debug is None:
            self.__debug = self.__manager.debug
        else:
            self.__debug = debug

        self.__permit = self.__manager.auth.shn_has_permission
        self.__accessible = self.__manager.auth.shn_accessible_query

        self.prefix = prefix
        self.name = name
        self.url_vars = None

        self.__query = None
        self.__length = None
        self.__multiple = True

        self.__set = None
        self.__ids = []
        self.__uids = []

        self.__bind(storage)

        self.components = Storage()
        self.parent = parent

        if self.parent is None:
            self.__attach(select=components)
            self.build_query(id=id, uid=uid, filter=filter, url_vars=url_vars)

        self.__files = Storage()

        self.__handler = Storage(options=self.__get_options,
                                 fields=self.__get_fields,
                                 export_tree=self.__get_tree,
                                 import_tree=self.__put_tree)

        self.push_limit = 1 #: maximum number of records accepted in PUT/POST


    # -------------------------------------------------------------------------
    def __dbg(self, msg):

        """ Write debug messages to stderr.

            @param msg: the debug message

        """

        if self.__debug:
            print >> sys.stderr, "S3Resource: %s" % msg


    # Configuration ===========================================================

    def set_handler(self, method, handler):

        """ Set method handler for this resource

            @param method: the method name
            @param handler: the handler function
            @type handler: handler(S3Request, **attr)

        """

        self.__handler[method] = handler


    # -------------------------------------------------------------------------
    def get_handler(self, method):

        """ Get method handler for this resource

            @param method: the method name
            @returns: the handler function

        """

        return self.__handler.get(method, None)


    # Data binding ============================================================

    def __bind(self, storage):

        """ Bind this resource to model and data store

            @param storage: the URL of the data store, None for DAL
            @type storage: str

        """

        self.__storage = storage

        self.__db = self.__manager.db
        self.tablename = "%s_%s" % (self.prefix, self.name)

        self.table = self.__db.get(self.tablename, None)
        if not self.table:
            raise KeyError("Undefined table: %s" % self.tablename)

        if self.__storage is not None:
            raise NotImplementedError


    # -------------------------------------------------------------------------
    def __attach(self, select=None):

        """ Attach components to this resource

            @param select: name or list of names of components to attach.
                If select is None (default), then all declared components
                of this resource will be attached, to attach none of the
                components, pass an empty list instead.

        """

        if select and not isinstance(select, (list, tuple)):
            select = [select]

        self.components = Storage()

        if self.parent is None:
            components = self.__manager.model.get_components(self.prefix, self.name)

            for i in xrange(len(components)):
                c, pkey, fkey = components[i]

                if select and c.name not in select:
                    continue

                resource = S3Resource(self.__manager, c.prefix, c.name,
                                      parent=self,
                                      storage=self.__storage,
                                      debug=self.__debug)

                self.components[c.name] = Storage(component=c,
                                                   pkey=pkey,
                                                   fkey=fkey,
                                                   resource=resource)


    # -------------------------------------------------------------------------
    def build_query(self, id=None, uid=None, filter=None, url_vars=None):

        """ Query builder

            @param id: record ID or list of record IDs to include
            @param uid: record UID or list of record UIDs to include
            @param filter: filtering query (DAL only)
            @param url_vars: dict of URL query variables

        """

        # Initialize
        self.clear()
        self.clear_query()

        xml = self.__manager.xml

        if url_vars:
            url_query = self.__manager.url_query(self, url_vars)
            if url_query:
                self.url_vars = url_vars
        else:
            url_query = Storage()

        if self.__storage is None:

            deletion_status = self.__manager.DELETED

            self.__multiple = True # multiple results expected by default

            # Master Query
            if self.__accessible is not None:
                master_query = self.__accessible("read", self.table)
            else:
                master_query = (self.table.id > 0)

            self.__query = master_query

            # Component Query
            if self.parent:

                parent_query = self.parent.get_query()
                if parent_query:
                    self.__query = self.__query & parent_query

                component = self.parent.components.get(self.name, None)
                if component:
                    pkey = component.pkey
                    fkey = component.fkey
                    self.__multiple = component.get("multiple", True)
                    join = self.parent.table[pkey] == self.table[fkey]
                    if str(self.__query).find(str(join)) == -1:
                        self.__query = self.__query & (join)

                if deletion_status in self.table.fields:
                    remaining = (self.table[deletion_status] == False)
                    self.__query = self.__query & remaining

            # Primary Resource Query
            else:

                if id or uid:
                    if self.name not in url_query:
                        url_query[self.name] = Storage()

                # Collect IDs
                if id:
                    if not isinstance(id, (list, tuple)):
                        self.__multiple = False # single result expected
                        id = [id]
                    id_queries = url_query[self.name].get("id", Storage())

                    ne = id_queries.get("ne", [])
                    eq = id_queries.get("eq", [])
                    eq = eq + [v for v in id if v not in eq]

                    if ne and "ne" not in id_queries:
                        id_queries.ne = ne
                    if eq and "eq" not in id_queries:
                        id_queries.eq = eq

                    if "id" not in url_query[self.name]:
                        url_query[self.name]["id"] = id_queries

                # Collect UIDs
                if uid:
                    if not isinstance(uid, (list, tuple)):
                        self.__multiple = False # single result expected
                        uid = [uid]
                    uid_queries = url_query[self.name].get(self.__manager.UID, Storage())

                    ne = uid_queries.get("ne", [])
                    eq = uid_queries.get("eq", [])
                    eq = eq + [v for v in uid if v not in eq]

                    if ne and "ne" not in uid_queries:
                        uid_queries.ne = ne
                    if eq and "eq" not in uid_queries:
                        uid_queries.eq = eq

                    if self.__manager.UID not in url_query[self.name]:
                        url_query[self.name][self.manager.__UID] = uid_queries

                # URL Queries
                for rname in url_query:

                    if rname == self.name:
                        table = self.table
                    elif rname in self.components:
                        component = self.components[rname]
                        table = component.resource.table
                        pkey = component.pkey
                        fkey = component.fkey

                        join = (self.table[pkey]==table[fkey])
                        self.__query = self.__query & join

                        if deletion_status in table.fields:
                            remaining = (table[deletion_status] == False)
                            self.__query = self.__query & remaining

                    for field in url_query[rname]:
                        if field in table.fields:
                            for op in url_query[rname][field]:
                                values = url_query[rname][field][op]
                                if field == xml.UID and xml.domain_mapping:
                                    uids = [xml.import_uid(v) for v in values]
                                    values = uids
                                if op == "eq":
                                    if len(values) == 1:
                                        query = (table[field] == values[0])
                                    elif len(values):
                                        query = (table[field].belongs(values))
                                elif op == "ne":
                                    if len(values) == 1:
                                        query = (table[field] != values[0])
                                    elif len(values):
                                        query = (~(table[field].belongs(values)))
                                elif op == "lt":
                                    v = values[-1]
                                    query = (table[field] < v)
                                elif op == "le":
                                    v = values[-1]
                                    query = (table[field] <= v)
                                elif op == "gt":
                                    v = values[-1]
                                    query = (table[field] > v)
                                elif op == "ge":
                                    v = values[-1]
                                    query = (table[field] >= v)
                                elif op == "like":
                                    query = None
                                    for v in values:
                                        v = "%%%s%%" % v
                                        q = (table[field].lower().like(v.lower()))
                                        if query:
                                            query = query | q
                                        else:
                                            query = q
                                    query = (query)
                                elif op == "unlike":
                                    query = None
                                    for v in values:
                                        v = "%%%s%%" % v
                                        q = (~(table[field].lower().like(v.lower())))
                                        if query:
                                            query = query & q
                                        else:
                                            query = q
                                    query = (query)
                                else:
                                    continue
                                self.__query = self.__query & query

                # Filter
                if filter:
                    self.__query = self.__query & filter

                # Deletion status
                if deletion_status in self.table.fields:
                    remaining = (self.table[deletion_status] == False)
                    self.__query = self.__query & remaining

        else:
            raise NotImplementedError

        return self.__query


    # -------------------------------------------------------------------------
    def add_filter(self, filter=None):

        """ Add a filter to the current query """

        if filter is not None:

            if self.__query:
                query = self.__query
                self.clear()
                self.clear_query()
                self.__query = (query) & (filter)
            else:
                self.build_query(filter=filter)

        return self.__query


    # -------------------------------------------------------------------------
    def get_query(self):

        """ Get the current query for this resource """

        if not self.__query:
            self.build_query()

        return self.__query


    # Data access =============================================================

    def count(self):

        """ Get the total number of available records in this resource """

        if not self.__query:
            self.build_query()
            self.__length = None

        if self.__length is None:

            if self.__storage is None:
                self.__length = self.__db(self.__query).count()
            else:
                raise NotImplementedError

        return self.__length


    # -------------------------------------------------------------------------
    def __load_ids(self):

        """ Loads the IDs of all records matching the master query, or,
            if no query is given, all IDs in the primary table

        """

        if self.__query is None:
            self.build_query()

        if self.__storage is None:

            if self.__manager.UID in self.table.fields:
                fields = (self.table.id, self.table[self.__manager.UID])
            else:
                fields = (self.table.id,)

            set = self.__db(self.__query).select(*fields)
            self.__ids = [row.id for row in set]
            if self.__manager.UID in self.table.fields:
                self.__uids = [row.uid for row in set]

        else:
            raise NotImplementedError


    # -------------------------------------------------------------------------
    def get_id(self):

        """ Returns all IDs of the current set, or, if no set is loaded,
            all IDs of the resource

        """

        if not self.__ids:
            self.__load_ids()

        if not self.__ids:
            return None
        elif len(self.__ids) == 1:
            return self.__ids[0]
        else:
            return self.__ids


    # -------------------------------------------------------------------------
    def get_uid(self):

        """ Returns all UIDs of the current set, or, if no set is loaded,
            all UIDs of the resource

        """

        if self.__manager.UID not in self.table.fields:
            return None

        if not self.__uids:
            self.__load_ids()

        if not self.__uids:
            return None
        elif len(self.__uids) == 1:
            return self.__uids[0]
        else:
            return self.__uids


    # -------------------------------------------------------------------------
    def load(self, start=None, limit=None):

        """ Loads a set of records of the current resource, which can be
            either a slice (for pagination) or all records

            @param start: the index of the first record to load
            @param limit: the maximum number of records to load

        """

        if self.__set is not None:
            self.clear()

        if not self.__query:
            self.build_query()

        if self.__storage is None:

            if not self.__multiple:
                limitby = (0, 1)
            else:
                # Slicing
                if start is not None:
                    self.__slice = True
                    if not limit:
                        limit = self.__manager.ROWSPERPAGE
                    if limit <= 0:
                        limit = 1
                    if start < 0:
                        start = 0
                    limitby = (start, start + limit)
                else:
                    limitby = None

            self.__set = self.__db(self.__query).select(self.table.ALL, limitby=limitby)

            self.__ids = [row.id for row in self.__set]
            uid = self.__manager.UID
            if uid in self.table.fields:
                self.__uids = [row[uid] for row in self.__set]

        else:
            raise NotImplementedError


    # -------------------------------------------------------------------------
    def save(self):

        """ Write the current set to the data store (not implemented yet)

            @todo 2.1: implement this.
        """

        # Not implemented yet
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def clear(self):

        """ Removes the current set """

        self.__set = None
        self.__length = None
        self.__ids = []
        self.__uids = []
        self.__files = Storage()

        self.__slice = False

        if self.components:
            for c in self.components:
                self.components[c].resource.clear()


    # -------------------------------------------------------------------------
    def clear_query(self):

        """ Removes the current query (does not remove the set) """

        self.__query = None

        if self.components:
            for c in self.components:
                self.components[c].resource.clear_query()


    # -------------------------------------------------------------------------
    def records(self):

        """ Get the current set """

        if self.__set is None:
            return []
        else:
            return self.__set


    # -------------------------------------------------------------------------
    def __getitem__(self, key):

        """ Retrieves a record from the current set by its ID

            @param key: the record ID

        """

        if self.__set is None:
            self.load()

        for i in xrange(len(self.__set)):
            row = self.__set[i]
            if str(row.id) == str(key):
                return row

        raise IndexError


    # -------------------------------------------------------------------------
    def __iter__(self):

        """ Generator for the current set """

        if self.__set is None:
            self.load()

        for i in xrange(len(self.__set)):
            yield self.__set[i]

        return


    # -------------------------------------------------------------------------
    def __call__(self, key, component=None):

        """ Retrieves component records of a record in the current set

            @param key: the record ID
            @param component: the name of the component
                (None to get the primary record)

        """

        if not component:
            return self[key]
        else:
            if isinstance(key, Row):
                master = key
            else:
                master = self[key]
            if component in self.components:
                c = self.components[component]
                r = c.resource
                pkey, fkey = c.pkey, c.fkey
                l = [record for record in r if master[pkey] == record[fkey]]
                return l
            else:
                raise AttributeError


    # Representation ==========================================================

    def __repr__(self):

        """ String representation of this resource """

        if self.__set:
            ids = [r.id for r in self]
            return "<S3Resource %s %s>" % (self.tablename, ids)
        else:
            return "<S3Resource %s>" % self.tablename


    # -------------------------------------------------------------------------
    def __len__(self):

        """ The number of records in the current set """

        if self.__set is not None:
            return len(self.__set)
        else:
            return 0


    # -------------------------------------------------------------------------
    def __nonzero__(self):

        """ Boolean test of this resource """

        return self is not None


    # -------------------------------------------------------------------------
    def __contains__(self, item):

        """ Tests whether a record is currently loaded """

        id = item.get("id", None)
        uid = item.get(self.__manager.UID, None)

        if (id or uid) and not self.__ids:
            self.__load_ids()

        if id and id in self.__ids:
            return 1
        elif uid and uid in self.__uids:
            return 1
        else:
            return 0


    # -------------------------------------------------------------------------
    def url(self):

        """ URL of this resource (not implemented yet)

            @todo 2.1: implement this.

        """

        # Not implemented yet
        raise NotImplementedError


    # -------------------------------------------------------------------------
    def files(self):

        """ Get the list of attached files """

        return self.__files


    # REST Interface ==========================================================

    def execute_request(self, r, **attr):

        """ Execute a request on this resource

            @param r: the request to execute
            @type r: S3Request
            @param attr: attributes to pass to method handlers

        """

        self.__dbg("execute_request(%s)" % self)

        r._bind(self) # Bind request to resource
        r.next = None

        bypass = False
        output = None

        hooks = r.response.get(self.__manager.HOOKS, None)
        preprocess = None
        postprocess = None

        push_limit = self.push_limit

        # Enforce primary record ID
        if not r.id and not r.custom_action and r.representation == "html":
            if r.component or r.method in ("read", "update"):
                count = self.count()
                if self.url_vars is not None and count == 1:
                    self.load()
                    r.record = self.__set.first()
                else:
                    model = self.__manager.model
                    search_simple = model.get_method(self.prefix, self.name,
                                                    method="search_simple")
                    if search_simple:
                        self.__dbg("no record ID - redirecting to search_simple")
                        redirect(URL(r=r.request, f=self.name, args="search_simple",
                                    vars={"_next": r.same()}))
                    else:
                        r.session.error = self.ERROR.BAD_RECORD
                        redirect(URL(r=r.request, c=self.prefix, f=self.name))

        # Pre-process
        if hooks is not None:
            preprocess = hooks.get("prep", None)
        if preprocess:
            self.__dbg("pre-processing")
            pre = preprocess(r)
            if pre and isinstance(pre, dict):
                bypass = pre.get("bypass", False) is True
                output = pre.get("output", None)
                if not bypass:
                    success = pre.get("success", True)
                    if not success:
                        self.__dbg("pre-process returned an error - aborting")
                        if r.representation == "html" and output:
                            if isinstance(output, dict):
                                output.update(jr=r)
                            return output
                        else:
                            status = pre.get("status", 400)
                            message = pre.get("message", self.ERROR.BAD_REQUEST)
                            raise HTTP(status, message)
            elif not pre:
                self.__dbg("pre-process returned an error - aborting")
                raise HTTP(400, body=self.ERROR.BAD_REQUEST)

        # Default view
        if r.representation <> "html":
            r.response.view = "xml.html"

        # Method handling
        handler = None
        if bypass:
            self.__dbg("bypass directive - skipping method handler")
        else:
            if r.method and r.custom_action:
                self.__dbg("custom method %s" % r.method)
                handler = r.custom_action
            elif r.http == "GET":
                self.push_limit = None
                handler = self.__get(r)
            elif r.http == "PUT":
                handler = self.__put(r)
            elif r.http == "POST":
                handler = self.__post(r)
            elif r.http == "DELETE":
                handler = self.__delete(r)
            else:
                raise HTTP(501, body=self.ERROR.BAD_METHOD)
            if handler is not None:
                self.__dbg("method handler found - executing request")
                output = handler(r, **attr)
                self.push_limit = push_limit
            else:
                self.__dbg("no method handler - finalizing request")

        # Post-process
        if hooks is not None:
            postprocess = hooks.get("postp", None)
        if postprocess is not None:
            self.__dbg("post-processing")
            output = postprocess(r, output)

        if output is not None and isinstance(output, dict):
            output.update(jr=r)

        # Redirection (makes no sense in GET)
        if r.next is not None and r.http != "GET" or r.method == "delete":
            if isinstance(output, dict):
                form = output.get("form", None)
                if form and form.errors:
                    return output
            self.__dbg("redirecting to %s" % str(r.next))
            r.session.flash = r.response.flash
            r.session.confirmation = r.response.confirmation
            r.session.error = r.response.error
            r.session.warning = r.response.warning
            redirect(r.next)

        return output


    # -------------------------------------------------------------------------
    def __get(self, r):

        """ Get GET method handler

            @param r: the S3Request

        """

        self.__dbg("GET method")

        method = r.method
        permit = self.__permit

        model = self.__manager.model

        tablename = r.component and r.component.tablename or r.tablename

        xml_export_formats = self.__manager.xml_export_formats
        json_export_formats = self.__manager.json_export_formats
        xml_import_formats = self.__manager.xml_import_formats
        json_import_formats = self.__manager.json_import_formats

        if method is None or method in ("read", "display"):
            authorised = permit("read", tablename)
            if r.representation in xml_export_formats or \
               r.representation in json_export_formats:
                method = "export_tree"
            elif r.component:
                if r.multiple and not r.component_id:
                    method = "list"
                else:
                    method = "read"
            else:
                if r.id or method in ("read", "display"):
                    # Enforce single record
                    if not self.__set:
                        self.load(start=0, limit=1)
                    if self.__set:
                        r.record = self.__set[0]
                        r.id = self.get_id()
                        r.uid = self.get_uid()
                    else:
                        raise HTTP(404, self.ERROR.BAD_RECORD)
                    method = "read"
                else:
                    method = "list"

        elif method in ("create", "update"):
            authorised = permit(method, tablename)
            # TODO: Add user confirmation here:
            if r.representation in xml_import_formats or \
               r.representation in json_import_formats:
                method = "import_tree"

        elif method == "copy":
            authorised = permit("create", tablename)

        elif method == "delete":
            return self.__delete(r)

        elif method == "options":
            authorised = permit("read", tablename)

        elif method == "fields":
            authorised = permit("read", tablename)

        elif method == "search" and not r.component:
            authorised = permit("read", tablename)

        elif method == "clear" and not r.component:
            self.__manager.clear_session(r.session, self.prefix, self.name)
            if "_next" in r.request.vars:
                request_vars = dict(_next=r.request.vars._next)
            else:
                request_vars = {}
            search_simple = model.get_method(self.prefix, self.name,
                                             method="search_simple")
            if r.representation == "html" and search_simple:
                r.next = URL(r=r.request,
                             f=self.name,
                             args="search_simple",
                             vars=request_vars)
            else:
                r.next = URL(r=r.request, f=self.name)
            return None

        else:
            raise HTTP(501, body=self.ERROR.BAD_METHOD)

        if not authorised:
            r.unauthorised()
        else:
            return self.get_handler(method)


    # -------------------------------------------------------------------------
    def __get_options(self, r, **attr):

        """ Method handler to get field options in the current resource

            @param r: the request
            @param attr: request attributes

        """

        if "field" in r.request.get_vars:
            items = r.request.get_vars["field"]
            if not isinstance(items, (list, tuple)):
                items = [items]
            fields = []
            for item in items:
                f = item.split(",")
                if f:
                    fields.extend(f)
        else:
            fields = None

        if r.representation == "xml":
            return self.options_xml(component=r.component_name, fields=fields)
        elif r.representation == "json":
            return self.options_json(component=r.component_name, fields=fields)
        else:
            raise HTTP(501, body=self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __get_fields(self, r, **attr):

        """ Method handler to get all fields in the primary table

            @param r: the request
            @param attr: the request attributes
        """

        if r.representation == "xml":
            return self.fields_xml(component=r.component_name)
        elif r.representation == "json":
            return self.fields_json(component=r.component_name)
        else:
            raise HTTP(501, body=self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __get_tree(self, r, **attr):

        """ Method handler to export this resource in XML or JSON formats

            @param r: the request
            @param attr: request attributes

        """

        xml_formats = self.__manager.xml_export_formats
        json_formats = self.__manager.json_export_formats

        template = None
        show_urls = True
        dereference = True

        if r.representation in xml_formats:
            r.response.headers["Content-Type"] = \
                xml_formats.get(r.representation, "application/xml")
        else:
            r.response.headers["Content-Type"] = \
                json_formats.get(r.representation, "text/x-json")
            if r.representation == "json":
                show_urls = False
                dereference = False

        if r.representation not in ("xml", "json"):
            template_name = "%s.%s" % (r.representation,
                                       self.__manager.XSLT_FILE_EXTENSION)

            template = os.path.join(r.request.folder,
                                    self.__manager.XSLT_EXPORT_TEMPLATES,
                                    template_name)

            if not os.path.exists(template):
                raise HTTP(501, body="%s: %s" % (self.ERROR.BAD_TEMPLATE, template))

        start = r.request.vars.get("start", None)
        if start is not None:
            try:
                start = int(start)
            except ValueError:
                start = None

        limit = r.request.vars.get("limit", None)
        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                limit = None

        marker = r.request.vars.get("marker", None)

        msince = r.request.vars.get("msince", None)
        if msince is not None:
            tfmt = "%Y-%m-%dT%H:%M:%SZ"
            try:
                (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(msince, tfmt)
                msince = datetime.datetime(y,m,d,hh,mm,ss)
            except ValueError:
                msince = None

        tree = self.__export_tree(start=start,
                                  limit=limit,
                                  marker=marker,
                                  msince=msince,
                                  show_urls=True,
                                  dereference=True)

        if template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args = dict(domain=self.__manager.domain,
                        base_url=self.__manager.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            if r.component:
                args.update(id=r.id, component=r.component.tablename)

            mode = r.request.vars.get("xsltmode", None)
            if mode is not None:
                args.update(mode=mode)

            tree = self.__manager.xml.transform(tree, template, **args)
            if not tree:
                error = self.__manager.xml.json_message(False, 400,
                            str("XSLT Transformation Error: %s ") % \
                            self.__manager.xml.error)
                raise HTTP(400, body=error)

        if r.representation in xml_formats:
            return self.__manager.xml.tostring(tree, pretty_print=True)
        else:
            return self.__manager.xml.tree2json(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def __put(self, r):

        """ Get PUT method handler

            @param r: the S3Request

        """

        self.__dbg("PUT method")
        permit = self.__permit

        xml_formats = self.__manager.xml_import_formats
        json_formats = self.__manager.json_import_formats

        if r.representation in xml_formats or \
           r.representation in json_formats:
            authorised = permit("create", self.tablename) and \
                         permit("update", self.tablename)
            if not authorised:
                r.unauthorised()
            else:
                return self.get_handler("import_tree")
        else:
            raise HTTP(501, body=self.ERROR.BAD_FORMAT)


    # -------------------------------------------------------------------------
    def __read_body(self, r):

        """ Read data from request body """

        self.__files = Storage()
        content_type = r.request.env.get("content_type", None)

        if content_type and content_type.startswith("multipart/"):

            # Get all attached files from POST
            for p in r.request.post_vars.values():
                if isinstance(p, cgi.FieldStorage) and p.filename:
                    self.__files[p.filename] = p.file

            # Find the source
            source_name = "%s.%s" % (r.name, r.representation)
            post_vars = r.request.post_vars
            source = post_vars.get(source_name, None)
            if isinstance(source, cgi.FieldStorage):
                if source.filename:
                    source = source.file
                else:
                    source = source.value
            if isinstance(source, basestring):
                source = StringIO.StringIO(source)
        else:

            # Body is source
            source = r.request.body
            source.seek(0)

        return source


    # -------------------------------------------------------------------------
    def __put_tree(self, r, **attr):

        """ Import XML/JSON data """

        xml = self.__manager.xml
        xml_formats = self.__manager.xml_import_formats

        vars = r.request.vars
        if r.representation in xml_formats:
            if "filename" in vars:
                source = vars["filename"]
            elif "fetchurl" in vars:
                source = vars["fetchurl"]
            else:
                source = self.__read_body(r)
            tree = xml.parse(source)
        else:
            if "filename" in vars:
                source = open(vars["filename"])
            elif "fetchurl" in vars:
                import urllib
                source = urllib.urlopen(vars["fetchurl"])
            else:
                source = self.__read_body(r)
            tree = xml.json2tree(source)

        if not tree:
            item = xml.json_message(False, 400, xml.error)
            raise HTTP(400, body=item)

        # XSLT Transformation
        if not r.representation in ("xml", "json"):
            template_name = "%s.%s" % (r.representation,
                                       self.__manager.XSLT_FILE_EXTENSION)

            template = os.path.join(r.request.folder,
                                    self.__manager.XSLT_IMPORT_TEMPLATES,
                                    template_name)

            if not os.path.exists(template):
                raise HTTP(501, body="%s: %s" % (self.ERROR.BAD_TEMPLATE, template))

            tree = xml.transform(tree, template,
                                 domain=self.__manager.domain,
                                 base_url=self.__manager.base_url)

            if not tree:
                error = xml.json_message(False, 400,
                            str("XSLT Transformation Error: %s ") % \
                            self.__manager.xml.error)
                raise HTTP(400, body=error)

        if r.component:
            skip_resource = True
        else:
            skip_resource = False

        if r.method == "create":
            id = None
        else:
            id = r.id

        if "ignore_errors" in r.request.vars:
            ignore_errors = True
        else:
            ignore_errors = False

        success = self.__import_tree(id, tree,
                                     push_limit=self.push_limit,
                                     ignore_errors=ignore_errors)

        if success:
            item = xml.json_message()
        else:
            tree = xml.tree2json(tree)
            item = xml.json_message(False, 400, self.__manager.error, tree=tree)
            raise HTTP(400, body=item)

        #return dict(item=item)
        return item


    # -------------------------------------------------------------------------
    def __post(self, r):

        """ Get POST method handler

            @param r: the S3Request

        """

        self.__dbg("POST method")

        if r.representation in self.__manager.xml_import_formats or \
           r.representation in self.__manager.json_import_formats:
            return self.__put(r)
        else:
            return self.__get(r)


    # -------------------------------------------------------------------------
    def __delete(self, r):

        """ Get DELETE method handler

            @param r: the S3Request

        """

        self.__dbg("DELETE method")

        permit = self.__permit

        tablename = r.component and r.component.tablename or r.tablename

        if r.id or \
           r.component and r.component_id:
            authorised = permit("delete", tablename, r.id)
            if not authorised:
                r.unauthorised()

            if r.next is None:
                r.next = r.there()
            return self.get_handler("delete")
        else:
            raise HTTP(501, body=self.ERROR.BAD_METHOD)


    # XML/JSON functions ======================================================

    def __export_tree(self,
                      start=None,
                      limit=None,
                      marker=None,
                      msince=None,
                      show_urls=True,
                      dereference=True):

        """ Export this resource as element tree """

        return self.__manager.export_tree(self,
                                          audit=self.__manager.audit,
                                          start=start,
                                          limit=limit,
                                          marker=marker,
                                          msince=msince,
                                          show_urls=show_urls,
                                          dereference=dereference)


    # -------------------------------------------------------------------------
    def export_xml(self, template=None, pretty_print=False, **args):

        """ Export this resource as XML """

        tree = self.__export_tree()

        if tree and template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args.update(domain=self.__manager.domain,
                        base_url=self.__manager.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = self.__manager.xml.transform(tree, template, **args)

        if tree:
            return self.__manager.xml.tostring(tree, pretty_print=pretty_print)
        else:
            return None


    # -------------------------------------------------------------------------
    def export_json(self, template=None, pretty_print=False, **args):

        """ Export this resource as JSON """

        tree = self.__export_tree()

        if tree and template is not None:
            tfmt = "%Y-%m-%d %H:%M:%S"
            args.update(domain=self.__manager.domain,
                        base_url=self.__manager.base_url,
                        prefix=self.prefix,
                        name=self.name,
                        utcnow=datetime.datetime.utcnow().strftime(tfmt))

            tree = self.__manager.xml.transform(tree, template, **args)

        if tree:
            return self.__manager.xml.tree2json(tree, pretty_print=pretty_print)
        else:
            return None


    # -------------------------------------------------------------------------
    def __import_tree(self, id, tree,
                      files=None,
                      push_limit=None,
                      ignore_errors=False):

        """ Import data from an element tree to this resource

            @param files: file attachments as {filename:file}

            @raise IOError: at insufficient permissions
        """

        if files is not None and isinstance(files, dict):
            self.__files = Storage(files)

        success = self.__manager.import_tree(self, id, tree,
                                             push_limit=push_limit,
                                             ignore_errors=ignore_errors)

        self.__files = Storage()
        return success


    # -------------------------------------------------------------------------
    def import_xml(self, source,
                   files=None,
                   id=None,
                   template=None,
                   ignore_errors=False, **args):

        """ Import data from an XML source to this resource

            @param source: the XML source (or ElementTree)
            @param files: file attachments as {filename:file}
            @param id: the ID or list of IDs of records to update (None for all)
            @param template: the XSLT template
            @param ignore_errors: do not stop on errors (skip invalid elements)
            @param args: arguments to pass to the XSLT template

            @raise SyntaxError: in case of a parser or transformation error
            @raise IOError: at insufficient permissions

        """

        xml = self.__manager.xml
        permit = self.__permit

        authorised = permit("create", self.table) and \
                     permit("update", self.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        if isinstance(source, etree._ElementTree):
            tree = source
        else:
            tree = xml.parse(source)

        if tree:
            if template is not None:
                tree = xml.transform(tree, template, **args)
                if not tree:
                    raise SyntaxError(xml.error)
            return self.__import_tree(id, tree,
                                      files=files,
                                      push_limit=None,
                                      ignore_errors=ignore_errors)
        else:
            raise SyntaxError("Invalid XML source")


    # -------------------------------------------------------------------------
    def import_json(self, source,
                    files=None,
                    id=None,
                    template=None,
                    ignore_errors=False, **args):

        """ Import data from a JSON source to this resource

            @param source: the JSON source (or ElementTree)
            @param files: file attachments as {filename:file}
            @param id: the ID or list of IDs of records to update (None for all)
            @param template: the XSLT template
            @param ignore_errors: do not stop on errors (skip invalid elements)
            @param args: arguments to pass to the XSLT template

            @raise SyntaxError: in case of a parser or transformation error
            @raise IOError: at insufficient permissions

        """

        xml = self.__manager.xml
        permit = self.__permit

        authorised = permit("create", self.table) and \
                     permit("update", self.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        if isinstance(source, etree._ElementTree):
            tree = source
        elif isinstance(source, basestring):
            from StringIO import StringIO
            source = StringIO(source)
            tree = xml.json2tree(source)
        else:
            tree = xml.json2tree(source)

        if tree:
            if template is not None:
                tree = xml.transform(tree, template, **args)
                if not tree:
                    raise SyntaxError(xml.error)
            return self.__import_tree(id, tree,
                                      files=files,
                                      push_limit=None,
                                      ignore_errors=ignore_errors)
        else:
            raise SyntaxError("Invalid JSON source.")


    # -------------------------------------------------------------------------
    def options_tree(self, component=None, fields=None):

        """ Export field options of this resource as element tree """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.resource.options_tree(fields=fields)
                return tree
            else:
                raise AttributeError
        else:
            tree = self.__manager.xml.get_options(self.prefix,
                                                  self.name,
                                                  fields=fields)
            return tree


    # -------------------------------------------------------------------------
    def options_xml(self, component=None, fields=None):

        """ Export field options of this resource as XML """

        tree = self.options_tree(component=component, fields=fields)
        return self.__manager.xml.tostring(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def options_json(self, component=None, fields=None):

        """ Export field options of this resource as JSON """

        tree = etree.ElementTree(self.options_tree(component=component,
                                                   fields=fields))
        return self.__manager.xml.tree2json(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def fields_tree(self, component=None):

        """ Export a list of fields in the primary table as element tree """

        if component is not None:
            c = self.components.get(component, None)
            if c:
                tree = c.resource.fields_tree()
                return tree
            else:
                raise AttributeError
        else:
            tree = self.__manager.xml.get_fields(self.prefix, self.name)
            return tree


    # -------------------------------------------------------------------------
    def fields_xml(self, component=None):

        """ Export a list of fields in the primary table as XML """

        tree = self.fields_tree(component=component)
        return self.__manager.xml.tostring(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def fields_json(self, component=None):

        """ Export a list of fields in the primary table as JSON """

        tree = etree.ElementTree(self.fields_tree(component=component))
        return self.__manager.xml.tree2json(tree, pretty_print=True)


    # -------------------------------------------------------------------------
    def __push_tree(self, url,
                    converter=None,
                    template=None,
                    xsltmode=None,
                    content_type=None,
                    username=None,
                    password=None,
                    proxy=None,
                    start=None,
                    limit=None,
                    marker=None,
                    msince=None,
                    show_urls=True,
                    dereference=True):

        """ Push (=POST) the current resource to a target URL """

        if not converter:
            raise SyntaxError

        xml = self.__manager.xml
        response = None

        tree = self.__export_tree(start=start,
                                  limit=limit,
                                  marker=marker,
                                  msince=msince,
                                  show_urls=show_urls,
                                  dereference=dereference)

        if tree:
            if template:
                tfmt = "%Y-%m-%d %H:%M:%S"
                args = dict(domain=self.__manager.domain,
                            base_url=self.__manager.base_url,
                            prefix=self.prefix,
                            name=self.name,
                            utcnow=datetime.datetime.utcnow().strftime(tfmt))

                if xsltmode:
                    args.update(mode=xsltmode)

                tree = xml.transform(tree, template, **args)
            data = converter(tree)

            url_split = url.split("://", 1)
            if len(url_split) == 2:
                protocol, path = url_split
                if username and password:
                    url = "%s://%s:%s@%s" % (protocol, username, password, path)
            else:
                protocol, path = http, None
            import urllib2
            req = urllib2.Request(url=url, data=data)
            if content_type:
                req.add_header('Content-Type', content_type)
            handlers = []
            if proxy:
                proxy_handler = urllib2.ProxyHandler({protocol:proxy})
                handlers.append(proxy_handler)
            if username and password:
                passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passwd_manager.add_password(realm=None,
                                            uri=url,
                                            user=username,
                                            passwd=password)
                auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
                handlers.append(auth_handler)
            if handlers:
                opener = urllib2.build_opener(*handlers)
                urllib2.install_opener(opener)
            try:
                f = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                response = e.read()
            else:
                response = f.read()

        return response


    # -------------------------------------------------------------------------
    def push_xml(self, url,
                 template=None,
                 xsltmode=None,
                 username=None,
                 password=None,
                 proxy=None,
                 start=None,
                 limit=None,
                 marker=None,
                 msince=None,
                 show_urls=True,
                 dereference=True):

        """ Push (=POST) this resource as XML to a target URL

            @param url: the URL to push to
            @param template: path to the XSLT stylesheet to use
            @param xsltmode: XSLT stylesheet "mode" parameter
            @param username: username for HTTP basic auth (optional)
            @param password: password for HTTP basic auth (optional)
            @param proxy: proxy server to use (optional)
            @param start: start record (for pagination)
            @param limit: maximum number of records to send (for pagination)
            @param marker: path to the default marker for GIS features
            @param msince: export only records modified after that datetime (ISO-format)
            @param show_urls: show URLs in resource elements
            @param dereference: export referenced objects in the tree

            @returns: the response from the peer as string

        """

        xml = self.__manager.xml

        converter = lambda tree: xml.tostring(tree)
        content_type = "application/xml"

        return self.__push_tree(url,
                                converter=converter,
                                template=template,
                                xsltmode=xsltmode,
                                content_type=content_type,
                                username=username,
                                password=password,
                                proxy=proxy,
                                start=start,
                                limit=limit,
                                marker=marker,
                                msince=msince,
                                show_urls=show_urls,
                                dereference=dereference)

    # -------------------------------------------------------------------------
    def push_json(self, url,
                  template=None,
                  xsltmode=None,
                  username=None,
                  password=None,
                  proxy=None,
                  start=None,
                  limit=None,
                  marker=None,
                  msince=None,
                  show_urls=True,
                  dereference=True):

        """ Push (=POST) this resource as JSON to a target URL

            @param url: the URL to push to
            @param template: path to the XSLT stylesheet to use
            @param xsltmode: XSLT stylesheet "mode" parameter
            @param username: username for HTTP basic auth (optional)
            @param password: password for HTTP basic auth (optional)
            @param proxy: proxy server to use (optional)
            @param start: start record (for pagination)
            @param limit: maximum number of records to send (for pagination)
            @param marker: path to the default marker for GIS features
            @param msince: export only records modified after that datetime (ISO-format)
            @param show_urls: show URLs in resource elements
            @param dereference: export referenced objects in the tree

            @returns: the response from the peer as string

        """

        xml = self.__manager.xml

        converter = lambda tree: xml.tree2json(tree)
        content_type = "text/x-json"

        return self.__push_tree(url,
                                converter=converter,
                                template=template,
                                xsltmode=xsltmode,
                                content_type=content_type,
                                username=username,
                                password=password,
                                proxy=proxy,
                                start=start,
                                limit=limit,
                                marker=marker,
                                msince=msince,
                                show_urls=show_urls,
                                dereference=dereference)


    # -------------------------------------------------------------------------
    def __fetch_tree(self, url,
                     username=None,
                     password=None,
                     proxy=None,
                     json=False,
                     template=None,
                     ignore_errors=False, **args):

        """ Fetch data to the current resource from a remote URL """

        xml = self.__manager.xml

        response = None
        url_split = url.split("://", 1)
        if len(url_split) == 2:
            protocol, path = url_split
            if username and password:
                url = "%s://%s:%s@%s" % (protocol, username, password, path)
        else:
            protocol, path = http, None
        import urllib2
        req = urllib2.Request(url=url)
        handlers = []
        if proxy:
            proxy_handler = urllib2.ProxyHandler({protocol:proxy})
            handlers.append(proxy_handler)
        if username and password:
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm=None,
                                        uri=url,
                                        user=username,
                                        passwd=password)
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)
        if handlers:
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)
        try:
            f = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            response = e.read()
        else:
            response = f.read()

        if json:
            return self.import_json(response,
                                    template=template,
                                    ignore_errors=ignore_errors,
                                    args=args)
        else:
            return self.import_xml(response,
                                   template=template,
                                   ignore_errors=ignore_errors,
                                   args=args)


    def fetch_xml(self, url,
                  username=None,
                  password=None,
                  proxy=None,
                  template=None,
                  ignore_errors=False, **args):

        return self.__fetch_tree(url,
                                 username=username,
                                 password=password,
                                 proxy=proxy,
                                 json=False,
                                 template=template,
                                 ignore_errors=ignore_errors, **args)


    def fetch_json(self, url,
                   username=None,
                   password=None,
                   proxy=None,
                   template=None,
                   ignore_errors=False, **args):

        return self.__fetch_tree(url,
                                 username=username,
                                 password=password,
                                 proxy=proxy,
                                 json=True,
                                 template=template,
                                 ignore_errors=ignore_errors, **args)


# *****************************************************************************
class S3Request(object):

    """ Class to handle requests """

    DEFAULT_REPRESENTATION = "html"
    UNAUTHORISED = "Not Authorised"

    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name,
                 request=None,
                 session=None,
                 response=None,
                 debug=None):

        """ Constructor

            @param manager: the resource controller
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param request: the web2py request object
            @param session: the session store
            @param response: the web2py response object
            @param debug: whether to print debug messages or not

        """

        assert manager is not None, "Undefined Resource Manager"
        self.__manager = manager

        if debug is None:
            self.debug = self.__manager.debug
        else:
            self.debug = debug

        self.error = None

        self.prefix = prefix or request.controller
        self.name = name or request.function

        self.request = request
        self.response = response
        self.session = session or Storage()

        # Prepare parsing
        self.representation = request.extension
        self.http = request.env.request_method
        self.extension = False

        self.args = []
        self.id = None
        self.component_name = None
        self.component_id = None
        self.record = None
        self.method = None

        # Parse the request
        self.__parse()

        # Append component ID to the URL query
        if self.component_name and self.component_id:
            varname = "%s.id" % self.component_name
            if varname in self.request.vars:
                var = self.request.vars[varname]
                if not isinstance(var, (list, tuple)):
                    var = [var]
                var.append(self.component_id)
                self.request.vars[varname] = var
            else:
                self.request.vars[varname] = self.component_id

        # Create the resource
        self.resource = manager.resource(self.prefix, self.name,
                                         id=self.id,
                                         filter=self.response[manager.HOOKS].filter,
                                         url_vars=self.request.vars,
                                         components=self.component_name)

        self.tablename = self.resource.tablename
        self.table = self.resource.table

        # Check for component
        self.component = None
        self.pkey = None
        self.fkey = None
        self.multiple = True
        if self.component_name:
            c = self.resource.components.get(self.component_name, None)
            if c:
                self.component = c.component
                self.pkey, self.fkey = c.pkey, c.fkey
                self.multiple = self.component.attr.get("multiple", True)
            else:
                manager.error = "%s not a component of %s" % \
                                (self.component_name, self.resource.tablename)
                raise SyntaxError(manager.error)

        # Find primary record
        uid = self.request.vars.get("%s.uid" % self.name, None)
        if self.component_name:
            cuid = self.request.vars.get("%s.uid" % self.component_name, None)
        else:
            cuid = None

        # Try to load primary record, if expected
        if self.id or self.component_id or \
           uid and not isinstance(uid, (list, tuple)) or \
           cuid and not isinstance(cuid, (list, tuple)):
            # Single record expected
            self.resource.load()
            if len(self.resource) == 1:
                self.record = self.resource.records().first()
                self.id = self.record.id
                self.__manager.store_session(self.session,
                                             self.resource.prefix,
                                             self.resource.name,
                                             self.id)
            else:
                manager.error = "No matching record found"
                raise KeyError(manager.error)

        # Check for custom action
        model = manager.model
        self.custom_action = model.get_method(self.prefix, self.name,
                                              component_name=self.component_name,
                                              method=self.method)


    # -------------------------------------------------------------------------
    def unauthorised(self):

        """ Action upon unauthorised request """

        if self.representation == "html":
            self.session.error = self.UNAUTHORISED
            login = URL(r=self.request,
                        c="default",
                        f="user",
                        args="login",
                        vars={"_next": self.here()})
            redirect(login)
        else:
            raise HTTP(401, body = self.UNAUTHORISED)


    # -------------------------------------------------------------------------
    def _bind(self, resource):

        self.resource = resource


    # -------------------------------------------------------------------------
    def __dbg(self, msg):

        if self.debug:
            print >> sys.stderr, "S3Request: %s" % msg


    # Request Parser ==========================================================

    def __parse(self):

        """ Parses a web2py request for the REST interface """

        self.args = []

        model = self.__manager.model
        components = [c[0].name for c in model.get_components(self.prefix, self.name)]

        if len(self.request.args) > 0:
            for i in xrange(len(self.request.args)):
                arg = self.request.args[i]
                if "." in arg:
                    arg, ext = arg.rsplit(".", 1)
                    if ext and len(ext) > 0:
                        self.representation = str.lower(ext)
                        self.extension = True
                if arg:
                    self.args.append(str.lower(arg))
            if self.args[0].isdigit():
                self.id = self.args[0]
                if len(self.args) > 1:
                    if self.args[1] in components:
                        self.component_name = self.args[1]
                        if len(self.args) > 2:
                            if self.args[2].isdigit():
                                self.component_id = self.args[2]
                                if len(self.args) > 3:
                                    self.method = self.args[3]
                            else:
                                self.method = self.args[2]
                                if len(self.args) > 3 and \
                                   self.args[3].isdigit():
                                    self.component_id = self.args[3]
                    else:
                        self.method = self.args[1]
            else:
                if self.args[0] in components:
                    self.component_name = self.args[0]
                    if len(self.args) > 1:
                        if self.args[1].isdigit():
                            self.component_id = self.args[1]
                            if len(self.args) > 2:
                                self.method = self.args[2]
                        else:
                            self.method = self.args[1]
                            if len(self.args) > 2 and self.args[2].isdigit():
                                self.component_id = self.args[2]
                else:
                    self.method = self.args[0]
                    if len(self.args) > 1 and self.args[1].isdigit():
                        self.id = self.args[1]

        if "format" in self.request.get_vars:
            self.representation = str.lower(self.request.get_vars.format)

        if not self.representation:
            self.representation = self.DEFAULT_REPRESENTATION


    # URL helpers =============================================================

    def __next(self, id=None, method=None, representation=None, vars=None):

        """ Returns a URL of the current request

            @param id: the record ID for the URL
            @param method: an explicit method for the URL
            @param representation: the representation for the URL

        """

        if vars is None:
            vars = self.request.get_vars
        if "format" in vars:
            del vars["format"]

        args = []
        read = False

        component_id = self.component_id
        if id is None:
            id = self.id
        else:
            read = True

        if not representation:
            representation = self.representation
        if method is None:
            method = self.method
        elif method=="":
            method = None
            if not read:
                if self.component:
                    component_id = None
                else:
                    id = None
        else:
            if id is None:
                id = self.id
            else:
                id = str(id)
                if len(id) == 0:
                    id = "[id]"
                #if self.component:
                    #component_id = None
                    #method = None

        if self.component:
            if id:
                args.append(id)
            args.append(self.component_name)
            if component_id:
                args.append(component_id)
            if method:
                args.append(method)
        else:
            if id:
                args.append(id)
            if method:
                args.append(method)

        f = self.request.function
        if not representation==self.DEFAULT_REPRESENTATION:
            if len(args) > 0:
                args[-1] = "%s.%s" % (args[-1], representation)
            else:
                #vars.update(format=representation)
                f = "%s.%s" % (f, representation)

        return URL(r=self.request,
                   c=self.request.controller,
                   f=f,
                   args=args, vars=vars)


    # -------------------------------------------------------------------------
    def here(self, representation=None, vars=None):

        """ URL of the current request

            @param representation: the representation for the URL

        """

        return self.__next(id=self.id, representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def other(self, method=None, record_id=None, representation=None, vars=None):

        """ URL of a request with different method and/or record_id
            of the same resource

            @param method: an explicit method for the URL
            @param record_id: the record ID for the URL
            @param representation: the representation for the URL

        """

        return self.__next(method=method, id=record_id,
                           representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def there(self, representation=None, vars=None):

        """ URL of a HTTP/list request on the same resource

            @param representation: the representation for the URL

        """

        return self.__next(method="", representation=representation, vars=vars)


    # -------------------------------------------------------------------------
    def same(self, representation=None, vars=None):

        """ URL of the same request with neutralized primary record ID

            @param representation: the representation for the URL

        """

        return self.__next(id="[id]", representation=representation, vars=vars)


    # Method handler helpers ==================================================

    def target(self):

        """ Get the target table of the current request """

        if self.component is not None:
            return (self.component.prefix,
                    self.component.name,
                    self.component.table,
                    self.component.tablename)
        else:
            return (self.prefix,
                    self.name,
                    self.table,
                    self.tablename)


# *****************************************************************************
class S3MethodHandler(object):

    """ Abstract class for REST method handlers """

    # -------------------------------------------------------------------------
    def __init__(self):

        """ Constructor """

        pass


    # -------------------------------------------------------------------------
    def __call__(self, r, **attr):

        """ Caller, invoked by the REST interface """

        return self.response(r, **attr)


    # -------------------------------------------------------------------------
    def response(self, r, **attr):

        """ Responder, to be implemented by subclasses """

        output = dict()
        return output


# *****************************************************************************
class S3ResourceComponent(object):

    """ Class to represent component relations between resources """

    # -------------------------------------------------------------------------
    def __init__(self, db, prefix, name, **attr):

        """ Constructor

            @param db: the database (DAL)
            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param attr: attributes

        """

        self.db = db
        self.prefix = prefix
        self.name = name

        self.tablename = "%s_%s" % (prefix, name)
        self.table = self.db.get(self.tablename, None)
        if not self.table:
            raise SyntaxError("Table must exist in the database.")

        self.attr = Storage(attr)
        if not "multiple" in self.attr:
            self.attr.multiple = True
        if not "deletable" in self.attr:
            self.attr.deletable = True
        if not "editable" in self.attr:
            self.attr.editable = True


    # Configuration ===========================================================

    def set_attr(self, name, value):

        """ Sets an attribute for a component

            @param name: attribute name
            @param value: attribute value

        """

        self.attr[name] = value


    # -------------------------------------------------------------------------
    def get_attr(self, name):

        """ Reads an attribute of the component

            @param name: attribute name

        """

        if name in self.attr:
            return self.attr[name]
        else:
            return None


# *****************************************************************************
class S3ResourceModel(object):


    """ Class to handle the compound resources model """


    # -------------------------------------------------------------------------
    def __init__(self, db):

        """ Constructor

            @param db: the database (DAL)

        """

        self.db = db
        self.components = {}
        self.config = Storage()
        self.methods = {}
        self.cmethods = {}


    # Configuration ===========================================================

    def configure(self, table, **attr):

        """ Updates the configuration of a resource

            @param table: the resource DB table
            @param attr: dict of attributes to update

        """

        cfg = self.config.get(table._tablename, Storage())
        cfg.update(attr)
        self.config[table._tablename] = cfg


    # -------------------------------------------------------------------------
    def get_config(self, table, key):

        """ Reads a configuration attribute of a resource

            @param table: the resource DB table
            @param key: the key (name) of the attribute

        """

        if table._tablename in self.config:
            return self.config[table._tablename].get(key, None)
        else:
            return None


    # -------------------------------------------------------------------------
    def clear_config(self, table, *keys):

        """ Removes configuration attributes of a resource

            @param table: the resource DB table
            @param keys: keys of attributes to remove (maybe multiple)

        """

        if not keys:
            if table._tablename in self.config:
                del self.config[table._tablename]
        else:
            if table._tablename in self.config:
                for k in keys:
                    if k in self.config[table._tablename]:
                        del self.config[table._tablename][k]


    # -------------------------------------------------------------------------
    def add_component(self, prefix, name, **attr):

        """ Adds a component to the model

            @param prefix: prefix of the component name (=module name)
            @param name: name of the component (=without prefix)

        """

        joinby = attr.get("joinby", None)
        if joinby:
            component = S3ResourceComponent(self.db, prefix, name, **attr)
            hook = self.components.get(name, Storage())
            if isinstance(joinby, dict):
                for tablename in joinby:
                    hook[tablename] = Storage(
                        _joinby = ("id", joinby[tablename]),
                        _component = component)
            elif isinstance(joinby, str):
                hook._joinby=joinby
                hook._component=component
            else:
                raise SyntaxError("Invalid join key(s)")
            self.components[name] = hook
            return component
        else:
            raise SyntaxError("Join key(s) must be defined.")


    # -------------------------------------------------------------------------
    def get_component(self, prefix, name, component_name):

        """ Retrieves a component of a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        table = self.db.get(tablename, None)

        hook = self.components.get(component_name, None)
        if table and hook:
            h = hook.get(tablename, None)
            if h:
                pkey, fkey = h._joinby
                component = h._component
                return (hook[tablename]._component, pkey, fkey)
            else:
                nkey = hook._joinby
                component = hook._component
                if nkey and nkey in table.fields:
                    return (component, nkey, nkey)

        return (None, None, None)


    # -------------------------------------------------------------------------
    def get_components(self, prefix, name):

        """ Retrieves all components related to a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        table = self.db.get(tablename, None)

        components = []
        if table:
            for hook in self.components.values():
                if tablename in hook:
                    h = hook[tablename]
                    pkey, fkey = h._joinby
                    component = h._component
                    components.append((component, pkey, fkey))
                else:
                    nkey = hook._joinby
                    component = hook._component
                    if nkey and nkey in table.fields:
                        components.append((component, nkey, nkey))

        return components


    # -------------------------------------------------------------------------
    def get_many2many(self, prefix, name):

        """ Finds all many-to-many links of a resource (introspective)

            This requires that the link references the respective
            tables <prefix>_<name> by fields '<name>_id', e.g.
            'pr_group' by field 'group_id', 'gis_location' by
            'location_id' etc.

        """

        m2m = dict()

        tablename = "%s_%s" % (prefix, name)
        if tablename not in self.db:
            return m2m
        else:
            table = self.db[tablename]

        this_id = "%s_id" % name
        for (ln, lf) in table._referenced_by:

            if lf == this_id:
                if ln not in self.db:
                    continue
                lt = self.db[ln]

                fields = filter(lambda f: f != lf and f[-3:] == "_id", lt.fields)
                for f in fields:
                    ftype = str(lt[f].type)
                    if ftype.startswith("reference"):
                        tn = ftype[10:]
                        tprefix, tname = tn.split("_", 1)
                        if f[:-3] == tname:
                            lprefix, lname = ln.split("_",1)
                            m2m[tname] = m2m.get(tname, dict())
                            m2m[tname][lname] = dict(linkto=tn, linkby=ln)

        return m2m


    # -------------------------------------------------------------------------
    def set_method(self, prefix, name,
                   component_name=None,
                   method=None,
                   action=None):

        """ Adds a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)
            @param method: name of the method
            @param action: function to invoke for this method

        """

        assert method is not None, "Method must be specified."
        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method not in self.methods:
                self.methods[method] = {}
            self.methods[method][tablename] = action
        else:
            component = self.get_component(prefix, name, component_name)[0]
            if component:
                if method not in self.cmethods:
                    self.cmethods[method] = {}
                if component.tablename not in self.cmethods[method]:
                    self.cmethods[method][component.tablename] = {}
                self.cmethods[method][component.tablename][tablename] = action

        return True


    # -------------------------------------------------------------------------
    def get_method(self, prefix, name, component_name=None, method=None):

        """ Retrieves a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)
            @param method: name of the method

        """

        if not method:
            return None

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method in self.methods and tablename in self.methods[method]:
                return self.methods[method][tablename]
            else:
                return None
        else:
            component = self.get_component(prefix, name, component_name)[0]
            if component and \
               method in self.cmethods and \
               component.tablename in self.cmethods[method] and \
               tablename in self.cmethods[method][component.tablename]:
                return self.cmethods[method][component.tablename][tablename]
            else:
                return None


    # -------------------------------------------------------------------------
    def set_attr(self, component_name, name, value):

        """ Sets an attribute for a component

            @param component_name: name of the component (without prefix)
            @param name: name of the attribute
            @param value: value for the attribute

        """

        return self.components[component_name].set_attr(name, value)


    # -------------------------------------------------------------------------
    def get_attr(self, component_name, name):

        """ Retrieves an attribute value of a component

            @param component_name: name of the component (without prefix)
            @param name: name of the attribute

        """

        return self.components[component_name].get_attr(name)


# *****************************************************************************
class S3ResourceController(object):

    """ S3 Resource Controller """

    UID = "uuid"
    DELETED = "deleted"

    HOOKS = "s3"
    RCVARS = "rcvars"

    XSLT_FILE_EXTENSION = "xsl"
    XSLT_IMPORT_TEMPLATES = "static/xslt/import"
    XSLT_EXPORT_TEMPLATES = "static/xslt/export"

    ACTION = dict(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )
    ROWSPERPAGE = 10
    MAX_DEPTH = 10

    # Error messages
    ERROR = Storage(
        BAD_RECORD = "Record not found",
        BAD_METHOD = "Invalid method",
        BAD_FORMAT = "Invalid data format",
        BAD_REQUEST = "Invalid request",
        BAD_TEMPLATE = "XSLT Template not found",
        BAD_RESOURCE = "Invalid Resource",
        PARSE_ERROR = "XML Parse Error",
        TRANSFORMATION_ERROR = "XSLT Transformation Error",
        BAD_SOURCE = "Invalid XML Source",
        NO_MATCH = "No matching element found in the data source",
        VALIDATION_ERROR = "Validation Error",
        DATA_IMPORT_ERROR = "Data Import Error",
        NOT_PERMITTED = "Operation Not Permitted",
        NOT_IMPLEMENTED = "Not Implemented"
    )

    # -------------------------------------------------------------------------
    def __init__(self, db,
                 domain=None,
                 base_url=None,
                 cache=None,
                 auth=None,
                 audit=None,
                 rpp=None,
                 gis=None,
                 messages=None,
                 debug=False,
                 **attr):

        """ Constructor

            @param db: the database (DAL)
            @param domain: name of the current domain
            @param base_url: base URL of this instance
            @param rpp: rows-per-page for server-side pagination
            @param gis: the GIS toolkit to use
            @param messages: a function to retrieve message URLs tagged for a resource
            @param cache: the cache object

        """

        assert db is not None, "Database must not be None."

        # Settings
        self.db = db
        self.cache = cache

        self.domain = domain
        self.base_url = base_url
        self.download_url = "%s/default/download" % base_url

        if rpp:
            self.ROWSPERPAGE = rpp

        self.show_ids = False

        # Errors and Debug messages
        self.error = None
        self.debug = debug

        # Toolkits
        self.auth = auth    # Auth
        self.gis = gis      # GIS

        self.model = S3ResourceModel(self.db)
        self.xml = S3XML(self.db,
                         domain=domain,
                         base_url=base_url,
                         gis=self.gis,
                         cache=cache)

        # Hooks
        self.audit = audit              # Audit
        self.messages = None            # Messages Finder
        self.tree_resolve = None        # Tree Resolver
        self.sync_resolve = None        # Sync Resolver
        self.sync_log = None            # Sync Logger

        # Import/Export formats
        attr = Storage(attr)

        self.xml_import_formats = attr.get("xml_import_formats", ["xml"])
        self.xml_export_formats = attr.get("xml_export_formats",
                                           dict(xml="application/xml"))

        self.json_import_formats = attr.get("json_import_formats", ["json"])
        self.json_export_formats = attr.get("json_export_formats",
                                            dict(json="text/x-json"))

        # Method Handlers
        self.__handler = Storage()


    # -------------------------------------------------------------------------
    def __dbg(self, msg):

        """ Print out debug messages. """

        if self.debug:
            print >> sys.stderr, "S3ResourceController: %s" % msg


    # -------------------------------------------------------------------------
    def invoke_hook(self, hook, *args, **vars):

        """ Invoke a hook or a list of hooks """

        name = vars.pop("name", None)

        if name and isinstance(hook, dict):
            hook = hook.get(name, None)

        if hook:
            if isinstance(hook, (list, tuple)):
                result = [f(*args, **vars) for f in hook]
            else:
                result = hook(*args, **vars)
            return result
        else:
            return None


    # -------------------------------------------------------------------------
    def __directory(self, d, l, k, v, e={}):

        """ Converts a list of dicts into a directory

            @param d: the directory
            @param l: the list
            @param k: the key field
            @param v: the value field
            @param e: directory of elements to exclude

        """

        if not d:
            d = {}

        for i in l:
            if k in i and v in i:
                c = e.get(i[k], None)
                if c and i[v] in c:
                    continue
                if i[k] in d:
                    if not i[v] in d[i[k]]:
                        d[i[k]].append(i[v])
                else:
                    d[i[k]] = [i[v]]
        return d


    # -------------------------------------------------------------------------
    def __fields(self, table, skip=[]):

        """
            Finds all readable fields in a table and splits
            them into reference and non-reference fields

            @param table: the DB table
            @param skip: list of field names to skip

        """

        fields = filter(lambda f:
                        f != self.xml.UID and
                        f not in skip and
                        f not in self.xml.IGNORE_FIELDS,
                        table.fields)

        if self.show_ids and "id" not in fields:
            fields.insert(0, "id")

        rfields = filter(lambda f:
                         str(table[f].type).startswith("reference") and
                         f not in self.xml.FIELDS_TO_ATTRIBUTES,
                         fields)

        dfields = filter(lambda f:
                         f not in rfields,
                         fields)

        return (rfields, dfields)


    # -------------------------------------------------------------------------
    def __vectorize(self, resource, element,
                    id=None,
                    files=[],
                    validate=None,
                    permit=None,
                    audit=None,
                    sync=None,
                    log=None,
                    tree=None,
                    directory=None,
                    vmap=None,
                    lookahead=True):

        """ Builds a list of vectors from an element

            @param resource: the resource name (=tablename)
            @param element: the element
            @param id: target record ID
            @param validate: validate hook (function to validate record)
            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param sync: sync hook (function to resolve sync conflicts)
            @param log: log hook (function to log imports)
            @param tree: the element tree of the source
            @param directory: the resource directory of the tree
            @param vmap: the vector map for the import
            @param lookahead: resolve any references

        """

        imports = []

        if vmap is not None and element in vmap:
            return imports

        table = self.db[resource]
        original = self.original(table, element)
        record = self.xml.record(table, element,
                                 original=original,
                                 files=files,
                                 validate=validate)

        mtime = element.get(self.xml.MTIME, None)
        if mtime:
            mtime, error = self.validate(table, None, self.xml.MTIME, mtime)
            if error:
                mtime = None

        if not record:
            self.error = self.ERROR.VALIDATION_ERROR
            return None

        if lookahead:
            (rfields, dfields) = self.__fields(table)
            rmap = self.xml.lookahead(table, element, rfields,
                                      directory=directory, tree=tree)
        else:
            rmap = []

        (prefix, name) = resource.split("_", 1)
        onvalidation = self.model.get_config(table, "onvalidation")
        onaccept = self.model.get_config(table, "onaccept")
        vector = S3Vector(self, prefix, name, id,
                          record=record,
                          element=element,
                          mtime=mtime,
                          rmap=rmap,
                          directory=directory,
                          permit=permit,
                          audit=audit,
                          sync=sync,
                          log=log,
                          onvalidation=onvalidation,
                          onaccept=onaccept)

        if vmap is not None:
            vmap[element] = vector

        for r in rmap:
            entry = r.get("entry")
            relement = entry.get("element")
            if relement is None:
                continue
            vectors = self.__vectorize(entry.get("resource"),
                                     relement,
                                     validate=validate,
                                     permit=permit,
                                     audit=audit,
                                     sync=sync,
                                     log=log,
                                     tree=tree,
                                     directory=directory,
                                     vmap=vmap)
            if vectors:
                if entry["vector"] is None:
                    entry["vector"] = vectors[-1]
                imports.extend(vectors)

        imports.append(vector)
        return imports


    # -------------------------------------------------------------------------
    def validate(self, table, record, fieldname, value):

        """ Validates a single value

            @param table: the DB table
            @param record: the existing DB record
            @param fieldname: name of the field
            @param value: value to check

        """

        field = table.get(fieldname, None)
        if field:
            if record:
                v = record.get(fieldname, None)
                if v and v == value:
                    return (value, None)

            value, error = field.validate(value)
            return (value, error)
        else:
            raise AttributeError("No field %s in %s" % (fieldname, table._tablename))


    # -------------------------------------------------------------------------
    def get_session(self, session, prefix, name):

        """ Reads the last record ID for a resource from a session

            @param session: the session store
            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        if self.RCVARS in session and tablename in session[self.RCVARS]:
            return session[self.RCVARS][tablename]
        else:
            return None


    # -------------------------------------------------------------------------
    def store_session(self, session, prefix, name, id):

        """ Stores a record ID for a resource in a session

            @param session: the session store
            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)
            @param id: the ID to store

        """

        if self.RCVARS not in session:
            session[self.RCVARS] = Storage()
        if self.RCVARS in session:
            tablename = "%s_%s" % (prefix, name)
            session[self.RCVARS][tablename] = id

        return True # always return True to make this chainable


    # -------------------------------------------------------------------------
    def clear_session(self, session, prefix=None, name=None):

        """ Clears one or all record IDs stored in a session

            @param session: the session store
            @param prefix: the prefix of the resource name (=module name)
            @param name: the name of the resource (=without prefix)

        """

        if prefix and name:
            tablename = "%s_%s" % (prefix, name)
            if self.RCVARS in session and tablename in session[self.RCVARS]:
                del session[self.RCVARS][tablename]
        else:
            if self.RCVARS in session:
                del session[self.RCVARS]

        return True # always return True to make this chainable


    # -------------------------------------------------------------------------
    def set_handler(self, method, handler):

        """ Set the default handler for a resource method """

        self.__handler[method] = handler


    # -------------------------------------------------------------------------
    def get_handler(self, method):

        """ Get the default handler for a resource method """

        return self.__handler.get(method, None)


    # REST Interface ==========================================================

    def resource(self, prefix, name,
                 id=None,
                 uid=None,
                 filter=None,
                 url_vars=None,
                 parent=None,
                 components=None,
                 storage=None,
                 debug=None):

        """ Wrapper function for S3Resource """

        resource = S3Resource(self, prefix, name,
                              id=id,
                              uid=uid,
                              filter=filter,
                              url_vars=url_vars,
                              parent=parent,
                              components=components,
                              storage=storage,
                              debug=debug)

        # Set default handlers
        for method in self.__handler:
            resource.set_handler(method, self.__handler[method])

        return resource


    # -------------------------------------------------------------------------
    def request(self, prefix, name,
                request=None, session=None, response=None, debug=None):

        """ Wrapper function for S3Request """

        return S3Request(self, prefix, name,
                         request=request,
                         session=session,
                         response=response,
                         debug=self.debug)


    # -------------------------------------------------------------------------
    def parse_request(self, prefix, name, session, request, response):

        """ Parse an HTTP request and generate the corresponding
            S3Request and S3Resource objects.

        """

        self.error = None

        try:
            req = self.request(prefix, name,
                               request=request,
                               session=session,
                               response=response,
                               debug=self.debug)
        except SyntaxError:
            raise HTTP(400, body=self.error)
        except KeyError:
            raise HTTP(404, body=self.error)

        res = req.resource

        return (res, req)


    # -------------------------------------------------------------------------
    def url_query(self, resource, url_vars):

        """ URL query parser """

        q = Storage()
        for k in url_vars:
            if k.find(".") > 0:
                rname, field = k.split(".", 1)
                if rname == resource.name:
                    table = resource.table
                elif rname in resource.components:
                    table = resource.components[rname].component.table
                else:
                    continue
                if field.find("__") > 0:
                    field, op = field.split("__", 1)
                else:
                    op = "eq"
                if field == "uid":
                    field = self.UID
                if field not in table.fields:
                    continue
                else:
                    ftype = str(table[field].type)
                    values = url_vars[k]

                    if op in ("lt", "le", "gt", "ge"):
                        if ftype not in ("integer", "double", "date", "time", "datetime"):
                            continue
                        if not isinstance(values, (list, tuple)):
                            values = [values]
                        vlist = []
                        for v in values:
                            if v.find(",") > 0:
                                v = v.split(",", 1)[-1]
                            vlist.append(v)
                        values = vlist
                    elif op == "eq":
                        if isinstance(values, (list, tuple)):
                            values = values[-1]
                        if values.find(",") > 0:
                            values = values.split(",")
                        else:
                            values = [values]
                    elif op == "ne":
                        if not isinstance(values, (list, tuple)):
                            values = [values]
                        vlist = []
                        for v in values:
                            if v.find(",") > 0:
                                v = v.split(",")
                                vlist.extend(v)
                            else:
                                vlist.append(v)
                        values = vlist
                    elif op in ("like", "unlike"):
                        if ftype not in ("string", "text"):
                            continue
                        if not isinstance(values, (list, tuple)):
                            values = [values]
                    else:
                        continue

                    vlist = []
                    for v in values:
                        if ftype == "boolean":
                            if v in ("true", "True"):
                                value = True
                            else:
                                value = False
                        elif ftype == "integer":
                            try:
                                value = float(v)
                            except ValueError:
                                continue
                        elif ftype == "double":
                            try:
                                value = float(v)
                            except ValueError:
                                continue
                        elif ftype == "date":
                            validator = IS_DATE()
                            value, error = validator(v)
                            if error:
                                continue
                        elif ftype == "time":
                            validator = IS_TIME()
                            value, error = validator(v)
                            if error:
                                continue
                        elif ftype == "datetime":
                            tfmt = "%Y-%m-%dT%H:%M:%SZ"
                            try:
                                (y,m,d,hh,mm,ss,t0,t1,t2) = time.strptime(v, tfmt)
                                value = datetime.datetime(y,m,d,hh,mm,ss)
                            except ValueError:
                                continue
                        else:
                            value = v

                        vlist.append(value)
                    values = vlist

                    if values:
                        if rname not in q:
                            q[rname] = Storage()
                        if field not in q[rname]:
                            q[rname][field] = Storage()
                        q[rname][field][op] = values

        return q


    # Resource functions ======================================================

    def original(self, table, record):

        """ Find the original record for a possible duplicate:

            - if the record contains a UUID, then only that UUID is used
              to match the record with an existing DB record

            - otherwise, if the record contains some values for unique fields,
              all of them must match the same existing DB record

        """

        # Get primary keys
        pkeys = [f for f in table.fields if table[f].unique]
        pvalues = Storage()

        # Get the values from record
        if isinstance(record, etree._Element):
            for f in pkeys:
                v = None
                if f == self.xml.UID or f in self.xml.ATTRIBUTES_TO_FIELDS:
                    v = record.get(f, None)
                else:
                    xexpr = "%s[@%s='%s']" % (self.xml.TAG.data, self.xml.ATTRIBUTE.field, f)
                    child = record.xpath(xexpr)
                    if child:
                        child = child[0]
                        v = child.get(self.xml.ATTRIBUTE.value, child.text)
                if v:
                    value = self.xml.xml_decode(v)
                    pvalues[f] = value

        elif isinstance(record, dict):
            for f in pkeys:
                v = record.get(f, None)
                if v:
                    pvalues[f] = v
        else:
            raise TypeError

        # Build match query
        if self.xml.UID in pvalues:
            uid = pvalues[self.xml.UID]
            if self.xml.domain_mapping:
                uid = self.xml.import_uid(uid)
            query = (table[self.xml.UID] == uid)
        else:
            query = None
            for f in pvalues:
                _query = (table[f] == pvalues[f])
                if query is not None:
                    query = query | _query
                else:
                    query = _query

        if query:
            original = self.db(query).select(table.ALL)
            if len(original) == 1:
                return original.first()

        return None


    # -------------------------------------------------------------------------
    def export_tree(self, resource,
                    skip=[],
                    audit=None,
                    start=None,
                    limit=None,
                    marker=None,
                    msince=None,
                    show_urls=True,
                    dereference=True):

        prefix = resource.prefix
        name = resource.name
        tablename = resource.tablename
        table = resource.table

        (rfields, dfields) = self.__fields(resource.table, skip=skip)

        # Total number of results
        results = resource.count()

        # Load slice
        resource.load(start=start, limit=limit)

        # Load component records
        crfields = Storage()
        cdfields = Storage()
        for c in resource.components.values():
            cresource = c.resource
            cresource.load()
            ctablename = cresource.tablename
            crfields[ctablename], \
            cdfields[ctablename] = self.__fields(cresource.table, skip=skip)

        # Resource base URL
        if self.base_url:
            url = "%s/%s/%s" % (self.base_url, prefix, name)
        else:
            url = "/%s/%s" % (prefix, name)

        element_list = []
        export_map = Storage()
        reference_map = []

        for record in resource:
            if audit:
                audit(self.ACTION["read"], prefix, name,
                      record=record.id,
                      representation="xml")

            if show_urls:
                resource_url = "%s/%s" % (url, record.id)
            else:
                resource_url = None

            msince_add = True
            if msince is not None and self.xml.MTIME in record:
                if record[self.xml.MTIME] < msince:
                    msince_add = False

            rmap = self.xml.rmap(table, record, rfields)
            element = self.xml.element(table, record,
                                       fields=dfields,
                                       url=resource_url,
                                       download_url=self.download_url,
                                       marker=marker)
            self.xml.add_references(element, rmap, show_ids=self.show_ids)
            self.xml.gis_encode(rmap,
                                download_url=self.download_url,
                                marker=marker)


            # Export components of this record
            r_url = "%s/%s" % (url, record.id)
            for c in resource.components.values():

                component = c.component
                cresource = c.resource
                cprefix = component.prefix
                cname = component.name
                ctable = component.table
                c_url = "%s/%s" % (r_url, cname)

                ctablename = component.tablename
                _rfields = crfields[ctablename]
                _dfields = cdfields[ctablename]

                crecords = resource(record.id, component=cname)
                for crecord in crecords:

                    if msince is not None and self.xml.MTIME in crecord:
                        if crecord[self.xml.MTIME] < msince:
                            continue
                    msince_add = True

                    if audit:
                        audit(self.ACTION["read"], cprefix, cname,
                              record=crecord.id,
                              representation="xml")

                    if show_urls:
                        resource_url = "%s/%s" % (c_url, crecord.id)
                    else:
                        resource_url = None

                    crmap = self.xml.rmap(ctable, crecord, _rfields)
                    celement = self.xml.element(ctable, crecord,
                                                fields=_dfields,
                                                url=resource_url,
                                                download_url=self.download_url,
                                                marker=marker)
                    self.xml.add_references(celement, crmap, show_ids=self.show_ids)
                    self.xml.gis_encode(rmap,
                                        download_url=self.download_url,
                                        marker=marker)

                    element.append(celement)
                    reference_map.extend(crmap)

                    if export_map.get(c.tablename, None):
                        export_map[c.tablename].append(crecord.id)
                    else:
                        export_map[c.tablename] = [crecord.id]

            if msince_add:
                reference_map.extend(rmap)
                element_list.append(element)
                if export_map.get(resource.tablename, None):
                    export_map[resource.tablename].append(record.id)
                else:
                    export_map[resource.tablename] = [record.id]
            else:
                results -= 1

        # Add referenced resources to the tree
        depth = dereference and self.MAX_DEPTH or 0
        while reference_map and depth:
            depth -= 1
            load_map = self.__directory(None, reference_map, "table", "id", e=export_map)
            reference_map = []

            for tablename in load_map:

                load_list = load_map[tablename]
                prefix, name = tablename.split("_", 1)
                rresource = self.resource(prefix, name, id=load_list, components=[])
                rresource.load()

                if self.base_url:
                    url = "%s/%s/%s" % (self.base_url, prefix, name)
                else:
                    url = "/%s/%s" % (prefix, name)

                table = rresource.table
                rfields, dfields = self.__fields(table, skip=skip)
                for record in rresource:
                    if audit:
                        audit(self.ACTION["read"], prefix, name,
                              record=record.id,
                              representation="xml")

                    rmap = self.xml.rmap(table, record, rfields)
                    if show_urls:
                        resource_url = "%s/%s" % (url, record.id)
                    else:
                        resource_url = None

                    element = self.xml.element(table, record,
                                               fields=dfields,
                                               url=resource_url,
                                               download_url=self.download_url,
                                               marker=marker)
                    self.xml.add_references(element, rmap, show_ids=self.show_ids)
                    self.xml.gis_encode(rmap,
                                        download_url=self.download_url,
                                        marker=marker)

                    element.set(self.xml.ATTRIBUTE.ref, "True")
                    element_list.append(element)

                    reference_map.extend(rmap)
                    if export_map.get(tablename, None):
                        export_map[tablename].append(record.id)
                    else:
                        export_map[tablename] = [record.id]

        # Complete the tree
        return self.xml.tree(element_list,
                             domain=self.domain,
                             url= show_urls and self.base_url or None,
                             results=results,
                             start=start,
                             limit=limit)


    # -------------------------------------------------------------------------
    def import_tree(self, resource, id, tree,
                    push_limit=None, ignore_errors=False):

        """ Imports data from an element tree to a resource

            @param resource: the resource
            @param id: record ID or list of record IDs to update
            @param tree: the element tree
            @param push_limit: maximum allowed number of imports
                (None for unlimited)
            @param ignore_errors: continue at errors (=skip invalid elements)

        """

        self.error = None

        if self.tree_resolve:
            if not isinstance(tree, etree._ElementTree):
                tree = etree.ElementTree(tree)
            self.invoke_hook(self.tree_resolve, tree)

        permit = self.auth.shn_has_permission
        audit = self.audit

        tablename = resource.tablename
        table = resource.table

        elements = self.xml.select_resources(tree, tablename)
        if not elements:
            return True

        # if a record ID is given, import only matching elements
        # TODO: match all possible fields (see original())
        if id and self.xml.UID in table:
            if not isinstance(id, (tuple, list)):
                query = (table.id == id)
            else:
                query = (table.id.belongs(id))
            set = self.db(query).select(table[self.xml.UID])
            uids = [row[self.xml.UID] for row in set]
            matches = []
            for element in elements:
                element_uid = element.get(self.xml.UID, None)
                if not element_uid:
                    continue
                if self.xml.domain_mapping:
                    element_uid = self.xml.import_uid(element_uid)
                if element_uid in uids:
                    matches.append(element)
            if not matches:
                self.error = self.ERROR.NO_MATCH
                return False
            else:
                elements = matches

        if push_limit is not None and len(elements) > push_limit:
            self.error = self.ERROR.NOT_PERMITTED
            return False

        # Import all matching elements
        error = None
        imports = []
        directory = {}
        vmap = {} # Element<->Vector Map

        for i in xrange(0, len(elements)):
            element = elements[i]
            vectors = self.__vectorize(tablename, element,
                                       id=id,
                                       files = resource.files(),
                                       validate=self.validate,
                                       permit=permit,
                                       audit=audit,
                                       sync=self.sync_resolve,
                                       log=self.sync_log,
                                       tree=tree,
                                       directory=directory,
                                       vmap=vmap,
                                       lookahead=True)

            if vectors:
                vector = vectors[-1]
            else:
                continue

            # Import components
            for item in resource.components.values():

                # Get component details
                c = item.component
                pkey = item.pkey
                fkey = item.fkey
                ctablename = c.tablename
                ctable = c.table

                # Find elements for the component
                celements = self.xml.select_resources(element, ctablename)

                if celements:
                    c_id = c_uid = None

                    # Get the original record ID/UID, if not multiple
                    if not c.attr.multiple:
                        if vector.id:
                            query = (table.id == vector.id) & (table[pkey] == ctable[pkey])
                            if self.xml.UID in ctable:
                                fields = (ctable.id, ctable[self.xml.UID])
                            else:
                                fields = (ctable.id,)
                            orig = self.db(query).select(limitby=(0,1), *fields).first()
                            if orig:
                                c_id = orig.id
                                c_uid = orig.get(self.xml.UID, None)

                        celements = [celements[0]]
                        if c_uid:
                            celements[0].set(self.xml.UID, c_uid)

                    # Generate vectors for the component elements
                    for k in xrange(0, len(celements)):
                        celement = celements[k]
                        cvectors = self.__vectorize(ctablename,
                                                    celement,
                                                    files = resource.files(),
                                                    validate=self.validate,
                                                    permit=permit,
                                                    audit=audit,
                                                    sync=self.sync_resolve,
                                                    log=self.sync_log,
                                                    tree=tree,
                                                    directory=directory,
                                                    vmap=vmap,
                                                    lookahead=True)

                        cvector = None
                        if cvectors:
                            cvector = cvectors.pop()
                        if cvectors:
                            vectors.extend(cvectors)
                        if cvector:
                            cvector.pkey = pkey
                            cvector.fkey = fkey
                            vector.components.append(cvector)

            if self.error is None:
                imports.extend(vectors)
            else:
                error = self.error
                self.error = None

        if error:
            self.error = error

        # Commit all vectors
        if self.error is None or ignore_errors:
            for i in xrange(0, len(imports)):
                vector = imports[i]
                success = vector.commit()
                if not success:
                    if not vector.permitted:
                        self.error = self.ERROR.NOT_PERMITTED
                    else:
                        self.error = self.ERROR.DATA_IMPORT_ERROR
                    if vector.element:
                        vector.element.set(self.xml.ATTRIBUTE.error, self.error)
                    if ignore_errors:
                        continue
                    else:
                        return False

        return ignore_errors or not self.error


    # -------------------------------------------------------------------------
    def search_simple(self, table, fields=None, label=None, filterby=None):

        """ Simple search function for resources

            @param table: the DB table
            @param fields: list of fields to search for the label
            @param label: label to be found
            @param filterby: filter query for results

        """

        mq = Storage()
        search_fields = Storage()

        prefix, name = table._tablename.split("_", 1)

        if fields and not isinstance(fields, (list, tuple)):
            fields = [fields]
        elif not fields:
            raise SyntaxError("No search fields specified.")

        for f in fields:
            _table = None
            component = None

            if f.find(".") != -1:
                cname, f = f.split(".", 1)
                component, pkey, fkey = self.model.get_component(prefix, name, cname)
                if component:
                    _table = component.table
                    tablename = component.tablename
            else:
                _table = table
                tablename = table._tablename

            if _table and tablename not in mq:
                query = (self.auth.shn_accessible_query("read", _table))
                if "deleted" in _table.fields:
                    query = (query & (_table.deleted == "False"))
                if component:
                    join = (table[pkey] == _table[fkey])
                    query = (query & join)
                mq[_table._tablename] = query

            if _table and f in _table.fields:
                if _table._tablename not in search_fields:
                    search_fields[tablename] = [_table[f]]
                else:
                    search_fields[tablename].append(_table[f])

        if not search_fields:
            return None

        if label and isinstance(label,str):
            labels = label.split()
            results = []

            for l in labels:
                wc = "%"
                _l = "%s%s%s" % (wc, l, wc)
                query = None
                for tablename in search_fields:
                    hq = mq[tablename]
                    fq = None
                    fields = search_fields[tablename]
                    for f in fields:
                        if fq:
                            fq = (f.like(_l)) | fq
                        else:
                            fq = (f.like(_l))
                    q = hq & fq
                    if query is None:
                        query = q
                    else:
                        query = query | q

                if results:
                    query = (table.id.belongs(results)) & query
                if filterby:
                    query = (filterby) & (query)

                records = self.db(query).select(table.id)
                results = [r.id for r in records]
                if not results:
                    return None

            return results
        else:
            return None


# *****************************************************************************
class S3Vector(object):

    """ Helper class for data imports """

    METHOD = Storage(
        CREATE="create",
        UPDATE="update"
    )

    RESOLUTION = Storage(
        THIS="THIS",                # keep local instance
        OTHER="OTHER",              # import other instance
        NEWER="NEWER",              # import other if newer
        MASTER="MASTER",            # import other if master
        MASTERCOPY="MASTERCOPY"     # import other if lower master-copy-index
    )

    UID = "uuid"
    MCI = "mci"
    MTIME = "modified_on"


    # -------------------------------------------------------------------------
    def __init__(self, manager, prefix, name, id,
                 record=None,
                 element=None,
                 mtime=None,
                 rmap=None,
                 directory=None,
                 permit=None,
                 audit=None,
                 sync=None,
                 log=None,
                 onvalidation=None,
                 onaccept=None):

        """ Constructor

            @param manager: the resource controller
            @param prefix: prefix of the resource name (=module name)
            @param name: the resource name (=without prefix)
            @param id: the target record ID
            @param record: the record data to import
            @param element: the corresponding element from the element tree
            @param rmap: map of references for this record
            @param directory: resource directory of the input tree
            @param permit: permit hook (function to check table permissions)
            @param audit: audit hook (function to audit table access)
            @param sync: sync hook (function to resolve sync conflicts)
            @param log: log hook (function to log imports)
            @param onvalidation: extra function to validate records
            @param onaccept: callback function for committed importes

        """

        self.__manager = manager
        self.db = self.__manager.db
        self.prefix = prefix
        self.name = name

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db[self.tablename]

        self.element = element
        self.record = record
        self.id = id

        if mtime:
            self.mtime = mtime
        else:
            self.mtime = datetime.datetime.utcnow()

        self.rmap = rmap

        self.components = []
        self.references = []
        self.update = []

        self.method = None
        self.strategy = [self.METHOD.CREATE, self.METHOD.UPDATE]

        self.resolution = self.RESOLUTION.OTHER
        self.default_resolution = self.RESOLUTION.THIS

        self.onvalidation = onvalidation
        self.onaccept = onaccept
        self.audit = audit
        self.sync = sync
        self.log = log

        self.accepted = True
        self.permitted = True
        self.committed = False

        self.uid = self.record.get(self.UID, None)
        self.mci = self.record.get(self.MCI, 2)

        if not self.id:
            self.id = 0
            self.method = permission = self.METHOD.CREATE
            orig = self.__manager.original(self.table, self.record)
            if orig:
                self.id = orig.id
                self.uid = orig.get(self.UID, None)
                self.method = permission = self.METHOD.UPDATE
        else:
            self.method = permission = self.METHOD.UPDATE
            if not self.db(self.table.id == id).count():
                self.id = 0
                self.method = permission = self.METHOD.CREATE

        # Do allow import to tables with these prefixes:
        if self.prefix in ("auth", "admin", "s3"):
            self.permitted = False

        # ...or check permission explicitly:
        elif permit and not \
           permit(permission, self.tablename, record_id=self.id):
            self.permitted = False

        # Once the vector has been created, update the entry in the directory
        if self.uid and \
           directory is not None and self.tablename in directory:
            entry = directory[self.tablename].get(self.uid, None)
            if entry:
                entry.update(vector=self)


    # Data import =============================================================

    def get_resolution(self, field):

        """ Find Sync resolution for a particular field in this record

            @param field: the field name

        """

        if isinstance(self.resolution, dict):
            r = self.resolution.get(field, self.default_resolution)
        else:
            r = self.resolution
        if not r in self.RESOLUTION.values():
            r = self.default_resolution
        return r


    # -------------------------------------------------------------------------
    def commit(self):

        """ Commits the vector to the database """

        self.resolve() # Resolve references

        skip_components = False

        if not self.committed:
            if self.accepted and self.permitted:

                #print >> sys.stderr, "Committing %s id=%s mtime=%s" % (self.tablename, self.id, self.mtime)

                # Create pseudoform for callbacks
                form = Storage()
                form.method = self.method
                form.vars = self.record
                form.vars.id = self.id
                form.errors = Storage()

                # Validate
                if self.onvalidation:
                    self.__manager.invoke_hook(self.onvalidation, form, name=self.tablename)
                if form.errors:
                    #print >> sys.stderr, form.errors
                    if self.element:
                        #TODO: propagate errors to element
                        pass
                    return False

                # Call Sync resolver+logger
                if self.sync:
                    self.sync(self)
                if self.log:
                    self.log(self)

                # Check for strategy
                if not isinstance(self.strategy, (list, tuple)):
                    self.strategy = [self.strategy]

                if self.method not in self.strategy:
                    # Skip this record ----------------------------------------

                    # Do not create/update components when skipping primary
                    skip_components = True

                elif self.method == self.METHOD.UPDATE:
                    # Update existing record ----------------------------------

                    # Merge as per Sync resolution:
                    query = (self.table.id == self.id)
                    this = self.db(query).select(self.table.ALL, limitby=(0,1))
                    if this:
                        this = this.first()
                        if self.MTIME in self.table.fields:
                            this_mtime = this[self.MTIME]
                        else:
                            this_mtime = None
                        if self.MCI in self.table.fields:
                            this_mci = this[self.MCI]
                        else:
                            this_mci = 0
                        for f in self.record:
                            r = self.get_resolution(f)
                            if r == self.RESOLUTION.THIS:
                                del self.record[f]
                            elif r == self.RESOLUTION.NEWER:
                                if this_mtime and \
                                   this_mtime > self.mtime:
                                    del self.record[f]
                            elif r == self.RESOLUTION.MASTER:
                                if this_mci == 0 or self.mci != 1:
                                    del self.record[f]
                            elif r == self.RESOLUTION.MASTERCOPY:
                                if this_mci == 0 or \
                                   self.mci == 0 or \
                                   this_mci < self.mci:
                                    del self.record[f]
                                elif this_mci == self.mci and \
                                     this_mtime and this_mtime > self.mtime:
                                        del self.record[f]

                    if len(self.record):
                        self.record.update({self.MCI:self.mci})
                        if "deleted" in self.table.fields:
                            self.record.update(deleted=False) # Undelete re-imported records!
                        try:
                            success = self.db(self.table.id == self.id).update(**dict(self.record))
                        except: # TODO: propagate error to XML importer
                            return False
                        if success:
                            self.committed = True
                    else:
                        self.committed = True

                elif self.method == self.METHOD.CREATE:
                    # Create new record ---------------------------------------

                    if self.UID in self.record:
                        del self.record[self.UID]
                    if self.MCI in self.record:
                        del self.record[self.MCI]
                    for f in self.record:
                        r = self.get_resolution(f)
                        if r == self.RESOLUTION.MASTER and self.mci != 1:
                            del self.record[f]

                    if not len(self.record):
                        skip_components = True
                    else:
                        if self.uid and self.UID in self.table.fields:
                            self.record.update({self.UID:self.uid})
                        if self.MCI in self.table.fields:
                            self.record.update({self.MCI:self.mci})
                        try:
                            success = self.table.insert(**dict(self.record))
                        except: # TODO: propagate error to XML importer
                            return False
                        if success:
                            self.id = success
                            self.committed = True

                # audit + onaccept on successful commits
                if self.committed:
                    form.vars.id = self.id
                    if self.audit:
                        self.audit(self.method, self.prefix, self.name,
                                   form=form, record=self.id, representation="xml")
                    if self.onaccept:
                        self.__manager.invoke_hook(self.onaccept, form, name=self.tablename)

        # Load record if components pending
        if self.id and self.components and not skip_components:
            db_record = self.db(self.table.id == self.id).select(self.table.ALL)
            if db_record:
                db_record = db_record.first()

            # Commit components
            for i in xrange(0, len(self.components)):
                component = self.components[i]
                pkey = component.pkey
                fkey = component.fkey
                component.record[fkey] = db_record[pkey]
                component.commit()

        # Update referencing vectors
        if self.update and self.id:
            for u in self.update:
                vector = u.get("vector", None)
                if vector:
                    field = u.get("field", None)
                    vector.writeback(field, self.id)

        # Phew...done!
        return True


    # -------------------------------------------------------------------------
    def resolve(self):

        """ Resolve references of this record """

        if self.rmap:
            for r in self.rmap:
                if r.entry:
                    id = r.entry.get("id", None)
                    if not id:
                        vector = r.entry.get("vector", None)
                        if vector:
                            id = vector.id
                            r.entry.update(id=id)
                        else:
                            continue
                    if id:
                        self.record[r.field] = id
                    else:
                        if r.field in self.record:
                            del self.record[r.field]
                        vector.update.append(dict(vector=self, field=r.field))


    # -------------------------------------------------------------------------
    def writeback(self, field, value):

        """ Update a field in the record

            @param field: field name
            @param value: value to write

        """

        if self.id and self.permitted:
            self.db(self.table.id == self.id).update(**{field:value})


# *****************************************************************************
class S3XML(object):

    """ XML+JSON toolkit for S3XRC """

    S3XRC_NAMESPACE = "http://eden.sahanafoundation.org/wiki/S3XRC"
    S3XRC = "{%s}" % S3XRC_NAMESPACE #: LXML namespace prefix
    NSMAP = {None: S3XRC_NAMESPACE} #: LXML default namespace

    CACHE_TTL = 5 # time-to-live of RAM cache for field representations

    UID = "uuid"
    MCI = "mci"
    MTIME = "modified_on"

    # GIS field names
    Lat = "lat"
    Lon = "lon"
    FeatureClass = "feature_class_id"
    #Marker = "marker_id"

    IGNORE_FIELDS = ["deleted", "id"]

    FIELDS_TO_ATTRIBUTES = [
            "id",
            "created_on",
            "modified_on",
            "created_by",
            "modified_by",
            "uuid",
            "mci",
            "admin"]

    ATTRIBUTES_TO_FIELDS = ["admin", "mci"]

    TAG = Storage(
        root="s3xrc",
        resource="resource",
        reference="reference",
        data="data",
        list="list",
        item="item",
        object="object",
        select="select",
        field="field",
        option="option",
        options="options",
        fields="fields"
    )

    ATTRIBUTE = Storage(
        id="id",
        name="name",
        table="table",
        field="field",
        value="value",
        resource="resource",
        ref="ref",
        domain="domain",
        url="url",
        filename="filename",
        error="error",
        start="start",
        limit="limit",
        success="success",
        results="results",
        lat="lat",
        latmin="latmin",
        latmax="latmax",
        lon="lon",
        lonmin="lonmin",
        lonmax="lonmax",
        marker="marker",
        sym="sym",
        type="type",
        readable="readable",
        writable="writable",
        has_options="has_options"
    )

    ACTION = Storage(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    PREFIX = Storage(
        resource="$",
        options="$o",
        reference="$k",
        attribute="@",
        text="$"
    )

    PY2XML = [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
              ('"', "&quot;"), ("'", "&apos;")]

    XML2PY = [("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"),
              ("'", "&apos;"), ("&", "&amp;")]


    # -------------------------------------------------------------------------
    def __init__(self, db, domain=None, base_url=None, gis=None, cache=None):

        """ Constructor

            @param db: the database (DAL)
            @param domain: name of the current domain
            @param base_url: base URL of the current instance
            @param gis: GIS toolkit to use

        """

        self.db = db
        self.error = None
        self.domain = domain
        self.base_url = base_url
        self.domain_mapping = True
        self.gis = gis
        self.cache = cache

    # XML+XSLT tools ==========================================================

    def parse(self, source):

        """ Parse an XML source into an element tree

            @param source: the XML source,
                can be a file-like object, a filename or a URL

        """

        self.error = None

        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            e = sys.exc_info()[1]
            self.error = e
            return None


    # -------------------------------------------------------------------------
    def transform(self, tree, template_path, **args):

        """ Transform an element tree with XSLT

            @param tree: the element tree
            @param template_path: pathname of the XSLT stylesheet
            @param args: dict of arguments to pass to the transformer

        """

        self.error = None

        if args:
            _args = [(k, "'%s'" % args[k]) for k in args]
            _args = dict(_args)
        else:
            _args = None
        ac = etree.XSLTAccessControl(read_file=True, read_network=True)
        template = self.parse(template_path)

        if template:
            try:
                transformer = etree.XSLT(template, access_control=ac)
                if _args:
                    result = transformer(tree, **_args)
                else:
                    result = transformer(tree)
                return result
            except:
                e = sys.exc_info()[1]
                self.error = e
                return None
        else:
            # Error parsing the XSL template
            return None


    # -------------------------------------------------------------------------
    def tostring(self, tree, pretty_print=False):

        """ Convert an element tree into XML as string

            @param tree: the element tree
            @param pretty_print: provide pretty formatted output

        """

        return etree.tostring(tree,
                              xml_declaration=True,
                              encoding="utf-8",
                              pretty_print=pretty_print)


    # -------------------------------------------------------------------------
    def tree(self, resources, domain=None, url=None,
             start=None, limit=None, results=None):

        """ Builds a tree from a list of elements

            @param resources: list of <resource> elements
            @param domain: name of the current domain
            @param url: url of the request
            @param start: the start record (in server-side pagination)
            @param limit: the page size (in server-side pagination)
            @param results: number of total available results

        """

        # For now we do not nsmap, because the default namespace cannot be
        # matched in XSLT templates (need explicit prefix) and thus this
        # would require a rework of all existing templates (which is
        # however useful)
        root = etree.Element(self.TAG.root) #, nsmap=self.NSMAP)

        root.set(self.ATTRIBUTE.success, str(False))

        if resources is not None:
            if resources:
                root.set(self.ATTRIBUTE.success, str(True))
            if start is not None:
                root.set(self.ATTRIBUTE.start, str(start))
            if limit is not None:
                root.set(self.ATTRIBUTE.limit, str(limit))
            if results is not None:
                root.set(self.ATTRIBUTE.results, str(results))
            root.extend(resources)

        if domain:
            root.set(self.ATTRIBUTE.domain, self.domain)

        if url:
            root.set(self.ATTRIBUTE.url, self.base_url)

        root.set(self.ATTRIBUTE.latmin,
                 str(self.gis.get_bounds()["min_lat"]))
        root.set(self.ATTRIBUTE.latmax,
                 str(self.gis.get_bounds()["max_lat"]))
        root.set(self.ATTRIBUTE.lonmin,
                 str(self.gis.get_bounds()["min_lon"]))
        root.set(self.ATTRIBUTE.lonmax,
                 str(self.gis.get_bounds()["max_lon"]))

        return etree.ElementTree(root)


    # -------------------------------------------------------------------------
    def xml_encode(self, obj):

        """ Encodes a Python string into an XML text node

            @param obj: string to encode

        """

        if obj:
            for (x,y) in self.PY2XML:
                obj = obj.replace(x, y)
        return obj


    # -------------------------------------------------------------------------
    def xml_decode(self, obj):

        """ Decodes an XML text node into a Python string

            @param obj: string to decode

        """

        if obj:
            for (x,y) in self.XML2PY:
                obj = obj.replace(y, x)
        return obj


    # -------------------------------------------------------------------------
    def export_uid(self, uid):

        """ Maps internal UUIDs to export format

            @param uid: the (internally used) UUID

        """

        if not self.domain:
            return uid
        x = uid.find("/")
        if x < 1 or x == len(uid)-1:
            return "%s/%s" % (self.domain, uid)
        else:
            return uid


    # -------------------------------------------------------------------------
    def import_uid(self, uid):

        """ Maps imported UUIDs to internal format

            @param uid: the (externally used) UUID

        """

        if not self.domain:
            return uid
        x = uid.find("/")
        if x < 1 or x == len(uid)-1:
            return uid
        else:
            (_domain, _uid) = uid.split("/", 1)
            if _domain == self.domain:
                return _uid
            else:
                return uid


    # Data export =============================================================

    def represent(self, table, f, v):

        """ Get the representation of a field value

            @param table: the database table
            @param f: the field name
            @param v: the value

        """

        text = str(table[f].represent(v)).decode("utf-8")
        # Filter out markup from text
        if "<" in text:
            try:
                markup = etree.XML(text)
                text = markup.xpath(".//text()")
                if text:
                    text = " ".join(text)
                else:
                    text = ""
            except etree.XMLSyntaxError:
                pass
        text = self.xml_encode(text)
        return text


    # -------------------------------------------------------------------------
    def rmap(self, table, record, fields):

        """ Generates a reference map for a record

            @param table: the database table
            @param record: the record
            @param fields: list of reference field names in this table

        """

        reference_map = []

        for f in fields:
            id = record.get(f, None)
            if not id:
                continue
            uid = None

            ktablename = str(table[f].type)[10:]
            ktable = self.db[ktablename]

            if self.UID in ktable.fields:
                query = (ktable.id == id)
                if "deleted" in ktable:
                    query = (ktable.deleted == False) & query
                krecord = self.db(query).select(ktable[self.UID],
                                                limitby=(0, 1))
                if krecord:
                    uid = krecord[0][self.UID]
                    if self.domain_mapping:
                        uid = self.export_uid(uid)
                else:
                    continue
            else:
                query = (ktable.id == id)
                if "deleted" in ktable:
                    query = (ktable.deleted == False) & query
                if not self.db(query).count():
                    continue

            value = record[f]
            value = text = self.xml_encode(str(
                           table[f].formatter(value)).decode("utf-8"))
            if table[f].represent:
                text = self.represent(table, f, value)

            reference_map.append(Storage(field=f,
                                         table=ktablename,
                                         id=id,
                                         uid=uid,
                                         text=text,
                                         value=value))

        return reference_map


    # -------------------------------------------------------------------------
    def add_references(self, element, rmap, show_ids=False):

        """ Adds <reference> elements to a <resource>

            @param element: the <resource> element
            @param rmap: the reference map for the corresponding record
            @param show_ids: insert the record ID as attribute in references

        """

        for i in xrange(0, len(rmap)):
            r = rmap[i]
            reference = etree.SubElement(element, self.TAG.reference)
            reference.set(self.ATTRIBUTE.field, r.field)
            reference.set(self.ATTRIBUTE.resource, r.table)
            if show_ids:
                reference.set(self.ATTRIBUTE.id, self.xml_encode(str(r.id)))
            if r.uid:
                reference.set(self.UID, r.uid )
                reference.text = r.text
            else:
                reference.set(self.ATTRIBUTE.value, r.value)
                # TODO: add in-line resource
            r.element = reference


    # -------------------------------------------------------------------------
    def gis_encode(self, rmap, download_url="", marker=None):

        """ GIS-encodes location references

            @param rmap: list of references to encode
            @param download_url: download URL of this instance
            @param marker: filename to override filenames in marker URLs

        """

        if not self.gis:
            return

        db = self.db

        references = filter(lambda r:
                            r.element is not None and \
                            self.Lat in self.db[r.table].fields and \
                            self.Lon in self.db[r.table].fields,
                            rmap)

        for i in xrange(0, len(references)):
            r = references[i]
            ktable = db[r.table]
            LatLon = db(ktable.id == r.id).select(ktable[self.Lat],
                                                  ktable[self.Lon],
                                                  #ktable[self.FeatureClass],
                                                  limitby=(0, 1))
            if LatLon:
                LatLon = LatLon.first()
                if LatLon[self.Lat] is not None and \
                   LatLon[self.Lon] is not None:
                    r.element.set(self.ATTRIBUTE.lat,
                                  self.xml_encode("%.6f" % LatLon[self.Lat]))
                    r.element.set(self.ATTRIBUTE.lon,
                                  self.xml_encode("%.6f" % LatLon[self.Lon]))
                    # Lookup Marker (Icon)
                    if marker:
                        marker_url = "%s/gis_marker.image.%s.png" % \
                                     (download_url, marker)
                    else:
                        marker = self.gis.get_marker(r.value)
                        marker_url = "%s/%s" % (download_url, marker)
                    r.element.set(self.ATTRIBUTE.marker,
                                  self.xml_encode(marker_url))
                    # Lookup GPS Marker
                    # @ToDo Fix for new FeatureClass
                    symbol = None
                    #if LatLon[self.FeatureClass]:
                    #    fctbl = db.gis_feature_class
                    #    query = (fctbl.id == str(LatLon[self.FeatureClass]))
                    #    try:
                    #        symbol = db(query).select(fctbl.gps_marker,
                    #                    limitby=(0, 1)).first().gps_marker
                    #    except:
                    #        pass
                    if not symbol:
                        symbol = "White Dot"
                    r.element.set(self.ATTRIBUTE.sym,
                                  self.xml_encode(symbol))


    # -------------------------------------------------------------------------
    def element(self, table, record,
                fields=[],
                url=None,
                download_url=None,
                marker=None):

        """ Creates an element from a Storage() record

            @param table: the database table
            @param record: the record
            @param fields: list of field names to include
            @param url: URL of the record
            @param download_url: download URL of the current instance
            @param marker: filename of the marker to override
                marker URLs in location references

        """

        if not download_url:
            download_url = ""

        resource = etree.Element(self.TAG.resource)
        resource.set(self.ATTRIBUTE.name, table._tablename)

        if self.UID in table.fields and self.UID in record:
            _value = str(table[self.UID].formatter(record[self.UID]))
            if self.domain_mapping:
                value = self.export_uid(_value)
            resource.set(self.UID, self.xml_encode(value))
            if table._tablename == "gis_location" and self.gis:
                # Look up the marker to display
                marker = self.gis.get_marker(_value)
                marker_url = "%s/%s" % (download_url, marker)
                resource.set(self.ATTRIBUTE.marker,
                                self.xml_encode(marker_url))
                # Look up the GPS Marker
                symbol = None
                try:
                    db = self.db
                    query = (db.gis_feature_class.id == record.feature_class_id)
                    symbol = db(query).select(limitby=(0, 1)).first().gps_marker
                except:
                    # No Feature Class
                    pass
                if not symbol:
                    symbol = "White Dot"
                resource.set(self.ATTRIBUTE.sym, self.xml_encode(symbol))

        for i in xrange(0, len(fields)):
            f = fields[i]
            v = record.get(f, None)
            if f == self.MCI and v is None:
                v = 0
            if f not in table.fields or v is None:
                continue

            text = value = self.xml_encode(
                           str(table[f].formatter(v)).decode("utf-8"))

            if table[f].represent:
                text = self.represent(table, f, v)

            fieldtype = str(table[f].type)

            if f in self.FIELDS_TO_ATTRIBUTES:
                if f == self.MCI:
                    resource.set(self.MCI, str(int(v) + 1))
                else:
                    resource.set(f, text)

            elif fieldtype == "upload":
                data = etree.SubElement(resource, self.TAG.data)
                data.set(self.ATTRIBUTE.field, f)
                fileurl = self.xml_encode("%s/%s" % (download_url, value))
                filename = self.xml_encode(value)
                data.set(self.ATTRIBUTE.url, fileurl)
                data.set(self.ATTRIBUTE.filename, filename)

            elif fieldtype == "password":
                # Do not export password fields
                continue

            elif fieldtype == "blob":
                # Not implemented yet
                continue

            else:
                data = etree.SubElement(resource, self.TAG.data)
                data.set(self.ATTRIBUTE.field, f)
                if table[f].represent:
                    data.set(self.ATTRIBUTE.value, value )
                data.text = text

        if url:
            resource.set(self.ATTRIBUTE.url, url)

        return resource


    # Data import =============================================================

    def select_resources(self, tree, tablename):

        """ Selects resources from an element tree

            @param tree: the element tree
            @param tablename: table name to search for

        """

        resources = []

        if isinstance(tree, etree._ElementTree):
            root = tree.getroot()
            if not root.tag == self.TAG.root:
                return resources
        else:
            root = tree

        if root is None or not len(root):
            return resources

        expr = './%s[@%s="%s"]' % (
               self.TAG.resource,
               self.ATTRIBUTE.name,
               tablename)

        resources = root.xpath(expr)
        return resources


    # -------------------------------------------------------------------------
    def lookahead(self, table, element, fields, tree=None, directory=None):

        """ Resolves references in XML resources

            @param table: the database table
            @param element: the element to resolve
            @param fields: fields to check for references
            @param tree: the element tree of the input source
            @param directory: the resource directory of the input tree

        """

        reference_list = []
        references = element.findall("reference")

        for r in references:
            field = r.get(self.ATTRIBUTE.field, None)
            if field and field in fields:
                resource = r.get(self.ATTRIBUTE.resource, None)
                if not resource:
                    continue
                table = self.db.get(resource, None)
                if not table:
                    continue

                id = None
                _uid = uid = r.get(self.UID, None)
                entry = None

                # If no UUID, try to find the reference in-line
                relement = None
                if not uid:
                    expr = './/%s[@%s="%s"]' % (
                        self.TAG.resource,
                        self.ATTRIBUTE.name, resource)
                    relements = r.xpath(expr)
                    if relements:
                        relement = relements[0]
                        _uid = uid = r.get(self.UID, None)

                if uid:
                    if self.domain_mapping:
                        uid = self.import_uid(uid)

                    # Check if this resource is already in the directory:
                    entry = None
                    if directory is not None and resource in directory:
                        entry = directory[resource].get(uid, None)

                    # Otherwise:
                    if not entry:
                        # Find the corresponding element in the tree
                        if tree and not relement:
                            expr = './/%s[@%s="%s" and @%s="%s"]' % (
                                   self.TAG.resource,
                                   self.ATTRIBUTE.name, resource,
                                   self.UID, _uid)
                            relements = tree.getroot().xpath(expr)
                            if relements:
                                relement = relements[0]

                        # Find the corresponding table record
                        if self.UID in table:
                            set = self.db(table[self.UID] == uid)
                            record = set.select(table.id, limitby=(0, 1)).first()
                            if record:
                                id = record.id

                # Update the entry
                if not entry:
                    entry = dict(vector=None)
                entry.update(resource=resource, element=relement, uid=uid, id=id)

                if uid:
                    # Add this entry to the directory
                    if directory is not None:
                        if resource not in directory:
                            directory[resource] = {}
                        if _uid not in directory[resource]:
                            directory[resource][uid] = entry

                # Add this entry to the reference list
                reference_list.append(Storage(field=field, entry=entry))

        return reference_list


    # -------------------------------------------------------------------------
    def record(self, table, element, original=None, files=[], validate=None, skip=[]):

        """ Creates a Storage() record from an element and validates it

            @param table: the database table
            @param element: the element
            @param validate: validate hook (function to validate fields)
            @param skip: fields to skip

        """

        valid = True
        record = Storage()

        if self.UID in table.fields and self.UID not in skip:
            uid = element.get(self.UID, None)
            if uid:
                if self.domain_mapping:
                    uid = self.import_uid(uid)
                record[self.UID] = uid

        for f in self.ATTRIBUTES_TO_FIELDS:
            if f in self.IGNORE_FIELDS or f in skip:
                continue
            if f in table.fields:
                v = value = self.xml_decode(element.get(f, None))
                if value is not None:
                    if validate is not None:
                        if not isinstance(value, (str, unicode)):
                            v = str(value)
                        (value, error) = validate(table, original, f, v)
                        if error:
                            element.set(self.ATTRIBUTE.error,
                                        "%s: %s" % (f, error))
                            valid = False
                            continue
                    record[f]=value

        for child in element:
            if child.tag == self.TAG.data:
                f = child.get(self.ATTRIBUTE.field, None)
                if not f or f not in table.fields:
                    continue
                if f in self.IGNORE_FIELDS or f in skip:
                    continue

                field_type = str(table[f].type)
                if field_type in ("id", "blob", "password"):
                    continue
                elif field_type == "upload":
                    # Handling of uploads
                    download_url = child.get(self.ATTRIBUTE.url, None)
                    filename = child.get(self.ATTRIBUTE.filename, None)
                    file = None
                    if filename:
                        if filename in files:
                            file = files[filename]
                        elif download_url:
                            # Try to download the file
                            import urllib
                            try:
                                file = urllib.urlopen(download_url)
                            except IOError:
                                pass
                        if file:
                            field = table[f]
                            value = field.store(file, filename)
                        else:
                            continue
                    elif filename is not None:
                        value = ""
                else:
                    value = child.get(self.ATTRIBUTE.value, None)
                    value = self.xml_decode(value)

                if field_type == 'boolean':
                    if value and value in ["True", "true"]:
                        value = True
                    else:
                        value = False
                if value is None:
                    value = self.xml_decode(child.text)
                if value == "" and not field_type == "string":
                    value = None
                if value is None:
                    value = table[f].default
                if value is None and field_type == "string":
                    value = ""

                if value is not None:
                    if validate is not None:
                        if not isinstance(value, basestring):
                            v = str(value)
                        else:
                            v = value
                        (value, error) = validate(table, original, f, v)
                        child.set(self.ATTRIBUTE.value, v)
                        if error:
                            child.set(self.ATTRIBUTE.error, "%s: %s" % (f, error))
                            valid = False
                            continue
                    record[f] = value

        if valid:
            return record
        else:
            return None


    # Data model helpers ======================================================

    def get_field_options(self, table, fieldname):

        """ Get options of a field as <select> """

        select = etree.Element(self.TAG.select)

        if fieldname in table.fields:
            field = table[fieldname]
        else:
            return select

        requires = field.requires
        select.set(self.ATTRIBUTE.id, "%s_%s" % (table._tablename, fieldname))
        select.set(self.ATTRIBUTE.name, fieldname)

        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            r = requires[0]
            options = []
            if isinstance(r, (IS_NULL_OR, IS_EMPTY_OR)) and hasattr(r.other, "options"):
                options = r.other.options()
            elif hasattr(r, "options"):
                options = r.options()
            for (value, text) in options:
                value = self.xml_encode(str(value).decode("utf-8"))
                text = self.xml_encode(str(text).decode("utf-8"))
                option = etree.SubElement(select, self.TAG.option)
                option.set(self.ATTRIBUTE.value, value)
                option.text = text

        return select


    # -------------------------------------------------------------------------
    def get_options(self, prefix, name, fields=None):

        """ Get options of option fields in a table as <select>s """

        db = self.db
        tablename = "%s_%s" % (prefix, name)
        table = db.get(tablename, None)

        options = etree.Element(self.TAG.options)

        if fields:
            if not isinstance(fields, (list, tuple)):
                fields = [fields]
            if len(fields) == 1:
                return(self.get_field_options(table, fields[0]))

        if table:
            options.set(self.ATTRIBUTE.resource, tablename)
            for f in table.fields:
                if fields and f not in fields:
                    continue
                select = self.get_field_options(table, f)
                if select is not None and len(select):
                    options.append(select)

        return options


    # -------------------------------------------------------------------------
    def get_fields(self, prefix, name):

        """ Get fields in a table as <fields> element """

        db = self.db
        tablename = "%s_%s" % (prefix, name)
        table = db.get(tablename, None)

        fields = etree.Element(self.TAG.fields)

        if table:
            fields.set(self.ATTRIBUTE.resource, tablename)
            for f in table.fields:
                field = etree.Element(self.TAG.field)
                field.set(self.ATTRIBUTE.name, self.xml_encode(f))
                ftype = str(table[f].type)
                field.set(self.ATTRIBUTE.type, self.xml_encode(ftype))
                readable = table[f].readable
                writable = table[f].writable
                field.set(self.ATTRIBUTE.readable, str(readable))
                field.set(self.ATTRIBUTE.writable, str(writable))
                options = self.get_field_options(table, f)
                field.set(self.ATTRIBUTE.has_options,
                          str(len(options) and True or False))
                fields.append(field)

        return fields


    # JSON toolkit ============================================================

    def __json2element(self, key, value, native=False):

        """ Converts a data field from JSON into an element

            @param key: key (field name)
            @param value: value for the field
            @param native: use native mode
            @type native: bool

        """

        if isinstance(value, dict):
            return self.__obj2element(key, value, native=native)

        elif isinstance(value, (list, tuple)):
            if not key == self.TAG.item:
                _list = etree.Element(key)
            else:
                _list = etree.Element(self.TAG.list)
            for obj in value:
                item = self.__json2element(self.TAG.item, obj,
                                           native=native)
                _list.append(item)
            return _list

        else:
            if native:
                element = etree.Element(self.TAG.data)
                element.set(self.ATTRIBUTE.field, key)
            else:
                element = etree.Element(key)
            if not isinstance(value, (str, unicode)):
                value = str(value)
            element.text = self.xml_encode(value)
            return element


    # -------------------------------------------------------------------------
    def __obj2element(self, tag, obj, native=False):

        """ Converts a JSON object into an element

            @param tag: tag name for the element
            @param obj: the JSON object
            @param native: use native mode for attributes

        """

        prefix = name = resource = field = None

        if not tag:
            tag = self.TAG.object

        elif native:
            if tag.startswith(self.PREFIX.reference):
                field = tag[len(self.PREFIX.reference) + 1:]
                tag = self.TAG.reference
            elif tag.startswith(self.PREFIX.options):
                resource = tag[len(self.PREFIX.options) + 1:]
                tag = self.TAG.options
            elif tag.startswith(self.PREFIX.resource):
                resource = tag[len(self.PREFIX.resource) + 1:]
                tag = self.TAG.resource
            elif not tag == self.TAG.root:
                field = tag
                tag = self.TAG.data

        element = etree.Element(tag)

        if native:
            if resource:
                if tag == self.TAG.resource:
                    element.set(self.ATTRIBUTE.name, resource)
                else:
                    element.set(self.ATTRIBUTE.resource, resource)
            if field:
                element.set(self.ATTRIBUTE.field, field)

        for k in obj:
            m = obj[k]
            if isinstance(m, dict):
                child = self.__obj2element(k, m, native=native)
                element.append(child)
            elif isinstance(m, (list, tuple)):
                #l = etree.SubElement(element, k)
                for _obj in m:
                    child = self.__json2element(k, _obj, native=native)
                    element.append(child)
            else:
                if k == self.PREFIX.text:
                    element.text = self.xml_encode(m)
                elif k.startswith(self.PREFIX.attribute):
                    a = k[len(self.PREFIX.attribute):]
                    element.set(a, self.xml_encode(m))
                else:
                    child = self.__json2element(k, m, native=native)
                    element.append(child)

        return element


    # -------------------------------------------------------------------------
    def json2tree(self, source, format=None):

        """ Converts JSON into an element tree

            @param source: the JSON source
            @param format: name of the XML root element

        """

        try:
            root_dict = json.load(source)
        except (ValueError,):
            e = sys.exc_info()[1]
            raise HTTP(400, body=self.json_message(False, 400, e))

        native=False

        if not format:
            format=self.TAG.root
            native=True

        if root_dict and isinstance(root_dict, dict):
            root = self.__obj2element(format, root_dict, native=native)
            if root:
                return etree.ElementTree(root)

        return None


    # -------------------------------------------------------------------------
    def __element2json(self, element, native=False):

        """ Converts an element into JSON

            @param element: the element
            @param native: use native mode for attributes

        """

        if element.tag == self.TAG.list:
            obj = []
            for child in element:
                tag = child.tag
                if tag[0] == "{":
                    tag = tag.rsplit("}",1)[1]
                child_obj = self.__element2json(child, native=native)
                if child_obj:
                    obj.append(child_obj)
            return obj
        else:
            obj = {}
            for child in element:
                tag = child.tag
                if tag[0] == "{":
                    tag = tag.rsplit("}",1)[1]
                collapse = True
                if native:
                    if tag == self.TAG.resource:
                        resource = child.get(self.ATTRIBUTE.name)
                        tag = "%s_%s" % (self.PREFIX.resource, resource)
                        collapse = False
                    elif tag == self.TAG.options:
                        resource = child.get(self.ATTRIBUTE.resource)
                        tag = "%s_%s" % (self.PREFIX.options, resource)
                    elif tag == self.TAG.reference:
                        tag = "%s_%s" % (self.PREFIX.reference,
                                         child.get(self.ATTRIBUTE.field))
                    elif tag == self.TAG.data:
                        tag = child.get(self.ATTRIBUTE.field)
                child_obj = self.__element2json(child, native=native)
                if child_obj:
                    if not tag in obj:
                        if isinstance(child_obj, list) or not collapse:
                            obj[tag] = [child_obj]
                        else:
                            obj[tag] = child_obj
                    else:
                        if not isinstance(obj[tag], list):
                            obj[tag] = [obj[tag]]
                        obj[tag].append(child_obj)

            attributes = element.attrib
            for a in attributes:
                if native:
                    if a == self.ATTRIBUTE.name and \
                       element.tag == self.TAG.resource:
                        continue
                    if a == self.ATTRIBUTE.resource and \
                       element.tag == self.TAG.options:
                        continue
                    if a == self.ATTRIBUTE.field and \
                    element.tag in (self.TAG.data, self.TAG.reference):
                        continue
                obj[self.PREFIX.attribute + a] = \
                    self.xml_decode(attributes[a])

            if element.text:
                obj[self.PREFIX.text] = self.xml_decode(element.text)

            if len(obj) == 1 and obj.keys()[0] in \
               (self.PREFIX.text, self.TAG.item, self.TAG.list):
                obj = obj[obj.keys()[0]]

            return obj


    # -------------------------------------------------------------------------
    def tree2json(self, tree, pretty_print=False):

        """ Converts an element tree into JSON

            @param tree: the element tree
            @param pretty_print: provide pretty formatted output

        """

        root = tree.getroot()

        if root.tag == self.TAG.root:
            native = True
        else:
            native = False

        root_dict = self.__element2json(root, native=native)

        if pretty_print:
            js = json.dumps(root_dict, indent=4)
            return "\n".join([l.rstrip() for l in js.splitlines()])
        else:
            return json.dumps(root_dict)


    # -------------------------------------------------------------------------
    def json_message(self,
                     success=True,
                     status_code="200",
                     message=None,
                     tree=None):

        """ Provide a nicely-formatted JSON Message

            @param success: action succeeded or failed
            @param status_code: the HTTP status code
            @param message: the message text
            @param tree: result tree to enclose

        """

        if success:
            status='"status": "success"'
        else:
            status='"status": "failed"'

        code = '"statuscode": "%s"' % status_code

        if not success:
            if message:
                return '{%s, %s, "message": "%s", "tree": %s }' % \
                       (status, code, message, tree)
            else:
                return '{%s, %s, "tree": %s }' % \
                       (status, code, tree)
        else:
            if message:
                return '{%s, %s, "message": "%s"}' % \
                       (status, code, message)
            else:
                return '{%s, %s}' % \
                       (status, code)

# *****************************************************************************
