from odoo import api, fields, models, SUPERUSER_ID
import base64
from odoo.exceptions import UserError
from ast import literal_eval

class ConsentWizard(models.Model):
    _name = "consent.wizard"
    _rec_name = 'consent_detail_id'
    _order = 'id desc'
    
    @api.model
    def default_get(self, field_list):
        res = super(ConsentWizard, self).default_get(field_list)
        self.env['field.view.update'].create({}).design_dynamic_field_view()
        
        consent_fields = self.env['ir.model.fields'].search([('consent_field', '=', True),
                                                                 ('related_xml_field_id', '=', False),
                                                                ('is_sign_field_id', '=', False)])
        
        consent_rec = self.env['consent.details'].browse(self.env.context.get('default_consent_detail_id',False))
        
        if consent_rec:
            # html_vals = {}
            # all_consent_fields = consent_rec.field_ids
            # for selected_fields in all_consent_fields:
            #     if selected_fields.ttype == 'html':
            #         if self.language == 'english':
            #             html_vals[str(selected_fields.name)] = selected_fields.html_default_content
            #         if self.language == 'arabic':
            #             html_vals[str(selected_fields.name)] = selected_fields.html_arabic_default_content
            #
            # res.update(html_vals)
            final_vals = {}
            for m_fields in consent_fields:
                final_vals[str(m_fields.name)] = False
            for m_fields in consent_fields:
                # consent_rec = rec.consent_detail_id
                if consent_rec:
                    all_consent_fields = consent_rec.field_ids
                    for selected_fields in all_consent_fields:
                        X = selected_fields.name + '_compute'
                        if(X == m_fields.name):
                            final_vals[str(m_fields.name)] = True
            
            res.update(final_vals)
            
            sign_consent_fields = []
            for original_field in self.env['ir.model.fields'].search([('related_xml_field_id', '!=', False)]):
                if original_field.is_sign_field_id and original_field.related_xml_field_id:
                    sign_consent_fields.append(original_field.related_xml_field_id)
            sign_final_vals = {}
            for sign_m_fields in sign_consent_fields:
                sign_final_vals[str(sign_m_fields.name)] = False
            for sign_m_fields in sign_consent_fields:
                    # consent_rec = rec.consent_detail_id
                    if consent_rec:
                        all_sign_consent_fields = consent_rec.signature_field_ids
                        for selected_sign_fields in all_sign_consent_fields:
                            X = selected_sign_fields.name + '_compute'
                            if(X == sign_m_fields.name):
                                sign_final_vals[str(sign_m_fields.name)] = True
            
            res.update(sign_final_vals)
            for field in consent_rec.field_ids.filtered(lambda c: c.ttype == 'one2many'):
                field_default = []
                if field.defaults_fields_ids:
                    for default_value in field.defaults_fields_ids.sorted(key=lambda l: l.sequence):
                        field_default.append((0,0,{'x_name':default_value.name}))
                    res.update({str(field.name):field_default})
            res.update({'patient_details':True if consent_rec.need_patient_details else False})
        return res
    
    @api.depends('language')
    def _get_header_need(self):
        for rec in self:
            conf_obj = self.env['ir.config_parameter'].sudo()
            consent_header = literal_eval(conf_obj.get_param('consent_header', default='False'))
            rec.header_need = consent_header
    
    @api.depends('language')
    def _get_company_header(self):
        for rec in self: 
            rec.company_header = self.env.user.company_id.logo
            if self.env.user.company_id.header_image:
                rec.company_header = self.env.user.company_id.header_image
            
    @api.depends('language')
    def _get_company_footer(self):
        for rec in self:   
            rec.company_footer = self.env.user.company_id.report_footer
     
    @api.depends('language')        
    def _get_header_note(self):
        for rec in self:     
            rec.header_report_note = self.env.user.company_id.report_header   

    register_date = fields.Date('Date', default=fields.Date.context_today, required=True)
    patient_id = fields.Many2one('medical.patient', 'Patient', required=True)
    doctor_id = fields.Many2one('medical.physician', 'Doctor')
    consent_detail_id = fields.Many2one('consent.details', string='Consent',required=True)
    sign_xpath_field_id = fields.Boolean(string='Sign xpath field')
    language = fields.Selection([('english', 'English'),
                                 ('arabic', 'Arabic')], 'Language', readonly=False, required=True, default='english')
    heading_english = fields.Char('Heading - English',required=False)
    heading_arabic = fields.Char('Heading - Arabic',required=False)
    content_english = fields.Html('Content - English',required=False)
    content_arabic = fields.Html('Content - Arabic',required=False)
    image_1 = fields.Binary('Image',required=False)
    image_2 = fields.Binary('Image',required=False)
    arabic_data = fields.Boolean(string="Arabic Data")
    arabic_sign = fields.Boolean(string="Arabic Data")
    company_header = fields.Binary(compute="_get_company_header",string='Header')
    company_footer = fields.Text(compute="_get_company_footer",string='Footer')
    header_need = fields.Boolean(compute="_get_header_need",string='Header Need')
    header_report_note = fields.Text(compute="_get_header_note",string='Header Note')
    company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.user.company_id.id)
    
    stamp = fields.Binary("Stamp and Seal")
    signature = fields.Binary("Signature")
    
    
    patient_details = fields.Boolean(string='Patient Details')
    mrn = fields.Char('MRN')
    patient_ref = fields.Char('ID Number')
    

    @api.onchange('consent_detail_id', 'language')
    def onchange_consent_detail_id(self):
        self.set_test_consent_compute()
        self.image_1 = self.consent_detail_id.image_1
        self.image_2 = self.consent_detail_id.image_2
        if self.language == 'english':
            self.heading_english = self.consent_detail_id.heading_english
            self.content_english = self.consent_detail_id.content_english
            self.heading_arabic = ''
            self.content_arabic = ''
            
        if self.language == 'arabic':
            self.heading_arabic = self.consent_detail_id.heading_arabic
            self.content_arabic = self.consent_detail_id.content_arabic
            self.heading_english = ''
            self.content_english = ''
        if not self.language:
            self.heading_arabic = ''
            self.content_arabic = ''
            self.heading_english = ''
            self.content_english = ''
        if self.language:
            for field in self.consent_detail_id.field_ids.filtered(lambda c: c.ttype == 'one2many'):
                    self.update({str(field.name):False})
                    field_default = []
                    if field.defaults_fields_ids:
                        for default_value in field.defaults_fields_ids.sorted(key=lambda l: l.sequence):
                            field_default.append((0,0,{'x_name':default_value.name if self.language == 'english' else default_value.arabic_name}))
                        self.update({str(field.name):field_default})
            html_vals = {}
            all_consent_fields = self.consent_detail_id.field_ids
            for selected_fields in all_consent_fields:
                if selected_fields.ttype == 'html':
                    if self.language == 'english':
                        html_vals[str(selected_fields.name)] = selected_fields.html_default_content
                    if self.language == 'arabic':
                        html_vals[str(selected_fields.name)] = selected_fields.html_arabic_default_content
            if html_vals:
                self.update(html_vals)

    @api.onchange('language','consent_detail_id')
    def onchange_language(self):
        update_dict = {}
        if self.consent_detail_id and self.language:
            for fields in self.consent_detail_id.field_ids.filtered(lambda x: x.ttype == 'html'):
                update_dict.update({fields.name:fields.html_default_content if self.language == 'english' else fields.html_arabic_default_content})
        self.update(update_dict)
    
    @api.onchange('consent_detail_id', 'doctor_id')
    def onchange_doctor_id(self):
        self.stamp = self.signature = False
        if self.consent_detail_id and self.consent_detail_id.doc_stamp_need and self.doctor_id and self.doctor_id.stamp:
            self.stamp = self.doctor_id.stamp
        if self.consent_detail_id and self.consent_detail_id.doc_stamp_need and self.doctor_id and self.doctor_id.signature:
            self.signature = self.doctor_id.signature
    
    @api.onchange('consent_detail_id', 'patient_id')
    def onchange_patient_id(self):
        self.mrn = self.patient_id.patient_id or False
        self.patient_ref = self.patient_id.qid or False
    
    def update_consent_detail_id(self):
        # pass
        return {
            "type": "ir.actions.do_nothing",
        }
        
    @api.depends('language')   
    def set_test_consent_compute(self):
        for rec in self:
            # consent_fields = self.env['ir.model.fields'].search([('consent_field', '=', True),
            #                                                      ('related_xml_field_id', '=', False),
            #                                                     ('is_sign_field_id', '=', False)])
            # html_vals = {}
            # consent_rec = rec.consent_detail_id
            # if consent_rec:
            #     all_consent_fields = consent_rec.field_ids
            #     for selected_fields in all_consent_fields:
            #         if selected_fields.ttype == 'html':
            #             if self.language == 'english':
            #                 html_vals[str(selected_fields.name)] = selected_fields.html_default_content
            #             if self.language == 'arabic':
            #                 html_vals[str(selected_fields.name)] = selected_fields.html_arabic_default_content
            # rec.write(html_vals)
            # final_vals = {}
            # for m_fields in consent_fields:
            #     final_vals[str(m_fields.name)] = False
            # for m_fields in consent_fields:
            #     consent_rec = rec.consent_detail_id
            #     if consent_rec:
            #         all_consent_fields = consent_rec.field_ids
            #         for selected_fields in all_consent_fields:
            #             X = selected_fields.name + '_compute'
            #             if(X == m_fields.name):
            #                 final_vals[str(m_fields.name)] = True
            # rec.write(final_vals)
            # sign_consent_fields = []
            # for original_field in self.env['ir.model.fields'].search([('related_xml_field_id', '!=', False)]):
            #     if original_field.is_sign_field_id and original_field.related_xml_field_id:
            #         sign_consent_fields.append(original_field.related_xml_field_id)
            # sign_final_vals = {}
            # for sign_m_fields in sign_consent_fields:
            #     sign_final_vals[str(sign_m_fields.name)] = False
            # for sign_m_fields in sign_consent_fields:
            #         consent_rec = rec.consent_detail_id
            #         if consent_rec:
            #             all_sign_consent_fields = consent_rec.signature_field_ids
            #             for selected_sign_fields in all_sign_consent_fields:
            #                 X = selected_sign_fields.name + '_compute'
            #                 if(X == sign_m_fields.name):
            #                     sign_final_vals[str(sign_m_fields.name)] = True
            #
            # rec.write(sign_final_vals)
            rec.test_consent_compute = True

    test_consent_compute = fields.Boolean(compute=set_test_consent_compute, string='Test compute')

    @api.multi
    def print_consent_report(self):
        if not self.consent_detail_id:
            raise UserError('Select Consent')
        if not self.consent_detail_id.report_template_id:
            self.consent_detail_id.create_report_template()
            # raise UserError('Create Report template for selected Consent (From Consent Template View)')
        dom_qweb_view = [('name', 'ilike', self.consent_detail_id.report_template_id.name), ('type', '=', 'qweb')]
        qweb_template_view_id = self.env['ir.ui.view'].search(dom_qweb_view)
        if len(qweb_template_view_id) == 0:
            self.consent_detail_id.modify_report_template()
        self.patient_id.attach_consent(self)
        return self.consent_detail_id.report_template_id.report_action(self)