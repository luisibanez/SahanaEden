    // Add checkbox to hide/unhide optional school fields.
    $('#cr_shelter_school_code__row').before(
        '{{=TR(TD(LABEL(T("Is this a School?"))),
               TD(INPUT(_type="checkbox",
                        _name="is_school", _id="is_school")),
               TD(DIV(_id="is_school_tooltip",
                  _class="tooltip",
                  _title=Tstr("School Information") + "|" +
                         Tstr("If this is a school that has a school code, " +
                              "please check the school checkbox, then enter " +
                              "the code. If the school code is not " +
                              "available, do not check the school checkbox. " +
                              "Instead include the school name in the " +
                              "shelter name or in the comments."))))}}');
    // Adding tooltip here is too late to get proper decorations, so add them.
    $('#is_school_tooltip').cluetip(
        {activation: 'hover', sticky: false, splitTitle: '|'});
    // If data is present (on update), or if there's a validation error
    // (meaning box was checked but no school code filled in on create),
    // set checked and do not hide.  (The jQuery selector with two terms
    // tests within the set selected by the first selector, for a child
    // matching the second.)
    if ($('#cr_shelter_school_code').val() != "" ||
        $('#cr_shelter_school_code__row #school_code__error').length != 0) {
        $('#is_school').attr('checked','on');
    } else {
        $('#cr_shelter_school_code__row').hide();
        $('#cr_shelter_school_pf__row').hide();
    }
    $('#is_school').change(function() {
        if ($(this).attr('checked')) {
            $('#cr_shelter_school_code__row').show();
            $('#cr_shelter_school_pf__row').show();
        } else {
            // Clear values if user unchecks? Nicer for user if the values
            // are left in, in case user accidentally unchecks.  If values not
            // cleared, either no values should be sent on submit if unchecked,
            // or checkbox setting should be tested on server and values not
            // stored if unchecked.
            $('#cr_shelter_school_code__row').hide();
            $('#cr_shelter_school_pf__row').hide();
        }
    })

    // If the optional hospital_id field is present, add checkbox to
    // hide/unhide it.
    if ($('#cr_shelter_hospital_id__row').length != 0) {
        $('#cr_shelter_hospital_id__row').before(
            '{{=TR(TD(LABEL(T("Is this a Hospital?"))),
                   TD(INPUT(_type="checkbox",
                            _name="is_hospital", _id="is_hospital")),
                   TD(DIV(_id="is_hospital_tooltip",
                      _class="tooltip",
                      _title=Tstr("Hospital Information") + "|" +
                             Tstr("If this is a hospital, please check the " +
                                  "hospital checkbox, then select the " +
                                  "hospital. If there is no record for " +
                                  "this hospital, you can create one and " +
                                  "enter just the name if no other " +
                                  "information is available."))))}}');
        // Add tooltip decorations.
        $('#is_hospital_tooltip').cluetip(
            {activation: 'hover', sticky: false, splitTitle: '|'});
        // If data is present (on update), or if there's a validation error
        // (meaning box was checked but no hospital id filled in on create),
        // set checked and do not hide.
        if ($('#cr_shelter_hospital_id').val() != "" ||
            $('#cr_shelter_hospital_id__row #hospital_id__error').length != 0) {
            $('#is_hospital').attr('checked','on');
        } else {
            $('#cr_shelter_hospital_id__row').hide();
        }
        $('#is_hospital').change(function() {
            if ($(this).attr('checked')) {
                $('#cr_shelter_hospital_id__row').show();
            } else {
                $('#cr_shelter_hospital_id__row').hide();
            }
        })
    }
