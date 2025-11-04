from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class ClinicalFindings(models.Model):
    _name = "complaint.finding"

    def update_complaint_finding_char_to_manytomany_to_char(self):
        complaint_m2many_without_val = self.search([('complaint', '!=', False),('complaint_new_ids', '=', False)])
        for complaint_id in complaint_m2many_without_val:
            complaint_exists = self.env['complaints'].search([('code', '=', complaint_id.complaint)])
            if not complaint_exists:
                complaint_exists = self.env['complaints'].create({'code': complaint_id.complaint})
            complaint_id.write({'complaint_new_ids': [(4, complaint_exists.id)]})
        complaint_text_without_val = self.search([('complaint_new_ids', '!=', False),('complaint', '=', False)])
        for complaint_id in complaint_text_without_val:
            all_complaint = ''
            for each_complaint in complaint_id.complaint_new_ids:
                if all_complaint:
                    all_complaint += ', '
                all_complaint += str(each_complaint.code)
            complaint_id.write({'complaint': all_complaint})
        finding_m2many_without_val = self.search([('finding', '!=', False),('finding_new_ids', '=', False)])
        for finding_id in finding_m2many_without_val:
            finding_exists = self.env['findings'].search([('code', '=', finding_id.finding)])
            if not finding_exists:
                finding_exists = self.env['findings'].create({'code': finding_id.finding})
            finding_id.write({'finding_new_ids': [(4, finding_exists.id)]})
        finding_text_without_val = self.search([('finding_new_ids', '!=', False),('finding', '=', False)])
        for finding_id in finding_text_without_val:
            all_finding = ''
            for each_finding in finding_id.finding_new_ids:
                if all_finding:
                    all_finding += ', '
                all_finding += str(each_finding.code)
            finding_id.write({'finding': all_finding})

    def update_diagnosis_char_to_manytomany_to_char(self):
        diagnosis_m2many_without_val = self.search([('diagnosis', '!=', False), ('diagnosis_new_ids', '=', False)])
        for diagnosis_id in diagnosis_m2many_without_val:
            diagnosis_exists = self.env['primary.diagnosis'].search([('code', '=', diagnosis_id.diagnosis)])
            if not diagnosis_exists:
                diagnosis_exists = self.env['primary.diagnosis'].create({'code': diagnosis_id.diagnosis})
            diagnosis_id.write({'diagnosis_new_ids': [(4, diagnosis_exists.id)]})
        diagnosis_text_without_val = self.search([('diagnosis_new_ids', '!=', False),('diagnosis', '=', False)])
        for diagnosis_id in diagnosis_text_without_val:
            all_diagnosis = ''
            for each_diagnosis in diagnosis_id.diagnosis_new_ids:
                if all_diagnosis:
                    all_diagnosis += ', '
                all_diagnosis += str(each_diagnosis.code)
            diagnosis_id.write({'diagnosis': all_diagnosis})

    def update_procedure_char_to_manytomany_to_char(self):
        procedure_m2many_without_val = self.search([('procedure', '!=', False), ('procedure_new_ids', '=', False)])
        for procedure_id in procedure_m2many_without_val:
            procedure_exists = self.env['procedure'].search([('code', '=', procedure_id.procedure)])
            if not procedure_exists:
                procedure_exists = self.env['procedure'].create({'code': procedure_id.procedure})
            procedure_id.write({'procedure_new_ids': [(4, procedure_exists.id)]})
        procedure_text_without_val = self.search([('procedure_new_ids', '!=', False),('procedure', '=', False)])
        for procedure_id in procedure_text_without_val:
            all_procedure = ''
            for each_procedure in procedure_id.procedure_new_ids:
                if all_procedure:
                    all_procedure += ', '
                all_procedure += str(each_procedure.code)
            procedure_id.write({'procedure': all_procedure})

    patient_id = fields.Many2one('medical.patient', 'Patient Details', required=True)
    appt_id = fields.Many2one('medical.appointment', 'Appointment ID', required=True)
    finding = fields.Text('Clinical/ X-ray Finding')
    complaint = fields.Text('Chief complaint/ History', required=True)
    diagnosis = fields.Text('Primary Diagnosis')
    diagnosis_id = fields.Many2one('diagnosis','Primary Diagnosis')
    diagnosis_ids = fields.Many2many('diagnosis', string='Additional Diagnosis')
    procedure = fields.Text('Procedure')
    date = fields.Datetime('Date', compute='_compute_date')

    complaint_new_ids = fields.Many2many('complaints', string='Chief complaint/ History')
    finding_new_ids = fields.Many2many('findings', string='Clinical/ X-ray Finding')
    procedure_new_ids = fields.Many2many('procedure', string="Procedure")
    diagnosis_new_ids = fields.Many2many('primary.diagnosis', string="Primary Diagnosis")

    @api.depends('appt_id', 'appt_id.appointment_sdate')
    def _compute_date(self):
        for record in self:
            if record.appt_id:
                record.date = record.appt_id.appointment_sdate

    @api.model
    def create(self, values):
        if 'complaint' in list(values.keys()):
            complaint = values['complaint']
            complaint = complaint.replace(' ', '')
            if complaint == "":
                raise UserError('Please enter chief complaint properly!!')
        line = super(ClinicalFindings, self).create(values)
        msg = "<b> Created New Complaints and Findings:</b><ul>"
        if values.get('complaint'):
            msg += "<li>" + _("Complaint") + ": %s<br/>" % (line.complaint)
        if values.get('finding'):
            msg += "<li>" + _("Findings") + ": %s  <br/>" % (line.finding)
        msg += "</ul>"
        line.appt_id.message_post(body=msg)
        return line

    @api.multi
    def write(self, values):
        if 'complaint' in list(values.keys()):
            complaint = values['complaint']
            complaint = complaint.replace(' ', '')
            if complaint == "":
                raise UserError('Please enter chief complaint properly!!')

        appoints = self.mapped('appt_id')
        for apps in appoints:
            order_lines = self.filtered(lambda x: x.appt_id == apps)
            msg = "<b> Updated Complaints and Findings :</b><ul>"
            for line in order_lines:
                if values.get('complaint'):
                    msg += "<li>" + _("Complaint") + ": %s -> %s <br/>" % (line.complaint, values['complaint'],)
                if values.get('finding'):
                    msg += "<li>" + _("Findings") + ": %s -> %s <br/>" % (line.finding, values['finding'],)
            msg += "</ul>"
            apps.message_post(body=msg)
        result = super(ClinicalFindings, self).write(values)
        return result

    @api.multi
    def unlink(self):
        for rec in self:
            msg = "<b> Deleted Complaints and Findings with Values:</b><ul>"
            if rec.complaint:
                msg += "<li>" + _("Complaint") + ": %s <br/>" % (rec.complaint,)
            if rec.finding:
                msg += "<li>" + _("Findings") + ": %s  <br/>" % (rec.finding,)
            msg += "</ul>"
            rec.appt_id.message_post(body=msg)
        return super(ClinicalFindings, self).unlink()