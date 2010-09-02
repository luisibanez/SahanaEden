"""This file was created by Selenium IDE.
Modified for a locally running instance of Sahana which is empty
Modified according to advice from Tim Farrell: http://groups.google.com/group/web2py/msg/d8c9fd6008029f6b
It is designed to be run by itself (it calls Selenium RC to open up a browser window)
The Python install needs to be prepared:
* easy_install selenium
* copy selenium-server.jar to site-packages
* copy seleniumtest.py to site-packages
"""
from selenium import selenium
import unittest, time, re
import seleniumtest

class NewTest(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://127.0.0.1:8000/")
        self.selenium.start()
    
    def test_new(self):
        sel = self.selenium
        sel.open("/sahana")
        # Register
        sel.click("link=Register")
        sel.wait_for_page_to_load("30000")
        sel.click("t2_person_name")
        sel.type("t2_person_name", "Joe Bloggs")
        sel.type("t2_person_email", "joe@bloggs.com")
        sel.type("t2_person_password", "joebloggs")
        sel.click("//input[@value='Submit']")
        sel.wait_for_page_to_load("30000")
        try: self.failUnless(sel.is_text_present("You have been successfully registered"))
        except AssertionError, e: self.verificationErrors.append(str(e))
        # Logout
        sel.open("/sahana/default/login")
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")
        try: self.failUnless(sel.is_text_present("Logged Out"))
        except AssertionError, e: self.verificationErrors.append(str(e))
        # Login
        sel.open("/sahana/default/login")
        sel.type("t2_person_email", "joe@bloggs.com")
        sel.type("t2_person_password", "joebloggs")
        sel.click("//input[@value='Submit']")
        sel.wait_for_page_to_load("30000")
        try: self.failUnless(sel.is_text_present("Logged In"))
        except AssertionError, e: self.verificationErrors.append(str(e))
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    #unittest.main()
    seleniumtest.runInSeleniumRC(unittest.main)() 
