# -*- coding: utf-8 -*-

"""
    Utilities
"""

def shn_sessions():
    """
        Extend session to support:
            Multiple flash classes
            Settings
                Debug mode
                Security mode
                Restricted mode
                Theme
                Audit modes
    """
    response.error = session.error
    response.confirmation = session.confirmation
    response.warning = session.warning
    session.error = []
    session.confirmation = []
    session.warning = []
    # Keep all our configuration options in a single pair of global variables
    # Use session for persistent variables
    if not session.s3:
        session.s3 = Storage()
    # Use response for one-off variables which are visible in views without explicit passing
    response.s3 = Storage()
    response.s3.countries = deployment_settings.get_L10n_countries()
    response.s3.formats = Storage()
    response.s3.gis = Storage()

    roles = []
    if auth.is_logged_in():
        user_id = auth.user.id
        _memberships = db.auth_membership
        memberships = db(_memberships.user_id == user_id).select(_memberships.group_id) # Cache this & invalidate when memberships are changed?
        for membership in memberships:
            roles.append(membership.group_id)
    session.s3.roles = roles

    controller_settings_table = "%s_setting" % request.controller
    controller_settings = controller_settings_table in db.tables and \
       db(db[controller_settings_table].id > 0).select(limitby=(0, 1)).first()

    settings = db(db.s3_setting.id > 0).select(db.s3_setting.debug, db.s3_setting.security_policy, db.s3_setting.self_registration, db.s3_setting.audit_read, db.s3_setting.audit_write, limitby=(0, 1)).first()
    # Are we running in debug mode?
    session.s3.debug = request.vars.get("debug", None) or settings and settings.debug
    session.s3.self_registration = (settings and settings.self_registration) or 1
    session.s3.security_policy = (settings and settings.security_policy) or 1

    # We Audit if either the Global or Module asks us to
    # (ignore gracefully if module author hasn't implemented this)
    session.s3.audit_read = (settings and settings.audit_read) \
        or (controller_settings and controller_settings.audit_read)
    session.s3.audit_write = (settings and settings.audit_write) \
        or (controller_settings and controller_settings.audit_write)

    return settings

s3_settings = shn_sessions()

# -----------------------------------------------------------------------------
# List of supported languages
#
shn_languages = {
    "en": T("English"),
    "fr": T("French"),
    "es": T("Spanish"),
    "zh-tw": T("Chinese")
}
auth.settings.table_user.language.requires = IS_IN_SET(shn_languages, zero=None)


# -----------------------------------------------------------------------------
# List of Nations (ISO-3166-1 Country Codes)
# @ToDo Add Telephone codes (need to convert to Storage())
#
shn_list_of_nations = {
    "AF": "Afghanistan",
    "AX": "Åland Islands",
    "AL": "Albania",
    "DZ": "Algeria",
    "AS": "American Samoa",
    "AD": "Andorra",
    "AO": "Angola",
    "AI": "Anguilla",
    "AQ": "Antarctica",
    "AG": "Antigua and Barbuda",
    "AR": "Argentina",
    "AM": "Armenia",
    "AW": "Aruba",
    "AU": "Australia",
    "AT": "Austria",
    "AZ": "Azerbaijan",
    "BS": "Bahamas",
    "BH": "Bahrain",
    "BD": "Bangladesh",
    "BB": "Barbados",
    "BY": "Belarus",
    "BE": "Belgium",
    "BZ": "Belize",
    "BJ": "Benin",
    "BM": "Bermuda",
    "BT": "Bhutan",
    "BO": "Bolivia, Plurinational State of",
    "BA": "Bosnia and Herzegovina",
    "BW": "Botswana",
    "BV": "Bouvet Island",
    "BR": "Brazil",
    "IO": "British Indian Ocean Territory",
    "BN": "Brunei Darussalam",
    "BG": "Bulgaria",
    "BF": "Burkina Faso",
    "BI": "Burundi",
    "KH": "Cambodia",
    "CM": "Cameroon",
    "CA": "Canada",
    "CV": "Cape Verde",
    "KY": "Cayman Islands",
    "CF": "Central African Republic",
    "TD": "Chad",
    "CL": "Chile",
    "CN": "China",
    "CX": "Christmas Island",
    "CC": "Cocos (Keeling) Islands",
    "CO": "Colombia",
    "KM": "Comoros",
    "CG": "Congo",
    "CD": "Congo, The Democratic Republic of the",
    "CK": "Cook Islands",
    "CR": "Costa Rica",
    "CI": "Côte d'Ivoire",
    "HR": "Croatia",
    "CU": "Cuba",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "DJ": "Djibouti",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "EC": "Ecuador",
    "EG": "Egypt",
    "SV": "El Salvador",
    "GQ": "Equatorial Guinea",
    "ER": "Eritrea",
    "EE": "Estonia",
    "ET": "Ethiopia",
    "FK": "Falkland Islands (Malvinas)",
    "FO": "Faroe Islands",
    "FJ": "Fiji",
    "FI": "Finland",
    "FR": "France",
    "GF": "French Guiana",
    "PF": "French Polynesia",
    "TF": "French Southern Territories",
    "GA": "Gabon",
    "GM": "Gambia",
    "GE": "Georgia",
    "DE": "Germany",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GR": "Greece",
    "GL": "Greenland",
    "GD": "Grenada",
    "GP": "Guadeloupe",
    "GU": "Guam",
    "GT": "Guatemala",
    "GG": "Guernsey",
    "GN": "Guinea",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HT": "Haiti",
    "HM": "Heard Island and McDonald Islands",
    "VA": "Holy See (Vatican City State)",
    "HN": "Honduras",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "IS": "Iceland",
    "IN": "India",
    "ID": "Indonesia",
    "IR": "Iran, Islamic Republic of",
    "IQ": "Iraq",
    "IE": "Ireland",
    "IM": "Isle of man",
    "IL": "Israel",
    "IT": "Italy",
    "JM": "Jamaica",
    "JP": "Japan",
    "JE": "Jersey",
    "JO": "Jordan",
    "KZ": "Kazakhstan",
    "KE": "Kenya",
    "KI": "Kiribati",
    "KP": "Korea, Democratic People's Republic of",
    "KR": "Korea, Republic of",
    "KW": "Kuwait",
    "KG": "Kyrgyzstan",
    "LA": "Lao People's Democratic Republic",
    "LV": "Latvia",
    "LB": "Lebanon",
    "LS": "Lesotho",
    "LR": "Liberia",
    "LY": "Libyan Arab Jamahiriya",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MO": "Macao",
    "MK": "Macedonia, the former Yugoslav Republic of",
    "MG": "Madagascar",
    "MW": "Malawi",
    "MY": "Malaysia",
    "MV": "Maldives",
    "ML": "Mali",
    "MT": "Malta",
    "MH": "Marshall Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MU": "Mauritius",
    "YT": "Mayotte",
    "MX": "Mexico",
    "FM": "Micronesia, Federated States of",
    "MD": "Moldova, Republic of",
    "MC": "Monaco",
    "MN": "Mongolia",
    "ME": "Montenegro",
    "MS": "Montserrat",
    "MA": "Morocco",
    "MZ": "Mozambique",
    "MM": "Myanmar",
    "NA": "Namibia",
    "NR": "Nauru",
    "NP": "Nepal",
    "NL": "Netherlands",
    "AN": "Netherlands Antilles",
    "NC": "New Caledonia",
    "NZ": "New Zealand",
    "NI": "Nicaragua",
    "NE": "Niger",
    "NG": "Nigeria",
    "NU": "Niue",
    "NF": "Norfolk Island",
    "MP": "Northern Mariana Islands",
    "NO": "Norway",
    "OM": "Oman",
    "PK": "Pakistan",
    "PW": "Palau",
    "PS": "Palestinian Territory, occupied",
    "PA": "Panama",
    "PG": "Papua New Guinea",
    "PY": "Paraguay",
    "PE": "Peru",
    "PH": "Philippines",
    "PN": "Pitcairn",
    "PL": "Poland",
    "PT": "Portugal",
    "PR": "Puerto Rico",
    "QA": "Qatar",
    "RE": "Réunion",
    "RO": "Romania",
    "RU": "Russian Federation",
    "RW": "Rwanda",
    "BL": "Saint Barthélemy",
    "SH": "Saint Helena, Ascension and Tristan da Cunha",
    "KN": "Saint Kitts and Nevis",
    "LC": "Saint Lucia",
    "MF": "Saint Martin",
    "PM": "Saint Pierre and Miquelon",
    "VC": "Saint Vincent and the Grenadines",
    "WS": "Samoa",
    "SM": "San Marino",
    "ST": "Sao Tome and Principe",
    "SA": "Saudi Arabia",
    "SN": "Senegal",
    "RS": "Serbia",
    "SC": "Seychelles",
    "SL": "Sierra Leone",
    "SG": "Singapore",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "SB": "Solomon Islands",
    "SO": "Somalia",
    "ZA": "South Africa",
    "GS": "South Georgia and the South Sandwich Islands",
    "ES": "Spain",
    "LK": "Sri Lanka",
    "SD": "Sudan",
    "SR": "Suriname",
    "SJ": "Svalbard and Jan Mayen",
    "SZ": "Swaziland",
    "SE": "Sweden",
    "CH": "Switzerland",
    "SY": "Syrian Arab Republic",
    "TW": "Taiwan, Province of China",
    "TJ": "Tajikistan",
    "TZ": "Tanzania, United Republic of",
    "TH": "Thailand",
    "TL": "Timor-Leste",
    "TG": "Togo",
    "TK": "Tokelau",
    "TO": "Tonga",
    "TT": "Trinidad and Tobago",
    "TN": "Tunisia",
    "TR": "Turkey",
    "TM": "Turkmenistan",
    "TC": "Turks and Caicos Islands",
    "TV": "Tuvalu",
    "UG": "Uganda",
    "UA": "Ukraine",
    "AE": "United Arab Emirates",
    "GB": "United Kingdom",
    "US": "United States",
    "UM": "United States Minor Outlying Islands",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VU": "Vanuatu",
    "VE": "Venezuela, Bolivarian Republic of",
    "VN": "Vietnam",
    "VG": "Virgin Islands, british",
    "VI": "Virgin Islands, U.S.",
    "WF": "Wallis and Futuna",
    "EH": "Western Sahara",
    "YE": "Yemen",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
    "XX": "Unknown"
}

# -----------------------------------------------------------------------------
# User Time Zone Operations:
from datetime import timedelta
import time

def shn_user_utc_offset():
    """
        returns the UTC offset of the current user or None, if not logged in
    """

    if auth.is_logged_in():
        return db(db.auth_user.id == session.auth.user.id).select(db.auth_user.utc_offset, limitby=(0, 1)).first().utc_offset
    else:
        try:
            offset = db().select(db.s3_setting.utc_offset, limitby=(0, 1)).first().utc_offset
        except:
            offset = None
        return offset


def shn_as_local_time(value):
    """
        represents a given UTC datetime.datetime object as string:

        - for the local time of the user, if logged in
        - as it is in UTC, if not logged in, marked by trailing +0000
    """

    format="%Y-%m-%d %H:%M:%S"

    offset = IS_UTC_OFFSET.get_offset_value(shn_user_utc_offset())

    if offset:
        dt = value + timedelta(seconds=offset)
        return dt.strftime(str(format))
    else:
        dt = value
        return dt.strftime(str(format))+" +0000"

# -----------------------------------------------------------------------------
# Phone number requires
shn_phone_requires = IS_NULL_OR(IS_MATCH('\+?\s*[\s\-\.\(\)\d]+(?:(?: x| ext)\s?\d{1,5})?$'))

# -----------------------------------------------------------------------------
# Make URLs clickable
shn_url_represent = lambda url: (url and [A(url, _href=url, _target="blank")] or [""])[0]


# -----------------------------------------------------------------------------
def myname(user_id):
    user = db.auth_user[user_id]
    return user.first_name if user else NONE


# -----------------------------------------------------------------------------
def unauthorised():
    session.error = T("Not Authorised!")
    redirect(URL(r=request, c="default", f="user", args="login"))


# -----------------------------------------------------------------------------
def shn_abbreviate(word, size=48):

    """
        Abbreviate a string. For use as a .represent
    """

    if word:
        if (len(word) > size):
            word = "%s..." % word[:size - 4]
        else:
            return word
    else:
        return word


# -----------------------------------------------------------------------------
def shn_action_buttons(jr, deletable=True, copyable=False):

    """
        Provide the usual Action Buttons for Column views.
        Designed to be called from a postp
    """

    if jr.component:
        args = [jr.component_name, "[id]"]
    else:
        args = ["[id]"]

    if shn_has_permission("update", jr.table):
        # Provide the ability to delete records in bulk
        response.s3.actions = [
            dict(label=str(UPDATE), _class="action-btn", url=str(URL(r=request, args = args + ["update"]))),
        ]
        if deletable and shn_has_permission("delete", jr.table):
            response.s3.actions.append(
                dict(label=str(DELETE), _class="action-btn", url=str(URL(r=request, args = args + ["delete"])))
            )
        if copyable:
            response.s3.actions.append(
                dict(label=str(COPY), _class="action-btn", url=str(URL(r=request, args = args + ["copy"])))
            )
    else:
        response.s3.actions = [
            dict(label=str(READ), _class="action-btn", url=str(URL(r=request, args = args)))
        ]

    return


# -----------------------------------------------------------------------------
def shn_compose_message(data, template):

    """
        Compose an SMS Message from an XSLT
    """

    if data:
        root = etree.Element("message")
        for k in data.keys():
            entry = etree.SubElement(root, k)
            entry.text = s3xrc.xml.xml_encode(str(data[k]))

        message = None
        tree = etree.ElementTree(root)

        if template:
            template = os.path.join(request.folder, "static", template)
            if os.path.exists(template):
                message = s3xrc.xml.transform(tree, template)

        if message:
            return str(message)
        else:
            return s3xrc.xml.tostring(tree, pretty_print=True)


# -----------------------------------------------------------------------------
def shn_crud_strings(table_name,
                     table_name_plural = None):
    """
        @author: Michael Howden (michael@aidiq.com)

        @description:
            Creates the strings for the title of/in the various CRUD Forms.

        @arguments:
            table_name - string - The User's name for the resource in the table - eg. "Person"
            table_name_plural - string - The User's name for the plural of the resource in the table - eg. "People"

        @returns:
            class "gluon.storage.Storage" (Web2Py)

        @example
            s3.crud_strings[<table_name>] = shn_crud_strings(<table_name>, <table_name_plural>)
    """

    if not table_name_plural:
        table_name_plural = table_name + "s"

    ADD = T("Add " + table_name)
    LIST = T("List "+ table_name_plural)

    table_strings = Storage(
    title = T(table_name),
    title_plural = T(table_name_plural),
    title_create = ADD,
    title_display = T(table_name + " Details"),
    title_list = LIST,
    title_update = T("Edit "+ table_name) ,
    title_search = T("Search " + table_name_plural) ,
    subtitle_create = T("Add New " + table_name) ,
    subtitle_list = T(table_name_plural),
    label_list_button = LIST,
    label_create_button = ADD,
    msg_record_created =  T(table_name +" added"),
    msg_record_modified =  T(table_name + " updated"),
    msg_record_deleted = T( table_name + " deleted"),
    msg_list_empty = T("No " + table_name_plural + " currently registered"))

    return table_strings


# -----------------------------------------------------------------------------
def shn_get_crud_string(tablename, name):
    """
        Get the CRUD strings for a table
    """

    crud_strings = s3.crud_strings.get(tablename, s3.crud_strings)
    not_found = s3.crud_strings.get(name, None)

    return crud_strings.get(name, not_found)


# -----------------------------------------------------------------------------
def shn_import_table(table_name,
                     import_if_not_empty = False):
    """
        @author: Michael Howden (michael@aidiq.com)

        @description:
            If a table is empty, it will import values into that table from:
            /private/import/tables/<table>.csv.

        @arguments:
            table_name - string - The name of the table
            import_if_not_empty - bool
    """

    table = db[table_name]
    if not db(table.id).count() or import_if_not_empty:
        import_file = os.path.join(request.folder,
                                   "private", "import", "tables",
                                   table_name + ".csv")
        table.import_from_csv_file(open(import_file,"r"))


# -----------------------------------------------------------------------------
def shn_last_update(table, record_id):

    if table and record_id:
        record = table[record_id]
        if record:
            mod_on_str  = T(" on ")
            mod_by_str  = T(" by ")

            modified_on = ""
            if "modified_on" in table.fields:
                modified_on = "%s%s" % (mod_on_str, shn_as_local_time(record.modified_on))

            modified_by = ""
            if "modified_by" in table.fields:
                user = auth.settings.table_user[record.modified_by]
                if user:
                    person = db(db.pr_person.uuid == user.person_uuid).select(limitby=(0, 1)).first()
                    if person:
                        modified_by = "%s%s" % (mod_by_str, vita.fullname(person))

            if len(modified_on) or len(modified_by):
                last_update = "%s%s%s" % (T("Record last updated"), modified_on, modified_by)
                return last_update
    return None


# -----------------------------------------------------------------------------
def shn_represent_file(file_name,
                       table,
                       field = "file"):
    """
        @author: Michael Howden (michael@aidiq.com)

        @description:
            Represents a file (stored in a table) as the filename with a link to that file
            THIS FUNCTION IS REDUNDANT AND CAN PROBABLY BE REPLACED BY shn_file_represent in models/06_doc.py
    """
    import base64
    url_file = crud.settings.download_url + "/" + file_name

    if db[table][field].uploadfolder:
        path = db[table][field].uploadfolder
    else:
        path = os.path.join(db[table][field]._db._folder, "..", "uploads")
    pathfilename = os.path.join(path, file_name)

    try:
        #f = open(pathfilename,"r")
        #filename = f.filename
        regex_content = re.compile("([\w\-]+\.){3}(?P<name>\w+)\.\w+$")
        regex_cleanup_fn = re.compile('[\'"\s;]+')

        m = regex_content.match(file_name)
        filename = base64.b16decode(m.group("name"), True)
        filename = regex_cleanup_fn.sub("_", filename)
    except:
        filename = file_name

    return A(filename, _href = url_file)


# -----------------------------------------------------------------------------
def shn_reference_field():

    return


# -----------------------------------------------------------------------------
def shn_insert_subheadings(form, tablename, subheadings):

    """
    Insert subheadings into forms

    @param form: the form
    @param tablename: the tablename
    @param subheadings: a dict of {"Headline": Fieldnames}, where Fieldname can
                        be either a single field name or a list/tuple of
                        field names belonging under that headline

    """

    if subheadings:
        if tablename in subheadings:
            subheadings = subheadings.get(tablename)
        form_rows = iter(form[0])
        tr = form_rows.next()
        i = 0
        done = []
        while tr:
            f = tr.attributes.get("_id", None)
            if f.startswith(tablename) and f[-5:] == "__row":
                f = f[len(tablename)+1:-5]
                for k in subheadings.keys():
                    if k in done:
                        continue
                    fields = subheadings[k]
                    if not isinstance(fields, (list, tuple)):
                        fields = [fields]
                    if f in fields:
                        done.append(k)
                        form[0].insert(i, TR(TD(k, _colspan=3, _class="subheading"),
                                             _class = "subheading",
                                             _id = "%s_%s__subheading" % (tablename, f)))
                        tr.attributes.update(_class="after_subheading")
                        tr = form_rows.next()
                        i += 1
            try:
                tr = form_rows.next()
            except StopIteration:
                break
            else:
                i += 1


# -----------------------------------------------------------------------------
def shn_rheader_tabs(r, tabs=[], paging=False):

    """
    Constructs a DIV of component links for a S3RESTRequest

    @param tabs: the tabs as list of tuples (title, component_name, vars), where vars is optional
    @param paging: add paging buttons previous/next to the tabs

    """

    rheader_tabs = []

    tablist = []
    previous = next = None

    for i in xrange(len(tabs)):
        title, component = tabs[i][:2]
        if len(tabs[i]) > 2:
            _vars = tabs[i][2]
        else:
            _vars = r.request.vars

        if component and component.find("/") > 0:
            function, component = component.split("/", 1)
            if not component:
                component = None
        else:
            function = r.request.function

        if i == len(tabs)-1:
            tab = Storage(title=title, _class = "rheader_tab_last")
        else:
            tab = Storage(title=title, _class = "rheader_tab_other")
        if i > 0 and tablist[i-1]._class == "rheader_tab_here":
            next = tab

        if component:
            if r.component and r.component.name == component or \
               r.custom_action and r.method == component:
                tab.update(_class = "rheader_tab_here")
                previous = i and tablist[i-1] or None
            args = [r.id, component]
            tab.update(_href=URL(r=request, f=function, args=args, vars=_vars))
        else:
            if not r.component:
                tab.update(_class = "rheader_tab_here")
                previous = i and tablist[i-1] or None
            args = [r.id]
            vars = Storage(_vars)
            if not vars.get("_next", None):
                vars.update(_next=URL(r=request, f=function, args=args, vars=_vars))
            tab.update(_href=URL(r=request, f=function, args=args, vars=vars))

        tablist.append(tab)
        rheader_tabs.append(SPAN(A(tab.title, _href=tab._href), _class=tab._class))

    if rheader_tabs:
        if paging:
            if next:
                rheader_tabs.insert(0, SPAN(A(">", _href=next._href), _class="rheader_next_active"))
            else:
                rheader_tabs.insert(0, SPAN(">", _class="rheader_next_inactive"))
            if previous:
                rheader_tabs.insert(0, SPAN(A("<", _href=previous._href), _class="rheader_prev_active"))
            else:
                rheader_tabs.insert(0, SPAN("<", _class="rheader_prev_inactive"))
        rheader_tabs = DIV(rheader_tabs, _id="rheader_tabs")
    else:
        rheader_tabs = ""

    return rheader_tabs

# -----------------------------------------------------------------------------
