# -*- coding: utf-8 -*-

"""
    Auth Controllers
"""

def user():
    "Defined in admin module, so redirect there"
    
    redirect(URL(r=request, c="admin", args=request.args, vars=request.vars))

def group():
    "Defined in admin module, so redirect there"
    
    redirect(URL(r=request, c="admin", args=request.args, vars=request.vars))

def membership():
    "Defined in admin module, so redirect there"
    
    redirect(URL(r=request, c="admin", args=request.args, vars=request.vars))
