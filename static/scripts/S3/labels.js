// Ability to specify site-wide what delimiter to use between labels & values in form fields
// from:  http://docs.jquery.com/Tutorials:jQuery_For_Designers
// Amended to filter-out the fields created by Web2Py which have these hardcoded
$(document).ready(function(){
    $("div.label label[id!='delete_record__label']").append(":");
    // Doesn't work due to nested DIVs
    //$('div:not(".t2-display") label[id!="delete_record__label"]').append(":");
});
// Can replace with CSS: http://www.alistapart.com/articles/progressiveenhancementwithcss
//label:after {
//  content: ":";
//}