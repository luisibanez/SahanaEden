// s3.auto.widget

// JS function which is used by the S3AutoWidget
// @author: Michael Howden (michael@aidiq.com)
// @date: 2010-04-21

// AutoID - the field name - no element has this ID
// AutoTextID - the field where the user types the text
// AutoJSONID - the hidden field where the JSON representation is stored

//TODO - work with multiple fields
//TODO - work with selects

function s3_auto_widget_options(AutocompleteField)
    {
    options = {
        minChars: 2,

        //mustMatch: true,
        matchContains: true,
        dataType: 'json',
        parse: function(data) {
            var rows = new Array();
            for(var i=0; i<data.length; i++) {
                rows[i] = { data:data[i], value:data[i].id, result:data[i][AutocompleteField] };
            }
            return rows;
        },
        formatItem: function(row, i, n) {
            return row[AutocompleteField];
        }
    };
    return options;
    };

// Populate the real Input when the Dummy is selected
function s3_auto_widget_result(event, data, formatted, AutoID, AutocompleteField, PopupURL) 
    {
    var NewJSON = "{'id':'" + data.id + "'}";
    var selAutoJSON = $("#" + AutoID + "_auto_json");
    var selAutoEdit = $("#" + AutoID + "_auto_edit");
    var selAutoNewLabel = $("#" + AutoID + "_auto_new_label");
    
    //This is where we do our  formatting magic for JSON
    selAutoJSON.val(NewJSON);  
    
    //Hide "New XXX" 
    selAutoNewLabel.hide();
    
    //Display popup "Edit" -> update link
    selAutoEdit.show();
    selAutoEdit.attr("href", PopupURL + "/" + data.id + "/update?format=popup" +
                                                                "&auto_id=" + AutoID +
                                                                "&fields=['" +  AutocompleteField + "']");
    }; 
    
function s3_auto_widget_keypress(AutoID)    
    {  
    var selAutoEdit = $("#" + AutoID + "_auto_edit");  
    selAutoEdit.show();
    }
    
function s3_auto_widget_change(AutoID, AutocompleteField, ParseChars, PopupURL)    
    {
    var selAutoJSON = $("#" + AutoID + "_auto_json");
    var selAutoEdit = $("#" + AutoID + "_auto_edit");
    var selAutoNewLabel = $("#" + AutoID + "_auto_new_label");
    
    var AutoText = $("#" + AutoID + "_auto_text").val();
    
    if (AutoText != "")
        {
        //TODO - use Split to separate AutocompleteText and for AutocompleteFields[1-n]
        AutoText = AutoText.replace(/'/g,"\"");
        var NewJSON = "{'"+ AutocompleteField + "':'" + 
                        AutoText + "'}";
        selAutoJSON.val(NewJSON);

        var strParseChars = "";
        if (ParseChars)
            {
            strParseChars = "&parse_chars=" + ParseChars;
            }

        //Add "Enter Details"" Link - var - <AutocompleteField> = $("#" + AutocompleteID).val()
        selAutoEdit.attr("href", PopupURL + 
                        "/create" +
                        "?format=popup" +
                        "&auto_id=" + AutoID +
                        "&fields=['" +  AutocompleteField + "']" +
                        "&auto_text_value=" + AutoText +
                        strParseChars);  

        //display popup "Edit" -> create link
        selAutoEdit.show();
        //Show "New XXX"
        selAutoNewLabel.show();
        }
        else
            {
            selAutoJSON.val("");
            selAutoEdit.hide();
            }
    };
