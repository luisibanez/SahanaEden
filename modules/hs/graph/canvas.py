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



from ..graphics.shapes import Circle, Line, Rectangle, Sector
from ..graphics.group import Group
from ..graphics.utils import red, green, blue

from ..utils.struct import Vector2D as V, Matrix
from ..utils.dictionary import DefaultDictionary

from axes import RegressionLine

from base import GraphCanvas

from copy import deepcopy

from math import pi

class ScatterCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
        self.data = Group (id = 'data')
        self.color1 = red
        self.color2 = green
        self.color3 = blue

    def drawPoint (self, name, x, y):
        c = Circle (radius = 2, x = x, y = y)
        c.xml['data'] = name
        self.data.draw (c)

    def addColor (self):
        for circle in self.data:
            perX = (circle.x - self.minX) / (self.maxX - self.minX)
            perY = (circle.y - self.minY) / (self.maxY - self.minY)
            c1 = self.color2.interpolate (self.color3, perX)
            c2 = self.color2.interpolate (self.color1, perY)
            per = (perY + (1 - perX)) / 2.0
            c = c1.interpolate (c2, per)
            circle.style.fill = c

    def setBounds (self):
        self.xlist = []
        self.ylist = []
        for child in self.data:
            self.xlist.append (child.x)
            self.ylist.append (child.y)
        
        minX = min (self.xlist)
        maxX = max (self.xlist)
        minY = min (self.ylist)
        maxY = max (self.ylist)

        self.minX = minX - minX * .05
        self.maxX = maxX + maxX * .05
        self.minY = minY - minY * .05
        self.maxY = maxY + maxY * .05

        self.xml['minX'] = self.minX
        self.xml['maxX'] = self.maxX
        self.xml['minY'] = self.minY
        self.xml['maxY'] = self.maxY

    def setRegLine (self):
        r = RegressionLine (self.xlist, self.ylist,
                            (self.minX, self.maxX),
                            (self.minY, self.maxY))
        r.style.strokeWidth = 1
        r.style.strokeColor = 'black'
        self.data.draw (r)

    def finalize (self):
        if len (self.data) > 0:
            self.draw (self.data)

        self.setRegLine ()
        self.addColor ()

        self.data.transform = self.makeTransform (self.minX, self.maxX, self.minY, self.maxY)

class DoubleScatterCanvas (ScatterCanvas):
    def __init__ (self, **attr):
        ScatterCanvas.__init__ (self, **attr)
        self.data2 = Group (id = 'data2')

    def drawPoint2 (self, name, x, y):
        c = Circle (radius = 2, x = x, y = y)
        c.xml['data'] = name
        self.data2.draw (c)

    def addColor (self):
        for child in self.data:
            child.style.fill = self.color1
        for child in self.data2:
            child.style.fill = self.color2

    def setBounds (self):
        self.xlist = []
        self.x2list = []
        self.ylist = []
        self.y2list = []
        for child in self.data:
            self.xlist.append (child.x)
            self.ylist.append (child.y)

        for child in self.data2:
            self.x2list.append (child.x)
            self.y2list.append (child.y)
        
        minX = min (self.xlist + self.x2list)
        maxX = max (self.xlist + self.x2list)
        minY = min (self.ylist)
        maxY = max (self.ylist)
        minY2 = min (self.y2list)
        maxY2 = max (self.y2list)

        self.minX = minX - minX * .05
        self.maxX = maxX + maxX * .05
        self.minY= minY - minY * .05
        self.maxY = maxY + maxY * .05
        self.minY2 = minY2 - minY2 * .05
        self.maxY2 = maxY2 + maxY2 * .05

        self.xml['minX'] = self.minX
        self.xml['maxX'] = self.maxX
        self.xml['minY'] = self.minY
        self.xml['maxY'] = self.maxY
        self.xml['minY2'] = self.minY2
        self.xml['maxY2'] = self.maxY2

    def setRegLine (self):
        r = RegressionLine (self.xlist, self.ylist,
                            (self.minX, self.maxX),
                            (self.minY, self.maxY))
        r.style.strokeWidth = 1
        r.style.strokeColor = self.color1
        self.data.draw (r)

    def setRegLine2 (self):
        r = RegressionLine (self.xlist, self.y2list,
                            (self.minX, self.maxX),
                            (self.minY2, self.maxY2))
        r.style.strokeWidth = 1
        r.style.strokeColor = self.color2
        self.data2.draw (r)

    def finalize (self):
        ScatterCanvas.finalize (self)
        if len (self.data2) > 0:
            self.draw(self.data2)
        self.setRegLine2 ()
        self.data2.transform = self.makeTransform (self.minX, self.maxX, self.minY2, self.maxY2)


class BarCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
        self.data = Group (id = 'data')
        self.counter = 0
        self.colors = {}

    def addBar (self, group, name, val):
        rect = Rectangle (x = self.counter, y = 0, height = val, width = 1)
        self.data.draw (rect)
        rect.xml['group'] = group
        rect.xml['name'] = name
        rect.xml['data'] = str(group) + ' ' + str(name) + ': ' + str (val)
        self.counter += 1
        
    def addSpace (self):
        self.counter += 1

    def setBounds (self):
        ylist = []
        for child in self.data:
            ylist.append (child.height)
        
        minY = min (ylist)
        maxY = max (ylist)

        self.minX = 0
        self.maxX = self.counter
        self.minY = minY - minY * .05
        self.maxY = maxY + maxY * .05

        self.xml['minX'] = self.minX
        self.xml['maxX'] = self.maxX
        self.xml['minY'] = self.minY
        self.xml['maxY'] = self.maxY


    def addColor (self):
        for child in self.data:
            try:
                key = child.xml['name']
                child.style.fill = self.colors[key]
            except KeyError:
                pass

    def finalize (self):
        self.addColor ()
        if len (self.data) > 0:
            self.draw (self.data)

        self.data.transform = self.makeTransform (self.minX, self.maxX, self.minY, self.maxY)
        

"""class ScatterCanvas (MeasurableCanvas):
    def __init__ (self, **attr):
        MeasurableCanvas.__init__ (self, **attr)
        self.data = TransformableGroup (id='data')
        self.regLine = RegressionLine ()
        self.color1 = red
        self.color2 = green
        self.color3 = blue

    def setSource (self, namedata, xdata, ydata):
        self.namedata = namedata
        self.xdata = xdata
        self.ydata = ydata
        self.regLine.setSource (xdata, ydata)
        
    def setViews (self, current, final):
        self.data.setCurrentView (current)
        self.data.setFinalView (final)

        self.regLine.setCurrentView (current)
        self.regLine.setFinalView (final)

    def drawData (self):
        for name, x, y in zip (self.namedata, self.xdata, self.ydata):
            shp = self.marker (V (x, y))
            shp.setAttribute ('name', name)
            self.data.draw (shp)
        #self.data.setCurrentView (self.currentView)
        #self.data.setFinalView (self.finalView)
        self.data.create ()
        self.draw (self.data)
        for node in self.data:
            self.addColor (node)

    def regression (self):
        #self.regLine.setCurrentView (self.currentView)
        #self.regLine.setFinalView (self.finalView)
        self.regLine.create ()
        self.draw (self.regLine)

    def addColor (self, node):
        pos = node.pos
        viewRange = self.maxPoint - self.minPoint
        perX = (pos - self.minPoint).x / viewRange.x
        perY = ((pos - self.minPoint).y / viewRange.y)
        c1 = self.color2.interpolate (self.color3, perX)
        c2 = self.color2.interpolate (self.color1, perY)
        per = (perY + (1 - perX)) / 2.0
        c = c1.interpolate (c2, per)
        node.setAttribute ('fill', c)
        
    def marker (self, pos):
        c = Circle (2, pos)
        return c

    #def addData (self, name, x, y):
    #    self.regLine.addData (x, y)
    #    c = Circle (2, V (x, y))
    #    c.setAttribute ('name', name)
    #    self.data.draw (c)
    
    def create (self):
        self.regression ()
        self.drawData ()"""


"""class DoubleScatterCanvas (ScatterCanvas):
    def __init__ (self, **attr):
        ScatterCanvas.__init__ (self, **attr)
        self.regLine2 = RegressionLine ()
        self.data2 = TransformableGroup (id='data-2')
        self.x2data = None
        self.y2data = None
        self.color1 = 'rgb(200,10,10)'
        self.color2 = 'rgb(10,10,200)'

    def setSource2 (self, namedata, xdata, ydata):
        self.name2data = namedata
        self.x2data = xdata
        self.y2data = ydata
        self.regLine2.setSource (xdata, ydata)

    def setViews2 (self, current, final):
        self.data2.setCurrentView (current)
        self.data2.setFinalView (final)
        self.regLine2.setCurrentView (current)
        self.regLine2.setFinalView (final)


    def drawData2 (self):
        for name, x, y in zip (self.name2data, self.x2data, self.y2data):
            shp = self.marker (V (x, y))
            shp.setAttribute ('name', name)
            self.data2.draw (shp)
        self.data2.create ()
        self.draw (self.data2)
        for node in self.data2:
            self.addColor (node, False)

    def addColor (self, node, group1 = True):
        if group1:
            node.setAttribute ('fill', self.color1)
        else:
            node.setAttribute ('fill', self.color2)

    #def addData (self, name, x, y, group1 = True):
    #    if group1:
    #        regLine = self.regLine
    #        data = self.data
    #    else:
    #        regLine = self.regLine2
    #        data = self.data2
    #    regLine.addData (x, y)
    #    c = Circle (2, V (x, y))
    #    c.setAttribute ('name', name)
    #    data.draw (c)
            
    def regression2 (self):
        self.regLine2.create ()
        self.draw (self.regLine2)

    def create (self):
        ScatterCanvas.create (self)
        self.regression2 ()
        self.drawData2 ()"""

class LineCanvas (ScatterCanvas):
    pass


"""class ScatterCanvas (MeasurableCanvas):
    def __init__ (self, **attr):
        MeasurableCanvas.__init__ (self, **attr)
        self.xlist = []
        self.ylist = []
        self.namelist = []
        self.data = TransformableGroup (id='data')
        self.regLine = RegressionLine ()

    def addPoint (self, name, x, y):
        self.regLine.addData (x, y)
        self.xlist.append (x)
        self.ylist.append (y)
        c = Circle (2, V (x, y))
        c.setAttribute ('name', name)
        self.data.draw (c)

    def addColor (self, node):
        pos = node.pos
        viewRange = self.viewBox.max - self.viewBox.min
        perX = (pos - self.viewBox.min).x / viewRange.x
        perY = 1 - ((pos - self.viewBox.min).y / viewRange.y)
        c1 = green.interpolate (blue, perX)
        c2 = green.interpolate (red, perY)
        per = (perY + (1 - perX)) / 2.0
        c = c1.interpolate (c2, per)
        node.setAttribute ('fill', c)

    def ySpace (self, ticks):
        tickSpace = self.getLength (ticks)
        dist = tickSpace * 5 + 10
        self.viewBox.min.x -= dist
        self.viewBox.max.x -= dist

    def getLength (self, strings):
        strings = map (str, strings)
        maxes = map (len, strings)
        return max (maxes)

    def regression (self):
        self.regLine.setCurrentView (self.currentView)
        self.regLine.setFinalView (self.finalView)
        self.regLine.create ()
        self.draw (self.regLine)"""


"""regGroup = TransformableGroup ()
        R.initr ()
        R.globalEnv['x'] = R.FloatSexpVector (self.xlist)
        R.globalEnv['y'] = R.FloatSexpVector (self.ylist)
        formula = RFormula ('y ~ x')
        rLine = R.globalEnv.get ('lm')(formula)
        slope = rLine[0][1]
        intercept = rLine[0][0]

        y1 = slope * self.xbounds[0] + intercept
        y2 = slope * self.xbounds[1] + intercept

        p1 = V (self.xbounds[0], y1)
        p2 = V (self.xbounds[1], y2)

        regGroup.draw (Line (p1, p2, id='regression-line'))
        regGroup.draw (Line (p1, p2, id='regression-shadow'))

        regGroup.setCurrentView (self.currentView)
        regGroup.setFinalView (self.finalView)
        regGroup.create ()
        self.draw (regGroup)"""

"""def yAxis (self):
        yaxis = Axis (V (0, 0),  V (0, self.viewBox.max.y), V (0 , 0), id='left-ticks')
        yaxis.setBounds (self.ybounds[0], self.ybounds[1])
        yaxis.setRule (Line (V (0, 0), V (self.viewBox.max.x, 0)))
        yaxis.create ()
        self.ySpace (yaxis.text)
        self.draw (yaxis)

    def xAxis (self):
        xaxis = Axis (V (0, 0),  V (self.viewBox.max.x, 0), V (0 , 0), id='bottom-ticks')
        xaxis.setBounds (self.xbounds[0], self.xbounds[1])
        xaxis.setRule (Line (V (0, 0), V (0, self.viewBox.max.y)))
        xaxis.create ()
        self.draw (xaxis)

    def drawData (self):
        self.data.setCurrentView (self.currentView)
        self.data.setFinalView (self.finalView)
        self.data.create ()
        self.draw (self.data)
        for node in self.data:
            self.addColor (node)

    def findExtents (self, lower, upper):
        boundRange = upper - lower
        lb = lower - boundRange * .05
        ub = upper + boundRange * .05
        return (lb, ub)

    def setBounds (self):
        self.xbounds = self.findExtents (min (self.xlist), max (self.xlist))
        self.ybounds = self.findExtents (min (self.ylist), max (self.ylist))
        minBounds = V (self.xbounds[0], self.ybounds[0])
        maxBounds = V (self.xbounds[1], self.ybounds[1])
        self.currentView = ViewBox (minBounds, maxBounds)
        self.finalView = ViewBox (V (0, 0), self.viewBox.max)

    #def findExtents (self):
    #   xb = self.getBounds (min (self.xlist), max (self.xlist))
    #    yb = self.getBounds (min (self.ylist), max (self.ylist))
    #    return (xb, yb)

    def setSVG (self): 
        self.viewBox.max.y -= 10
        
        self.setBounds ()

        self.yAxis ()
        self.xAxis ()
        self.regression ()
        self.drawData ()

        self.setAttribute ('minX', self.xbounds[0])
        self.setAttribute ('minY', self.ybounds[0])
        self.setAttribute ('maxX', self.xbounds[1])
        self.setAttribute ('maxY', self.ybounds[1])

        MeasurableCanvas.setSVG (self)

        self.viewBox.max.y += 10

class DoubleScatterCanvas (ScatterCanvas):
    def __init__ (self):
        ScatterCanvas.__init__ (self)
        self.x2list = []
        self.y2list = []

    def addPoint1 (self, name, x, y):
        ScatterCanvas.addPoint (self, name, x, y)
        
    def addPoint2 (self, name, x, y):
        self.x2list.append (x)
        self.y2list.append (y)
        c = Circle (2, V (x, y))
        c.setAttribute ('name', name)
        self.data2.draw (c)

    def setBounds (self):
        self.y2bounds = self.getBounds (min (self.y2list), max (self.y2list))
        ScatterCanvas.setBounds (self)

    def y2Axis (self):
        yaxis = Axis (V (self.viewBox.max.x, 0),  
                      V (self.viewBox.max.x, self.viewBox.max.y), 
                      V (0 , 0), id='left-2-ticks')
        yaxis.setBounds (self.y2bounds[0], self.y2bounds[1])
        yaxis.setRule (Line (V (0, 0), V (self.viewBox.max.x, 0)))
        yaxis.create ()
        self.ySpace (yaxis.text)
        self.draw (yaxis)
        
    def setSVG (self):
        ScatterCanvas.setSVG (self)
        self.y2Axis ()"""


"""class LineCanvas (ScatterCanvas):
    def __init__ (self, **attr):
        ScatterCanvas.__init__ (self, **attr)
        self.colors = {}

    def findExtents (self):
        xb =  self.getBounds (min (self.xlist), max (self.xlist))
        yb = self.getBounds (min (self.ylist), max (self.ylist))
        return (xb, yb)

    def regression (self):
        return

    def addData (self, name, series):
        group = Group ()
        group.setAttribute ('name', name)
        prev = None
        path = []
        for i, value in enumerate (series):
            if not value is None:
                self.addPoint (group, i, value)
                path.append (V (i, value))
        if len (path) > 0 :
            self.addLine (group, path)
        self.data.draw (group)

    def addColors (self, pairs):
        self.colors.update (pairs)

    def addPoint (self, group, x, y):
        self.xlist.append (x)
        self.ylist.append (y)
        c = Circle (2, V (x, y))
        group.draw (c)
            
    def addLine (self, group, path):
        p = Path (*path)
        p.closed = False
        p.setAttribute ('fill', 'none')
        p.setAttribute ('stroke-width', '2')
        group.draw (p)

    def setSeriesTitles (self, seriesList):
        self.seriesNames = seriesList

    def setXTickText (self, ticks):
        return self.seriesNames

    def addColor (self, node):
        name =node.getAttribute('name')
        if self.colors.has_key (name):
            color = self.colors[name]
        else:
            color = 'black'
        node.setAttribute ('style', 'fill: ' + color)
        node.setAttribute ('stroke', color)

    def setXIncrement (self):
        return (0, 1)"""

class PieCanvas (GraphCanvas):
    def __init__ (self, **attr):
        GraphCanvas.__init__ (self, **attr)
        self.names = []
        self.data = []

    def addData (self, name, value):
        self.names.append (name)
        self.data.append (float (value))

    def create (self):
        total = sum (self.data)
        angle = 0
        for point in self.data:
            delta = (point / total) * (2.0 * pi)
            s = Sector (100, angle, angle + delta)
            s.setAttribute ('fill', 'red')
            s.setAttribute ('stroke', 'black')
            self.draw (s)
            angle += delta


"""class BarCanvas:
    def __init__ (self, **attr):
        MeasurableCanvas.__init__ (self, **attr)
        self.data = TransformableGroup (id='data')
        self.dataPoints = None
        self.colors = DefaultDictionary ('rgb(200,10,10)')
        self.counter = 0

    def setDataSource (self, datalist, namelist, grouplist):
        self.dataPoints = datalist
        self.names = namelist
        self.groups = grouplist

    def setViews (self, currentView, finalView):
        self.currentView = currentView
        self.finalView = finalView

    #def addBar (self, data):
    #    self.dataPoints.append (data)

    #def addSpace (self):
    #    self.dataPoints.append (None)
        
    def drawBars (self):
        self.data.setCurrentView (self.currentView)
        self.data.setFinalView (self.finalView)
        for value, name, group in zip (self.dataPoints, self.names, self.groups):
            if value != None: 
                h = value - self.currentView.min.y
                r = Rectangle (V (self.counter, self.currentView.min.y),
                               width=1, height=h)
                r.setAttribute ('fill', self.colors[name])
                r.setAttribute ('name', str(group) + ': ' + str(name))
                self.data.draw (r)
            self.counter += 1
        self.data.create ()
        self.draw (self.data)

    def create (self):
        self.drawBars ()"""

"""class BarCanvas (MeasurableCanvas):
    def __init__ (self, **attr):
        MeasurableCanvas.__init__ (self, **attr)
        self.data = Group (id='data')
        self.draw (self.data)
        self.counter = 0.0
        self.datalist = []
        self.rules = Group (id='rule-lines')
        self.drawAt (self.rules, 0)
        self.leftTicks = Group (id='left-ticks')
        
    def addBar (self, name, val):
        self.datalist.append (val)

        rect = Rectangle (V (self.counter, val), height = 0, width = 1.0)
        self.data.draw (rect)
        self.counter += 1
        
    def addSpace (self):
        self.counter += 1

    def yNumbers (self, ticks):
        self.draw (self.leftTicks)
        tickSpace = self.getLength (ticks)
        dist = tickSpace * 5 + 10
        self.viewBox.min.x -= dist
        self.viewBox.max.x -= dist
        translates = []
        for t in ticks:
            translates.append (V (0, t))
        textGroup = self.labels (ticks, translates)
        for text in textGroup:
            self.leftTicks.draw (text)

    def getLength (self, strings):
        strings = map (str, strings)
        maxes = map (len, strings)
        return max (maxes)

    def horizontalLines (self, yTicks):
        translates = []
        for point in yTicks:
            translates.append (V (0, point))
        minPoint = V (self.minBounds.x, 0)
        maxPoint = V (self.maxBounds.x, 0)
        protoline = Line (minPoint, maxPoint)
        horizontal = self.lines (protoline, translates)
        for line in horizontal:
            self.rules.draw (line)

    def setSVG (self):
        xb = (0, self.counter - 1)
        yb = self.getBounds (min (self.datalist), max (self.datalist))
        self.setBounds (xbounds = xb, ybounds = yb)
        for bar in self.data:
            if bar.name == 'rect':
                bar.changeSize (0, -bar.minPoint.y + self.minBounds.y)
                bar.setAttribute ('fill', 'rgb(210,10,10)')

        yinc = self.increment (self.minBounds.y, self.maxBounds.y)
        yTicks = self.ticks (yinc, self.minBounds.y, self.maxBounds.y)
        self.horizontalLines (yTicks)
        self.yNumbers (yTicks)

        MeasurableCanvas.setSVG (self)
        
        for node in self.leftTicks:
            node.minPoint.x = -1
"""
