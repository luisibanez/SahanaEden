# -*- coding: utf-8 -*-

"""
    Logistics
"""

module = request.controller

response.menu_options = logs_menu

def index():

    """
        Simple Home Page
    """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)
