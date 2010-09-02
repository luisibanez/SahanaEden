#!/usr/bin/env python 
# coding: utf8 
from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
# request, response, session, cache, T, db(s) 
# must be passed and cannot be imported!


try:
    from xlrd import *
except ImportError:
    pass
    # On server shows up in Apache error log
    print >> sys.stderr, "WARNING: %s: XLRD not installed" % __name__

import os

def removerowcol(path_to_file):
    
    spreadsheet = list()
    wb = open_workbook(path_to_file)
    s = wb.sheet_by_index(0)  
    for r in range(0, s.nrows):
        l = list()
        for c in range(0, s.ncols):
            l.append(s.cell(r, c).value)
        check = 0
        for k in range(0, len(l)):
            if l[k] is not "":
                check += 1
        if check is not 0:
            spreadsheet.append(l)
        l = list()
    new_col = len(spreadsheet[0])
    new_row = len(spreadsheet)
    empty_column = list()
    for x in range(0, new_col):
        l = list()
        for y in range(0, new_row):
            l.append(spreadsheet[y][x])
        ck = 0
        for k in l:
            if k is not "":
                ck += 1
        if ck is 0:
            empty_column.append(x)
    #removing empty columns
    new_spreadsheet = list()
    for x in range(0, new_row):
        l = list()
        for y in range(0,new_col):
            if y not in empty_column:
                l.append(spreadsheet[x][y])
        new_spreadsheet.append(l)
    return new_spreadsheet

def json(path_to_file, appname):
    spreadsheet = removerowcol(path_to_file)
    nrow = len(spreadsheet)
    ncol = len(spreadsheet[0])
    json = "{"
    json += "\"rows\": %i,\n" % nrow
    json += "\"columns\": %i,\n" %ncol
    json += "\"data\": [\n"
    for x in range(0, nrow):
        json += "{\n"
        json += "\t\"id\":%i," % (x)
        for y in range(0, ncol):
            temp = "\n\t\"column%i\":" % y
            try:
		cell = str(spreadsheet[x][y])    
            	cell = cell.replace("\n", "")
		temp += "\"" + cell + "\""
            except:
            	temp += "\"\""
            if(y is not ncol - 1): 
                temp += ","
            json += temp
        json += "\n\t}"
        if x is not nrow - 1:
            json += "\n\t,"


    json += "\n]}"
    '''jsonfile = open("/%s/static/test1.json" % appname, "wb")
    jsonfile.write(json)
    jsonfile.close()
    '''
    return json

def pathfind(filename):
    str  =  os.path.join("uploads", filename)
    return str

def jaro_winkler(str1, str2):
	"""Return Jaro_Winkler distance of two strings (between 0.0 and 1.0)

	ARGUMENTS:
	  str1  The first string
	  str2  The second string

	"""

	jaro_winkler_marker_char = chr(1)
	if (str1 == str2):
	    return 1.0

	len1 = len(str1)
	len2 = len(str2)
	halflen = max(len1,len2) / 2 - 1

	ass1  = ""  # Characters assigned in str1
	ass2  = "" # Characters assigned in str2
	workstr1 = str1
	workstr2 = str2

	common1 = 0    # Number of common characters
	common2 = 0

	for i in range(len1):
	    start = max(0, i - halflen)
	    end   = min(i + halflen + 1, len2)
	    index = workstr2.find(str1[i], start, end)
	    if (index > -1):    # Found common character
		common1 += 1
		ass1 = ass1 + str1[i]
		workstr2 = workstr2[:index] + jaro_winkler_marker_char + workstr2[index + 1:]
	
	for i in range(len2):
	    start = max(0, i - halflen)
	    end   = min(i + halflen + 1, len1)
	    index = workstr1.find(str2[i], start, end)
	    #print 'len2', str2[i], start, end, index, ass1, workstr1, common2
	    if (index > -1):    # Found common character
		common2 += 1
		#ass2 += str2[i]
		ass2 = ass2 + str2[i]
		workstr1 = workstr1[:index] + jaro_winkler_marker_char + workstr1[index + 1:]

	if (common1 != common2):
	    print('Winkler: Wrong common values for strings "%s" and "%s"' % \
			(str1, str2) + ', common1: %i, common2: %i' % (common1, common2) + \
			', common should be the same.')
	    common1 = float(common1 + common2) / 2.0   

	if (common1 == 0):
	    return 0.0

	# Compute number of transpositions
	transposition = 0
	for i in range(len(ass1)):
	    if (ass1[i] != ass2[i]):
		transposition += 1
	transposition = transposition / 2.0

	# Compute number of characters are common at beginning of both strings, for Jaro-Winkler distance
	
	minlen = min(len1, len2)
	for same in range(minlen + 1):
	    if (str1[:same] != str2[:same]):
		break
	same -= 1
	if (same > 4):
	    same = 4

	common1 = float(common1)
	w = 1. / 3. * (common1 / float(len1) + common1 / float(len2) + (common1 - transposition) / common1)

	wn = w + same * 0.1 * (1.0 - w)
	return wn


def jaro_winkler_distance_row(row1, row2):
    '''
       Used as a measure of similarity between two strings, 
       see http://en.wikipedia.org/wiki/Jaro-Winkler_distance
    '''
    num_similar = 0
    for x in range(0, len(row1)):
        str1 = row1[x]
	str2 = row2[x]
	dw = jaro_winkler(str1, str2)
	if dw > 0.8:
	   num_similar += 1
    if num_similar > (0.75 * (len(row1))):
        return True
    else:
	return False
