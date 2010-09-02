# -*- coding: utf-8 -*-

"""
    VITA Sahana-Eden Person Data Toolkit

    @version: 0.5

    @author: nursix
    @copyright: 2010 (c) Sahana Software Foundation
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

from gluon.storage import Storage

__all__ = ["S3Vita",]

# *****************************************************************************
class S3Vita(object):

    """ Toolkit for Person Identification, Tracking and Tracing """

    # -------------------------------------------------------------------------
    def __init__(self, environment, db=None, T=None):

        self.environment = Storage(environment)
        self.db = db

        if T:
            self.T = T
        elif "T" in self.environment:
            self.T = self.environment["T"]

        # -------------------------------------------------------------------------
        #: Trackable entity types
        self.trackable_types = {
            1:self.T("Person"),          # an individual
            2:self.T("Group"),           # a group
            3:self.T("Body"),            # a dead body or body part
            4:self.T("Object"),          # other objects belonging to persons
            5:self.T("Organisation"),    # an organisation
            6:self.T("Office"),          # an office
        }
        self.DEFAULT_TRACKABLE = 1

        # -------------------------------------------------------------------------
        #: Presence Conditions
        self.presence_conditions = {
            1:self.T("Check-In"),        # Arriving at a location for accommodation/storage
            2:self.T("Reconfirmation"),  # Reconfirmation of accomodation/storage at a location
            3:self.T("Check-Out"),       # Leaving from a location after accommodation/storage
            4:self.T("Found"),           # Temporarily at a location
            5:self.T("Procedure"),       # Temporarily at a location for a procedure (checkpoint)
            6:self.T("Transit"),         # Temporarily at a location between two transfers
            7:self.T("Transfer"),        # On the way from one location to another
            8:self.T("Missing"),         # Been at a location, and missing from there
            9:self.T("Lost")             # Been at a location, and destroyed/disposed/deceased there
        }
        self.DEFAULT_PRESENCE = 4

    # -------------------------------------------------------------------------
    def pentity(self, entity):

        """ Get the PersonEntity record for the given ID, ID label, sub-entity
            or related record

        """

        table = self.db.pr_pentity

        if entity:

            query = (table.deleted==False)

            if isinstance(entity, (int, long)) or \
               (isinstance(entity, str) and entity.strip().isdigit()):
                query = (table.id == entity) & query

            elif isinstance(entity, str):
                query = (table.label.strip().lower() == entity.strip().lower()) & query

            elif isinstance(entity, dict):
                if "pe_id" in entity:
                    query = (table.id == entity.pe_id) & query
                else:
                    return entity # entity already given?

            else:
                return None

            try:
                record = self.db(query).select(table.ALL, limitby=(0, 1)).first()
                return record
            except:
                return None

        else:
            return None

    # -------------------------------------------------------------------------
    def person(self, entity):

        """ Get the Person record for the given ID, PersonEntity record or
            Person-related record

        """

        table = self.db.pr_person

        if entity:

            query = (table.deleted==False)

            if isinstance(entity, (int, long)) or \
               (isinstance(entity, str) and entity.strip().isdigit()):
                query = (table.id == entity) & query

            elif isinstance(entity, dict):
                if "pe_id" in entity:
                    query = (table.pe_id == entity.pe_id) & query
                elif "person_id" in entity:
                    query = (table.id == entity.person_id) & query
                elif "id" in entity:
                    query = (table.pe_id == entity.id) & query
                else:
                    return None

            else:
                return None

            try:
                record = self.db(query).select(table.ALL, limitby=(0, 1)).first()
                return record
            except:
                return None

        else:
            return None

    # -------------------------------------------------------------------------
    def group(self, entity):

        """ Get the Group record for the given ID, PersonEntity record or
            Group-related record

        """

        table = self.db.pr_group

        if entity:

            query = (table.deleted == False)

            if isinstance(entity, (int, long)) or \
               (isinstance(entity, str) and entity.strip().isdigit()):
                query = (table.id == entity) & query

            elif isinstance(entity, dict):
                if "pe_id" in entity:
                    query = (table.pe_id == entity.pe_id) & query
                elif "group_id" in entity:
                    query = (table.id == entity.group_id) & query
                elif "id" in entity:
                    query = (table.pe_id == entity.id) & query
                else:
                    return None

            else:
                return None

            try:
                record = self.db(query).select(table.ALL, limitby=(0, 1)).first()
                return record
            except:
                return None

        else:
            return None


    # -------------------------------------------------------------------------
    def fullname(self, record):

        """ Returns the full name of a person

        """

        if record:
            fname, mname, lname = "", "", ""
            if record.first_name:
                fname = "%s " % record.first_name.strip()
            if record.middle_name:
                mname = "%s " % record.middle_name.strip()
            if record.last_name:
                lname = record.last_name.strip()

            if mname.isspace():
                return "%s%s" % (fname, lname)
            else:
                return "%s%s%s" % (fname, mname, lname)
        else:
            return ""

    # -------------------------------------------------------------------------
    def rlevenshtein(self, str1, str2):

        """ Returns a relative value for the Levenshtein distance of two strings

            Levenshtein distance:
            Number of character insertions/deletions/replacements necessary to
            morph one string into the other. Here calculated in relation to the
            maximum string length, hence 0.0 for identical and 1.0 for completely
            different strings.

            Note: Unfortunately, this doesn't work in SQL queries :(

        """

        matrix = {}
        l1 = len(str1)
        l2 = len(str2)

        for i in range(0, l1+1): matrix[i, 0] = i
        for j in range(0, l2+1): matrix[0, j] = j

        for i in range(1, l1+1):
            for j in range(1, l2+1):
                x = matrix[i-1, j] + 1
                y = matrix[i, j-1] + 1

                if str1[i-1] == str2[j-1]:
                    z = matrix[i-1, j-1]
                else:
                    z = matrix[i-1, j-1] + 1

                matrix[i, j] = min(x, y, z)

        return float(matrix[l1, l2]) / float(max(l1, l2))

#
# *****************************************************************************
