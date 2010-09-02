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



from base import Element
from utils import attributesToSVG, ViewBox

from ..utils.struct import identity

class GroupableElement (Element):
    def __init__ (self, **attr):
        Element.__init__ (self, **attr)
        self.children = []
        self.transform = identity (3)

    def clear (self):
        for child in self.children:
            child.parent = None
        self.children = []
    
    def draw (self, nodeToDraw):
        nodeToDraw.parent = self
        self.children.append (nodeToDraw)

    def nodePosition (self, nodeToFind):
        index = 0
        for node in self.children:
            if nodeToFind is node:
                return index
            index += 1
        return None

    def drawBefore (self, nodeToDraw, existingNode):
        index = self.nodePosition (existingNode)
        if index is None:
            raise RuntimeError ('Element not inserted')
        self.drawAt (nodeToDraw, index)

    def drawAfter (self, nodeToDraw, existingNode):
        index = self.nodePosition (existingNode)
        if index is None:
            raise RuntimeError ('Element not inserted')
        self.drawAt (nodeToDraw, index + 1)

    def drawAt (self, nodeToDraw, index):
        nodeToDraw.parent = self
        self.children.insert (index, nodeToDraw)
        
    def getElementById (self, id):
        for node in self.children:
            if node.id == id:
                return node
        return None

    def getElementByName (self, name):
        for node in self.children:
            if node.name == name:
                return node
        return None

    def removeElementById (self, id):
        index = 0
        for node in self.children:
           if node.id == id:
               self.children[index].parent = None
               del self.children[index]
               return
           else:
               index += 1

    def __len__ (self):
        return len (self.children)

    def __iter__ (self):
        return iter (self.children)

    def childrenSVG (self, indent):
        output = ''
        for child in self.children:
            output += child.SVG (indent)
        return output

    def SVG (self, indent):
        attr = self.setSVG ()
        nextIndent = indent + '    '
        if len (self) > 0:
            output = indent + '<' + self.name
            attributes = attributesToSVG (attr)
            if attributes != '':
                output += ' ' + attributes
            output += '>\n'
            output += self.childrenSVG (nextIndent)
            output += indent + '</' + self.name + '>\n'
        else:
            output = Element.SVG (self, indent)
        return output

class Grouping (GroupableElement):
    def __init__ (self, **attr):
        GroupableElement.__init__ (self, **attr)

    def SVG (self, indent):
        return self.childrenSVG (indent)


class Group (GroupableElement):
    def __init__ (self, **attr):
        GroupableElement.__init__ (self, name = 'g', **attr)
        self.postTransforms = []

    def appendTransform (self, transform):
        self.postTransforms.append (transform)

    def setSVG (self):
        attr = GroupableElement.setSVG (self)
        transforms = ' '.join (map (str, self.postTransforms))
        if transforms != '':
            attr.update ([('transform', transforms)])
        return attr
