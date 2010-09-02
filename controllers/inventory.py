# -*- coding: utf-8 -*-

"""
    Inventory 
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16    
    
    A module to record inventories of items at a location (store)
"""

module = request.controller

response.menu_options = logs_menu

#==============================================================================
def shn_store_rheader(r, tabs=[]):
    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)
        inventory_store = r.record
        rheader = DIV(TABLE(TR(
                               TH(Tstr("Location") + ": "), shn_gis_location_represent(inventory_store.location_id),
                               TH(Tstr("Description") + ": "), inventory_store.comments,
                               ),
                           ),
                      rheader_tabs
                      )
        return rheader
    return None

def store():

    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # Don't send the locations list to client (pulled by AJAX instead)
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    def postp(jr, output):                          
        shn_action_buttons(jr)
        return output
    response.s3.postp = postp

    tabs = [
            (T("Details"), None),
            (T("Items"), "store_item"),
           ]
    rheader = lambda r: shn_store_rheader(r, tabs)

    return shn_rest_controller(module, resource, rheader=rheader)

def index():

    """
        Default to the inventory_store list view
        @TODO does not work with paginate!!!
    """

    request.function = "store"
    request.args = []
    return store()
    #module_name = deployment_settings.modules[module].name_nice
    #return dict(module_name=module_name)

#==============================================================================
def store_item():

    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
       
    def postp(jr, output):                          
        shn_action_buttons(jr)
        return output
    response.s3.postp = postp    
    
    return shn_rest_controller(module, resource)