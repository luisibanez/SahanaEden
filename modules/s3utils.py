# -*- coding: utf-8 -*-

"""
    Sahana Eden Utilities Module

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Fran Boon <fran@aidiq.com>
    @author: Michael Howden (michael@aidiq.com)
    @copyright: (c) 2010 Sahana Software Foundation
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

import re

# Modified versions of URL from gluon/html.py
# we need simplified versions for our jquery functions
def URL2(a=None, c=None, r=None):
    """
    example:

    >>> URL(a="a",c="c")
    "/a/c"

    generates a url "/a/c" corresponding to application a & controller c
    If r=request is passed, a & c are set, respectively,
    to r.application, r.controller

    The more typical usage is:

    URL(r=request) that generates a base url with the present application and controller.

    The function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a
    if c:
        controller = c
    if not (application and controller):
        raise SyntaxError, "not enough information to build the url"
    #other = ""
    url = "/%s/%s" % (application, controller)
    return url

def URL3(a=None, r=None):
    """
    example:

    >>> URL(a="a")
    "/a"

    generates a url "/a" corresponding to application a
    If r=request is passed, a is set
    to r.application

    The more typical usage is:

    URL(r=request) that generates a base url with the present application.

    The controller & function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a
    if not (application and controller):
        raise SyntaxError, "not enough information to build the url"
    #other = ""
    url = "/%s" % application
    return url

# Copied from Selenium Plone Tool
def getBrowserName(userAgent):
    "Determine which browser is being used."
    if userAgent.find("MSIE") > -1:
        return "IE"
    elif userAgent.find("Firefox") > -1:
        return "Firefox"
    elif userAgent.find("Gecko") > -1:
        return "Mozilla"
    else:
        return "Unknown"

# shn_get_db_field_value -----------------------------------------------------
def shn_split_multi_value(value):
    """
    @author: Michael Howden (michael@aidiq.com)

    Converts a series of numbers delimited by |, or already in a string into a list

    If value = None, returns []
    """

    if not value:
        return []

    elif isinstance(value, ( str ) ):   
        if "[" in value:
            #Remove internal lists
            value = value.replace("[", "")
            value = value.replace("]", "")
            value = value.replace("'", "")
            value = value.replace('"', "")
            return eval("[" + value + "]")  
        else:
            return re.compile('[\w\-:]+').findall(str(value))  
    else:
        return [str(value)]
# shn_get_db_field_value -----------------------------------------------------
def shn_get_db_field_value(db,
                           table,
                           field,
                           look_up,
                           look_up_field = "id",
                           match_case = True):
    """
    @author: Michael Howden (michael@aidiq.com)

    @description:
        returns the value of <field> from the first record in <table_name>
        with <look_up_field> = <look_up>

    @arguements:
        table - string - The name of the table
        field - string - the field to find the value from
        look_up - string - the value to find
        look_up_field - string - the field to find <look_up> in
        match_case - bool

    @returns:
        Field Value if there is a record
        None - if there is no matching record

    @example
        shn_get_db_field_value("or_organisation",
                               "id",
                               look_up = "UNDP",
                               look_up_field = "name" )
    """
    if match_case or db[table][look_up_field].type != "string":
        row = db(db[table][look_up_field] == look_up).select(field, limitby = [0, 1]).first()
    else:
       row = db(db[table][look_up_field].lower() == look_up).select(field, limitby = [0, 1]).first()

    if row:
        return row[field]
    else:
        return None
