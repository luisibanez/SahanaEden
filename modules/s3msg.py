# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__doc__ = \
"""
Module providing an API to send messages
- Currently SMS and Email
"""

__author__ = "Praneeth Bodduluri <lifeeth[at]gmail.com>"

import string
import urllib

DELETECHARS = string.translate(string.printable, string.maketrans(string.printable, string.printable), string.digits)

class Msg(object):
    """ Toolkit for hooking into the Messaging framework """

    sms_api_post_config = {}
    sms_api_enabled = False

    def __init__(self, environment, db=None, T=None, mail=None, modem=None):
        try:
            self.db = db
            settings = db(db.msg_setting.id > 0).select(limitby=(0, 1)).first()
            self.default_country_code = settings.default_country_code
            self.outgoing_is_gateway = settings.outgoing_sms_handler == "Gateway"
            self.sms_api = db(db.msg_gateway_settings.enabled == True).select(limitby=(0, 1)).first()
            if self.sms_api:
                tmp_parameters = self.sms_api.parameters.split("&")
                self.sms_api_enabled = self.sms_api.enabled
                for tmp_parameter in tmp_parameters:
                    self.sms_api_post_config[tmp_parameter.split("=")[0]] = tmp_parameter.split("=")[1]
            self.mail = mail
            self.modem = modem
        except:
            pass

    def sanitise_phone(self, phone):
        """
        Strip out unnecessary characters from the string:
        +()- & space
        """

        clean = string.translate(phone, None, DELETECHARS)

        # If number starts with a 0 then need to remove this & add the country code in
        if clean[0] == "0":
            # Add default country code
            if self.default_country_code == 39:
                # Italy keeps 0 after country code
                clean = str(self.default_country_code) + clean
            else:
                clean = str(self.default_country_code) + string.lstrip(clean, "0")

        return clean
    
    def send_sms_via_modem(self, mobile, text=""):
        """
        Function to send SMS via locally-attached Modem
        """
        
        mobile = self.sanitise_phone(mobile)

        # Add '+' before country code
        mobile = "+" + mobile
        
        try:
            self.modem.send_sms(mobile, text)
            return True
        except:
            return False

    def send_sms_via_api(self, mobile, text=""):
        """
        Function to send SMS via API
        """
        
        mobile = self.sanitise_phone(mobile)
        
        try:
            self.sms_api_post_config[self.sms_api.message_variable] = text
            self.sms_api_post_config[self.sms_api.to_variable] = str(mobile)
            query = urllib.urlencode(self.sms_api_post_config)
            request = urllib.urlopen(self.sms_api.url, query)
            output = request.read()
            return True
        except:
            return False

    def send_email_via_api(self, to, subject, message):
        """
        Function to send Email via API
        - simple Wrapper over Web2Py's Email API
        """

        return self.mail.send(to, subject, message)

    def check_pe_id_validity(self, pe_id):
        """ To check if the pe_id passed is valid or not """

        db = self.db

        if pe_id == db(db.pr_person.pe_id == 1).select(db.pr_person.pe_id, limitby=(0, 1)).first()["pe_id"]:
            return True
        else:
            return False

    def send_by_pe_id(self,
                      pe_id,
                      subject="",
                      message="",
                      sender_pe_id = None,
                      pr_message_method = 1,
                      sender="",
                      fromaddress="",
                      system_generated = False):
        """ As the function name suggests - depends on pr_message_method """

        db = self.db

        try:
            message_log_id = db.msg_log.insert(pe_id = sender_pe_id,
                                               subject = subject,
                                               message = message,
                                               sender  = sender,
                                               fromaddress = fromaddress)
        except:
            return False
            #2) This is not transaction safe - power failure in the middle will cause no message in the outbox

        if isinstance(pe_id, list):
            listindex = 0
            for prpeid in pe_id:
                try:
                    db.msg_outbox.insert(message_id = message_log_id,
                                         pe_id = prpeid,
                                         pr_message_method = pr_message_method,
                                         system_generated = system_generated)
                    listindex = listindex + 1
                except:
                    return listindex
        else:
            try:
                db.msg_outbox.insert(message_id = message_log_id,
                                     pe_id = pe_id,
                                     pr_message_method = pr_message_method,
                                     system_generated = system_generated)
            except:
                return False
        # Explicitly commit DB operations when running from Cron
        db.commit()
        return True

    def send_email_by_pe_id(self,
                            pe_id,
                            subject="",
                            message="",
                            sender_pe_id=None,
                            sender="",
                            fromaddress="",
                            system_generated=False):
        """ API wrapper over send_by_pe_id - depends on pr_message_method """
        
        return self.send_by_pe_id(pe_id,
                                  subject,
                                  message,
                                  sender_pe_id,
                                  1, # To set as an email
                                  sender,
                                  fromaddress,
                                  system_generated)

    def process_outbox(self, contact_method=1, option=1): #pr_message_method dependent
        """
        Send Pending Messages from Outbox.
        If succesful then move from Outbox to Sent. A modified copy of send_email
        """

        db = self.db

        table = self.db.msg_outbox
        query = ((table.status == 1) & (table.pr_message_method == contact_method))
        rows = db(query).select()
        chainrun = False # Used to fire process_outbox again - Used when messages are sent to groups
        for row in rows:
            status = True
            message_id = row.message_id
            logrow = db(db.msg_log.id == message_id).select(limitby=(0, 1)).first()
            # Get message from msg_log
            message = logrow.message
            subject = logrow.subject
            sender_pe_id = logrow.pe_id
            # Determine list of users
            entity = row.pe_id
            table2 = db.pr_pentity
            query = table2.id == entity
            entity_type = db(query).select(table2.pe_type, limitby=(0, 1)).first().pe_type
            def dispatch_to_pe_id(pe_id):
                table3 = db.pr_pe_contact
                query = (table3.pe_id == pe_id) & (table3.contact_method == contact_method)
                recipient = db(query).select(table3.value, orderby = table3.priority, limitby=(0, 1)).first()
                if recipient:
                    if (contact_method == 2 and option == 2):
                        if self.outgoing_is_gateway:
                            return False
                        else:
                            return self.send_sms_via_modem(recipient.value, message)
                    if (contact_method == 2 and option == 1):
                        if self.outgoing_is_gateway:
                            return self.send_sms_via_api(recipient.value, message)
                        else:
                            return False
                    if (contact_method == 1):
                        return self.send_email_via_api(recipient.value, subject, message)
                return False

            if entity_type == "pr_group":
                # Take the entities of it and add in the messaging queue - with
                # sender as the original sender and marks group email processed
                # Set system generated = True
                table3 = db.pr_group
                query = (table3.pe_id == entity)
                group_id = db(query).select(table3.id, limitby=(0, 1)).first().id
                table4 = db.pr_group_membership
                query = (table4.group_id == group_id)
                recipients = db(query).select()
                for recipient in recipients:
                    person_id = recipient.person_id
                    table5 = db.pr_person
                    query = (table5.id == person_id)
                    pe_id = db(query).select(table5.pe_id, limitby=(0, 1)).first().pe_id
                    db.msg_outbox.insert(message_id = message_id,
                                         pe_id = pe_id,
                                         pr_message_method = contact_method,
                                         system_generated = True)
                status = True
                chainrun = True

            if entity_type == "pr_person":
                # Person
                status = dispatch_to_pe_id(entity)

            if status:
                # Update status to sent in Outbox
                db(table.id == row.id).update(status=2)
                # Set message log to actioned
                db(db.msg_log.id == message_id).update(actioned=True)
                # Explicitly commit DB operations when running from Cron
                db.commit()

        if chainrun :
            self.process_outbox(contact_method, option)

        return

    def receive_msg(self,
                      subject="",
                      message="",
                      sender="",
                      fromaddress="",
                      system_generated = False,
                      inbound = True,
                      pr_message_method = 1,
                      ):
        """ Function to call to drop messages into msg_log """

        db = self.db

        try:
            message_log_id = db.msg_log.insert(inbound = inbound,
                                               subject = subject,
                                               message = message,
                                               sender  = sender,
                                               fromaddress = fromaddress,
                                               )
        except:
            return False
            #2) This is not transaction safe - power failure in the middle will cause no message in the outbox
        try:
            db.msg_channel.insert(message_id = message_log_id,
                                    pr_message_method = pr_message_method)
        except:
            return False
        # Explicitly commit DB operations when running from Cron
        db.commit()
        return True
