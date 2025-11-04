from odoo import api, fields, models



class IncomeByDoctorDpt(models.TransientModel):
    _inherit = 'income.by.doctor.report.wizard'


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

    department_ids = fields.Many2many(comodel_name="medical.department",  string="Department", )
    doctor_ids = fields.Many2many('medical.physician', string="Doctor", domain=_get_doctor_id)

    
    @api.onchange('department_ids')
    def onchange_department_ids(self):
        return {
            'domain': {
                'doctor_ids': self._get_doctor_id()
            }
        }
        