# -*- coding: utf-8 -*-

"""
    OCR - Controllers
"""

import StringIO
#Importing reportlab stuff
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

# Fonts
Courier = 'Courier'
Helvetica = 'Helvetica'
Helvetica_Bold = 'Helvetica-Bold'
Helvetica_Bold_Oblique = 'Helvetica-BoldOblique'
Helvetica_Oblique = 'Helvetica-Oblique'

class Form:
    def __init__(self, pdfname = "ocrform.pdf", margintop = 20, marginsides = 20, **kw):
	"""Form initialization"""
        self.pdfpath = kw.get('pdfpath', pdfname)
        self.verbose = kw.get('verbose', 0)
	# set the default font sizes
        self.font = kw.get('typeface', Helvetica)
        self.fontsize = kw.get('fontsize', 13)
	# setting it to A4 for now
        self.canvas = Canvas(self.pdfpath, pagesize = A4)
	self.width, self.height = A4
	self.x = marginsides
	self.lastx = marginsides
	self.marginsides = marginsides
	self.margintop = margintop
	self.y = self.height - margintop

    def print_text(self, lines, fontsize = 8, gray = 0, seek = 0, continuetext = 0,style = "default"):
	"""Give the lines to be printed as a list, set the font and grey level"""
        c = self.canvas
        self.fontsize = fontsize
	if style == "center":
	   self.x = self.width/2
	if seek > (self.width - (self.marginsides + self.fontsize) ) :
	  seek = 0
	if seek != 0 :
	  self.x = self.x + seek
	if continuetext == 1:
	  self.x = self.lastx + seek
	  if seek == 0:
	    self.y = self.y + fontsize
        for line in lines:
            t = c.beginText(self.x, self.y)
            t.setFont(Helvetica, fontsize)
            t.setFillGray(gray)
            t.textOut(line)
            c.drawText(t)
	    self.y =  self.y - fontsize
	    self.lastx = t.getX()
	self.x = self.marginsides

    def draw_check_boxes(self, boxes = 1, seek = 0, continuetext = 0, fontsize = 0, gray = 0, style = ""):
	"""Function to draw check boxes default no of boxes = 1"""
        c = self.canvas
        c.setLineWidth(0.20)
	c.setStrokeGray(gray)
	if style == "center":
	   self.x = self.width/2
	if style == "right":
	   self.x = self.width - self.marginsides - self.fontsize
	if seek > (self.width - (self.marginsides + self.fontsize) ) :
	  seek = 0
	if continuetext == 1:
	  self.y = self.y + self.fontsize
	  self.x = self.lastx
	else:
	  self.y = self.y - self.fontsize
	if seek != 0 :
	  self.x = self.x + seek
	if fontsize == 0 :
	  fontsize = self.fontsize
	else:
	  self.fontsize = fontsize
	for i in range(boxes):
	  c.rect(self.x, self.y, self.fontsize, self.fontsize, stroke=1)
	  self.x = self.x + self.fontsize
	  if self.x > (self.width - (self.marginsides + self.fontsize) ) :
	    break
	self.x = self.marginsides
	self.y = self.y - self.fontsize

    def draw_line(self, gray = 0):
	"""Function to draw a straight line"""
        c = self.canvas
	c.setStrokeGray(gray)
        c.setLineWidth(0.40)
	self.y = self.y - (self.fontsize )
        c.line(self.x, self.y, self.width-self.x, self.y)
	self.y = self.y - (self.fontsize )

    def set_title(self,title = ""):
	c = self.canvas.setTitle(title)

    def save(self):
        self.canvas.save()


def create():
    """
    Function to create OCRforms from the tables

    """
    if len(request.args) == 0:
        session.error = T("Need to specify a table!")
        redirect(URL(r=request))
    output = StringIO.StringIO()
    form = Form(pdfname=output)
    _table = request.args(0)
    title = _table
    table = db[_table]
    import string
    title = string.capitalize(title.rpartition('_')[2])
    form.set_title(title)
    form.print_text([title], fontsize = 20, style = "center", seek = -100)
    form.print_text(["",Tstr("1. Fill the necessary fields in BLOCK letters."),
		        Tstr("2. Always use one box per letter and leave one box space to seperate words.")], fontsize = 13, gray = 0)
    form.draw_line()
    form.print_text([""])
    for field in table.fields:
        if field in ['id', 'created_on', 'modified_on', 'uuid', 'deleted','admin'] :
            # These aren't needed I guess
            pass
        else:
	  form.print_text([str(table[field].label)],fontsize = 13)
	  if table[field].type == "integer":
	    form.print_text([""]) # leave a space
	    for i in range(100):
	      try:
		choice = str(table[field].represent(i+1))
		form.print_text([str(i+1)+". "],seek = 20, fontsize = 12)
		form.print_text([choice],continuetext = 1, fontsize = 12)
		#form.draw_check_boxes(continuetext=1,style = "center",fontsize = 10, gray = 0.9) # reduce font size by 2
	      except:
		break
	    form.print_text([""]) # leave a space
	    form.print_text([Tstr("Put a choice in the box")], fontsize = 13, gray = 0)
	    form.draw_check_boxes(boxes = 2, continuetext=1, gray = 0.9, fontsize = 20, seek = 10)
	    form.print_text([""]) # leave a space
	  else:
	    form.draw_check_boxes(boxes = table[field].length,fontsize = 20, gray = 0.9)

    form.save()
    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.pdf')
    filename = "%s_%s.pdf" % (request.env.server_name, str(table))
    response.headers['Content-disposition'] = "attachment; filename=\"%s\"" % filename
    return output.read()
