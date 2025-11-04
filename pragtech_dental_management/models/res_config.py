# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_drug_list_doctors = fields.Boolean('Restrict Drug list to created by doctors')
    restrict_checkin = fields.Boolean('Restrict Checkin if there are Open Appointments')
    restrict_completion = fields.Boolean('Restrict Appointment Completion without Consent')
    restrict_completion_complaint = fields.Boolean('Restrict Appointment Completion without Chief Complaint')
    restrict_completion_treatment_plan = fields.Boolean('Restrict Appointment Completion without Treatment Plan')
    show_only_dr_alert = fields.Boolean('Show only Medical history specified by the doctors', help="Show Alert for field: Medical/Surgical History")
    restrict_auto_missed = fields.Boolean('Restrict Appointment Auto Missed Option')
    group_dashboard_complaint_form = fields.Boolean("Show Complaint Form in Medical Dashboard",
        implied_group='pragtech_dental_management.group_complaint_form', default=True)
    # Added below fields to avoid xml issue while upgrading
    default_discount_account = fields.Many2one('account.account', string='Invoice Discount Account')
    default_insurance_diff_account = fields.Many2one('account.account', string='Insurance difference Account')
    feedback_delete_allow = fields.Boolean('Feedback Delete Allow')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        restrict_drug_list_doctors = literal_eval(ICPSudo.get_param('restrict_drug_list_doctors', default='False'))
        restrict_checkin = literal_eval(ICPSudo.get_param('restrict_checkin', default='False'))
        restrict_completion = literal_eval(ICPSudo.get_param('restrict_completion', default='False'))
        restrict_completion_complaint = literal_eval(ICPSudo.get_param('restrict_completion_complaint', default='False'))
        restrict_completion_treatment_plan = literal_eval(ICPSudo.get_param('restrict_completion_treatment_plan', default='False'))
        show_only_dr_alert = literal_eval(ICPSudo.get_param('show_only_dr_alert', default='False'))
        restrict_auto_missed = literal_eval(ICPSudo.get_param('restrict_auto_missed', default='False'))
        feedback_delete_allow = literal_eval(ICPSudo.get_param('feedback_delete_allow', default='False'))
        res.update({
                    'restrict_drug_list_doctors': restrict_drug_list_doctors,
                    'restrict_checkin': restrict_checkin,
                    'restrict_completion': restrict_completion,
                    'restrict_completion_complaint': restrict_completion_complaint,
                    'restrict_completion_treatment_plan': restrict_completion_treatment_plan,
                    'restrict_auto_missed': restrict_auto_missed,
                    'show_only_dr_alert': show_only_dr_alert,
                    'feedback_delete_allow':feedback_delete_allow,
                    })
        return res

    @api.multi
    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).set_values()
        ICPSudo.set_param("restrict_drug_list_doctors", self.restrict_drug_list_doctors)
        ICPSudo.set_param("restrict_checkin", self.restrict_checkin)
        ICPSudo.set_param("restrict_completion", self.restrict_completion)
        ICPSudo.set_param("restrict_completion_complaint", self.restrict_completion_complaint)
        ICPSudo.set_param("restrict_completion_treatment_plan", self.restrict_completion_treatment_plan)
        ICPSudo.set_param("restrict_auto_missed", self.restrict_auto_missed)
        ICPSudo.set_param("show_only_dr_alert", self.show_only_dr_alert)
        ICPSudo.set_param("feedback_delete_allow", self.feedback_delete_allow)

class ResCompany(models.Model):
    _inherit = "res.company"

    @api.constrains('default_insurance_diff_account', 'name')
    def _check_same_company_insurance_diff_account(self):
        if self.default_insurance_diff_account.company_id:
            if self.id != self.default_insurance_diff_account.company_id.id:
                raise ValidationError(_('Error ! Insurance difference Account should be of same company'))

    def _getIncomeId(self):
        return [('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id),
                ('deprecated', '=', False)]

    default_insurance_diff_account = fields.Many2one('account.account', string='Insurance difference Account',
                                       domain=_getIncomeId,
                                       help="The Insurance difference account used for this invoice.")

    @api.constrains('default_discount_account', 'name')
    def _check_same_company_discount_account(self):
        if self.default_discount_account.company_id:
            if self.id != self.default_discount_account.company_id.id:
                raise ValidationError(_('Error ! Discount Account should be of same company'))

    def _getExpenseId(self):
        return [('user_type_id', '=', self.env.ref('account.data_account_type_expenses').id),
                ('deprecated', '=', False)]

    default_discount_account = fields.Many2one('account.account', string='Invoice Discount Account',
                                               domain=_getExpenseId,
                                               help="The discount account used for this invoice.")