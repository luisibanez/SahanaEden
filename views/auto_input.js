// reusable module - pop-up, autocomplete and post-processing
// author:  sunneach
// created: Feb 27 2010
// Auto_input {{=entity_id}}
{{if entity_id:}}
    // Hide the real Input Field
    $('#{{=entity_id}}').hide();
    {{dummy_input = "dummy_" + entity_id}}
    {{try:}}      
        {{default_value}}
    {{except:}}   
        {{default_value = None}}
    {{pass}}
    
    {{if default_value is None:}}
        {{default_value = ""}}
    {{pass}}

    {{try:}} 
        {{is_person}}
    {{except:}}
        {{is_person = False}}
    {{pass}}

    // Add a dummy field
    {{try:}} 
        {{dummy_select}}
    {{except:}}
        {{dummy_select = None}}
    {{pass}}
    
    {{if dummy_select:}}
        $('#{{=entity_id}}').after("<select id='{{=dummy_input}}' class='reference'><option value=''>{{=default_value}}</option></select>");
        // Populate the id when the Dummy selection is changed
        copy_dummy = function(event){
           var newvalue = $('#{{=dummy_input}} option:selected').val();
           $('#{{=entity_id}}').val(newvalue);
         };
        $('#{{=dummy_input}}').change(copy_dummy); 
    {{else:}}
        $('#{{=entity_id}}').after("<input id='{{=dummy_input}}' class='ac_input' value='{{=default_value}}' size=50 />");
        {{if is_person:}}
            {{include "pr/person_autocomplete.js"}}
        {{else:}}
            {{include "autocomplete.js"}}
        {{pass}}
    {{pass}}
    
    // Populate the dummy Input at start (Update forms)
    var represent = $('#{{=entity_id}} > [selected]').html();
    $('#{{=dummy_input}}').val(represent);
    
    // Populate the real Input when the Dummy is selected
    $('#{{=dummy_input}}').result(function(event, data, formatted) {
        var newvalue = data.id;
        $('#{{=entity_id}}').val(newvalue);
        {{try:}}{{=post_process}}{{except:}}{{pass}}
    }); 
    {{entity_id = None}}
    {{default_value = None}}
    {{dummy_select = False}}
    {{is_person = False}}
{{pass}}
