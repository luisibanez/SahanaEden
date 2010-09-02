# -*- coding: utf-8 -*-

"""
    Disaster Victim Registry - Controllers

    @author: nursix
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Add Disaster Victims'), False,  URL(r=request, f='index'),[
        [T('Add new Group'), False, URL(r=request, f='index')],
        [T('Add new Individual'), False, URL(r=request, f='index')]
    ]],
    [T('Edit Disaster Victims'), False,  URL(r=request, f='index'),[
        [T('Search and Edit Group'), False, URL(r=request, f='index')],
        [T('Search and Edit Individual'), False, URL(r=request, f='index')]
    ]],
    [T('List Groups'), False,  URL(r=request, f='index'),[
        [T('List Groups/View Members'), False, URL(r=request, f='index')]
    ]],
    [T('Reports'), False,  URL(r=request, f='index'),[
        [T('Drill Down by Group'), False, URL(r=request, f='index')],
        [T('Drill Down by Shelter'), False, URL(r=request, f='index')],
        [T('Drill Down by Incident'), False, URL(r=request, f='index')]
    ]],
]

def index():
    "Module's Home Page"
    
    module_name = deployment_settings.modules[module].name_nice
    
    return dict(module_name=module_name)
