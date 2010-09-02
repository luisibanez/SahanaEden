# -*- coding: utf-8 -*-

"""
    Project 
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25    
    
    Project Management
"""

module = request.controller

response.menu_options = org_menu

#==============================================================================
# @ToDo: Create should be restricted to Admin
def activity_type():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    return shn_rest_controller(module, resource, listadd=False)

#==============================================================================
def activity():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    def postp(jr, output):                          
        shn_action_buttons(jr)
        return output
    response.s3.postp = postp
        
    return shn_rest_controller(module, resource)