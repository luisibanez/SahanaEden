    // Autocomplete-enable the Dummy Input
    $('#{{=dummy_input}}').autocomplete('{{=URL(r=request, c="cr", f="shelter", args="search.json", vars={"filter":"~", "field":"name"})}}', {
        minChars: 2,
		//mustMatch: true,
		matchContains: true,
        dataType: 'json',
        parse: function(data) {
            var rows = new Array();
            for(var i=0; i<data.length; i++){
                rows[i] = { data:data[i], value:data[i].id, result:data[i].name };
            }
            return rows;
        },
        formatItem: function(row, i, n) {
            return row.name;
		}
    });
