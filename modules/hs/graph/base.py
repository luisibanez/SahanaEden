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




from ..graphics.image import Canvas, PrintableCanvas
from ..graphics.group import Group, Grouping
from ..graphics.shapes import Line, Rectangle, Text
from ..graphics.utils import ViewBox, Translate, Rotate

from ..utils.struct import Matrix
from ..utils.struct import Vector2D as V


class Graph (PrintableCanvas):
    def __init__ (self, canvasType):
        view = ViewBox (0, 0, 300, 200)
        PrintableCanvas.__init__ (self, viewBox = view)

        self.dataGroup = Grouping ()
        self.canvas = canvasType (width = 300, height = 200, 
                                  id='canvas-root')
        self.initialFormatting ()

    def initialFormatting  (self):
        self.draw (self.dataGroup)
        self.dataGroup.draw (self.canvas)

        # Format Label Group
        self.labels = Group (className = 'labels')

        # Format Title
        self.title = Text (text = '', id = 'title', textHeight= 15, horizontalAnchor = 'center')

        # Format X Label
        self.xlabel = Text (text = '', id = 'xlabel', textHeight = 10, verticalAnchor = 'bottom', horizontalAnchor = 'center')

        # Format Y Label
        self.ylabel = Group ()
        ylabelRotate = Rotate (-90)
        #self.ylabelTranslate = Translate (-100, 0)
        self.ylabel.appendTransform (ylabelRotate)
        #self.ylabel.appendTransform (self.ylabelTranslate)
        self.ylabelText = Text (text = '', id = 'ylabel', textHeight = 10, horizontalAnchor = 'center')
        self.ylabel.draw (self.ylabelText)

        # Format Y2 Label
        self.y2label = Group ()
        y2labelRotate = Rotate (90, 300, 0)
        self.y2label.appendTransform (y2labelRotate)
        self.y2labelText = Text (text = '', id = 'y2label', textHeight = 10, horizontalAnchor = 'center')
        self.y2label.draw (self.y2labelText)

    def positionLabels (self):
        topY = 200.0 - (self.canvas.height + self.canvas.y)
        midX = self.canvas.x + (self.canvas.width) / 2.0
        midY = topY + (self.canvas.height) / 2.0 

        # Title Position
        self.title.move (150, 5)

        # Y Label Position
        self.ylabelText.move (-midY, 5)
    
        # X Label Position
        self.xlabel.move (midX, 195) 

        # Y2 Label Position
        self.y2labelText.move (300 + midY, 5)

    def setTitle (self, title):
        self.title.setText (title)
        self.labels.draw (self.title)
        self.canvas.changeSize (0, -22)

    def setXLabel (self, xlabel):
        self.xlabel.setText (xlabel)
        self.labels.draw (self.xlabel)
        self.canvas.move (0, 17)
        self.canvas.changeSize (0, -17) 

    def setYLabel (self, ylabel):
        self.ylabelText.setText (ylabel)
        self.labels.draw (self.ylabel)
        self.canvas.move (17, 0)
        self.canvas.changeSize (-17, 0)

    def setY2Label (self, ylabel):
        self.y2labelText.setText (ylabel)
        self.labels.draw (self.y2label)
        self.canvas.changeSize (-17, 0)

    def finalize (self):
        self.dataGroup.transform.set (-1, 1, 1)
        self.dataGroup.transform.set (self.viewBox.y + self.viewBox.height, 1, 2)
        self.positionLabels ()
        if len (self.labels) > 0:
            self.drawAt (self.labels, 1)


class GraphCanvas (Canvas):
    def __init__ (self, **attr):
        Canvas.__init__ (self, **attr)

    def changeSize (self, dx, dy):
        self.width += dx
        self.height += dy

    def move (self, dx, dy):
        self.x += dx
        self.y += dy

    def makeTransform (self, minX, maxX, minY, maxY):
        matrix1 = Matrix (3, 3)
        matrix1.set (-minX, 0, 2)
        matrix1.set (-minY, 1, 2)

        currentRangeX = float (maxX - minX)
        currentRangeY = float (maxY - minY)

        matrix2 = Matrix (3, 3)
        matrix2.set (self.width / currentRangeX, 0, 0)
        matrix2.set (self.height / currentRangeY, 1, 1)
        
        matrix3 = Matrix (3, 3)
        matrix3.set (self.x, 0, 2)
        matrix3.set (self.y, 1, 2)
        return (matrix3 * (matrix2 * matrix1))

    def setSVG (self):
        attr = Canvas.setSVG (self)
        if not attr['viewBox']:
            attr['viewBox'] = ViewBox (attr['x'],
                                       attr['y'], 
                                       attr['x'] + attr['width'],
                                       attr['y'] + attr['height'])
        return attr

class UnifiedCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
    

"""class MeasurableCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
        self.name = 'g'

    def setSVG (self):
        x1 = self.minPoint.x
        y1 = self.minPoint.y
        x2 = self.maxPoint.x
        y2 = self.maxPoint.y
        axes = Path (V (x1, y1), V (x2, y1), V (x2, y2), V (x1, y2), id='axes')
        axes.closed = True
        self.drawAt (axes, 2)

        GraphCanvas.setSVG (self)"""
