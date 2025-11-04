from odoo import models,fields,api


class IncomeByInsuranceCompanyWizard(models.TransientModel):
    _name = 'income.by.insurance.company.wizard'
    _description = 'Income By Insurance company Wizard'

    def _get_treatment_ids(self):
        return [('is_treatment', '=', True)]

    def _get_doctor_id(self):
        domain = []
        if self.department_ids:
            domain += [('department_id', 'in', self.department_ids.ids)]
        doc_ids = None
        group_dental_doc_menu = self.env.user.has_group(
            'pragtech_dental_management.group_dental_doc_menu')
        group_dental_user_menu = self.env.user.has_group(
            'pragtech_dental_management.group_dental_user_menu')
        group_dental_mng_menu = self.env.user.has_group(
            'pragtech_dental_management.group_dental_mng_menu')
        if (group_dental_doc_menu and not group_dental_user_menu and not
                group_dental_mng_menu):
            partner_ids = self.env['res.partner'].search([
                ('user_id', '=', self.env.user.id), ('is_doctor', '=', True),
                ('company_id', '=', self.company_id.id)]).ids
            if partner_ids:
                doc_ids = self.env['medical.physician'].search([
                    ('name', 'in', partner_ids),
                    ('company_id', '=', self.company_id.id)]).ids
            domain += [('id', 'in', doc_ids)]
        return domain

    date_start = fields.Date(
        'From Date',required = True, default=fields.Date.context_today)
    date_end = fields.Date(
        'To Date',required = True, default=fields.Date.context_today)
    insurance_company = fields.Many2one('res.partner', 'Insurance Company')
    doctor_ids = fields.Many2many(
        'medical.physician', string="Doctor", domain=_get_doctor_id)
    service_ids = fields.Many2many(
        'product.product', string="Service", domain=_get_treatment_ids)
    department_ids = fields.Many2many('medical.department', string='Department')

    name = fields.Char()
    data = fields.Binary()
    state = fields.Selection([('set', 'Set'), ('get', 'Get')], default='set')

    @api.onchange('department_ids')
    def onchange_department_ids(self):
        return {
            'domain': {
                'doctor_ids': self._get_doctor_id()
            }
        }
    
    @api.multi
    def print_report(self):
        datas = {
            'active_ids': self.env.context.get('active_ids', []),
            'form': self.read()[0]
        }
        values=self.env.ref(
            'basic_insurance.income_by_insurance_company_qweb').report_action(
            self, data=datas)
        return values
