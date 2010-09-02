
"""                                                                                                                            
    Healthscapes Geolytics Module                                                                                                   
                                                                                                                                                                               
                                                                                                                               
    @author: Nico Preston <nicopresto@gmail.com>                                                                                 
    @author: Colin Burreson <kasapo@gmail.com>                                                                         
    @author: Zack Krejci <zack.krejci@gmail.com>                                                                             
    @copyright: (c) 2010 Healthscapes                                                                             
    @license: MIT                                                                                                              
                                                                                                                               
    Permission is hereby granted, free of charge, to any person                                                                
    obtaining a copy of this software and associated documentation                                                             
    files (the "Software"), to deal in the Software without                                                                    
    restriction, including without limitation the rights to use,                                                               
    copy, modify, merge, publish, distribute, sublicense, and/or sell                                                          
    copies of the Software, and to permit persons to whom the                                                                  
    Software is furnished to do so, subject to the following                                                                   
    conditions:                                                                                                                
          
    The above copyright notice and this permission notice shall be                                                             
    included in all copies or substantial portions of the Software.                                                            
                                                                                                                               
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                                                            
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                                                            
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND                                                                   
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT                                                                
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,                                                               
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING                                                               
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR                                                              
    OTHER DEALINGS IN THE SOFTWARE.                                                                                            
                                                                                                                               
"""


from base import BoxElement, Script
from group import GroupableElement
from defs import Defs
from utils import ViewBox

class Canvas (GroupableElement, BoxElement):
    def __init__ (self, **attr):
        BoxElement.__init__ (self, name = 'svg', **attr)
        GroupableElement.__init__ (self, name = 'svg', **attr)
        if attr.has_key ('viewBox'):
            self.viewBox = attr['viewBox']
        else:
            self.viewBox = None

    def setSVG (self):
        attr = BoxElement.setSVG (self)
        attr.update (GroupableElement.setSVG (self))
        attr.update ([('viewBox', self.viewBox)])
        return attr


class PrintableCanvas (Canvas):
    def __init__ (self, **attr):
        Canvas.__init__ (self, **attr)
        self.xmlns = 'http://www.w3.org/2000/svg'
        self.xlink = 'http://www.w3.org/1999/xlink'
        self.ev = 'http://www.w3.org/2001/xml-events'
        self.defs = Defs ()
        self.scripts = []

    def addScript (self, filename):
        self.scripts.append (Script (filename))

    def setSVG (self):
        self.addDefTags ()
        if len (self.defs) > 0:
            self.drawAt (self.defs, 0)
        attr = Canvas.setSVG (self)
        attr.update ([('xmlns', self.xmlns),
                      ('xmlns:xlink', self.xlink),
                      ('xmlns:ev', self.ev)])
        return attr

    def addDefTags (self):
        dlist = {}
        for child in self:
            self.addDefs (child, dlist)
        for key, value in dlist.iteritems ():
            self.defs.draw (value)
        

    def addDefs (self, node, dlist):
        if hasattr (node, '__iter__'):
            for child in node:
                self.addDefs (child, dlist)
        if hasattr (node, 'defs'):
            for d in node.defs:
                dlist.update ([(d.id, d)])

    def SVG (self, indent):
        prepend = '<?xml version="1.0" standalone="no"?>\n'
        prepend += '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
        prepend += '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
        self.scripts.reverse ()
        for script in self.scripts:
            self.drawAt (script, 0)
        return prepend + Canvas.SVG (self, indent)

    def save (self, fileOrString):
        needToClose = False
        if isinstance (fileOrString, str):
            needToClose = True
            fileOrString = open (fileOrString, 'w')
        fileOrString.write (self.SVG (''))
        if needToClose:
            fileOrString.close ()
