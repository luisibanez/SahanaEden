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



from ..utils.struct import Vector2D as V
from ..graphics.group import Group
from ..graphics.shapes import Text, Line

from copy import deepcopy

class Axis (Group):
    def __init__ (self, **attr):
        Group.__init__ (self, **attr)
        self.incr = None
        if attr.has_key ('inf'):
            self.inf = attr['inf']
        else:
            self.inf = 0
        if attr.has_key ('sup'):
            self.sup = attr['sup']
        else:
            self.sup = 0
        if attr.has_key ('lower'):
            self.lower = attr['lower']
        else:
            self.lower = 0
        if attr.has_key ('upper'):
            self.upper = attr['upper']
        else:
            self.upper = 0
        if attr.has_key ('textProperties'):
            self.textProperties = attr['textProperties']
        else:
            self.textPrperties = {}

    def bounds (self, lower, upper):
        self.lower = lower
        self.upper = upper

    def increment (self, incr=None):
        self.incr = incr

    def findIncrement (self):
        numberRange = self.upper - self.lower
        if numberRange == 0:
            raise RuntimeError ('upper == lower')
        incr = 0
        div = 1.0
        if numberRange < 1:
            while numberRange / pow (10, incr) < 1:
                incr -= 1
            #incr += 1
        elif numberRange > 1:
            while numberRange / pow (10, incr) > 1:
                incr += 1
            incr -= 1
        ticks = self.tickPositions (pow (10, incr) / div)
        if len (ticks) < 2:
            incr -= 1
        elif len (ticks) < 5:
            div = 2
        return pow (10, incr) / div


        ## TMP Break
        """self.incr = (incr, div)
        self.setTickPositions ()
        numTicks = len (self.positions)
        if numTicks <= 1:
            incr -= 1
        elif numTicks < 5:
            div = 2
        return (incr, div)"""

    def setText (self, text=None):
        if text:
            self.labels = text
        else:
            self.labels = self.ticks

    def tickPositions (self, incr):
        current = 0
        ticks = []
        while current > self.lower:
            current -= incr
        while current < self.lower:
            current += incr
        while current <= self.upper:
            ticks.append (current)
            current += incr
        return ticks

    def createTicks (self):
        if not self.incr:
            self.incr = self.findIncrement ()
        ticks = self.tickPositions (self.incr)
        self.ticks = []
        self.labels = []
        for tick in ticks:
            per = ((tick - self.lower) / (self.upper - self.lower))
            val = ((1 - per) * self.inf) + (per * self.sup)
            self.ticks.append (val)
            self.labels.append (str (tick))
        return deepcopy (self.ticks)

    def drawTicks (self):
        raise NotImplementedError ()

    def move (self, dx, dy):
        for child in self:
            child.move (dx, dy)


class XAxis (Axis):
    def __init__ (self, **attr):
        Axis.__init__ (self, **attr)
        if attr.has_key ('y'):
            self.y = attr['y']
        else:
            self.y = 0

    def drawTicks (self):
        for pos, label in zip (self.ticks, self.labels):
            t = Text(text = label, x = pos, y = self.y, **self.textProperties)
            self.draw (t)

class YAxis (Axis):
    def __init__ (self, **attr):
        Axis.__init__ (self, **attr)
        if attr.has_key ('x'):
            self.x = attr['x']
        else:
            self.x = 0

    def drawTicks (self):
        width = []
        for pos, label in zip (self.ticks, self.labels):
            t = Text(text = label, y = pos, x = self.x, **self.textProperties)
            width.append (t.width)
            self.draw (t)
        self.width = max (width)


class RegressionLine (Line):
    def __init__ (self, xdata, ydata, xbounds, ybounds):
        from rpy2.robjects import RFormula
        from rpy2 import rinterface as R

        R.initr ()
        R.globalEnv['x'] = R.FloatSexpVector (xdata)
        R.globalEnv['y'] = R.FloatSexpVector (ydata)
        formula = RFormula ('y ~ x')
        rLine = R.globalEnv.get ('lm')(formula)
        slope = rLine[0][1]
        intercept = rLine[0][0]

        y1 = slope * xbounds[0] + intercept
        y2 = slope * xbounds[1] + intercept

        p1 = (xbounds[0], y1)
        p2 = (xbounds[1], y2)

        Line.__init__ (self, point1 = p1, point2 = p2)


"""class Axis (Group):
    def __init__ (self, inf, sup, tickOffset, **attr):
        Group.__init__ (self, **attr)
        self.inf = inf
        self.sup = sup
        self.lower = inf
        self.upper = sup
        self.offset = tickOffset
        self.increment = None
        self.rule = None

    def drawTicks (self):
        ruleGroup = Group (className='axis-lines')
        textGroup = Group (className='axes-text')
        for label, pos in zip (self.text, self.positions):
            if self.rule:
                rule = deepcopy (self.rule)
                rule.translate (pos)
                ruleGroup.draw (rule)
            tPos = pos + self.offset
            textGroup.draw (Text (text = str(label), 
                                  x = tPos.x, 
                                  y = tPos.y,
                                  horizontalAnchor = 'center',
                                  textHeight = 8))
        #self.draw (Line (self.inf, self.sup))
        self.draw (ruleGroup)
        self.draw (textGroup)

    def setBounds (self, lower, upper):
        self.lower = lower
        self.upper = upper
        self.setTickPositions ()
        self.setTickText ()

    def setTickPositions (self):
        if not self.increment:
            self.setIncrement ()
        power = self.increment[0]
        div =  self.increment[1]
        increment = pow (10, power) / div
        self.initialPositions = []
        current = 0
        if self.lower < 0:
            while current > self.lower:
                current -= increment
        while current < self.lower:
            current += increment
        while current <= self.upper:
            self.initialPositions.append (current)
            current += increment

        self.positions = []

        for p in self.initialPositions:
            p -= self.lower
            p /= (self.upper - self.lower)
            pos = self.inf + (self.sup - self.inf) * p
            self.positions.append (pos)

    def setTickText (self, text = None):
        if not text:
            self.text = []
            for p in self.initialPositions:
                self.text.append (p)
        else:
            self.text = text

    def setRule (self, rule):
        self.rule = rule
    
    def setIncrement (self, incr=None):
        if not incr:
            self.findIncrement ()
        else:
            self.increment = incr

    def findIncrement (self):
        numberRange = self.upper - self.lower
        incr = 0
        div = 1
        if numberRange < 1:
            while numberRange / pow (10, incr) < 1:
                incr -= 1
            incr += 1
        elif numberRange > 1:
            while numberRange / pow (10, incr) > 1:
                incr += 1
            incr -= 1
        self.increment = (incr, div)
        self.setTickPositions ()
        numTicks = len (self.positions)
        if numTicks <= 1:
            incr -= 1
        elif numTicks < 5:
            div = 2
        self.increment = (incr, div)

    def create (self):
        self.drawTicks ()
        
"""
