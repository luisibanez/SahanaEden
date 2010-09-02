// s3.multiselect.widget.js

// JS function which is used by the S3MultiSelectWidget
// @author: Michael Howden (michael@aidiq.com)
// @date: 2010-05-18


var S3MultiselectWidgetFileCounter = 0;

//TODO more data validation
//TODO before adding a new row, check rows which were added previous - not just the JSON
//TODo produce the DummyDisplayValues and DummyJSONValues using a loop - probably don't need a reg-ex anymore!

function S3MultiselectWidgetAddClick(Args)
    {
    var WidgetID = Args.WidgetID;

    var DummyDisplayValues = [ /DummyDisplay0/g, /DummyDisplay1/g, /DummyDisplay2/g, /DummyDisplay3/g, /DummyDisplay4/g]  
    var DummyJSONValues = [ /DummyJSON0/g, /DummyJSON1/g, /DummyJSON2/g, /DummyJSON3/g, /DummyJSON4/g]

    //Get the current value of the JSON Input
    var JSONInputValue = $("#"+ WidgetID + "_json").val();
    var newJSONInputValue = "{";

    var JSONValue;

    var InputBlank = true;

    var NewRow = Args.NewRow;

    var FileInputID = "";
    var NewFileInputID = "";

    for (i= 0; i < Args.ColumnFields.length; i++)
        {
        //Get the value of the new data
        var InputID = "#" + WidgetID + "_" + Args.ColumnFields[i]
        var InputSelector = $(InputID)
        var AutoTextValue = $(InputID + "_auto_text").val();
        DisplayValue = "";
        if (InputSelector.is("select") )
            {
            JSONValue = "'" + InputSelector.val() + "'";
            DisplayValue = $(InputID + " option:selected").text();
            InputSelector.val("");
            }
        else if ( AutoTextValue != undefined )
            {
            //This is an autocomplete
            DisplayValue = AutoTextValue
            JSONValue = $(InputID + "_auto_json").val();
            //MH DRRPP hack - don't allow empty JSON from Autocomplete
            if (Args.ColumnFields[i].slice(-3) == "_id" && JSONValue == "")
	            {
	            DisplayValue = "";
	            break;
                }
            $(InputID + "_auto_text").val("");
            $(InputID + "_auto_json").val("");
            $(InputID + "_auto_edit").hide();
            }
        else if ( InputSelector.attr("type") == "file")
            {
            DisplayValue = InputSelector.val();
            if (DisplayValue != "")
                { //There is a file
                FileInputID = InputID;
                NewFileInputID = Args.ColumnFields[i] + S3MultiselectWidgetFileCounter;
                JSONValue = "'" + NewFileInputID + "'"
                //DisplayValue = "<div id ='" + NewFileInputID + "'></div>" + 
                //                DisplayValue;
                S3MultiselectWidgetFileCounter++;
                }
            }
        else
            {
            DisplayValue = InputSelector.val();
            InputSelector.val("");

            if (InputSelector.attr("class") == "currency")
                {
                DisplayValue = JSONValue.replace("$","");
                }
            DisplayValue = DisplayValue.replace(/'/g,"\"");    
            JSONValue = "'" + DisplayValue + "'"
            }

        if (DisplayValue != "")
            {
            InputBlank = false;
            }

        //Replace the dummy value in the Append Row with this value
        NewRow = NewRow.replace(DummyDisplayValues[i], DisplayValue);
        NewRow = NewRow.replace(DummyJSONValues[i], JSONValue);

        //Add the new data to the JSON Input        
        newJSONInputValue = newJSONInputValue + "'" + Args.ColumnFields[i]+ "':" + JSONValue + "," 
        }

    newJSONInputValue = newJSONInputValue.slice(0, -1) + "}"

    //Test: if there is data in the input fields, and it does not match data whcih has already been added
    if (!InputBlank && !JSONInputValue.match(newJSONInputValue))
        {
        if (JSONInputValue != "")
        {
            JSONInputValue = JSONInputValue + ",";
        }

        JSONInputValue = JSONInputValue + newJSONInputValue;

        //Update the Dummy Widget
        $("#"+ WidgetID + "_json").val(JSONInputValue);

        //Insert the new Row into the table 
        $(NewRow).insertBefore("#" + Args.WidgetID + "_input_row");

        if (FileInputID != "")
            {
            //There is a file input in the Row
            //Change the ID of the old file input
            $(FileInputID).attr("id",NewFileInputID);
            $("#" + NewFileInputID).attr("name",NewFileInputID);
            //Hide the old file input
            $("#" + NewFileInputID).hide();
            //add a new file input
            $('<input class="upload" id="drrpp_framework_file_dummy_file" type="file" />').insertAfter("#" + NewFileInputID)
            
            
            //Copy the current file input
            //$("#" + NewFileInputID).replaceWith( $(FileInputID).clone() );
            
            //Change the ID of the new file input
            //$(FileInputID + ":first").attr("id",NewFileInputID);
            //Set the Name of the new file input (so that it is passed back to the server)
            //$("#" + NewFileInputID).attr("name",NewFileInputID);
            //$("#" + NewFileInputID).hide();

            //$(FileInputID).val("");
            }
        }
    };

function S3MultiselectWidgetDeleteClick(WidgetDelete, Args)
    {
    var WidgetID = Args.WidgetID;

    var RowID = $(WidgetDelete).attr("row_id");
    var DummyWidgetValue = $("#"+ Args.DummyName).val();
    var JSONInputValue = $("#"+ WidgetID + "_json").val();

    //Remove the row from the display
    //(this is button).parent(is data cell / td). parent( is row / tr)
    $(WidgetDelete).parent().parent().remove();

    //test to see if this is an existing entry in the impl_org table != 0
    if (RowID != "New") 
        {
        if (JSONInputValue != "")
        {
            JSONInputValue = JSONInputValue + ",";
        }
        //Marker to delete this record 
        JSONInputValue = JSONInputValue + "{'id':'" + RowID + "','deleted':True},";
        } 
    else // the record hasn't been saved'
        {
        //Delete the marker for this record
        var DeleteJSON ="{";
        for (i= 0; i < Args.ColumnFields.length; i++)
            {
            DeleteJSON = DeleteJSON +
                        "'" + Args.ColumnFields[i] + "':'"+ $(WidgetDelete).attr(Args.ColumnFields[i])+ "',"
            }
        DeleteJSON = DeleteJSON.slice(0,-1) + "}";

        JSONInputValue = JSONInputValue.replace(DeleteJSON, "");
        }

    JSONInputValue = JSONInputValue.replace(",,", ",");
    if (JSONInputValue.slice(-1) == ",")
        {
        JSONInputValue = JSONInputValue.slice(0,-1)
        }

    $("#" + WidgetID + "_json").val(JSONInputValue);
    };
