# -*- coding: utf-8 -*-

"""
    Global settings
    Those which are typically edited during a deployment are in 000_config.py & their results parsed into here.
    Deployers shouldn't typically need to edit any settings here
"""

BREADCRUMB = ">> "
UNKNOWN_OPT = T("Unknown")
NONE = "-"
READ = T("Open")
#READ = T("Details")
UPDATE = T("Open")
#UPDATE = T("Edit")
#UPDATE = T("Update")
DELETE = T("Delete")
COPY = T("Copy")
NOT_APPLICABLE = T("N/A")

s3.l10n_languages = deployment_settings.get_L10n_languages()

# Default strings are in US English
T.current_languages = ["en", "en-us"]
# Check if user has selected a specific language
if request.vars._language:
    session._language = request.vars._language
if session._language:
    T.force(session._language)
else:
    # Use what browser requests
    T.force(T.http_accept_language)

######
# Mail
######

# These settings could be made configurable as part of the Messaging Module
# - however also need to be used by Auth (order issues), DB calls are overheads
# - as easy for admin to edit source here as to edit DB (although an admin panel can be nice)
mail.settings.server = deployment_settings.get_mail_server()
mail_server_login = deployment_settings.get_mail_server_login()
if mail_server_login:
    mail.settings.login = mail_server_login
mail.settings.sender = deployment_settings.get_mail_sender()

######
# Auth
######

#auth.settings.username_field = True
auth.settings.hmac_key = deployment_settings.get_auth_hmac_key()
auth.define_tables()

if deployment_settings.get_auth_openid():
    # Requires http://pypi.python.org/pypi/python-openid/
    try:
        from gluon.contrib.login_methods.openid_auth import OpenIDAuth
        openid_login_form = OpenIDAuth(auth)
        from gluon.contrib.login_methods.extended_login_form import ExtendedLoginForm
        extended_login_form = ExtendedLoginForm(auth, openid_login_form, signals=["oid", "janrain_nonce"])
        auth.settings.login_form = extended_login_form
    except ImportError:
        session.warning = T("Library support not available for OpenID")

auth.settings.expiration = 3600  # seconds
# Require captcha verification for registration
#auth.settings.captcha = RECAPTCHA(request, public_key="PUBLIC_KEY", private_key="PRIVATE_KEY")
# Require Email Verification
auth.settings.registration_requires_verification = deployment_settings.get_auth_registration_requires_verification()
# Email settings for registration verification
auth.settings.mailer = mail
auth.messages.verify_email = Tstr("Click on the link ") + deployment_settings.get_base_public_url() + "/" + request.application + "/default/user/verify_email/%(key)s " + Tstr("to verify your email")
auth.settings.on_failed_authorization = URL(r=request, c="default", f="user", args="not_authorized")
auth.settings.reset_password_requires_verification = True
auth.messages.reset_password = Tstr("Click on the link ") + deployment_settings.get_base_public_url() + "/" + request.application + "/default/user/reset_password/%(key)s " + Tstr("to reset your password")
# Require Admin approval for self-registered users
auth.settings.registration_requires_approval = deployment_settings.get_auth_registration_requires_approval()
auth.messages.registration_pending = T("Email address verified, however registration is still pending approval - please wait until confirmation received.")
# Notify UserAdmin of new pending user registration to action
if deployment_settings.get_auth_registration_requires_approval():
    auth.settings.verify_email_onaccept = lambda form: \
        auth.settings.mailer.send(to=deployment_settings.get_mail_approver(),
                                  subject=T("Sahana Login Approval Pending"),
                                  message=Tstr("Your action is required. Please approve user %s asap: " % form.email) +
                                  deployment_settings.get_base_public_url() + "/" + request.application + "/admin/user")

# Allow use of LDAP accounts for login
# NB Currently this means that change password should be disabled:
#auth.settings.actions_disabled.append("change_password")
# (NB These are not automatically added to PR or to Authenticated role since they enter via the login() method not register())
#from gluon.contrib.login_methods.ldap_auth import ldap_auth
# Require even alternate login methods to register users 1st
#auth.settings.alternate_requires_registration = True
# Active Directory
#auth.settings.login_methods.append(ldap_auth(mode="ad", server="dc.domain.org", base_dn="ou=Users,dc=domain,dc=org"))
# or if not wanting local users at all (no passwords saved within DB):
#auth.settings.login_methods = [ldap_auth(mode="ad", server="dc.domain.org", base_dn="ou=Users,dc=domain,dc=org")]
# Domino
#auth.settings.login_methods.append(ldap_auth(mode="domino", server="domino.domain.org"))
# OpenLDAP
#auth.settings.login_methods.append(ldap_auth(server="directory.sahanafoundation.org", base_dn="ou=users,dc=sahanafoundation,dc=org"))
# Allow use of Email accounts for login
#auth.settings.login_methods.append(email_auth("smtp.gmail.com:587", "@gmail.com"))
# We don't wish to clutter the groups list with 1 per user.
auth.settings.create_user_groups = False
# We need to allow basic logins for Webservices
auth.settings.allow_basic_login = True

auth.settings.lock_keys = False
auth.settings.logout_onlogout = shn_auth_on_logout
auth.settings.login_onaccept = shn_auth_on_login
# Uncomment to have complex redirects post login
#if not request.vars._next:
#	auth.settings.login_next = URL(r=request, c="default", f="user",
#		args="login_next")
#if not deployment_settings.auth.registration_requires_verification:
#    auth.settings.register_next = URL(r=request, c="default", f="user",
#            args="login_next")

auth.settings.lock_keys = True

######
# Crud
######

# Breaks refresh of List after Create: http://groups.google.com/group/web2py/browse_thread/thread/d5083ed08c685e34
#crud.settings.keepvalues = True
crud.messages.submit_button = T("Save")

##########
# Messages
##########

from gluon.storage import Messages
s3.messages = Messages(T)
s3.messages.confirmation_email_subject = T("Sahana access granted")
s3.messages.confirmation_email = Tstr("Welcome to the Sahana Portal at ") + deployment_settings.get_base_public_url() + Tstr(". Thanks for your assistance.")
