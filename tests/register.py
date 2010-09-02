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
        #  Register 
        sel.open("/sahana")
        sel.click("link=Register")
        sel.wait_for_page_to_load("30000")
        sel.click("t2_person_name")
        #sel.store_random("8", "user")
        #sel.store_random("8", "domain")
        email = "${user}@${domain}.com"
        sel.type("t2_person_name", "${user}")
        sel.type("t2_person_email", email)
        #sel.store_random("8", "password")
        sel.type("t2_person_password", "${password}")
        sel.click("//input[@value='Submit']")
        sel.wait_for_page_to_load("30000")
        try: self.failUnless(sel.is_text_present("You have been successfully registered"))
        except AssertionError, e: self.verificationErrors.append(str(e))
        #  Logout 
        sel.open("/sahana/default/login")
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")
        try: self.failUnless(sel.is_text_present("Logged Out"))
        except AssertionError, e: self.verificationErrors.append(str(e))
        #  Login 
        sel.open("/sahana/default/login")
        sel.click("link=Login")
        sel.wait_for_page_to_load("30000")
        sel.type("t2_person_email", "${email}")
        sel.type("t2_person_password", "${password}")
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