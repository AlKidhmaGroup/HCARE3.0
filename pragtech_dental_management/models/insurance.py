# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MedicalInsurance(models.Model):
    _name = "medical.insurance"

    @api.multi
    @api.depends('code', 'description')
    def name_get(self):
        result = []
        for med_ins in self:
            name = med_ins.company_id.name or ''
            if med_ins.number:
                name += ':' + med_ins.number
            result.append((med_ins.id, name))
        return result

    def _default_company(self):
        return self.env['res.company']._company_default_get('res.partner') or self.env.user.company_id.id

    res_company_id = fields.Many2one('res.company', 'Company', index=True, default=_default_company)
    company_id = fields.Many2one('res.partner', 'Insurance Company', required=True,
                                 domain="[('company_id','=',res_company_id), ('is_insurance_company', '=', '1')]")
    name = fields.Many2one('res.partner', string='Member', required=True, domain=[('is_patient', '=', True)])
    patient_id = fields.Many2one('medical.patient', 'Patient', required=True)
    number = fields.Char('Policy Number', size=64)
    group_name = fields.Char('Group Name')
    insurance_id_no = fields.Char('Member ID')
    member_since = fields.Date('Valid from')
    member_exp = fields.Date('Valid To')
    category = fields.Char('Category', size=64, help="Insurance company plan / category")
    type = fields.Selection([('state', 'State'), ('labour_union', 'Labour Union / Syndical'), ('private', 'Private'), ],
                            'Insurance Type')
    notes = fields.Text('Extra Info')
    co_payment_method = fields.Selection([('Amount', 'Amount'), ('Percentage', 'Percentage')],
                                         'Co-payment Method', default='Percentage', required=True)
    amt_paid_by_patient = fields.Float('Co-payment(%)', default=0)
    amt_fixed_paid_by_patient = fields.Float('Co-payment')
    is_deductible = fields.Boolean('Is Deductible?', related='company_id.is_deductible')
    is_policy_mandatory = fields.Boolean('Set Policy Number Mandatory?', related='company_id.is_policy_mandatory')
    is_member_mandatory = fields.Boolean('Set Member ID Mandatory?', related='company_id.is_member_mandatory')
    deductible = fields.Float('Deductible', default=0)
    policy_holder_mandatory = fields.Boolean('Policy holder Mandatory?', related='company_id.policy_holder_mandatory')
    policy_holder_id = fields.Many2one('policy.holder', string='Policy holder')

    @api.onchange('amt_paid_by_patient')
    @api.depends('amt_paid_by_patient')
    def onchange_amt_paid_by_patient(self):
        if self.amt_paid_by_patient > 100:
            raise UserError('Co-payment(%) should not be greater than 100')
        self.amt_paid_by_insurance = 100 - self.amt_paid_by_patient

    @api.model
    def create(self, vals):
        if vals.get('amt_paid_by_patient') > 100:
            raise UserError('Co-payment(%) should not be greater than 100')
        return super(MedicalInsurance, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(MedicalInsurance, self).write(vals)
        if self.amt_paid_by_patient > 100:
            raise UserError('Co-payment(%) should not be greater than 100')
        return res

    @api.onchange('name')
    def onchange_name(self):
        self.patient_id = False
        if self.name:
            patient_exist = self.env['medical.patient'].search([('name', '=', self.name.id)])
            if patient_exist:
                self.patient_id = patient_exist[0]
