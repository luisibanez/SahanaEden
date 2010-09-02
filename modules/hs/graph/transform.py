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



from ..utils.struct import Matrix
from ..utils.struct import Vector2D as V

from ..graph.base import Group
from ..graphics.shapes import Line

#from ..graphics.shapes import Circle

from rpy2.robjects import RFormula
from rpy2 import rinterface as R

class TransformableGroup (Group):
    def __init__ (self, **attr):
        Group.__init__ (self, **attr)

    def setCurrentView (self, view):
        self.currentView = view

    def setFinalView (self,view):
        self.finalView = view
        #self.draw (Circle (1, Vector (336, 2626)))

    #def transformChildren (self, node, mapping):
    #    if hasattr (node, 'transform'):
    #        node.transform (mapping)
    #    if hasattr (node, '__iter__'):
    #        for child in node:
    #            self.transformChildren (child, mapping)

    def create (self):
        matrix1 = Matrix (3, 3)
        matrix1.set (-self.currentView.min.x, 0, 2)
        matrix1.set (-self.currentView.min.y, 1, 2)

        currentRange = self.currentView.max - self.currentView.min
        finalRange = self.finalView.max - self.finalView.min

        matrix2 = Matrix (3, 3)
        matrix2.set (float (finalRange.x) / float (currentRange.x), 0, 0)
        matrix2.set (float (finalRange.y) / float (currentRange.y), 1, 1)
        
        matrix3 = Matrix (3, 3)
        matrix3.set (self.finalView.min.x, 0, 2)
        matrix3.set (self.finalView.min.y, 1, 2)

        self.transform ((matrix3 * (matrix2 * matrix1)))

class RegressionLine (TransformableGroup):
    def __init__ (self, **attr):
        TransformableGroup.__init__ (self, **attr)
        self.xdata = None
        self.ydata = None

    def setSource (self, xdata, ydata):
        self.xdata = xdata
        self.ydata = ydata

    #def addData (self, x, y):
    #    self.xdata.append (x)
    #    self.ydata.append (y)

    def create (self):
        R.initr ()
        R.globalEnv['x'] = R.FloatSexpVector (self.xdata)
        R.globalEnv['y'] = R.FloatSexpVector (self.ydata)
        formula = RFormula ('y ~ x')
        rLine = R.globalEnv.get ('lm')(formula)
        slope = rLine[0][1]
        intercept = rLine[0][0]

        y1 = slope * self.currentView.min.x + intercept
        y2 = slope * self.currentView.max.x + intercept

        p1 = V (self.currentView.min.x, y1)
        p2 = V (self.currentView.max.x, y2)

        self.draw (Line (p1, p2, className='regression-line'))
        self.draw (Line (p1, p2, className='regression-shadow'))

        TransformableGroup.create (self)
        
