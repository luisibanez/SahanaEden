# coding: utf8

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

import gluon.contrib.simplejson as json
importer = local_import("importer")

response.menu_options = [
    [
	    T("Upload Spreadsheet"), False, URL(r=request, f="spreadsheet", args=["create"])
    ]
]

module_name = deployment_settings.modules[module].name_nice

def index():
    # Bypass Index page
    redirect( URL(r=request, c="importer", f="spreadsheet/create"))
    return dict(module_name=module_name)

@auth.requires_membership("Administrator")
def spreadsheet():
    """ RESTful Controller """
    resource = request.function
    crud.settings.create_onaccept = lambda form: redirect(URL(r=request, c="importer", f="spreadsheetview")) 
    return shn_rest_controller(module, resource, listadd=False)

def spreadsheetview():
    k = db(db.importer_spreadsheet.id > 0).select(limitby=(0, 1)).last()
    k = k.path;
    str = importer.pathfind(k)
    str = request.folder + str
    temp = importer.removerowcol(str)
    #appname = request.application
    v = importer.json(str, request.folder)
    #fields = shn_get_writecolumns(
    return dict(ss=v)
    
def import_spreadsheet():
    spreadsheet = request.body.read()
    from StringIO import StringIO
    spreadsheet_json = StringIO(spreadsheet)
    spreadsheet_json.seek(0)
    #j = json.loads(spreadsheet)
    exec("j = " + spreadsheet)
    similar_rows = []
    importable_rows = []
    if j.has_key("header_row"):
         j["spreadsheet"].pop(j["header_row"])
         j["rows"] -= 1
    if j.has_key("re_import"):
        for x in range(0, len(j["map"])):
	    j["map"][x][2] = j["map"][x][2].replace("&gt;", ">")
    if not j.has_key("re_import"):# and j["re_import"] is not True:
    	for x in range(0, len(j["spreadsheet"])):
	    for y in range(x + 1, len(j["spreadsheet"])):
 	        k = importer.jaro_winkler_distance_row(j["spreadsheet"][x], j["spreadsheet"][y])
	        if k is True:
	           similar_rows.append(j["spreadsheet"][x])
	           similar_rows.append(j["spreadsheet"][y])
	        else:
	           pass 
	for k in similar_rows:
	    for l in k:
	       l = l.encode("ascii")
        session.similar_rows = similar_rows
    for k in j["spreadsheet"]:
        if k in similar_rows:
	    j["spreadsheet"].remove(k)
	    j["rows"] -= 1
    i = k = 0
    send_dict = {}
    resource = j["resource"].encode("ascii")
    send_dict[resource] = []
    while (i < j["rows"]):
	res = {}
	k = 0
	while (k < j["columns"]):
	    if " --> " in j["map"][k][2]:
		field, nested_resource, nested_field = j["map"][k][2].split(" --> ")
		field = "$k_" + field
		nr = nested_resource
		nested_resource= "$_" + nested_resource
		if res.has_key(field) is False: 
		   res[field] = {}
		   res[field]["@resource"] = nr 
		   res[field][nested_resource] = [{}]
		res[field][nested_resource][0][nested_field] = j["spreadsheet"][i][k].encode("ascii")
		k += 1
		continue
	    if "opt_" in j["map"][k][2]:
		res[j["map"][k][2].encode("ascii")]["@value"] = j["spreadsheet"][i][k].encode("ascii")
	    	res[j["map"][k][2].encode("ascii")]["$"] = j["spreadsheet"][i][k].encode("ascii")
	    else:
		res[j["map"][k][2].encode("ascii")] = j["spreadsheet"][i][k].encode("ascii")
		if j["map"][k][2].encode("ascii") == "comments":
			res[j["map"][k][2].encode("ascii")] = j["map"][k][1] + "-->" + j["spreadsheet"][i][k].encode("ascii")
	    res["@modified_at"] = j["modtime"]
	    k += 1
	send_dict[resource].append(res)
	i += 1
	
    word = json.dumps(send_dict[resource])
    # Remove all white spaces and newlines in the JSON
    new_word = ""
    cntr = 1
    for i in range(0,len(word)):
        if word[i] == "\"":
           cntr = cntr + 1
      	   cntr = cntr % 2
        if cntr == 0:
           new_word += word[i]
        if cntr == 1:
           if word[i] == " " or word[i] == "\n":
	      continue
           else:
    	      new_word += word[i] 
    # new_word is without newlines and whitespaces	  
    new_word  = "{\"$_" + resource + "\":"+ new_word + "}"
    # added resource name
    send = StringIO(new_word)
    tree = s3xrc.xml.json2tree(send)
    prefix, name = resource.split("_")
    res = s3xrc.resource(prefix, name)
    res.import_xml(source = tree, ignore_errors = True)
    returned_json = s3xrc.xml.tree2json(tree)
    if "@error" not in repr(returned_json):
	    return dict(module_name = module_name)
    invalid_rows = []
    exec("returned_json = " + returned_json)
    for record in returned_json["$_"+resource]:
	 del record["@modified_at"]
    for record in returned_json["$_"+resource]:
	wrong_dict = {}
        for field in record:
	    if field[0:3] == "$k_":
		nest_res = "$_" + record[field]["@resource"]
		for nested_fields in record[field][nest_res][0]:
		    if "@error" in record[field][nest_res][0][nested_fields]:
		       	wrong_dict[field + " --> " + nest_res + " --> " + nested_fields] = "*_error_*" + record[field][nest_res][0][nested_fields.encode("ascii")]["@error"] + " You entered " + record[field][nest_res][0][nested_fields.encode("ascii")]["@value"]
		    else:
			    try:	    
			        wrong_dict[field + " --> " + nest_res + " --> " + nested_fields] = record[field][nest_res][0][nested_fields.encode("ascii")]["@value"]
			    except:
				    wrong_dict[field + " --> " + nest_res + " --> " + nested_fields] = record[field][nest_res][0][nested_fields.encode("ascii")]
	    else:
	        if "@error" in record[field]:
		    wrong_dict[field] = "*_error_*" + record[field]["@error"] + ". You entered " + record[field]["@value"]
		else:
		    wrong_dict[field]  = record[field]["@value"]
	if "Data Import Error" not in wrong_dict.values():
	    invalid_rows.append(wrong_dict)
    temp = []
    for k in invalid_rows:
        for l in k.values():
	    if "*_error_*" in l:
	        temp.append(k)
    invalid_rows = temp 
    '''f.write("\n\nInvalid rows " + repr(invalid_rows))
    session.import_success = len(invalid_rows) 
    incorrect_rows = []
    correct_rows = []
    returned_tree = tree
    returned_json = s3xrc.xml.tree2json(returned_tree)
    returned_json = returned_json.encode('ascii')
    f.write("THIS IS ASCII returned_json " + returned_json + "\n\n\n")
    returned_json = json.loads(returned_json,encoding = 'ascii')
    f.write("-->\n\n\n<--" + repr(type(returned_json)))
    for resource_name in returned_json:
	for record in returned_json[resource_name]:
	     if '@error' in repr(record):
		incorrect_rows.append(record)
		f.write("\n\n\n" + repr(record))
	     else:
		correct_rows.append(record)
    correct_rows_send = {}
    correct_rows_send[('$_'+prefix+'_'+name)] = correct_rows
    f.write("The correct rows are " + repr(correct_rows_send))
    for k in incorrect_rows:
	 del k['@modified_at']
    send_json = json.dumps(correct_rows_send)
    send_json = StringIO(send_json)
    tree = s3xrc.xml.json2tree(send_json)
    k = res.import_xml(tree)
    if k:
       f.write("RE_IMPORT SUCCEEDED\n\n\n")
    else:
       f.write("DID NOT SUCCEED AGAIN\n\n")
    session.fields = []
    '''
    '''
    for k in invalid_rows:
        for l in k.keys():
 	    if l[0:3] == "$k_":
	    	nest_res = k[l]['@resource']
 	        for m in k[l]["$_"+nest_res][0].keys():
	            session.fields.append(l[3:].encode('ascii') + ' --> ' + nest_res.encode('ascii') + ' --> ' + m.encode('ascii'))
    '''
    ''' 
	for i in range(0,len(session.fields)):
       	    session.fields[i]=session.fields[i].encode('ascii')
    	f.write("Session fields \n" + repr(session.fields)+"\n\n\n")
    	session.import_rows = len(incorrect_rows)
    	for record in incorrect_rows:
       	   for field in record:
               if '@error' in record[field]:
                  f.write(repr(record[field]))
		  record[field] = '*_error_*' + record[field]['@error'] + '. You entered ' + record[field]['@value']
	       else:
	          f.write("in else " + repr(record[field]))
	          record[field] = record[field]['@value'] 
    	f.write("These rows are incorrect "+repr(incorrect_rows))
    	
	incorrect_rows = json.dumps(incorrect_rows,ensure_ascii=True)
    	'''
    session.invalid_rows = invalid_rows
    session.import_columns = j["columns"]
    session.import_map = json.dumps(j["map"], ensure_ascii=True)
    session.import_resource = resource.encode("ascii") 
    return dict()

def re_import():
    """ Custom View """
    return dict()

def similar_rows():
    """ Custom View """
    return dict()
