function popup(url) {
  newwindow=window.open(url,'name','height=400,width=600');
  if (window.focus) newwindow.focus();
  return false;
}
function collapse(id) { jQuery('#'+id).slideToggle(); }
function fade(id,value) { if(value>0) jQuery('#'+id).hide().fadeIn('slow'); else jQuery('#'+id).show().fadeOut('slow'); }
function ajax(u,s,t) {
    query = '';
    if (typeof s == "string") {
        d = jQuery(s).serialize();
        if(d){ query = d; }
    } else {
        pcs = [];
        for(i=0; i<s.length; i++) {
            q = jQuery("#"+s[i]).serialize();
            if(q){pcs.push(q);}
        }
        if (pcs.length>0){query = pcs.join("&");}
    }
    jQuery.ajax({type: "POST", url: u, data: query, success: function(msg) { if(t) { if(t==':eval') eval(msg); else jQuery("#" + t).html(msg); } } }); 
}
String.prototype.reverse = function () { return this.split('').reverse().join('');};
function web2py_ajax_init() {
  jQuery('.hidden').hide();
  jQuery('.error').hide().slideDown('slow');
  jQuery('.flash').click(function() { jQuery(this).fadeOut('slow'); return false; });
  jQuery('input.string').attr('size',50);
  jQuery('textarea.text').attr('cols',50).attr('rows',10);
  jQuery('input.integer').keyup(function(){this.value=this.value.reverse().replace(/[^0-9\-]|\-(?=.)/g,'').reverse();});
  jQuery('input.double').keyup(function(){this.value=this.value.reverse().replace(/[^0-9\-\.]|[\-](?=.)|[\.](?=[0-9]*[\.])/g,'').reverse();});
  try { jQuery("input.time").clockpick({
      starthour:0, endhour:23, showminutes:true, military:true
  }); } catch(e) {};
};
jQuery(document).ready(function() {
    jQuery('.flash').hide().slideDown('slow')
   if (jQuery('.flash').html()!='') jQuery('.flash').slideDown('slow');
   web2py_ajax_init();
});

function web2py_trap_form(action,target) {
   jQuery('#'+target+' form').each(function(i){
      var form=jQuery(this);
      if(!form.hasClass('no_trap'))
        form.submit(function(obj){
         jQuery('.flash').hide().html('');
         web2py_ajax_page('post',action,form.serialize(),target);
         return false;
      });
   });
}
function web2py_ajax_page(method,action,data,target) {
  jQuery.ajax({'type':method,'url':action,'data':data,
    'beforeSend':function(xhr){
      xhr.setRequestHeader('web2py-component-location',document.location);
      xhr.setRequestHeader('web2py-component-element',target);},
    'complete':function(xhr,text){
      command=xhr.getResponseHeader('web2py-component-command');
      if(command) eval(command);
      flash=xhr.getResponseHeader('web2py-component-flash');
      if(flash) jQuery('.flash').html(flash).slideDown();
      },
    'success': function(text) {
      jQuery('#'+target).html(text);
      web2py_trap_form(action,target);
      web2py_ajax_init();
      }
    });
}
function web2py_component(action,target) {
    jQuery(document).ready(function(){ web2py_ajax_page('get',action,null,target); });
}
