# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FieldViewUpgrade(models.TransientModel):
    _name = "field.view.update"
    _description = "Field View Upgrade"

    @api.multi
    def design_dynamic_field_view(self):
        view_arch = """<data>
                    """
        dynamic_fields = self.env['ir.model.fields'].search(
            [('active', '=', True), ('consent_field', '=', True),
             ('related_xml_field_id', '!=', False)],
            order="dynamic_sequence asc")
        sign_arch = """"""
        un_sign_arch = """"""
        un_sign_arch_arabic = """"""
        sign_arch_arabic = """"""
        extra_fields = """"""
        dependent_fields = [
            i.dependent_field.id for i in dynamic_fields if i.dependent_field]
        for consent_new_field in dynamic_fields.filtered(
                lambda f: f.id not in dependent_fields):
            related_field_id = consent_new_field.related_xml_field_id

            # if consent_new_field.ttype == 'binary' and consent_new_field.is_sign_field_id:
            #    sign_arch += """
            #             <field name='""" + related_field_id.name + """' invisible="1"/>
            #             <field name='""" + consent_new_field.name + """' widget="signature" attrs="{'invisible': ['|',('""" + related_field_id.name + """', '=', False),('language', '=', 'arabic')]}"/>
            #             <field name='""" + consent_new_field.name + """' string= '""" + consent_new_field.field_arabic_description + """' widget="signature" attrs="{'invisible': ['|' ,('""" + related_field_id.name + """', '=', False),('language', '=', 'english')]}"/>
            #         """
            # elif consent_new_field.ttype == 'many2many':
            #     un_sign_arch += """
            #             <field name='""" + related_field_id.name + """' invisible="1"/>
            #             <field name='""" + consent_new_field.name + """' widget="many2many_tags" attrs="{'invisible': ['|',('""" + related_field_id.name + """', '=', False),('language', '=', 'arabic')]}"/>
            #             <field name='""" + consent_new_field.name + """' string= '""" + consent_new_field.field_arabic_description + """' widget="many2many_tags" attrs="{'invisible': ['|' ,('""" + related_field_id.name + """', '=', False),('language', '=', 'english')]}"/>
            #         """
            # else:
            #     un_sign_arch += """
            #             <field name='""" + related_field_id.name + """' invisible="1"/>
            #             <field name='""" + consent_new_field.name + """' attrs="{'invisible': ['|',('""" + related_field_id.name + """', '=', False),('language', '=', 'arabic')]}"/>
            #             <field name='""" + consent_new_field.name + """' string= '""" + consent_new_field.field_arabic_description + """' attrs="{'invisible': ['|' ,('""" + related_field_id.name + """', '=', False),('language', '=', 'english')]}"/>
            #         """

            if consent_new_field.ttype == 'binary' and consent_new_field.is_sign_field_id:
                sign_arch += """
                        <field name='""" + related_field_id.name + """' invisible="1"/>
                        <field name='""" + consent_new_field.name + """' widget="signature" attrs="{'invisible': ['|',('""" + related_field_id.name + """', '=', False),('language', '=', 'arabic')]}"/>
                        """
                sign_arch_arabic += """
                        <field name='""" + consent_new_field.name + """' widget="signature" attrs="{'invisible': ['|' ,('""" + related_field_id.name + """', '=', False),('language', '=', 'english')]}" nolabel="1"/><label style="padding-left:10px;" string='""" + consent_new_field.field_arabic_description + """'attrs="{'invisible': ['|' ,('""" + related_field_id.name + """', '=', False),('language', '=', 'english')]}"/>
                    """
            elif consent_new_field.ttype == 'many2many':

                extra_fields += """
                        <field name='""" + related_field_id.name + """' invisible="1"/>"""
                un_sign_arch += """ 
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                        <td style="width:70%;"><label for='""" + consent_new_field.name + """'/></td>
                        <td style="width:30%;"><field name='""" + consent_new_field.name + """' widget="many2many_tags" style="width:100%"/></td>
                    </tr>
                    """

                un_sign_arch_arabic += """ 
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                        <td style="width:30%;text-align:right;"><field name='""" + consent_new_field.name + """' widget="many2many_tags"/></td>
                        <td style="width:70%;text-align:right;"><label for='""" + consent_new_field.name + """'string='""" + consent_new_field.field_arabic_description + """'/></td>
                    </tr>

                    """
            elif consent_new_field.ttype == 'one2many':
                extra_fields += """
                        <field name='""" + related_field_id.name + """' invisible="1"/>"""
                # un_sign_arch += """ 
                #     <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                #         <td style="width:70%;"><label for='""" + consent_new_field.name + """'/></td>
                #         <td style="width:30%;"><field name='""" + consent_new_field.name + """'/></td>
                #     </tr>
                #     """
                
                view = self.env['ir.ui.view'].search([('model','=',consent_new_field.relation)])
                if view:
                    
                    un_sign_arch += """
                        <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                           <td colspan="2"><label for='""" + consent_new_field.name + """'/></td>
                        </tr>
                        <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                          <td colspan="2"><field name='""" + consent_new_field.name + """' context="{'tree_view_ref':'"""+view.name+"""'}"/></td>  
                        </tr>
                        """ 
                    un_sign_arch_arabic += """ 
                        <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                           <td colspan="2" style="text-align:right;"><label for='""" + consent_new_field.name + """'/></td>
                        </tr>
                        <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                          <td colspan="2"><field name='""" + consent_new_field.name + """' context="{'tree_view_ref':'"""+view.name+"""'}"/></td>  
                        </tr>
                        """ 
                # un_sign_arch_arabic += """ 
                #     <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                #         <td style="width:30%;text-align:right;"><field name='""" + consent_new_field.name + """'/></td>
                #         <td style="width:70%;text-align:right;"><label for='""" + consent_new_field.name + """'string='""" + consent_new_field.field_arabic_description + """'/></td>
                #     </tr>
                #
                #     """      
            elif consent_new_field.ttype == 'text' and consent_new_field.readonly:
                extra_fields += """
                        <field name='""" + related_field_id.name + """' invisible="1"/>"""
                un_sign_arch += """ 
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                        <td colspan="2"><label for='""" + consent_new_field.name + """'/></td>
                    </tr>
                    """
                un_sign_arch_arabic += """ 
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                        <td colspan="2" style="text-align:right;"><label for='""" + consent_new_field.name + """'string='""" + consent_new_field.field_arabic_description + """'/></td>
                    </tr>
                    """   
            elif  consent_new_field.ttype == 'html':
                extra_fields += """
                        <field name='""" + related_field_id.name + """' invisible="1"/>"""
                un_sign_arch += """ 
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                           <td colspan="2"><label for='""" + consent_new_field.name + """'/></td>
                    </tr>
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                        <td colspan="2"><field name='""" + consent_new_field.name + """' force_save="1"/></td>
                    </tr>
                    """
                un_sign_arch_arabic += """ 
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                           <td colspan="2" style="text-align:right;"><label for='""" + consent_new_field.name + """'/></td>
                        </tr>
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                        <td colspan="2"><field name='""" + consent_new_field.name + """' force_save="1" style="width:100%" /></td>
                    </tr>
                    """
            else:
                extra_fields += """
                        <field name='""" + related_field_id.name + """' invisible="1"/>"""
                un_sign_arch += """ 
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                        <td style="width:70%;"><label for='""" + consent_new_field.name + """'/></td>
                        <td style="width:30%;"><field name='""" + consent_new_field.name + """' style="width:100%"/></td>
                    </tr>
                    """
                un_sign_arch_arabic += """ 
                    <tr attrs="{'invisible': [('""" + related_field_id.name + """', '=', False)]}">
                        <td style="width:30%;text-align:right;"><field name='""" + consent_new_field.name + """' style="width:100%"/></td>
                        <td style="width:70%;text-align:right;"><label for='""" + consent_new_field.name + """'string='""" + consent_new_field.field_arabic_description + """'/></td>
                    </tr>
                    """
            # check and add dependent fields
            result = self.add_dependent_field(consent_new_field)
            sign_arch += result.get('sign_arch', '')
            un_sign_arch += result.get('un_sign_arch', '')
            un_sign_arch_arabic += result.get('un_sign_arch_arabic', '')
            sign_arch_arabic += result.get('sign_arch_arabic', '')
            extra_fields += result.get('extra_fields', '')
        
        if extra_fields:
            view_arch += """<field name="language" position="after">
                        """ + extra_fields + """ 
                    </field>"""

        if un_sign_arch:
            view_arch += """<table name="english_table" position="inside">
                        """ + un_sign_arch + """ 
                    </table>"""

        if un_sign_arch_arabic:
            view_arch += """<table name="arabic_table" position="inside">
                        """ + un_sign_arch_arabic + """ 
                    </table>"""
        if sign_arch_arabic:
            view_arch += """<field name="arabic_sign" position="after">
                        """ + sign_arch_arabic + """ 
                    </field>"""

        if sign_arch:
            view_arch += """<field name="sign_xpath_field_id" position="after">
                        """ + sign_arch + """ 
                    </field>"""

        view_arch += """
                </data>"""
        view_id = self.env['ir.ui.view'].browse(
            self.env['ir.ui.view'].get_view_id(
                'dynamic_consent_form.consent_form_wizard'))
        dom_qweb_view = [
            ('name', '=', 'Consent Dynamic Field with Dynamic Template'),
            ('type', '=', 'form'),
            ('model', '=', 'consent.wizard')]
        qweb_template_view_id = self.env['ir.ui.view'].search(dom_qweb_view)
        if len(qweb_template_view_id) == 0:
            self.env['ir.ui.view'].create({
                'name': 'Consent Dynamic Field with Dynamic Template',
                'model': 'consent.wizard',
                'model_data_id': 'consent.wizard',
                'type': 'form',
                'mode': 'extension',
                'action': True,
                'arch': view_arch,
                'inherit_id': view_id.id,
            })
        if len(qweb_template_view_id) == 1:
            qweb_template_view_id.write({'arch': view_arch})

    def add_dependent_field(self, active_field=None):
        """check for field dependency and return the xml architecture
        if the field has a dependent field"""
        if active_field and active_field.has_dependency:
            return self.do_process_field(active_field)
        else:
            return {}

    def do_process_field(self, active_field):
        sign_arch = """"""
        un_sign_arch = """"""
        un_sign_arch_arabic = """"""
        sign_arch_arabic = """"""
        extra_fields = """"""
        attr_val = active_field.dependent_value
        attrs_inv = ""
        if active_field.ttype == 'boolean' and active_field.dependent_value:
            attr_val = active_field.dependent_value.lower() == 'true' and "True" or "False"
        if attr_val:
            attrs_inv = "('" + active_field.name + "', '!=', '" + attr_val + "')"

        dependent_field = active_field.dependent_field
        related_field_id = dependent_field.related_xml_field_id
        attrs_ar = "('language', '=', 'arabic')"
        attrs_en = "('language', '=', 'english')"
        
        if active_field.ttype == 'selection' and not dependent_field:
            for line in active_field.select_related_field_ids:
                attrs_inv = "('" + active_field.name + "', '!=', '" + line.value + "')"
                if line.related_field_id:
                    extra_fields += """<field name='""" + line.related_field_id.name + """'
                        invisible="1"/>"""
                    un_sign_arch += """ 
                        <tr attrs="{'invisible': [%s]}">
                            <td style="%s"><label for='%s'/></td>
                            <td style="%s"><field name='%s' style="%s"/></td>
                        </tr>
                    """ % (attrs_inv, "width:70%;padding-left:10px;", line.related_field_id.name,
                           "width:30%;", line.related_field_id.name, "width:100%")
                    un_sign_arch_arabic += """ 
                        <tr attrs="{'invisible': [%s]}">
                            <td style="%s text-align:right;">
                                <field name='%s' style="%s"/></td>
                            <td style="%s text-align:right;">
                                <label for='%s'string='%s'/></td>
                        </tr>
                    """ % (attrs_inv, "width:30%;", line.related_field_id.name, "width:100%;",
                           "width:70%;padding-right:10px;", line.related_field_id.name,
                           line.related_field_id.field_arabic_description)
                else:
                    un_sign_arch += """ 
                        <tr attrs="{'invisible': [%s]}">
                            <td style="%s"><strong>%s</strong></td>
                            <td style="%s"></td>
                        </tr>
                    """ % (attrs_inv, "width:70%;padding-left:10px;",line.value,
                           "width:30%;")
                    un_sign_arch_arabic += """ 
                        <tr attrs="{'invisible': [%s]}">
                            <td style="%s text-align:right;">
                                </td>
                            <td style="%s text-align:right;">
                                <strong>%s</strong></td>
                        </tr>
                    """ % (attrs_inv, "width:30%;","width:70%;padding-right:10px;", line.value)
        else:
            if dependent_field.ttype == 'binary' and dependent_field.is_sign_field_id:
                sign_arch += """
                    <field name='%s' invisible='1'/>
                    <field name='%s' widget='signature' attrs="{'invisible': ['|', %s, %s]}"/>
                """ % (related_field_id.name,
                       dependent_field.name, attrs_inv, attrs_ar)
    
                sign_arch_arabic += """
                    <field name='%s' widget='signature' attrs="{'invisible': ['|', %s, %s]}" nolabel='1'/>
                    <label style="padding-left:10px;" string='%s' attrs="{'invisible': ['|', %s, %s]}"/>
                """ % (dependent_field.name, attrs_inv, attrs_en,
                       dependent_field.field_arabic_description, attrs_inv,
                       attrs_en)
            elif dependent_field.ttype == 'many2many':
                extra_fields += """
                    <field name='""" + related_field_id.name + """' 
                    invisible="1"/>"""
    
                un_sign_arch += """ 
                    <tr attrs="{'invisible': [ %s]}">
                        <td style="%s"><label for='%s'/></td>
                        <td style="%s"><field name='%s' 
                            widget="many2many_tags" style="%s"/></td>
                    </tr>
                """ % (attrs_inv, "width:70%;", "width:30%;",
                       dependent_field.name, dependent_field.name, "width:100%")
                un_sign_arch_arabic += """ 
                    <tr attrs="{'invisible': [%s]}">
                        <td style="%s text-align:right;">
                            <field name='%s' widget="many2many_tags"/></td>
                        <td style="%s text-align:right;">
                            <label for='%s' string='%s'/></td>
                    </tr>
                """ % (attrs_inv, "width:30%;", dependent_field.name,
                       "width:70%;", dependent_field.name,
                       dependent_field.field_arabic_description)
            else:
                if active_field.ttype == 'boolean' and active_field.boolean_related_field_ids:
                    for line in active_field.boolean_related_field_ids:
                        attrs_inv = "('" + active_field.name  + "', '!=', True)"
                        if line.related_text_field_id and line.related_bool_field_id:
                            un_sign_arch += """ 
                                <tr attrs="{'invisible': [%s]}">
                                    <td style="%s"><field name='%s' class="oe_inline"/><label for='%s' class="oe_inline"/></td>
                                    <td style="%s"><field name='%s' style="%s" attrs="{'invisible': [('%s', '!=', %s)]}"/></td>
                                </tr>
                                """ % (attrs_inv,"width:70%;padding-left:10px;", line.related_bool_field_id.name,line.related_bool_field_id.name,
                                       "width:30%;", line.related_text_field_id.name, "width:100%",line.related_bool_field_id.name,str(line.visible_in))
                            un_sign_arch_arabic += """ 
                                <tr attrs="{'invisible': [%s]}">
                                    <td style="%s text-align:right;">
                                        <field name='%s' style="%s" attrs="{'invisible': [('%s', '!=', %s)]}"/></td>
                                    <td style="%s text-align:right;">
                                        <label for='%s'string='%s' class="oe_inline"/><field name='%s' class="oe_inline"/></td>
                                </tr>
                            """ % (attrs_inv,"width:30%;", line.related_text_field_id.name, "width:100%;",line.related_bool_field_id.name,str(line.visible_in),
                                   "width:70%;padding-right:10px;", line.related_bool_field_id.name,
                                   line.related_bool_field_id.field_arabic_description,line.related_bool_field_id.name)
                        
                        elif not line.related_text_field_id and line.related_bool_field_id:
                            un_sign_arch += """ 
                                <tr attrs="{'invisible': [%s]}">
                                    <td style="%s"><field name='%s' class="oe_inline"/><label for='%s' class="oe_inline"/></td>
                                    <td></td>
                                </tr>
                                """ % (attrs_inv,"width:70%;padding-left:10px;", line.related_bool_field_id.name,line.related_bool_field_id.name)
                                       
                            un_sign_arch_arabic += """ 
                                <tr attrs="{'invisible': [%s]}">
                                    <td></td>
                                    <td style="%s text-align:right;">
                                        <label for='%s'string='%s' class="oe_inline"/><field name='%s' class="oe_inline"/></td>
                                </tr>
                            """ % (attrs_inv,"width:70%;padding-right:10px;", line.related_bool_field_id.name,line.related_bool_field_id.field_arabic_description,line.related_bool_field_id.name)
                
                else:
                
                    if related_field_id:
                        extra_fields += """<field name='""" + related_field_id.name + """'
                            invisible="1"/>"""
                    un_sign_arch += """ 
                        <tr attrs="{'invisible': [%s]}">
                            <td style="%s"><label for='%s'/></td>
                            <td style="%s"><field name='%s' style="%s"/></td>
                        </tr>
                    """ % (attrs_inv, "width:70%;", dependent_field.name,
                           "width:30%;", dependent_field.name, "width:100%")
                    un_sign_arch_arabic += """ 
                        <tr attrs="{'invisible': [%s]}">
                            <td style="%s text-align:right;">
                                <field name='%s' style="%s"/></td>
                            <td style="%s text-align:right;">
                                <label for='%s'string='%s'/></td>
                        </tr>
                    """ % (attrs_inv, "width:30%;", dependent_field.name, "width:100%;",
                           "width:70%;", dependent_field.name,
                           dependent_field.field_arabic_description)

        return {
            'sign_arch': sign_arch,
            'un_sign_arch': un_sign_arch,
            'un_sign_arch_arabic': un_sign_arch_arabic,
            'sign_arch_arabic': sign_arch_arabic,
            'extra_fields': extra_fields,
        }
        
    @api.multi   
    def design_dynamic_field_report(self):
        for rec in self.env['consent.details'].search([]):
            rec.modify_report_template()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
