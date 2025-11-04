# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class Fields(models.Model):
    _inherit = 'ir.model.fields'

    consent_field = fields.Boolean('Is machine related?')
    related_xml_field_id = fields.Many2one('ir.model.fields', string='Xml compute field')
    is_sign_field_id = fields.Boolean(string='Signature field')
    field_arabic_description = fields.Char('Field Label-Arabic')
    dynamic_sequence = fields.Integer(default=1)
    html_default_content = fields.Html('Html English Default Content')
    html_arabic_default_content = fields.Html('Html Arabic Default Content')
    active = fields.Boolean(default=True, copy=False)
    has_dependency = fields.Boolean(string="Has Dependent Field")
    dependent_value = fields.Char(string="Dependent Value")
    dependent_field = fields.Many2one('ir.model.fields',
                                      string="Dependent Field")
    select_related_field_ids = fields.One2many('selection.field.values','field_id',string='Related Selection Fields')
    boolean_related_field_ids = fields.One2many('boolean.field.values','field_id',string='Related Boolean Fields')
    visible_in_consent_tree = fields.Boolean(string='Visible in Consent Tree')
    defaults_fields_ids = fields.One2many('consent.defaults','field_id',string='Default(s)')
    
    @api.multi
    def name_get(self):
        res = []
        for field in self:
            res.append((field.id, '%s - %s (%s)' % (field.dynamic_sequence, field.field_description, field.model)))
        return res

    @api.multi
    def toggle_active(self):
        for rec in self:
            if self.active:
                if rec.consent_field:
                    rec.active = False
                    field_ids = self.env['consent.details'].search([('field_ids', 'in', rec.ids)])
                    signature_field_ids = self.env['consent.details'].search([('signature_field_ids', 'in', rec.id)])
                    remove_field = [(3, rec.id)]
                    for field in field_ids:
                        field.write({'field_ids': remove_field})
                    for signature in field_ids:
                        signature.write({'signature_field_ids': remove_field})

                    # ......Update report template......
                    for each_consent in self.env['consent.details'].search([]):
                        if each_consent.report_template_id:
                            each_consent.modify_report_template()
                    # ......Update view......
                    wiz_update_view = self.env['field.view.update'].browse(1)
                    wiz_update_view.design_dynamic_field_view()
            else:
                rec.active = True
                
class SelectionValues(models.Model):
    _name = 'selection.field.values'

    value = fields.Char()
    related_field_id = fields.Many2one('ir.model.fields') 
    field_id = fields.Many2one('ir.model.fields')
    
class BooleanValues(models.Model):
    _name = 'boolean.field.values'

    value = fields.Char()
    related_bool_field_id = fields.Many2one('ir.model.fields') 
    related_text_field_id = fields.Many2one('ir.model.fields') 
    field_id = fields.Many2one('ir.model.fields')  
    visible_in = fields.Boolean(string='Visible In')     
                
