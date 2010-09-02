    // Autocomplete-enable the Dummy Input
    $('#{{=dummy_input}}').autocomplete('{{=URL(r=request, c="pr", f="person", args="search.json", vars={"filter":"~", "field":"first_name", "field2":"middle_name", "field3":"last_name"})}}', {
        minChars: 2,
		//mustMatch: true,
		matchContains: true,
        dataType: 'json',
        parse: function(data) {
            var rows = new Array();
            for(var i=0; i<data.length; i++){
                var name = '';
                if (data[i].first_name != null) {
                    name += data[i].first_name + ' ';
                }
                if (data[i].middle_name != null) {
                    name += data[i].middle_name + ' ';
                }
                if (data[i].last_name != null) {
                    name += data[i].last_name;
                }
                rows[i] = { data:data[i], value:data[i].id, result:name };
            }
            return rows;
        },
        formatItem: function(row, i, n) {
            var name = '';
            if (row.first_name != null) {
                name += row.first_name + ' ';
            }
            if (row.middle_name != null) {
                name += row.middle_name + ' ';
            }
            if (row.last_name != null) {
                name += row.last_name;
            }
            return name;
		}
    });
