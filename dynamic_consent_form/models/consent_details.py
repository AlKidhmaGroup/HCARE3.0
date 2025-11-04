# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
# import sys
from ast import literal_eval
# reload(sys)
# sys.setdefaultencoding('utf-8')
from odoo.exceptions import UserError, ValidationError


class ConsentDetails(models.Model):
    _name = 'consent.details.category'
    _description = 'Consent Details Category'

    name = fields.Char('Name',required=True)


class ConsentDetails(models.Model):
    _name = 'consent.details'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', default=0)
    active = fields.Boolean(default=True, copy=False)
    name = fields.Char('Name',required=True)
    heading_english = fields.Char('Heading - English',required=False)
    heading_arabic = fields.Char('Heading - Arabic',required=False)
    content_english = fields.Html('Content - English',required=False)
    content_arabic = fields.Html('Content - Arabic',required=False)
    image_1 = fields.Binary('Image',required=False)
    image_2 = fields.Binary('Image',required=False)
    field_ids = fields.Many2many('ir.model.fields', 'field_field_consent_rel', 'field_id', 'consent_id',
                                 'Fields',
                                   domain=[('consent_field', '=', True),('related_xml_field_id', '!=', False),('is_sign_field_id', '=', False)])
    signature_field_ids = fields.Many2many('ir.model.fields', 'sign_field_consent_rel', 'sign_field_id', 'consent_id',
                                 'Signature Fields',
                                   domain=[('consent_field', '=', True),('related_xml_field_id', '!=', False),
                                           ('is_sign_field_id', '=', True)])
    report_template_id = fields.Many2one('ir.actions.report', string='Report template', readonly=0, copy=False)
    report_blank_template_id = fields.Many2one('ir.actions.report', string='Blank Report template', readonly=1, copy=False)
    blank_report_language = fields.Selection([('english', 'English'),
                                 ('arabic', 'Arabic')], 'Blank Report Language', readonly=False, required=True, default='english')
    consent_category_id = fields.Many2one('consent.details.category', string='Category',required=False)
    hide_fields_in_print = fields.Boolean('Hide fields if no data entered')
    doc_stamp_need = fields.Boolean('Need Doctor Stamp')
    need_patient_details = fields.Boolean('Need Patient Details')
    
    
    def open_consent_wizard(self):
        
        context = {'default_consent_detail_id': self.id}
        if self.env.context.get('default_patient_id',False):
            context.update({'default_patient_id':self.env.context.get('default_patient_id',False)})
        if self.env.context.get('default_doctor_id',False):
            context.update({'default_doctor_id':self.env.context.get('default_doctor_id',False)})
        return {
            'name': _('Clinical form'),
            'view_id': self.env.ref('dynamic_consent_form.consent_form_wizard').id,
            'type': 'ir.actions.act_window',
            'res_model': 'consent.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': context
        }

    def modify_report_template(self):
        dom_qweb_view = [('name', 'ilike', self.report_template_id.name), ('type', '=', 'qweb')]
        qweb_template_view_id = self.env['ir.ui.view'].search(dom_qweb_view)
        if len(qweb_template_view_id) == 1:
            view_arch = self.design_qweb_view()
            qweb_template_view_id.write({'arch': view_arch})
        if len(qweb_template_view_id) == 0:
            self.delete_report_template()
            self.create_report_template()

    def modify_blank_report_template(self):
        dom_qweb_view = [('name', 'ilike', 'Blank_' + self.report_blank_template_id.name), ('type', '=', 'qweb')]
        qweb_template_view_id = self.env['ir.ui.view'].search(dom_qweb_view)
        if len(qweb_template_view_id) == 1:
            view_arch = self.design_blank_qweb_view()
            qweb_template_view_id.write({'arch': view_arch})
        if len(qweb_template_view_id) == 0:
            self.delete_blank_report_template()
            self.create_blank_report_template()

    @api.multi
    def write(self, vals):
        # if vals.get('need_patient_details',False):
        #     for rec in self:
        #         consent_data = self.env['consent.wizard'].search([('consent_detail_id','=',rec.id)])
        #         for constent in consent_data:
        #             constent.write({'patient_details':vals.get('need_patient_details',False),
        #                             'mrn':constent.patient_id.patient_id or False,
        #                             'patient_ref':constent.patient_id.qid or False})
        name_changed = 0
        if vals.get('name'):
            name_changed = 1
        result = super(ConsentDetails, self).write(vals)
        for rec in self:
            if name_changed:
                if rec.report_template_id:
                    rec.delete_report_template()
                    rec.modify_report_template()
                if rec.report_blank_template_id:
                    rec.delete_blank_report_template()
                    rec.create_blank_report_template()
            if rec.report_template_id:
                rec.modify_report_template()
            # if rec.report_blank_template_id:
            #     rec.modify_blank_report_template()
        return result

    def design_qweb_view(self):
        field_arch_english = ''
        arabic_date  = 'Date'
        arabic_patient  = 'Patient'
        arabic_doctor  = ' Doctor'
        arabic_patient_ref = 'ID Number'
        arabic_mrn = 'MRN'
        
        
        
        
        # arabic_date  = 'التاريخ'
        # arabic_patient  = 'اسم المريض'
        # arabic_doctor  = ' الطبيب'
        field_arch_arabic = """<table width="100%">
                                <colgroup>
                                    <col width='40%' />
                                    <col width='60%' />
                                </colgroup>
                                <thead>
                                    <tr>
                                        <th></th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody >
                                    <tr>
                                        <td colspan="2" style="text-align: right;"><span t-esc="o.register_date"/><strong>&#160;:&#160;"""+ arabic_date + """ </strong></td>
                                    </tr>
                                    <tr>
                                         <td colspan="2" style="text-align: right;"><span t-esc="o.patient_id.patient_name"/><strong>&#160;:&#160;"""+ arabic_patient+ """</strong></td>
                                    </tr>
                                    
                                    <tr t-if="o.patient_details">
                                         <td colspan="2" style="text-align: right;"><span t-esc="o.patient_ref"/><strong>&#160;:&#160;"""+ arabic_patient_ref+ """</strong></td>
                                    </tr>
                                    
                                     <tr t-if="o.patient_details">
                                         <td colspan="2" style="text-align: right;"><span t-esc="o.mrn"/><strong>&#160;:&#160;"""+ arabic_mrn+ """</strong></td>
                                    </tr>
                                    
                                    <tr t-if="o.doctor_id">
                                        <td colspan="2" style="text-align: right;"><span t-esc="o.doctor_id.name.name"/><strong>&#160;:&#160;"""+ arabic_doctor+ """</strong></td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"><span>&#160;</span></td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"><span>&#160;</span></td>
                                    </tr>
                                    
                                """
        field_arch_english = """<table width="100%">
                                <colgroup>
                                    <col width='60%' />
                                    <col width='40%' />
                                </colgroup>
                                <thead>
                                    <tr>
                                        <th></th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody >
                                    <tr>
                                        <td colspan="2"><strong>Date&#160;:&#160;</strong><span t-esc="o.register_date"/></td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"><strong>Patient&#160;:&#160;</strong><span t-esc="o.patient_id.patient_name"/></td>
                                    </tr>
                                    
                                    <tr t-if="o.patient_details">
                                        <td colspan="2"><strong>ID Number&#160;:&#160;</strong><span t-esc="o.patient_ref"/></td>
                                    </tr>
                                    
                                    <tr t-if="o.patient_details">
                                        <td colspan="2"><strong>MRN&#160;:&#160;</strong><span t-esc="o.mrn"/></td>
                                    </tr>
                                    
                                    <tr t-if="o.doctor_id">
                                        <td colspan="2"><strong>Doctor&#160;:&#160;</strong><span t-esc="o.doctor_id.name.name"/></td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"><span>&#160;</span></td>
                                    </tr>
                                    <tr>
                                        <td colspan="2"><span>&#160;</span></td>
                                    </tr>
                                    
                                """
        # field_arch_english += """<strong>Date : &#160;&#160;</strong>"""
        # field_arch_english += """<t t-esc="o.register_date"/><br/>"""
        # field_arch_english += """<strong>Patient : &#160;&#160;</strong>"""
        # field_arch_english += """<t t-esc="o.patient_id.patient_name" /><br/>"""
        # field_arch_english += """<strong>Doctor : &#160;&#160;</strong>"""
        # field_arch_english += """<td t-esc="o.doctor_id.name.name"/><br/>"""
        for normal_field in self.field_ids.sorted(lambda r: r.dynamic_sequence):
            # field_arch_english += """<strong>""" + normal_field.field_description + """: &#160;&#160;</strong>"""
            
            
            
            not_value_display = ""
            if self.hide_fields_in_print:
                not_value_display = """ t-if='o."""+normal_field.name+"'"
            field_arch_english += "<tr"+not_value_display+">"
            
            if normal_field.ttype =='text' and normal_field.readonly:
               field_arch_english += """<td colspan="2" style="text-align: left;"><strong>""" + normal_field.field_description + """</strong></td>""" 
            else:
                if normal_field.ttype not in ('one2many','html'):
                    field_arch_english += """<td style="text-align: left;"><strong>""" + normal_field.field_description + """</strong></td>"""
            field_arch_arabic += "<tr"+not_value_display+">"
            if normal_field.ttype in ('char', 'date') or normal_field.ttype =='text' and not normal_field.readonly:
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-esc="o.""" + normal_field.name + """"/>"""
                field_arch_english += """<td style="text-align: left;"><span t-field="o.""" + normal_field.name + """"/></td>"""
                field_arch_arabic += """<td style="text-align: right;"><span t-field="o.""" + normal_field.name + """"/></td>"""
            
            elif normal_field.ttype == 'html':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-raw="o.""" + normal_field.name + """"/>"""
                field_arch_arabic += """<td colspan="2" style="text-align: right;"><strong>""" + normal_field.field_description + """</strong></td></tr>
                <tr><td colspan="2"><span t-raw="o.""" + normal_field.name + """"/></td>"""
                field_arch_english += """<td colspan="2" style="text-align: left;"><strong>""" + normal_field.field_description + """</strong></td></tr>
                <tr><td colspan="2"><span t-raw="o.""" + normal_field.name + """"/></td>"""
                
                # field_arch_arabic += """<td style="text-align: right;"><span t-raw="o.""" + normal_field.name + """"/></td>"""
                # field_arch_english += """<td style="text-align: left;"><span t-raw="o.""" + normal_field.name + """"/></td>"""
            elif normal_field.ttype == 'boolean':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """"> <input type="checkbox" checked="True"/></t> """
                # field_arch_english += """<t t-if="not o.""" + normal_field.name + """"> <input type="checkbox"/></t> """
                field_arch_arabic += """<t t-if="o.""" + normal_field.name + """"><td style="text-align: right;"><input type="checkbox" checked="True"/></td></t> """
                field_arch_arabic += """<t t-if="not o.""" + normal_field.name + """"><td style="text-align: right;"><input type="checkbox" /></td></t> """
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-raw="o.""" + normal_field.name + """"/>"""
                # field_arch_arabic += """<td style="text-align: right;"><span t-raw="o.""" + normal_field.name + """"/></td>"""
                field_arch_english += """<t t-if="o.""" + normal_field.name + """"><td style="text-align: left;"><input type="checkbox" checked="True"/></td></t> """
                field_arch_english += """<t t-if="not o.""" + normal_field.name + """"><td style="text-align: left;"><input type="checkbox" /></td></t> """
                # print(field_arch_englishddddd)
            elif normal_field.ttype == 'many2one':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-esc="o.""" + normal_field.name + """.display_name"/>"""
                field_arch_arabic += """<td style="text-align: right;"><span t-esc="o.""" + normal_field.name + """.display_name"/></td>"""
                field_arch_english += """<td style="text-align: left;"><span t-esc="o.""" + normal_field.name + """.display_name"/></td>"""
            elif normal_field.ttype == 'many2many':
                # or normal_field.ttype == 'one2many':
                # field_arch_english += """<t t-foreach="o.""" + normal_field.name + """" t-as="xxx"><span t-esc="xxx.display_name"/>,</t>"""
                field_arch_arabic += """<td style="text-align: right;"><span t-esc="', '.join([ xxx.display_name or '' for xxx in o.""" + normal_field.name + """])"/></t></td>"""
                field_arch_english += """<td style="text-align: left;"><span t-esc="', '.join([ xxx.display_name or '' for xxx in o.""" + normal_field.name + """])"/></t></td>"""
            elif normal_field.ttype == 'selection':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-esc="o.""" + normal_field.name + """"/>"""
                field_arch_arabic += """<td style="text-align: right;"><span t-esc="o.""" + normal_field.name + """"/></td>"""
                field_arch_english += """<td style="text-align: left;"><span t-esc="o.""" + normal_field.name + """"/></td>"""
            elif normal_field.ttype == 'one2many':
                local_string = """<td colspan="2">"""
                local_string += """<t t-if="o.language=='english'">
                       <strong>"""+ normal_field.field_description + """</strong></t>
                       <t t-else=""><div style="text-align: right;"><strong>"""+ normal_field.field_arabic_description + """</strong></div></t>"""           
                local_string += """<table t-if="o."""+normal_field.name+"""" class="table table-condensed">"""
                model = self.env['ir.model'].search([('model','=',normal_field.relation)])
                if model:
                    local_string += """<thead><tr t-if="o.language == 'english'">"""
                    for field in model.field_id.filtered(lambda r: r.visible_in_consent_tree).sorted(lambda c: c.dynamic_sequence):
                        local_string += """<th>"""+field.field_description+"""</th>"""
                    local_string += """</tr><tr t-if="o.language == 'arabic'">"""
                    for field in model.field_id.filtered(lambda r: r.visible_in_consent_tree).sorted(lambda c: c.dynamic_sequence):
                        local_string += """<th>"""
                        local_string += field.field_arabic_description if field.field_arabic_description else field.field_description +"""</th>"""
                    local_string+="""</tr></thead>"""
                    local_string+=    """<tbody><t t-foreach="o."""+normal_field.name+""""t-as="l">
                    <tr>"""
                    for field in model.field_id.filtered(lambda r: r.visible_in_consent_tree).sorted(lambda c: c.dynamic_sequence):
                        if field.ttype == "boolean":
                            local_string += """<td><t t-if="l."""+field.name+""""><input type="checkbox" checked="True"/></t><t t-else=""><input type="checkbox"/></t></td>"""
                        else:
                            local_string += """<td><span t-field="l."""+field.name+""""></td>"""
                    local_string += """</tr></tbody>"""   
                local_string +=  """</table></td>"""   
                field_arch_english += local_string
                field_arch_arabic += local_string
                
            if normal_field.ttype =='text' and normal_field.readonly:
               field_arch_arabic += """<td colspan="2" style="text-align: right;"><strong>""" + normal_field.field_arabic_description + """</strong></td>"""
            else:
                if normal_field.ttype not in ('one2many','html'):
                    field_arch_arabic += """<td colspan="2" style="text-align: right;"><strong>""" + normal_field.field_arabic_description + """</strong></td>"""
            field_arch_arabic += "</tr>"
            field_arch_english += "</tr>"
            # field_arch_english += """ 
            #                      <br/>
            # """

            # check and add dependent fields
            result = self.add_dependent_field(normal_field)
            field_arch_english += result.get('field_arch_english', '')
            field_arch_arabic += result.get('field_arch_arabic', '')

        field_arch_arabic += """
                                </tbody>
                            </table>"""
        field_arch_english += """
                                </tbody>
                            </table>"""
        
        sign_arch_english = ''
        sign_arch_arabic = ''
        for sign_field in self.signature_field_ids:
            sign_arch_english += """<strong>""" + sign_field.field_description + """</strong>"""
            sign_arch_english += """<img t-if='o.""" + sign_field.name + """' t-att-src="'data:image/png;base64,%s' % to_text(o.""" + sign_field.name + """)" class="pull-right" height="60"/>"""
            sign_arch_arabic += """<img t-if='o.""" + sign_field.name + """' t-att-src="'data:image/png;base64,%s' % to_text(o.""" + sign_field.name + """)" class="pull-left" height="60"/>"""
            sign_arch_arabic += """<strong class="pull-right" style="display: inline-block;">""" + sign_field.field_arabic_description.replace(' ','&#160;') + """</strong>"""
            sign_arch_english += """<br/><br/><br/><br/>"""
            sign_arch_arabic += """<br/><br/><br/><br/>"""
        config_obj = self.env['ir.config_parameter'].sudo()
        consent_form_font_size = literal_eval(config_obj.get_param('dynamic_consent_form.consent_form_font_size',
                                                                           default='20'))
        font_size = "style='font-size:" + str(consent_form_font_size) +"px;padding-top:45px;'"
        view_arch = """
            <t t-name='dynamic_consent_form.""" + self.name + """'>
                <t t-call="web.html_container">
                    <t t-call="web.external_layout">
                        <t t-foreach="docs" t-as="o">
                            <div class="page" """ + font_size + """ >
                                <t t-if="o.language=='english'">
                                    <div class="text-center">
                                        <h3> <t t-esc="o.heading_english"/> </h3>
                                    </div> 
                                    """ + field_arch_english + """
                                    <br/>
                                    <div t-if="o.image_1" >
                                        <img t-if="o.image_1" t-att-src="'data:image/png;base64,%s' % to_text(o.image_1)"
                                            style="min-width: 700px;max-width: 900px;max-height: 700px;"/>
                                        <br/>
                                    </div>  
                                    <div t-if="o.image_2" >
                                        <img t-if="o.image_2" t-att-src="'data:image/png;base64,%s' % to_text(o.image_2)"
                                            style="min-width: 700px;max-width: 900px;max-height: 700px;"/>
                                        <br/>
                                    </div>  
                                    <t t-raw="o.content_english"/>
                                    <br/>
                                    """ + sign_arch_english + """
                                    <br/>
                                    <div t-if="o.stamp or o.signature" >
                                        <img t-if="o.stamp" t-att-src="'data:image/png;base64,%s' % to_text(o.stamp)" style="max-height: 100px;"/>
                                        <img t-if="o.signature" t-att-src="'data:image/png;base64,%s' % to_text(o.signature)" style="max-height: 100px;"/>
                                        <br/>
                                    </div> 
                                    
                                </t> 
                                <t t-if="o.language=='arabic'">
                                    <div class="text-center" >
                                        <h3> <t t-esc="o.heading_arabic"/> </h3>
                                    </div> 
                                    """ + field_arch_arabic + """
                                    <br/><br/><br/>
                                    <div t-if="o.image_1" >
                                        <img t-if="o.image_1" t-att-src="'data:image/png;base64,%s' % to_text(o.image_1)"
                                            style="min-width: 700px;max-width: 900px;max-height: 700px;"/>
                                        <br/>
                                    </div>  
                                    <div t-if="o.image_2" >
                                        <img t-if="o.image_2" t-att-src="'data:image/png;base64,%s' % to_text(o.image_2)"
                                            style="min-width: 700px;max-width: 900px;max-height: 700px;"/>
                                        <br/>
                                    </div>    
                                    <t t-raw="o.content_arabic"/>
                                    <br/>
                                    """ + sign_arch_arabic + """
                                    <br/>
                                    <div t-if="o.stamp or o.signature" >
                                        <img t-if="o.stamp" t-att-src="'data:image/png;base64,%s' % to_text(o.stamp)" style="max-height: 100px;" class="pull-right"/>
                                        <img t-if="o.signature" t-att-src="'data:image/png;base64,%s' % to_text(o.signature)" style="max-height: 100px;padding-right:3px;" class="pull-right"/>
                                        <br/>
                                    </div>   
                                    
                                </t> 
                            </div>    
                        </t>
                    </t>
                </t>
            </t>
        """
        return view_arch

    def design_blank_qweb_view(self):
        field_arch_english = ''
        arabic_date  = 'Date'
        arabic_patient  = 'Patient'
        arabic_doctor  = ' Doctor'
        # arabic_date  = 'التاريخ'
        # arabic_patient  = 'اسم المريض'
        # arabic_doctor  = ' الطبيب'
        field_arch_arabic = """<table width="100%">
                                <colgroup>
                                    <col width='40%' />
                                    <col width='60%' />
                                </colgroup>
                                <thead>
                                    <tr>
                                        <th></th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody >
                                    <tr>
                                        <td style="text-align: right;"></td>
                                        <td style="text-align: right;"><strong>"""+ arabic_date + """ </strong></td>
                                    </tr>
                                    <tr>
                                        <td style="text-align: right;"></td>
                                        <td style="text-align: right;"><strong>"""+ arabic_patient+ """ </strong></td>
                                    </tr>
                                    <tr>
                                        <td style="text-align: right;"></td>
                                        <td style="text-align: right;"><strong>"""+ arabic_doctor+ """  </strong></td>
                                    </tr>
                                """
                                
        field_arch_english =   """<table width="100%">
                                <colgroup>
                                    <col width='60%' />
                                    <col width='40%' />
                                </colgroup>
                                <thead>
                                    <tr>
                                        <th></th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody >
                                    <tr>
                                        <td style="text-align: left;"><strong>"""+ arabic_date + """ </strong></td>
                                        <td></td>
                                    </tr>
                                    <tr>
                                        <td style="text-align: left;"><strong>"""+ arabic_patient+ """ </strong></td>
                                        <td></td>
                                    </tr>
                                    <tr>
                                        <td style="text-align: left;"><strong>"""+ arabic_doctor+ """  </strong></td>
                                        <td></td>
                                    </tr>
                                    <tr>
                                        <td ><strong>"""+ "               "+ """  </strong></td>
                                        <td></td>
                                    </tr>
                                    
                                """                      
                                
        # field_arch_english += """<strong>Date : &#160;&#160;</strong>"""
        # field_arch_english += """<br/>"""
        # field_arch_english += """<strong>Patient : &#160;&#160;</strong>"""
        # field_arch_english += """<br/>"""
        # field_arch_english += """<strong>Doctor : &#160;&#160;</strong>"""
        # field_arch_english += """<br/>"""
        for normal_field in self.field_ids:
            # field_arch_english += """<strong>""" + normal_field.field_description + """: &#160;&#160;</strong>"""
            field_arch_arabic += "<tr>"
            field_arch_english += "<tr>"
            
            if normal_field.ttype =='text' and normal_field.readonly:
               field_arch_english += """<td colspan="2" style="text-align: left;"><strong>""" + normal_field.field_description + """</strong></td>""" 
            else:
                field_arch_english += """<td style="text-align: left;"><strong>""" + normal_field.field_description + """</strong></td>"""
            
            if normal_field.ttype in ('char', 'date') or normal_field.ttype =='text' and not normal_field.readonly:
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-esc="o.""" + normal_field.name + """"/>"""
                field_arch_arabic += """<td style="text-align: right;"></td>"""
                field_arch_english += """<td></td>"""
            elif normal_field.ttype == 'html':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-raw="o.""" + normal_field.name + """"/>"""
                field_arch_arabic += """<td style="text-align: right;"></td>"""
                field_arch_english += """<td></td>"""
            elif normal_field.ttype == 'boolean':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-raw="o.""" + normal_field.name + """"/>"""
                field_arch_arabic += """<td style="text-align: right;"></td>"""
                field_arch_english += """<td></td>"""
            elif normal_field.ttype == 'many2one':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-esc="o.""" + normal_field.name + """.display_name"/>"""
                field_arch_arabic += """<td style="text-align: right;"></td>"""
                field_arch_english += """<td></td>"""
            elif normal_field.ttype == 'many2many' or normal_field.ttype == 'one2many':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-esc="o.""" + normal_field.name + """.display_name"/>"""
                field_arch_arabic += """<td style="text-align: right;"></td>"""
                field_arch_english += """<td></td>"""
            elif normal_field.ttype == 'selection':
                # field_arch_english += """<t t-if="o.""" + normal_field.name + """" t-esc="o.""" + normal_field.name + """"/>"""
                field_arch_arabic += """<td style="text-align: right;"></td>"""
                field_arch_english += """<td></td>"""
            if normal_field.ttype =='text' and normal_field.readonly:
               field_arch_arabic += """<td colspan="2" style="text-align: right;"><strong>""" + normal_field.field_arabic_description + """</strong></td>"""
            else:
                field_arch_arabic += """<td style="text-align: right;"><strong>""" + normal_field.field_arabic_description + """</strong></td>"""
            field_arch_arabic += "</tr>"
            # field_arch_english += """ 
            #                      <br/>
            # """
            field_arch_english += "</tr>"
            
            
        field_arch_arabic += """
                                </tbody>
                            </table>"""
                            
        field_arch_english += """
                                </tbody>
                            </table>"""
        
        sign_arch_english = ''
        sign_arch_arabic = ''
        for sign_field in self.signature_field_ids:
            sign_arch_english += """<strong>""" + sign_field.field_description + """</strong>"""
            sign_arch_arabic += """<strong class="pull-right">""" + sign_field.field_arabic_description.replace(' ','&#160;') + """</strong>"""
            # sign_arch_english += """<img t-if='o.""" + sign_field.name + """' t-att-src="'data:image/png;base64,%s' % to_text(o.""" + sign_field.name + """)" class="pull-right" height="60"/>"""
            # sign_arch_arabic += """<img t-if='o.""" + sign_field.name + """' t-att-src="'data:image/png;base64,%s' % to_text(o.""" + sign_field.name + """)" class="pull-right" height="60"/>"""
            sign_arch_english += """<br/><br/><br/><br/>"""
            sign_arch_arabic += """<br/><br/><br/><br/>"""
        config_obj = self.env['ir.config_parameter'].sudo()
        consent_form_font_size = literal_eval(config_obj.get_param('dynamic_consent_form.consent_form_font_size',
                                                                           default='20'))
        font_size = "style='font-size:" + str(consent_form_font_size) +"px;padding-top:45px;'"
        view_arch = """
            <t t-name='dynamic_consent_form.Blank_""" + self.name + """'>
                <t t-call="web.html_container">
                    <t t-call="web.external_layout">
                        <t t-foreach="docs" t-as="o">
                            <div class="page" """ + font_size + """ >
                                <t t-if="o.blank_report_language=='english'">
                                    <div class="text-center">
                                        <h3> Blank <t t-esc="o.heading_english"/> </h3>
                                    </div> 
                                    """ + field_arch_english + """
                                    <br/>
                                    <div t-if="o.image_1" >
                                        <img t-if="o.image_1" t-att-src="'data:image/png;base64,%s' % to_text(o.image_1)"
                                            style="min-width: 700px;max-width: 900px;max-height: 700px;"/>
                                        <br/>
                                    </div>  
                                    <div t-if="o.image_2" >
                                        <img t-if="o.image_2" t-att-src="'data:image/png;base64,%s' % to_text(o.image_2)"
                                            style="min-width: 700px;max-width: 900px;max-height: 700px;"/>
                                        <br/>
                                    </div>   
                                    <t t-raw="o.content_english"/>
                                    <br/>
                                    """ + sign_arch_english + """
                                </t> 
                                <t t-if="o.blank_report_language=='arabic'">
                                    <div class="text-center" >
                                        <h3> <t t-esc="o.heading_arabic"/> </h3>
                                    </div> 
                                    """ + field_arch_arabic + """
                                    <br/><br/><br/>
                                    <div t-if="o.image_1" >
                                        <img t-if="o.image_1" t-att-src="'data:image/png;base64,%s' % to_text(o.image_1)"
                                            style="min-width: 700px;max-width: 900px;max-height: 700px;"/>
                                        <br/>
                                    </div>  
                                    <div t-if="o.image_2" >
                                        <img t-if="o.image_2" t-att-src="'data:image/png;base64,%s' % to_text(o.image_2)"
                                            style="min-width: 700px;max-width: 900px;max-height: 700px;"/>
                                        <br/>
                                    </div>    
                                    <t t-raw="o.content_arabic"/>
                                    <br/>
                                    """ + sign_arch_arabic + """
                                </t> 
                            </div>    
                        </t>
                    </t>
                </t>
            </t>
        """
        return view_arch

    def delete_report_template(self):
        # delete report template related qweb view
        dom_qweb_view = [('name', 'ilike', self.report_template_id.name), ('type', '=', 'qweb')]
        qweb_template_view_id = self.env['ir.ui.view'].search(dom_qweb_view)
        if qweb_template_view_id:
            qweb_template_view_id.unlink()
        # delete ir_model_data
        dom_ir_model_data  = [('module', '=', 'dynamic_consent_form'),('name', '=', self.name),('model', '=','ir.ui.view')]
        ir_model_data_exists = self.env['ir.model.data'].search(dom_ir_model_data)
        if ir_model_data_exists:
            ir_model_data_exists.unlink()
        # delete report template
        self.report_template_id.sudo().unlink()

    def delete_blank_report_template(self):
        # delete report template related qweb view
        dom_qweb_view = [('name', 'ilike', 'Blank_' + self.report_blank_template_id.name), ('type', '=', 'qweb')]
        qweb_template_view_id = self.env['ir.ui.view'].search(dom_qweb_view)
        if qweb_template_view_id:
            qweb_template_view_id.unlink()
        # delete ir_model_data
        dom_ir_model_data  = [('module', '=', 'dynamic_consent_form'),('name', '=', 'Blank_' + self.name),('model', '=','ir.ui.view')]
        ir_model_data_exists = self.env['ir.model.data'].search(dom_ir_model_data)
        if ir_model_data_exists:
            ir_model_data_exists.unlink()
        # delete report template
        self.report_blank_template_id.unlink()

    def create_report_template(self):
        report_template_vals = {
            'name': self.name,
            'report_type': 'qweb-pdf',
            'model': 'consent.wizard',
            'binding_model_id': False,
            'report_name': 'dynamic_consent_form.' + self.name,
        }
        report_template_id = self.env['ir.actions.report'].sudo().create(report_template_vals)
        view_arch = self.design_qweb_view()
        dom_ir_model_data  = [('module', '=', 'dynamic_consent_form'),('name', '=', self.name),('model', '=','ir.ui.view')]
        ir_model_data_exists = self.env['ir.model.data'].search(dom_ir_model_data)
        if ir_model_data_exists:
            ir_model_data_exists.unlink()
        ir_model_data_id = self.env['ir.model.data'].create({
            'name':  self.name ,
            'module':  'dynamic_consent_form',
            'display_name':  self.name ,
            'model': 'ir.ui.view',
        })
        qweb_view_id = self.env['ir.ui.view'].create({
            'name':  self.name ,
            'key':  'dynamic_consent_form.' + self.name ,
            'xml_id':  'dynamic_consent_form.' + self.name ,
            'type': 'qweb',
            'mode': 'primary',
            'model': 'consent.wizard',
            'active': True,
            'arch': view_arch,
        })
        ir_model_data_id.write({'reference': qweb_view_id.id,'res_id': qweb_view_id.id})
        self.write({'report_template_id':report_template_id.id})

    def create_blank_report_template(self):
        report_template_vals = {
            'name': 'Blank_' + self.name,
            'report_type': 'qweb-pdf',
            'model': 'consent.details',
            'binding_model_id': False,
            'report_name': 'dynamic_consent_form.Blank_' + self.name,
        }
        report_blank_template_id = self.env['ir.actions.report'].create(report_template_vals)
        view_arch = self.design_blank_qweb_view()
        dom_ir_model_data  = [('module', '=', 'dynamic_consent_form'),('name', '=', 'Blank_' + self.name),('model', '=','ir.ui.view')]
        ir_model_data_exists = self.env['ir.model.data'].search(dom_ir_model_data)
        if ir_model_data_exists:
            ir_model_data_exists.unlink()
        ir_model_data_id = self.env['ir.model.data'].create({
            'name':  'Blank_' + self.name ,
            'module':  'dynamic_consent_form',
            'display_name':  self.name ,
            'model': 'ir.ui.view',
        })
        qweb_view_id = self.env['ir.ui.view'].create({
            'name':  'Blank_' + self.name ,
            'key':  'dynamic_consent_form.Blank_' + self.name ,
            'xml_id':  'dynamic_consent_form.Blank_' + self.name ,
            'type': 'qweb',
            'mode': 'primary',
            'model': 'consent.details',
            'active': True,
            'arch': view_arch,
        })
        ir_model_data_id.write({'reference': qweb_view_id.id,'res_id': qweb_view_id.id})
        self.write({'report_blank_template_id':report_blank_template_id.id})

    @api.multi
    def print_blank_report(self):
        if self.report_template_id:
            self.modify_report_template()
        if self.report_blank_template_id:
            self.modify_blank_report_template()
        if not self.report_blank_template_id:
            self.create_blank_report_template()
        dom_qweb_view = [('name', 'ilike', self.report_blank_template_id.name), ('type', '=', 'qweb')]
        qweb_template_view_id = self.env['ir.ui.view'].search(dom_qweb_view)
        if len(qweb_template_view_id) == 0:
            self.modify_blank_report_template()
        # self.patient_id.attach_blank_consent(self)
        return self.report_blank_template_id.report_action(self)

    def add_dependent_field(self, active_field=None):
        """check for field dependency and return the xml architecture
        if the field has a dependent field"""
        if active_field and active_field.has_dependency:
            return self.do_process_field(active_field)
        else:
            return {}

    def do_process_field(self, active_field):
        field_arch_english = """"""
        field_arch_arabic = """"""

        dependent_field = active_field.dependent_field
        if dependent_field:
            dep_ftype = dependent_field.ttype
            dep_fname = "o." + dependent_field.name
        parent_fname = "o." + active_field.name

        attr_val = active_field.dependent_value
        if active_field.ttype == 'boolean' and active_field.dependent_value:
            attr_val = active_field.dependent_value.lower() == 'true' and "True" or "False"
        attrs_inv = "%s=='%s'" % (parent_fname, attr_val)
        if active_field.ttype == 'selection' and active_field.select_related_field_ids:
            # Additional Features with and without fields in selection field
            for line in active_field.select_related_field_ids:
                attrs_inv = "" + parent_fname + "=='" + line.value + "'"
                field_arch_arabic += """<tr t-if="%s">""" % attrs_inv
                field_arch_english += """<tr t-if="%s">""" % attrs_inv
                if line.related_field_id:
                    field_arch_english += """
                        <td style="text-align: left;padding-left:10px;"><strong>
                        """ + line.related_field_id.field_description + """
                        </strong></td>"""
                    
                    field_arch_english +=("""<td style="text-align: left;"><span t-esc="%s"/></td>
                            """ % ("o." + line.related_field_id.name))
                    
                    field_arch_arabic += (
                            """<td style="text-align: right;"><span t-esc="%s"/></td>
                            """ % ("o." + line.related_field_id.name))
            
                    field_arch_arabic += """
                        <td style="text-align: right;padding-right:10px;"><strong>
                        """ + line.related_field_id.field_arabic_description + """
                        </strong></td></tr>"""
                    field_arch_english += """</tr>"""
                else:
                    field_arch_english += """
                        <td style="text-align: left;padding-left:10px;"><strong>
                        """ + line.value + """
                        </strong></td>"""
                    field_arch_english +="""<td style="text-align: left;"></td>""" 
                    
                    field_arch_arabic += """<td style="text-align: right;"></td>"""
                    field_arch_arabic += """
                        <td style="text-align: right;padding-right:10px;"><strong>
                        """ + line.value + """
                        </strong></td></tr>"""
                    field_arch_english += """</tr>"""
                    
        else:
            if active_field.ttype == 'boolean' and active_field.boolean_related_field_ids:
                for line in active_field.boolean_related_field_ids:
                    attrs_inv = "" + parent_fname + "==True" 
                    field_arch_arabic += """<tr t-if="%s">""" % attrs_inv
                    field_arch_english += """<tr t-if="%s">""" % attrs_inv
                    if line.related_text_field_id and line.related_bool_field_id:
                        field_arch_english += """
                            <td style="text-align: left;padding-left:10px;"><strong><t t-if="%s"><input type="checkbox" checked="True"/></t><t t-if="not %s"><input type="checkbox"/></t>
                            """% ('o.'+line.related_bool_field_id.name, 'o.'+line.related_bool_field_id.name)+ line.related_bool_field_id.field_description + """
                            </strong></td>""" 
                        
                        field_arch_english +=("""<td style="text-align: left;"><t t-if="%s"><span t-field="%s"/></t></td>
                                """ % ("o."+line.related_bool_field_id.name +"=="+str(line.visible_in),"o." + line.related_text_field_id.name))
                        
                        field_arch_arabic += (
                                """<td style="text-align: right;"><t t-if="%s"><span t-field="%s"/></t></td>
                                """ % ("o."+line.related_bool_field_id.name +"=="+str(line.visible_in),"o." + line.related_text_field_id.name))
                
                        field_arch_arabic += """
                            <td style="text-align: right;padding-right:10px;"><strong>
                            """ + line.related_bool_field_id.field_arabic_description + """
                            </strong><t t-if="%s"><input type="checkbox" checked="True"/></t><t t-if="not %s"><input type="checkbox"/></t></td></tr>"""% ('o.'+line.related_bool_field_id.name, 'o.'+line.related_bool_field_id.name) 
                    elif not line.related_text_field_id and line.related_bool_field_id:
                        field_arch_english += """
                            <td style="text-align: left;padding-left:10px;"><strong><t t-if="%s"><input type="checkbox" checked="True"/></t><t t-if="not %s"><input type="checkbox"/></t>
                            """% ('o.'+line.related_bool_field_id.name, 'o.'+line.related_bool_field_id.name)+ line.related_bool_field_id.field_description + """
                            </strong></td>""" 
                        field_arch_english +=("""<td style="text-align: left;"></td>""" )
                        field_arch_arabic += (
                                """<td style="text-align: right;"></td>""" )
                        field_arch_arabic += """
                            <td style="text-align: right;padding-right:10px;"><strong>
                            """ + line.related_bool_field_id.field_arabic_description + """
                            </strong><t t-if="%s"><input type="checkbox" checked="True"/></t><t t-if="not %s"><input type="checkbox"/></t></td></tr>"""% ('o.'+line.related_bool_field_id.name, 'o.'+line.related_bool_field_id.name) 
                    
                    field_arch_english += """</tr>"""
            else:

                # field_arch_english += """
                #     <t t-if="%s" <strong> %s: &#160;&#160;</strong>""" % (
                #     attrs_inv, dependent_field.field_description)
                
                field_arch_arabic += """<tr t-if="%s">""" % attrs_inv
                field_arch_english += """<tr t-if="%s">""" % attrs_inv
                
                field_arch_english += """
                    <td style="text-align: left;"><strong>
                    """ + dependent_field.field_arabic_description + """
                    </strong></td>"""
                
                if dep_ftype in ('char', 'date', 'text'):
                    # field_arch_english += """<t t-if="%s" t-esc="%s"/>""" % (
                    #     dep_fname, dep_fname)
                    field_arch_english +=("""<td style="text-align: left;"><span t-esc="%s"/></td>
                            """ % dep_fname)
                    
                    field_arch_arabic += (
                            """<td style="text-align: right;"><span t-esc="%s"/></td>
                            """ % dep_fname)
                elif dep_ftype == 'html':
                    # field_arch_english += ("""<t t-if="%s" t-raw="%s"/>""" % (
                    #     dep_fname, dep_fname))
                    field_arch_english += (
                            """<td style="text-align: left;"><span t-raw="%s"/></td>
                            """ % dep_fname)
                    
                    field_arch_arabic += (
                            """<td style="text-align: right;"><span t-raw="%s"/></td>
                            """ % dep_fname)
                elif dep_ftype == 'boolean':
                    # field_arch_english += """<t t-if="%s">
                    #     <input type="checkbox" checked="True"/></t>
                    #     <t t-if="%s"> <input type="checkbox"/></t> 
                    # """ % (dep_fname, dep_fname)
                    
                    field_arch_english += """
                        <t t-if="%s"><td style="text-align: left;">
                        <input type="checkbox" checked="True"/></td></t>
                        <t t-if="not %s"><td style="text-align: left;">
                        <input type="checkbox"/></td></t> """ % (dep_fname, dep_fname) 
                    
                    field_arch_arabic += """
                        <t t-if="%s"><td style="text-align: right;">
                        <input type="checkbox" checked="True"/></td></t>
                        <t t-if="not %s"><td style="text-align: right;">
                        <input type="checkbox"/></td></t> """ % (dep_fname, dep_fname)
                elif dep_ftype == 'many2one':
                    # field_arch_english += """
                    #     <t t-if="%s" t-esc="%s.display_name"/>""" % (
                    #     dep_fname, dep_fname)
                    field_arch_english += """
                        <td style="text-align: left;">
                        <span t-esc="%s.display_name"/></td>""" % dep_fname
                    field_arch_arabic += """
                        <td style="text-align: right;">
                        <span t-esc="%s.display_name"/></td>""" % dep_fname
                elif dep_ftype == 'many2many':
                    # field_arch_english += """
                    #     <t t-foreach="%s" t-as="xxx"> 
                    #     <span t-esc="xxx.display_name"/>,</t>""" % dep_fname
                    field_arch_english += """
                        <td style="text-align: left;">
                        <t t-foreach="%s" t-as="xxx"><span t-esc="xxx.display_name"/>
                        ,</t></td>""" % dep_fname
                    
                    field_arch_arabic += """
                        <td style="text-align: right;">
                        <t t-foreach="%s" t-as="xxx"><span t-esc="xxx.display_name"/>
                        ,</t></td>""" % dep_fname
                elif dep_ftype == 'selection':
                    # field_arch_english += """<t t-if="%s" t-esc="%s"/>""" % (
                    #     dep_fname, dep_fname)
                    field_arch_english += """
                        <td style="text-align: left;"><span t-esc="%s"/></td>
                        """ % dep_fname
                    
                    field_arch_arabic += """
                        <td style="text-align: right;"><span t-esc="%s"/></td>
                        """ % dep_fname
                field_arch_arabic += """
                    <td style="text-align: right;"><strong>
                    """ + dependent_field.field_arabic_description + """
                    </strong></td></tr>"""
                # field_arch_english += """<br/></t>"""
                field_arch_english += """</tr>"""
        
        return {
            'field_arch_english': field_arch_english,
            'field_arch_arabic': field_arch_arabic
        }
        

    
    
    
    
    
    
    
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
