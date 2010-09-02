# -*- coding: utf-8 -*-

db.define_table("atable",
                Field("afield"))


def shn_m2m_widget(self, value, options=[]):
    """Many-to-Many widget
    Currently this is just a renamed copy of t2.tag_widget"""

    script=SCRIPT("""
    function web2py_m2m(self, other, option) {
       var o=document.getElementById(other)
       if(self.className=='option_selected') {
          self.setAttribute('class','option_deselected');
          o.value=o.value.replace('['+option+']','');
       }
       else if(self.className=='option_deselected') {
          self.setAttribute('class','option_selected');
          o.value=o.value+'['+option+']';
       }
    }
    """)
    id = self._tablename + "_" + self.name
    def onclick(x):
        return "web2py_m2m(this, '%s', '%s');" % (id, x.lower())
    buttons = [SPAN(A(x, _class="option_selected" if value and "[%s]" % x.lower() in value else "option_deselected", _onclick=onclick(x)), " ") for x in options]
    return DIV(script, INPUT(_type="hidden", _id=id, _name=self.name, _value=value), *buttons)
