"""
No description.
"""

S.open('/sahana/default/login')
S.clickAndWait('link=Logout')
S.verifyTextPresent('Logged Out')
