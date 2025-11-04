from odoo import models, fields, api


class UserCreation(models.TransientModel):
    _inherit = 'user.creation'

    speciality = fields.Many2one('medical.speciality', 'Specialty')
    department = fields.Char(string='Department')
    code = fields.Char('ID', size=128)
    department_id = fields.Many2one('medical.department', 'Department')

    @api.multi
    def get_doctor_group(self, user):
        doctor_group = self.env['ir.model.data'].get_object('pragtech_dental_management', 'group_dental_doc_menu')
        doctor_group.write({'users': [(4, user.id)]})
        cost_center = self.env['account.cost.center'].create({
            'name': self.name,
            'code': self.name,
            'company_id': self.company_id.id
        })
        # dep = self.env['medical.department'].create({
        #     'name': self.department,
        #     'cost_center_id': cost_center.id,
        #     'company_id': self.company_id.id
        # })
        physician = self.env['medical.physician'].create({
            'name': user.partner_id.id,
            'code': self.code,
            'department_id': self.department_id and self.department_id.id or False,
            'speciality': self.speciality.id,
            'company_id': self.company_id.id,
        })
        user.write({'physician_ids': [(4, physician.id)]})
