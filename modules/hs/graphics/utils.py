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


class ViewBox:
    def __init__ (self, minX, minY, maxX, maxY):
        self.x = minX
        self.y = minY
        self.width = maxX - minX
        self.height = maxY - minY
    
    def __str__ (self):
        values = map (str, [self.x, self.y, self.width, self.height])
        return ' '.join (values)

### OLD CODE ###
"""class ViewBox:
    def __init__ (self, min = V(0, 0), max = V(1, 1)):
        self.min = min
        self.max = max

    def __str__ (self):
        diff = (self.max - self.min)
        vals = [self.min.x, self.min.y, diff.x, diff.y]
        return ' '.join (map (str, vals))"""


class Translate:
    def __init__ (self, x, y):
        self.x = x
        self.y = y
        
    def __str__ (self):
        return 'translate(' + str(self.x) + ',' + str(self.y) + ')'

class Rotate:
    def __init__ (self, angle, x = None, y = None):
        self.angle = angle
        self.x = x
        self.y = y
        
    def __str__ (self):
        output = 'rotate(' + str (self.angle)
        if not ((self.x is None) or (self.y is None)):
            output += ',' + str(self.x) + ',' + str(self.y)
        output += ')'
        return output

def color_from_hex (string):
    if len (string) != 6:
        raise RuntimeError ('Not a hex color')
    red = int ('0x' + string[0:2], 0)
    green = int ('0x' + string[2:4], 0)
    blue = int ('0x' + string [4:6], 0)
    return Color (red, green, blue)

class Color:
    def __init__ (self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue
        
    def interpolate (self, c, percent):
        return ((c * percent) + (self * (1.0 - percent)))

    def __add__ (self, c):
        r = self.red + c.red
        g = self.green + c.green
        b = self.blue + c.blue
        return Color (r, g, b)

    def __mul__ (self, scalar):
        r = self.red * scalar
        g = self.green * scalar
        b = self.blue * scalar
        return Color (r, g, b)

    def __str__ (self):
        rgb = 'rgb('
        rgb += str(int(self.red))+ ',' 
        rgb += str(int(self.green))+ ',' 
        rgb += str(int(self.blue))+ ')' 
        return rgb

red = Color (200, 10, 10)
green = Color (10, 200, 10)
blue = Color (10, 10, 200)


def attributesToSVG (dictionary):
    output = []
    for key, value in dictionary.iteritems ():
        if not value is None:
            attr = key + '="' + str (value) + '"'
            output.append (attr)
    return ' '.join (output)
