openerp.resource = function (openerp)
{
   openerp.web.form.widgets.add('test', 'openerp.resource.Mywidget');
   openerp.resource.Mywidget = openerp.web.form.FieldChar.extend(
       {
       window.alert("test if widget is called");
   });
}
