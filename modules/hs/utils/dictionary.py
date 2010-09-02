"""                                                                                                                            
    Healthscapes Geolytics Module                                                                                                   
                                                                                                                               
    @author: Nico Preston <nicopresto@gmail.com>                                                                                   @author: Colin Burreson <kasapo@gmail.com>                                                                         
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



class Dictionary (dict):
    def __init__ (self):
        self._keys = []
        #self._sorted = True
        dict.__init__(self)
    
    def update (self, pairs):
        try:
            for key, value in pairs.iteritems ():
                if not self.has_key (key):
                    self._keys.append (key)
        except AttributeError:
            for pair in pairs:
                if not self.has_key (pair[0]):
                    self._keys.append (pair[0])                   
        #for key in pairs:
        #    print key
        #    try:
        #        self[key]
        #    except KeyError:
        #        self._keys.append (key)
        #self._sorted = False
        dict.update (self, pairs)

    def __iter__ (self):
        return DictIterator (self, iter(self._keys))


class DictIterator:
    def __init__ (self, dictionary, listIter):
        self._dictionary = dictionary
        self._listIter = listIter
        
    def __iter__ (self):
        return self

    def next (self):
        key = self._listIter.next ()
        return (key, self._dictionary[key])


class DefaultDictionary (Dictionary):
    def __init__ (self, default):
        self.default = default
        Dictionary.__init__ (self)

    def __getitem__ (self, item):
        try:
            return dict.__getitem__ (self, item)
        except KeyError:
            if not self.default is None:
                return self.default
            else:
                raise KeyError ()
