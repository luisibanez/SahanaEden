# -*- coding: utf-8 -*-

"""
    Sahana Eden Tools Module

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Fran Boon <francisboon@gmail.com>
    @author: sunneach
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

__name__ = "S3TOOLS"

__all__ = ["AuthS3", "CrudS3", "FieldS3"]

#import datetime
import re
import urllib
import uuid

from gluon.html import *
from gluon.http import HTTP, redirect
from gluon.storage import Storage, Messages
from gluon.validators import *
#try:
#    from gluon.contrib.gql import Field, Row, Query
#except ImportError:
from gluon.sql import Field, Row, Query
from gluon.sqlhtml import SQLFORM
from gluon.tools import Auth
from gluon.tools import Crud

DEFAULT = lambda: None
table_field = re.compile("[\w_]+\.[\w_]+")

class AuthS3(Auth):
    """
        Extended version of Auth from gluon/tools.py
        - override:
            login()
            register()
            requires_membership()
        - add
            shn_has_role()
            shn_has_permission()
            shn_accessible_query()
            shn_register() callback
            shn_link_to_person()
        - language
    """

    def __init__(self, environment, deployment_settings, db=None):

        """ Initialise parent class & make any necessary modifications """

        Auth.__init__(self, environment, db)

        self.deployment_settings = deployment_settings
        self.session = self.environment.session

        self.settings.lock_keys = False
        self.settings.username_field = False
        self.settings.lock_keys = True
        self.messages.lock_keys = False
        self.messages.email_sent = 'Verification Email sent - please check your email to validate. If you do not receive this email please check you junk email or spam filters'
        self.messages.email_verified = 'Email verified - you can now login'
        self.messages.registration_disabled = "Registration Disabled!"
        self.messages.lock_keys = True

    def __get_migrate(self, tablename, migrate=True):

        if type(migrate).__name__ == "str":
            return (migrate + tablename + ".table")
        elif migrate == False:
            return False
        else:
            return True

    def define_tables(self, migrate=True):
        """
        to be called unless tables are defined manually

        usages::

            # defines all needed tables and table files
            # UUID + "_auth_user.table", ...
            auth.define_tables()

            # defines all needed tables and table files
            # "myprefix_auth_user.table", ...
            auth.define_tables(migrate="myprefix_")

            # defines all needed tables without migration/table files
            auth.define_tables(migrate=False)

        """

        db = self.db
        request = self.environment.request
        if not self.settings.table_user:
            passfield = self.settings.password_field
            if self.settings.username_field:
                self.settings.table_user = db.define_table(
                    self.settings.table_user_name,
                    Field("first_name", length=128, default="",
                            label=self.messages.label_first_name),
                    Field("last_name", length=128, default="",
                            label=self.messages.label_last_name),
                    Field("person_uuid", length=64, default="",
                             readable=False, writable=False),
                    # TODO:
                    #   - Needs Validation if possible
                    #Field("mobile_phone", length=32, default=""),
                    # add UTC Offset (+/-HHMM) to specify the user's timezone
                    # TODO:
                    #   - this could need a nice label and context help
                    #   - entering timezone from a drop-down would be more comfortable
                    #   - automatic DST adjustment could be nice
                    Field("utc_offset", length=16, default="UTC +0000", readable=False, writable=False),
                    Field("username", length=128, default=""),
                    Field("language", length=16),
                    Field("email", length=512, default="",
                            label=self.messages.label_email),
                    Field(passfield, "password", length=512,
                             readable=False, label=self.messages.label_password),
                    Field("registration_key", length=512,
                            writable=False, readable=False, default="",
                            label=self.messages.label_registration_key),
                    Field("reset_password_key", length=512,
                            writable=False, readable=False, default="",
                            label=self.messages.label_registration_key),
                    Field("timestmp", "datetime", writable=False,
                            readable=False, default=""),
                    migrate=\
                        self.__get_migrate(self.settings.table_user_name, migrate))
            else:
                self.settings.table_user = db.define_table(
                    self.settings.table_user_name,
                    Field("first_name", length=128, default="",
                            label=self.messages.label_first_name),
                    Field("last_name", length=128, default="",
                            label=self.messages.label_last_name),
                    Field("person_uuid", length=64, default="",
                             readable=False, writable=False),
                    #Field("mobile_phone", length=32, default=""),
                    # add UTC Offset (+/-HHMM) to specify the user's timezone
                    # TODO:
                    #   - this could need a nice label and context help
                    #   - entering timezone from a drop-down would be more comfortable
                    #   - automatic DST adjustment could be nice
                    Field("utc_offset", length=16, default="UTC +0000", readable=False, writable=False),
                    #Field("username", length=128, default=""),
                    Field("language", length=16),
                    Field("email", length=512, default="",
                            label=self.messages.label_email),
                    Field(passfield, "password", length=512,
                             readable=False, label=self.messages.label_password),
                    Field("registration_key", length=512,
                            writable=False, readable=False, default="",
                            label=self.messages.label_registration_key),
                    Field("reset_password_key", length=512,
                            writable=False, readable=False, default="",
                            label=self.messages.label_registration_key),
                    Field("timestmp", "datetime", writable=False,
                            readable=False, default=""),
                    migrate=\
                        self.__get_migrate(self.settings.table_user_name, migrate))
            table = self.settings.table_user
            table.first_name.requires = \
                IS_NOT_EMPTY(error_message=self.messages.is_empty)
            table.last_name.requires = \
                IS_NOT_EMPTY(error_message=self.messages.is_empty)
            table.utc_offset.label = "UTC Offset"
            table.utc_offset.comment = A(SPAN("[Help]"), _class="tooltip", _title="UTC Offset|The time difference between UTC and your timezone, specify as +HHMM for eastern or -HHMM for western timezones.")
            try:
                #from applications.eden.modules.validators import IS_UTC_OFFSET
                #validators = local_import("validators")
                exec("from applications.%s.modules.validators import IS_UTC_OFFSET" % request.application)
                table.utc_offset.requires = IS_UTC_OFFSET()
            except:
                pass
            table[passfield].requires = [CRYPT(key=self.settings.hmac_key, digest_alg="sha512")]
            if self.settings.username_field:
                table.username.requires = IS_NOT_IN_DB(db, "%s.username" % self.settings.table_user._tablename)
            table.email.requires = \
                [IS_EMAIL(error_message=self.messages.invalid_email),
                 IS_NOT_IN_DB(db, "%s.email"
                     % self.settings.table_user._tablename)]
            table.registration_key.default = ""
        if not self.settings.table_group:
            self.settings.table_group = db.define_table(
                self.settings.table_group_name,
                Field("role", length=512, default="",
                        label=self.messages.label_role),
                Field("description", "text",
                        label=self.messages.label_description),
                migrate=self.__get_migrate(
                    self.settings.table_group_name, migrate))
            table = self.settings.table_group
            table.role.requires = IS_NOT_IN_DB(db, "%s.role"
                 % self.settings.table_group._tablename)
        if not self.settings.table_membership:
            self.settings.table_membership = db.define_table(
                self.settings.table_membership_name,
                Field("user_id", self.settings.table_user,
                        label=self.messages.label_user_id),
                Field("group_id", self.settings.table_group,
                        label=self.messages.label_group_id),
                migrate=self.__get_migrate(
                    self.settings.table_membership_name, migrate))
            table = self.settings.table_membership
            table.user_id.requires = IS_IN_DB(db, "%s.id" %
                    self.settings.table_user._tablename,
                    "%(id)s: %(first_name)s %(last_name)s")
            table.group_id.requires = IS_IN_DB(db, "%s.id" %
                    self.settings.table_group._tablename,
                    "%(id)s: %(role)s")
        if not self.settings.table_permission:
            self.settings.table_permission = db.define_table(
                self.settings.table_permission_name,
                Field("group_id", self.settings.table_group,
                        label=self.messages.label_group_id),
                Field("name", default="default", length=512,
                        label=self.messages.label_name),
                Field("table_name", length=512,
                        label=self.messages.label_table_name),
                Field("record_id", "integer",
                        label=self.messages.label_record_id),
                migrate=self.__get_migrate(
                    self.settings.table_permission_name, migrate))
            table = self.settings.table_permission
            table.group_id.requires = IS_IN_DB(db, "%s.id" %
                    self.settings.table_group._tablename,
                    "%(id)s: %(role)s")
            table.name.requires = IS_NOT_EMPTY()
            table.table_name.requires = IS_IN_SET(self.db.tables)
            table.record_id.requires = IS_INT_IN_RANGE(0, 10 ** 9)
        if not self.settings.table_event:
            self.settings.table_event = db.define_table(
                self.settings.table_event_name,
                Field("time_stamp", "datetime",
                        default=self.environment.request.now,
                        label=self.messages.label_time_stamp),
                Field("client_ip",
                        default=self.environment.request.client,
                        label=self.messages.label_client_ip),
                Field("user_id", self.settings.table_user, default=None,
                        label=self.messages.label_user_id),
                Field("origin", default="auth", length=512,
                        label=self.messages.label_origin),
                Field("description", "text", default="",
                        label=self.messages.label_description),
                migrate=self.__get_migrate(
                    self.settings.table_event_name, migrate))
            table = self.settings.table_event
            table.user_id.requires = IS_IN_DB(db, "%s.id" %
                    self.settings.table_user._tablename,
                    "%(id)s: %(first_name)s %(last_name)s")
            table.origin.requires = IS_NOT_EMPTY()
            table.description.requires = IS_NOT_EMPTY()

    def login(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
        log=DEFAULT,
        ):
        """
            Overrides Web2Py's login() to use custom flash styles & utcnow

            returns a login form

            .. method:: Auth.login([next=DEFAULT [, onvalidation=DEFAULT
                [, onaccept=DEFAULT [, log=DEFAULT]]]])
        """

        table_user = self.settings.table_user
        if "username" in table_user.fields:
            username = "username"
        else:
            username = "email"
        old_requires = table_user[username].requires
        table_user[username].requires = IS_NOT_EMPTY()
        request = self.environment.request
        response = self.environment.response
        session = self.environment.session
        passfield = self.settings.password_field
        if next == DEFAULT:
            next = request.vars._next or self.settings.login_next
        if onvalidation == DEFAULT:
            onvalidation = self.settings.login_onvalidation
        if onaccept == DEFAULT:
            onaccept = self.settings.login_onaccept
        if log == DEFAULT:
            log = self.messages.login_log

        user = None # default

        # do we use our own login form, or from a central source?
        if self.settings.login_form == self:
            form = SQLFORM(
                table_user,
                fields=[username, passfield],
                hidden=dict(_next=request.vars._next),
                showid=self.settings.showid,
                submit_button=self.messages.submit_button,
                delete_label=self.messages.delete_label,
                )
            accepted_form = False
            if form.accepts(request.vars, session,
                            formname="login", dbio=False,
                            onvalidation=onvalidation):
                accepted_form = True
                # check for username in db
                users = self.db(table_user[username] == form.vars[username]).select()
                if users:
                    # user in db, check if registration pending or disabled
                    temp_user = users[0]
                    if temp_user.registration_key == "pending":
                        response.warning = self.messages.registration_pending
                        return form
                    elif temp_user.registration_key == "disabled":
                        response.error = self.messages.login_disabled
                        return form
                    elif temp_user.registration_key:
                        response.warning = \
                            self.messages.registration_verifying
                        return form
                    # try alternate logins 1st as these have the current version of the password
                    for login_method in self.settings.login_methods:
                        if login_method != self and \
                                login_method(request.vars[username],
                                             request.vars[passfield]):
                            if not self in self.settings.login_methods:
                                # do not store password in db
                                form.vars[passfield] = None
                            user = self.get_or_create_user(form.vars)
                            break
                    if not user:
                        # alternates have failed, maybe because service inaccessible
                        if self.settings.login_methods[0] == self:
                            # try logging in locally using cached credentials
                            if temp_user[passfield] == form.vars.get(passfield, ""):
                                # success
                                user = temp_user
                else:
                    # user not in db
                    if not self.settings.alternate_requires_registration:
                        # we're allowed to auto-register users from external systems
                        for login_method in self.settings.login_methods:
                            if login_method != self and \
                                    login_method(request.vars[username],
                                                 request.vars[passfield]):
                                if not self in self.settings.login_methods:
                                    # do not store password in db
                                    form.vars[passfield] = None
                                user = self.get_or_create_user(form.vars)
                                break
                if not user:
                    # invalid login
                    session.error = self.messages.invalid_login
                    redirect(self.url(args=request.args))
        else:
            # use a central authentication server
            cas = self.settings.login_form
            cas_user = cas.get_user()
            if cas_user:
                cas_user[passfield] = None
                user = self.get_or_create_user(cas_user)
            elif hasattr(cas, "login_form"):
                return cas.login_form()
            else:
                # we need to pass through login again before going on
                next = URL(r=request) + "?_next=" + next
                redirect(cas.login_url(next))

        # process authenticated users
        if user:
            user = Storage(table_user._filter_fields(user, id=True))
            session.auth = Storage(user=user, last_visit=request.now,
                                   expiration=self.settings.expiration)
            self.user = user
            session.confirmation = self.messages.logged_in
        if log and self.user:
            self.log_event(log % self.user)

        # how to continue
        if self.settings.login_form == self:
            if accepted_form:
                if onaccept:
                    onaccept(form)
                if isinstance(next, (list, tuple)):
                    # fix issue with 2.6
                    next = next[0]
                if next and not next[0] == "/" and next[:4] != "http":
                    next = self.url(next.replace("[id]", str(form.vars.id)))
                redirect(next)
            table_user[username].requires = old_requires
            return form
        else:
            redirect(next)

    def register(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
        log=DEFAULT,
        ):
        """
        Overrides Web2Py's register() to add new functionality:
            * Checks whether registration is permitted
            * Custom Flash styles
            * utcnow
            * Allow form to be embedded in other pages

        returns a registration form

        .. method:: Auth.register([next=DEFAULT [, onvalidation=DEFAULT
            [, onaccept=DEFAULT [, log=DEFAULT]]]])


        """

        request = self.environment.request
        response = self.environment.response
        session = self.environment.session

        # S3: Don't allow registration if disabled
        db = self.db
        settings = db(db.s3_setting.id > 0).select(db.s3_setting.utc_offset, limitby=(0, 1)).first()
        if settings:
            self_registration = session.s3.self_registration
            utc_offset = settings.utc_offset
        else:
            # db empty and prepopulate is false
            self_registration = True
            utc_offset = self.deployment_settings.get_L10n_utc_offset()
        if not self_registration:
            session.error = self.messages.registration_disabled
            redirect(URL(r=request, args=["login"]))


        if self.is_logged_in() and request.function != "index":
            redirect(self.settings.logged_url)


        if next == DEFAULT:
            next = request.vars._next or self.settings.register_next
        if onvalidation == DEFAULT:
            onvalidation = self.settings.register_onvalidation
        if onaccept == DEFAULT:
            onaccept = self.settings.register_onaccept
        if log == DEFAULT:
            log = self.messages.register_log

        user = self.settings.table_user

        user.utc_offset.default = utc_offset

        passfield = self.settings.password_field
        form = SQLFORM(user, hidden=dict(_next=request.vars._next),
                       showid=self.settings.showid,
                       submit_button=self.messages.submit_button,
                       delete_label=self.messages.delete_label)
        for i, row in enumerate(form[0].components):
            item = row[1][0]
            if isinstance(item, INPUT) and item["_name"] == passfield:
                form[0].insert(i + 1, TR(
                        LABEL(self.messages.verify_password + ":"),
                        INPUT(_name="password_two",
                              _type="password",
                              requires=IS_EXPR("value==%s" % \
                               repr(request.vars.get(passfield, None)),
                        error_message=self.messages.mismatched_password)),
                "", _class="%s_%s__row" % (user, "password_two")))
        if self.settings.captcha != None:
            form[0].insert(-1, TR("", self.settings.captcha, ""))

        user.registration_key.default = key = str(uuid.uuid4())

        if form.accepts(request.vars, session, formname="register",
                        onvalidation=onvalidation):
            description = \
                "group uniquely assigned to %(first_name)s %(last_name)s"\
                 % form.vars
            if self.settings.create_user_groups:
                group_id = self.add_group("user_%s" % form.vars.id, description)
                self.add_membership(group_id, form.vars.id)
            if self.settings.registration_requires_verification and self.db(self.settings.table_user.id > 0).count() > 1:
                if not self.settings.mailer or \
                   not self.settings.mailer.send(to=form.vars.email,
                        subject=self.messages.verify_email_subject,
                        message=self.messages.verify_email
                         % dict(key=key)):
                    self.db.rollback()
                    response.error = self.messages.invalid_email
                    return form
                session.confirmation = self.messages.email_sent
            elif self.settings.registration_requires_approval and self.db(self.settings.table_user.id > 0).count() > 1:
                user[form.vars.id] = dict(registration_key="pending")
                session.warning = self.messages.registration_pending
            else:
                user[form.vars.id] = dict(registration_key="")
                session.confirmation = self.messages.registration_successful

                table_user = self.settings.table_user
                if "username" in table_user.fields:
                    username = "username"
                else:
                    username = "email"
                user = self.db(table_user[username] == form.vars[username]).select(limitby=(0, 1)).first()
                user = Storage(table_user._filter_fields(user, id=True))

                # Add the first user to admin group
                # Installers should create a default user with random password to make this safe
                if self.db(table_user.id > 0).count() == 1:
                    table_group = self.settings.table_group
                    admin_group = self.db(table_group.role == "Administrator").select(table_group.id, limitby=(0, 1)).first()
                    if admin_group:
                        self.add_membership(admin_group.id, user.id)
                    # Add extra startup roles for system administrator
                    roles = self.settings.admin_startup_roles
                    if roles:
                        for r in roles:
                            group = self.db(table_group.role == r).select(table_group.id, limitby=(0, 1)).first()
                            if group:
                                self.add_membership(group.id, user.id)

                session.auth = Storage(user=user, last_visit=request.now,
                                   expiration=self.settings.expiration)
                self.user = user
                session.flash = self.messages.logged_in

            if log:
                self.log_event(log % form.vars)
            if onaccept:
                onaccept(form)
            if not next:
                next = self.url(args = request.args)
            elif isinstance(next, (list, tuple)):
                # fix issue with 2.6
                next = next[0]

            elif next and not next[0] == "/" and next[:4] != "http":
                next = self.url(next.replace("[id]", str(form.vars.id)))

            redirect(next)
        return form

    def shn_logged_in(self):
        """
            Check whether the user is currently logged-in
        """

        session = self.session
        if not self.is_logged_in():
            if not self.basic():
                return False
            else:
                roles = []
                table = self.db.auth_membership
                set = self.db(table.user_id == self.user.id).select(table.group_id)
                session.s3.roles = [s.group_id for s in set]

        return True

    def shn_has_role(self, role):
        """
            Check whether the currently logged-in user has a role
            @param role can be integer or a name
        """

        #deployment_settings = self.deployment_settings
        db = self.db
        session = self.session

        # Administrators have all roles
        if 1 in session.s3.roles:
            return True

        try:
            role = int(role)
        except:
            #role = deployment_settings.auth.roles[role]
            try:
                role = db(db.auth_group.role == role).select(db.auth_group.id, limitby=(0, 1)).first().id
            except:
                # Role doesn't exist in the Database
                return False

        if role in session.s3.roles:
            return True
        else:
            return False


    def shn_has_permission(self, method, table, record_id = 0):

        """
            S3 framework function to define whether a user can access a record in manner "method"
            Designed to be called from the RESTlike controller
            @note: This is planned to be rewritten: http://eden.sahanafoundation.org/wiki/BluePrintAuthorization

            @param table: the table or tablename
        """

        db = self.db
        session = self.session

        if not hasattr(table, "_tablename"):
            table = db[table]

        if session.s3.security_policy == 1:
            # Simple policy
            # Anonymous users can Read.
            if method == "read":
                authorised = True
            else:
                # Authentication required for Create/Update/Delete.
                authorised = self.shn_logged_in()

        elif session.s3.security_policy == 2:
            # Editor policy
            # Anonymous users can Read.
            if method == "read":
                authorised = True
            elif method == "create":
                # Authentication required for Create.
                authorised = self.shn_logged_in()
            elif record_id == 0 and method == "update":
                # Authenticated users can update at least some records
                authorised = self.shn_logged_in()
            else:
                # Editor role required for Update/Delete.
                authorised = self.shn_has_role("Editor")
                if not authorised and self.user and "created_by" in table:
                    # Creator of Record is allowed to Edit
                    record = db(table.id == record_id).select(table.created_by, limitby=(0, 1)).first()
                    if record and self.user.id == record.created_by:
                        authorised = True

        else:
            # Full policy
            if shn_logged_in():
                # Administrators are always authorised
                if self.shn_has_role(1):
                    authorised = True
                else:
                    # Require records in auth_permission to specify access (default Web2Py-style)
                    authorised = self.has_permission(method, table, record_id)
            else:
                # No access for anonymous
                authorised = False

        return authorised

    def shn_accessible_query(self, method, table):

        """
            Returns a query with all accessible records for the current logged in user
            @note: This method does not work on GAE because it uses JOIN and IN
        """

        db = self.db
        session = self.session
        T = self.environment.T

        # If using the "simple" security policy then show all records
        if session.s3.security_policy == 1:
            # simple
            return table.id > 0
        # If using the "editor" security policy then show all records
        elif session.s3.security_policy == 2:
            # editor
            return table.id > 0
        # Administrators can see all data
        if self.shn_has_role(1):
            return table.id > 0
        # If there is access to the entire table then show all records
        try:
            user_id = self.user.id
        except:
            user_id = 0
        if self.has_permission(method, table, 0, user_id):
            return table.id > 0
        # Filter Records to show only those to which the user has access
        session.warning = T("Only showing accessible records!")
        membership = self.settings.table_membership
        permission = self.settings.table_permission
        return table.id.belongs(db(membership.user_id == user_id)\
                           (membership.group_id == permission.group_id)\
                           (permission.name == method)\
                           (permission.table_name == table)\
                           ._select(permission.record_id))

    def shn_register(self, form):
        """
            S3 framework function
            Designed to be used as an onaccept callback for register()
            Whenever someone registers, it:
                * adds them to the 'Authenticated' role
                * adds their name to the Person Registry
        """

        # Add to 'Authenticated' role
        authenticated = self.id_group("Authenticated")
        self.add_membership(authenticated, form.vars.id)

        # S3: Add to Person Registry as well and Email to pr_pe_contact
        self.shn_link_to_person(user=form.vars)


    def shn_has_membership(self, group_id=None, user_id=None, role=None):
        """
            Checks if user is member of group_id or role

            Extends Web2Py's requires_membership() to add new functionality:
                * Custom Flash style
                * Uses shn_has_role()
        """

        group_id = group_id or self.id_group(role)
        try:
            group_id = int(group_id)
        except:
            group_id = self.id_group(group_id) # interpret group_id as a role

        if self.shn_has_role(group_id):
            r = True
        else:
            r = False

        log = self.messages.has_membership_log
        if log:
            if not user_id and self.user:
                user_id = self.user.id
            self.log_event(log % dict(user_id=user_id,
                                      group_id=group_id, check=r))
        return r

    # Override original method
    has_membership = shn_has_membership

    def shn_requires_membership(self, role):
        """
            Decorator that prevents access to action if not logged in or
            if user logged in is not a member of group_id.
            If role is provided instead of group_id then the group_id is calculated.

            Extends Web2Py's requires_membership() to add new functionality:
                * Custom Flash style
                * Uses shn_has_role()
                * Administrators (id=1) are deemed to have all roles
        """

        def decorator(action):

            def f(*a, **b):
                if not self.shn_logged_in():
                    request = self.environment.request
                    next = URL(r=request, args=request.args, vars=request.get_vars)
                    redirect(self.settings.login_url + "?_next=" + urllib.quote(next))

                if not self.shn_has_role(role) and not self.shn_has_role(1):
                    self.environment.session.error = self.messages.access_denied
                    next = self.settings.on_failed_authorization
                    redirect(next)

                return action(*a, **b)

            f.__doc__ = action.__doc__

            return f

        return decorator

    # Override original method
    requires_membership = shn_requires_membership

    def shn_link_to_person(self, user=None):

        """
            Links user accounts to person registry entries

            Policy for linking to pre-existing person records:

            If and only if:
                a person record with exactly the same first name and
                last name exists, which has a contact information record
                with exactly the same email address as used in the user
                account, and which is not linked to another user account,
                then this person record will be linked to this user account,

            otherwise:
                a new person record is created, and a new email contact
                record with the email address from the user record is
                registered for that person

        """

        db = self.db
        utable = self.settings.table_user
        ptable = db.pr_person
        ctable = db.pr_pe_contact
        etable = db.pr_pentity

        if user is None:
            users = db(utable.person_uuid == None).select(utable.ALL)
        else:
            users = [user]

        for user in users:
            if "email" in user:

                first_name = user.first_name
                last_name = user.last_name
                email = user.email.lower()

                query = (ptable.first_name == first_name) & \
                        (ptable.last_name == last_name) & \
                        (ctable.pe_id == ptable.pe_id) & \
                        (ctable.contact_method == 1) & \
                        (ctable.value.lower() == email)
                person = db(query).select(ptable.uuid).first()
                if person:
                    if not db(utable.person_uuid == person.uuid).count():
                        db(utable.id == user.id).update(person_uuid=person.uuid)
                        if self.user and self.user.id == user.id:
                            self.user.person_uuid = person.uuid
                        continue

                pe_id = etable.insert(pe_type="pr_person")
                db(etable.id == pe_id).update(pe_id=pe_id)
                if pe_id:
                    new_id = ptable.insert(
                        pe_id = pe_id,
                        first_name = user.first_name,
                        last_name = user.last_name)
                    if new_id:
                        person_uuid = ptable[new_id].uuid
                        db(utable.id == user.id).update(person_uuid=person_uuid)
                        db(etable.id == pe_id).update(uuid=person_uuid)
                        # The following adds the email to pr_pe_contact
                        ctable.insert(
                                pe_id = pe_id,
                                contact_method = 1,
                                priority = 1,
                                value = email)
                        # The following adds the mobile to pr_pe_contact
                        ctable.insert(
                                pe_id = pe_id,
                                contact_method = 2,
                                priority = 2,
                                value = self.environment.request.vars["mobile"])

                if self.user and self.user.id == user.id:
                    self.user.person_uuid = person_uuid



class CrudS3(Crud):
    """
        Extended version of Crud from gluon/tools.py
        - select() uses SQLTABLE2 (to allow different linkto construction)
    """

    def __init__(self, environment, db=None):
        """ Initialise parent class & make any necessary modifications """
        Crud.__init__(self, environment, db)

    def select(
        self,
        table,
        query=None,
        fields=None,
        orderby=None,
        limitby=None,
        headers={},
        **attr
        ):
        request = self.environment.request
        if not (isinstance(table, self.db.Table) or table in self.db.tables):
            raise HTTP(404)
        if not self.has_permission("select", table):
            redirect(self.settings.auth.settings.on_failed_authorization)
        #if record_id and not self.has_permission("select", table):
        #    redirect(self.settings.auth.settings.on_failed_authorization)
        if not isinstance(table, self.db.Table):
            table = self.db[table]
        if not query:
            query = table.id > 0
        if not fields:
            fields = [table.ALL]
        rows = self.db(query).select(*fields, **dict(orderby=orderby,
            limitby=limitby))
        if not rows:
            return None # Nicer than an empty table.
        if not "linkto" in attr:
            attr["linkto"] = self.url(args="read")
        if not "upload" in attr:
            attr["upload"] = self.url("download")
        if request.extension != "html":
            return rows.as_list()
        return SQLTABLE2(rows, headers=headers, **attr)


# Modified version of SQLTABLE from gluon/sqlhtml.py
# we need a different linkto construction for our CRUD controller
# we need to specify a different ID field to direct to for the M2M controller
class SQLTABLE2(TABLE):
    """
    given a SQLRows object, as returned by a db().select(), generates
    an html table with the rows.

    optional arguments:

    :param linkto: URL (or lambda to generate a URL) to edit individual records
    :param upload: URL to download uploaded files
    :param orderby: Add an orderby link to column headers.
    :param headers: dictionary of headers to headers redefinions
    :param truncate: length at which to truncate text in table cells.
        Defaults to 16 characters.

    optional names attributes for passed to the <table> tag

    Simple linkto example::

        rows = db.select(db.sometable.ALL)
        table = SQLTABLE2(rows, linkto="someurl")

    This will link rows[id] to .../sometable/value_of_id


    More advanced linkto example::

        def mylink(field):
            return URL(r=request, args=[field])

        rows = db.select(db.sometable.ALL)
        table = SQLTABLE2(rows, linkto=mylink)

    This will link rows[id] to
        current_app/current_controller/current_function/value_of_id
    """

    def __init__(
        self,
        sqlrows,
        linkto=None,
        upload=None,
        orderby=None,
        headers={},
        truncate=16,
        **attributes
        ):

        TABLE.__init__(self, **attributes)
        self.components = []
        self.attributes = attributes
        self.sqlrows = sqlrows
        (components, row) = (self.components, [])
        if not orderby:
            for c in sqlrows.colnames:
                colname = c.split(".")[-1]
                row.append(TH(headers.get(c, c), _class="column_%s" % colname))
        else:
            for c in sqlrows.colnames:
                colname = c.split(".")[-1]
                row.append(TH(A(headers.get(c, c), _href="?orderby="
                            + c), _class="column_%s" % colname))
        components.append(THEAD(TR(*row)))
        tbody = []
        for (rc, record) in enumerate(sqlrows):
            row = []
            row_id = None
            if rc % 2 == 0:
                _class = "even"
            else:
                _class = "odd"
            for colname in sqlrows.colnames:
                if not table_field.match(colname):
                    r = record._extra[colname]
                    row.append(TD(r), _class="column_%s" % colname)
                    continue
                (tablename, fieldname) = colname.split(".")
                field = sqlrows.db[tablename][fieldname]
                if tablename in record and isinstance(record,
                        Row) and isinstance(record[tablename],
                        Row):
                    r = record[tablename][fieldname]
                elif fieldname in record:
                    r = record[fieldname]
                else:
                    raise SyntaxError, "something wrong in SQLRows object"
                if fieldname == "id":
                    row_id = r
                if field.represent:
                    r = field.represent(r)
                    row.append(TD(r, _class="column_%s" % fieldname))
                    continue
                if field.type == "blob" and r:
                    row.append(TD("DATA", _class="column_%s" % fieldname))
                    continue
                r = str(field.formatter(r))
                if field.type == "upload":
                    if upload and r:
                        row.append(TD(A("file", _href="%s/%s" % (upload, r)),
                                      _class="column_%s" % fieldname))
                    elif r:
                        row.append(TD("file", _class="column_%s" % fieldname))
                    else:
                        row.append(TD(_class="column_%s" % fieldname))
                    continue
                ur = unicode(r, "utf8")
                if len(ur) > truncate:
                    r = ur[:truncate - 3].encode("utf8") + "..."
                if linkto and field.type == "id":
                    try:
                        #href = linkto(r, "table", tablename)
                        href = linkto(r)
                    except TypeError:
                        #href = "%s/%s/%s" % (linkto, tablename, r)
                        href = "%s/%s" % (linkto, r)
                    row.append(TD(A(r, _href=href), _class="column_%s" % fieldname))
                # Reference record without a .represent defined
                # We can't assume  controller exists for linked resources
                # so better to use response.s3.actions for this
                #elif linkto and field.type[:9] == "reference":
                #    ref = field.type[10:]
                #    try:
                #        #href = linkto(r, "reference", ref)
                #        href = linkto(r)
                #    except TypeError:
                #        href = "%s/%s/%s" % (linkto, ref, r)
                #        if ref.find(".") >= 0:
                #            tref,fref = ref.split(".")
                #            if hasattr(sqlrows.db[tref], "_primarykey"):
                #                href = "%s/%s?%s" % (linkto, tref, urllib.urlencode({fref:ur}))
                #
                #    row.append(TD(A(r, _href=href, _class="column_%s" % fieldname)))
                elif linkto and hasattr(field._table, "_primarykey") and fieldname in field._table._primarykey:
                    # have to test this with multi-key tables
                    key = urllib.urlencode(dict( [ \
                                ((tablename in record \
                                      and isinstance(record, Row) \
                                      and isinstance(record[tablename], Row)) and
                                 (k, record[tablename][k])) or (k, record[k]) \
                                    for k in field._table._primarykey ] ))
                    row.append(TD(A(r, _href="%s/%s?%s" % (linkto, tablename, key)),
                                  _class="column_%s" % fieldname))
                else:
                    row.append(TD(r, _class="column_%s" % fieldname))
            rowattrs = {}
            if row_id:
                rowattrs["_id"] = "row_%s_%d" % (tablename, row_id)
            tbody.append(TR(_class=_class, *row, **rowattrs))
        components.append(TBODY(*tbody))


# Modified version of MENU2
# Only supports 2 levels
# Each menu is a UL not an LI
# A tags have classes
class MENU2(DIV):
    """
        Used to build modules menu
        Each list has 3 options: Name, Right & Link
        (NB In Web2Py's MENU, the 2nd option is 'Active')
        Right=True means that menu item floats right

        Optional arguments
          _class: defaults to 'S3menuInner'
          ul_main_class: defaults to 'S3menuUL'
          ul_sub_class: defaults to 'S3menuSub'
          li_class: defaults to 'S3menuLI'
          a_class: defaults to 'S3menuA'

        Example:
            menu = MENU2([["name", False, URL(...), [submenu]], ...])
            {{=menu}}
    """

    tag = "div"

    def __init__(self, data, **args):
        self.data = data
        self.attributes = args

    def serialize(self, data, level=0):
        if level == 0:
            # Top-level menu
            div = UL(**self.attributes)
            for i in range(len(data)):
                (name, right, link) = data[i][:3]
                if not link:
                        link = "#null"
                if right:
                    style = "float: right;"
                else:
                    style = "float: left;"
                if len(data[i]) > 3 and data[i][3]:
                    # Submenu
                    ul_inner = self.serialize(data[i][3], level+1)
                    in_ul = LI(DIV(A(name, _href=link), _class="hoverable"), ul_inner, _style=style)
                else:
                    if (i == 0) and (self.attributes["_id"] == "modulenav"):
                        # 1st item, so display logo
                        in_ul = LI(DIV(A(SPAN(_class="S3menulogo"), _href=link),
                                    SPAN(A(name, _href=link, _class="S3menuHome")),_class="hoverable"), _style=style )
                    else:
                        in_ul = LI(DIV(A(name, _href=link), _class="hoverable"), _style=style)
                div.append(in_ul)
        else:
            # Submenu
            div = UL()
            for item in data:
                (name, right, link) = item[:3]
                li = LI(A(name, _href=link))
                div.append(li)
        return div

    def xml(self):
        return self.serialize(self.data, 0).xml()

# class QueryS3 -----------------------------------------------------------------------
# added by sunneach on Feb 9, 2010
#
class QueryS3(Query):
    """
    If Server Side Pagination is on, the proper CAST is needed to match the string-typed id to lookup table id
    """
    def __init__(self,
                 left,
                 op=None,
                 right=None,
                ):

        if op <> "join_via":
            Query.__init__(self, left, op, right)
        else:
            self.sql = "CAST(TRIM(%s,"|") AS INTEGER)=%s" % (left, right)

#
# class FieldS3 -----------------------------------------------------------------------
# added by sunneach on Feb 9, 2010
#
class FieldS3(Field):
    """
    If Server Side Pagination is on, the proper CAST is needed to match the lookup table id
    """
    def __init__(
        self,
        fieldname,
        type="string",
        length=None,
        default=None,
        required=False,
        requires="<default>",
        ondelete="CASCADE",
        notnull=False,
        unique=False,
        uploadfield=True,
        widget=None,
        label=None,
        comment=None,
        writable=True,
        readable=True,
        update=None,
        authorize=None,
        autodelete=False,
        represent=None,
        uploadfolder=None,
        compute=None,
        sortby=None,
        ):

        self.sortby = sortby

        Field.__init__(self,
                       fieldname,
                       type,
                       length,
                       default,
                       required,
                       requires,
                       ondelete,
                       notnull,
                       unique,
                       uploadfield,
                       widget,
                       label,
                       comment,
                       writable,
                       readable,
                       update,
                       authorize,
                       autodelete,
                       represent,
                       uploadfolder,
                       compute)

    def join_via(self, value):
        if self.type.find("reference") == 0:
            return Query(self, "=", value)
        else:
            return QueryS3(self, "join_via", value)
