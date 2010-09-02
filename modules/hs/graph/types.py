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



from base import Graph, UnifiedCanvas

from canvas import ScatterCanvas, DoubleScatterCanvas, BarCanvas 
#from canvas import ScatterCanvas, DoubleScatterCanvas, BarCanvas, LineCanvas, PieCanvas

from ..utils.struct import Vector2D as V

from ..graphics.utils import ViewBox, Translate
from ..graphics.shapes import Line, Rectangle

from axes import XAxis, YAxis


class UnifiedGraph (Graph):
    def __init__ (self, canvas,  **attr):
        Graph.__init__ (self, canvas)
        self.setProperties ()

    def setProperties (self):
        self.xaxis = True
        self.yaxis = True
        self.y2axis = True

    def boundingBox (self):
        bbox = Rectangle (x =  self.canvas.x,
                          y = self.canvas.y,
                          width=self.canvas.width, 
                          height = self.canvas.height)
        bbox.style.strokeColor = 'black'
        bbox.style.strokeWidth = '1'
        bbox.style.fill = 'none'
        self.dataGroup.draw (bbox)
        
    def background (self):
        barHeight = self.canvas.height / 6.0
        for i in range (6):
            rect = Rectangle (x = self.canvas.x,
                              y = (self.canvas.y + barHeight * i),
                              width = self.canvas.width,
                              height = barHeight)
            if i % 2 == 0:
                fill = '#efefef'
            else:
                fill = '#c1c1c1'
            rect.style.fill = fill
            rect.style.strokeWidth = 0
            rect.style.opacity = .35
            self.dataGroup.drawAt (rect, 0)

    def setXBounds (self):
        raise RuntimeError ()

    def setYBounds (self):
        raise RuntimeError ()
    
    def setY2Bounds (self):
        raise RuntimeError ()

    def createXAxisSpace (self):
        self.canvas.move (0, 10)
        self.canvas.changeSize (0, -10)

    def createXAxis (self):
        xbounds = self.setXBounds ()
        textProperties = {'textHeight': 8,
                          'horizontalAnchor': 'center',
                          }
        xaxis = XAxis (inf = self.canvas.x,
                       sup = self.canvas.x + self.canvas.width,
                       y = self.canvas.y - 1,
                       lower = xbounds[0],
                       upper = xbounds[1],
                       textProperties = textProperties)
        xaxis.createTicks ()
        xaxis.drawTicks ()
        self.dataGroup.drawAt (xaxis, 0)

    def createYAxis (self):
        ybounds = self.setYBounds ()
        textProperties = {'textHeight': 8,
                          'horizontalAnchor': 'right',
                          'verticalAnchor': 'middle',
                          }
        yaxis = YAxis (inf = self.canvas.y,
                       sup = self.canvas.y + self.canvas.height,
                       x = 0,
                       lower = ybounds[0],
                       upper = ybounds[1],
                       textProperties = textProperties)
        yaxis.createTicks ()
        yaxis.drawTicks ()
        self.canvas.changeSize (-yaxis.width - 5, 0)
        self.canvas.move (yaxis.width + 5, 0)
        yaxis.move (self.canvas.x - 1, 0)
        self.dataGroup.drawAt (yaxis, 0)

    def createY2Axis (self):
        ybounds = self.setY2Bounds ()
        textProperties = {'textHeight': 8,
                          'horizontalAnchor': 'left',
                          'verticalAnchor': 'middle',
                          }
        yaxis = YAxis (inf = self.canvas.y,
                       sup = self.canvas.y + self.canvas.height,
                       x = 0,
                       lower = ybounds[0],
                       upper = ybounds[1],
                       textProperties = textProperties)
        yaxis.createTicks ()
        yaxis.drawTicks ()
        self.canvas.changeSize (-yaxis.width - 5, 0)
        yaxis.move (self.canvas.x + self.canvas.width + 1, 0)
        self.dataGroup.drawAt (yaxis, 0)

    def finalize (self):
        self.canvas.setBounds ()
        if self.xaxis:
            self.createXAxisSpace ()
        if self.yaxis:
            self.createYAxis ()
        if self.y2axis:
            self.createY2Axis ()
        if self.xaxis:
            self.createXAxis ()
        Graph.finalize (self)
        self.background ()
        self.boundingBox ()
        self.canvas.finalize ()


class ScatterPlot (UnifiedGraph):
    def __init__ (self, **attr):
        UnifiedGraph.__init__ (self, ScatterCanvas, **attr)
        self.addScript ('/dmz/static/highlight.js')
        self.addScript ('/dmz/static/scatter.js')
        self.addScript ('/dmz/static/sScatter.js')

    def setColors (self, color1, color2, color3):
        self.canvas.color1 = color1
        self.canvas.color2 = color2
        self.canvas.color3 = color3

    def setProperties (self):
        self.xaxis = True
        self.yaxis = True
        self.y2axis = False

    def setXBounds (self):
        return (self.canvas.minX, self.canvas.maxX)

    def setYBounds (self):
        return (self.canvas.minY, self.canvas.maxY)

    def addPoint (self, name, x, y):
        self.canvas.drawPoint (name, x, y)


class DoubleScatterPlot (ScatterPlot):
    def __init__ (self, **attr):
        UnifiedGraph.__init__ (self, DoubleScatterCanvas, **attr)
        self.addScript('/dmz/static/highlight.js')
        self.addScript('/dmz/static/scatter.js')
        self.addScript('/dmz/static/dScatter.js')

    def setColors (self, color1, color2):
        self.canvas.color1 = color1
        self.canvas.color2 = color2

    def setProperties (self):
        self.xaxis = True
        self.yaxis = True
        self.y2axis = True

    def setY2Bounds (self):
        return (self.canvas.minY2, self.canvas.maxY2)

    def addPoint1 (self, name, x, y):
        self.canvas.drawPoint (name, x, y)        

    def addPoint2 (self, name, x, y):
        self.canvas.drawPoint2 (name, x, y)


class BarGraph (UnifiedGraph):
    def __init__ (self, **attr):
        UnifiedGraph.__init__ (self, BarCanvas, **attr)
        self.addScript('/dmz/static/highlight.js')

    def setProperties (self):
        self.xaxis = False
        self.yaxis = True
        self.y2axis = False

    def setYBounds (self):
        return (self.canvas.minY, self.canvas.maxY)

    def setColors (self, colors):
        self.canvas.colors = colors

    def addGroup (self, name, data):
        for key, value in data:
            self.canvas.addBar (name, key, value)
        self.canvas.addSpace ()


"""class ScatterPlot (Graph):
    def __init__ (self, **attr):
        Graph.__init__ (self, ScatterCanvas)
        #self.addCSS ('graph.css')
        #self.addJS ('highlight.js')
        #self.addJS ('sScatter.js')
        #self.addJS ('scatter.js')
        self.namelist = []
        self.xlist = []
        self.ylist = []
        self.xRule = None
        self.yRule = None
        self.canvas.maxPoint.y -= 10
        self.canvas.setSource (self.namelist, self.xlist, self.ylist)

    def setXBounds (self):
        self.xbounds = self.findExtents (min (self.xlist), max (self.xlist))

    def setYBounds (self):
        self.ybounds = self.findExtents (min (self.ylist), max (self.ylist))

    def findExtents (self, lower, upper):
        boundRange = upper - lower
        lb = lower - boundRange * .05
        ub = upper + boundRange * .05
        return (lb, ub)

    def setView (self):
        minBounds = V (self.xbounds[0], self.ybounds[0])
        maxBounds = V (self.xbounds[1], self.ybounds[1])
        currentView = ViewBox (minBounds, maxBounds)
        finalView = ViewBox (self.canvas.minPoint, self.canvas.maxPoint)
        self.canvas.setViews (currentView, finalView)
        
    def setXRule (self):    
        self.xRule = Line (V (0, 0), V (0, self.canvas.height ()))

    def setYRule (self):
        self.yRule = Line (V (0, 0), V (self.canvas.width (), 0))

    def setColors (self, color1, color2, color3):
        self.canvas.color1 = color1
        self.canvas.color2 = color2
        self.canvas.color3 = color3

    def yAxis (self):
        yaxis = Axis (V (0, self.canvas.maxPoint.y), V (0, self.canvas.minPoint.y), V (0 , 0), id='left-ticks')
        yaxis.setBounds (self.ybounds[0], self.ybounds[1])
        self.ySpace (yaxis.text)
        self.setYRule ()
        yaxis.setRule (self.yRule)
        yaxis.create ()
        yaxis.appendTransform (Translate (self.canvas.minPoint.x , 0))
        self.dataGroup.drawAt (yaxis, 0)

    def xAxis (self):
        self.setXRule ()
        xaxis = Axis (V (self.canvas.minPoint.x, self.canvas.minPoint.y),  
                      V (self.canvas.maxPoint.x, self.canvas.minPoint.y), 
                      V (0 , self.canvas.height ()), id='bottom-ticks')
        xaxis.setBounds (self.xbounds[0], self.xbounds[1])
        xaxis.setRule (self.xRule)
        xaxis.create ()
        self.dataGroup.drawAt (xaxis, 0)

    def ySpace (self, ticks):
        tickSpace = self.getLength (ticks)
        dist = tickSpace * 5 + 10
        self.canvas.minPoint.x += dist

    def getLength (self, strings):
        strings = map (str, strings)
        maxes = map (len, strings)
        return max (maxes)
    
    def addPoint (self, name, x, y):
        self.xlist.append (x)
        self.ylist.append (y)
        self.namelist.append (name)

    def create (self):
        self.setXBounds ()
        self.setYBounds ()
        self.setView ()

        self.yAxis ()
        self.xAxis ()
        self.canvas.create ()

    def setSVG (self):
        self.create ()
        Graph.setSVG (self)
        self.canvas.setAttribute ('minX', self.xbounds[0])
        self.canvas.setAttribute ('minY', self.ybounds[0])
        self.canvas.setAttribute ('maxX', self.xbounds[1])
        self.canvas.setAttribute ('maxY', self.ybounds[1])"""

"""class DoubleScatterPlot (ScatterPlot):
    def __init__ (self):
        Graph.__init__ (self, DoubleScatterCanvas)
        self.addCSS ('../static/graph.css') 
        self.addJS ('../static/highlight.js')
        self.addJS ('../static/dScatter.js')
        self.addJS ('../static/scatter.js')
        self.namelist = []
        self.xlist = []
        self.ylist = []
        self.xRule = None
        self.yRule = None
        self.canvas.maxPoint.y -= 10

        self.name2list = []
        self.x2list = []
        self.y2list = []
        self.canvas.setSource (self.namelist, self.xlist, self.ylist)
        self.canvas.setSource2 (self.name2list, self.x2list, self.y2list)

    def addPoint1 (self, name, x, y):
        self.addPoint (name, x, y)

    def addPoint2 (self, name, x, y):
        self.name2list.append (name)
        self.x2list.append (x)
        self.y2list.append (y)

    def setColors (self, color1, color2):
        self.canvas.color1 = color1
        self.canvas.color2 = color2

    def setXBounds (self):
        newXList = []
        for x in self.xlist:
            newXList.append (x)
        for x in self.x2list:
            newXList.append (x)
        self.xbounds = self.findExtents (min (newXList), max (newXList))

    def setY2Bounds (self):
        self.y2bounds = self.findExtents (min (self.y2list), max (self.y2list))

    def setXRule (self):
        self.xRule = None

    def setYRule (self):
        self.yRule = Line (V (0, 0), V (5, 0))

    def setY2Rule (self):
        self.y2Rule = Line (V (-5, 0), V (0, 0))

    def y2Space (self, ticks):
        tickSpace = self.getLength (ticks)
        dist = tickSpace * 5 + 10
        self.canvas.maxPoint.x -= dist

    def setView2 (self):
        minBounds = V (self.xbounds[0], self.y2bounds[0])
        maxBounds = V (self.xbounds[1], self.y2bounds[1])
        currentView = ViewBox (minBounds, maxBounds)
        finalView = ViewBox (self.canvas.minPoint, self.canvas.maxPoint)
        self.canvas.setViews2 (currentView, finalView)

    def y2Axis (self):
        yaxis = Axis (V (0, self.canvas.maxPoint.y), V (0, self.canvas.minPoint.y), V (0 , 0), id='right-ticks')
        yaxis.setBounds (self.y2bounds[0], self.y2bounds[1])
        self.y2Space (yaxis.text)
        self.setY2Rule ()
        yaxis.setRule (self.y2Rule)
        yaxis.create ()
        yaxis.appendTransform (Translate (self.canvas.maxPoint.x , 0))
        self.drawAt (yaxis, 0)

    def create (self):
        self.setXBounds ()
        self.setYBounds ()
        self.setY2Bounds ()
        self.setView ()
        self.setView2 ()

        self.yAxis ()
        self.xAxis ()
        self.y2Axis ()

        self.canvas.create ()

    def setSVG (self):
        ScatterPlot.setSVG (self)
        self.canvas.setAttribute ('minY2', self.y2bounds[0])
        self.canvas.setAttribute ('maxY2', self.y2bounds[1])"""


"""class BarGraph (Graph):
    def __init__ (self):
        Graph.__init__ (self, BarCanvas)
        #self.addCSS ('graph.css')
        #self.addJS ('highlight.js')
        self.data = []
        self.names = []
        self.groups = []
        self.canvas.setDataSource (self.data, self.names, self.groups)

    def setXBounds (self):
        self.xbounds = (0, len (self.data) - 1)

    def setYRule (self):
        self.yRule = Line (V (0, 0), V (self.canvas.width (), 0))

    def setYBounds (self):
        cleanedData = []
        for d in self.data:
            if d != None:
                cleanedData.append (d)
        self.ybounds = self.findExtents (min (cleanedData), max (cleanedData))

    def findExtents (self, lower, upper):
        boundRange = upper - lower
        lb = lower - boundRange * .05
        ub = upper + boundRange * .05
        return (lb, ub)

    def setView (self):
        minBounds = V (self.xbounds[0], self.ybounds[0])
        maxBounds = V (self.xbounds[1], self.ybounds[1])
        currentView = ViewBox (minBounds, maxBounds)
        finalView = ViewBox (self.canvas.minPoint, self.canvas.maxPoint)
        self.canvas.setViews (currentView, finalView)

    def addGroup (self, groupname, dataPairs):
        for key, value in dataPairs:
            self.data.append (value)
            self.names.append (key)
            self.groups.append (groupname)
            #self.namelist.append (str(groupname) + ': ' + str(key))
        self.data.append (None)
        self.names.append (None)
        self.groups.append (None)

    def ySpace (self, ticks):
        tickSpace = self.getLength (ticks)
        dist = tickSpace * 5 + 10
        self.canvas.minPoint.x += dist

    def getLength (self, strings):
        strings = map (str, strings)
        maxes = map (len, strings)
        return max (maxes)

    def yAxis (self):
        yaxis = Axis (V (0, self.canvas.maxPoint.y), V (0, self.canvas.minPoint.y), V (0 , 0), id='left-ticks')
        yaxis.setBounds (self.ybounds[0], self.ybounds[1])
        self.ySpace (yaxis.text)
        self.setYRule ()
        yaxis.setRule (self.yRule)
        yaxis.create ()
        yaxis.appendTransform (Translate (self.canvas.minPoint.x , 0))    
        self.drawAt (yaxis, 0)

    def setColors (self, colors):
        self.canvas.colors = colors

    def setSVG (self):
        self.create ()
        Graph.setSVG (self)

    def create (self):
        self.setXBounds ()
        self.setYBounds ()
        self.setView ()


        self.yAxis ()

        self.canvas.create ()"""


class LineChart (Graph):
    def __init__ (self):
        Graph.__init__ (self, LineCanvas)
        self.addCSS ('graph.css') 
        
    def addSeries (self, name, series):
        self.canvas.addData (name, series)
        
    def addColors (self, pairs):
        self.canvas.addColors (pairs)

    def setSeriesTitles (self, series):
        self.canvas.setSeriesTitles (series)

class PieChart (Graph):
    def __init__ (self):
        Graph.__init__ (self, PieCanvas)
        self.addCSS ('graph.css') 
        
    def addWedge (self, name, value):
        self.canvas.addData (name, value)

    def setSVG (self):
        self.canvas.create ()
        Graph.setSVG (self)

