# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import hashlib
import time
from odoo.exceptions import Warning
from ast import literal_eval
import base64

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class MedicalPatient(models.Model):
    _name = "medical.patient"
    _inherit = 'mail.thread'
    _description = "Patient related information"

    @api.multi
    def show_advance(self):
        pass

    @api.multi
    def get_patient_seq_val(self, patient_seq):
        seq_val = patient_seq.next_by_code('medical.patient')
        return seq_val

    @api.multi
    def get_patient_sequence(self):
        company_obj = self.env.user.company_id
        patient_seq =  self.env['ir.sequence'].search([('code', '=', 'medical.patient'),
                                                  ('company_id', '=', company_obj.id)])
        if not patient_seq:
            raise UserError(_("You have to define a sequence for %s in your company: %s.")
                            % ('medical.patient', company_obj.name))
        return patient_seq

    @api.multi
    def patient_sequence_generation(self):
        company_obj = self.env.user.company_id
        patient_seq = self.get_patient_sequence()
        seq_val = self.get_patient_seq_val(patient_seq)
        len_prefix = len(patient_seq[0].prefix)
        seq_without_prefix = seq_val[len_prefix:]
        if company_obj.patient_prefix:
            vals_patient_id = company_obj.patient_prefix + seq_without_prefix
        else:
            vals_patient_id = seq_without_prefix
        return vals_patient_id

    @api.multi
    def medical_patient_teeth_attachment(
        self, appointment_id, tooth_base64URL, isChart
    ):
        self.env['ir.attachment'].create({
            'name': isChart and 'Tooth Chart' or 'Initial Treatments',
            'type': 'binary',
            'datas': tooth_base64URL.replace(
                'data:image/octet-stream;base64,', ''),
            'datas_fname': (
                isChart and 'Tooth Chart.jpg' or 'Initial Treatments.jpg'),
            'res_model': 'medical.patient',
            'res_id': self.id,
            'patient_id': self.id,
            'appointment_id': appointment_id
        })

    @api.multi
    def unlink(self):
        for patient in self:
            if not patient.env.user.has_group('pragtech_dental_management.group_access_delete_patient'):
                raise ValidationError(_("Please contact your system administrator, because you don't have access to delete this record"))
            complaints = self.env['complaint.finding'].search([('patient_id','=',patient.id)])
            attachments = self.env['ir.attachment'].search([('patient_id','=',patient.id)])
            prescription = self.env['prescription.line'].search([('patient_id','=',patient.id)])
            attachments.sudo().unlink()
            complaints.unlink()
            prescription.unlink()
        return super(MedicalPatient, self).unlink()

    @api.multi
    def is_warning_needed(self, treatment):
        selected_treatment = treatment['treatment_id']
        patient = self.id
        appt_obj = self.env['medical.appointment']
        latest_app = appt_obj.search([('patient', '=', patient), ('state', 'in', ['checkin', 'ready'])], order='id asc')
        latest_appt = False
        if latest_app:
            latest_appt = latest_app[-1]
        if latest_appt:
            if latest_appt.insurance_id:
                ins_treatments = [line.id for line in latest_appt.insurance_id.company_id.treatment_ids]
                if not selected_treatment in ins_treatments:
                    return True
        return False

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        recs = self.browse()
        if name:
            name += '%'
            self._cr.execute("SELECT mp.id FROM medical_patient mp JOIN res_partner rp  ON(mp.name=rp.id) "
                         "WHERE (rp.name ilike %s) OR (mp.patient_id ilike %s) OR (rp.mobile ilike %s) "
                         "OR (mp.other_mobile ilike %s) OR (rp.lastname ilike %s) OR (rp.middle_name ilike %s)",
                         (name, name, name, name, name, name))
        if not name:
            self._cr.execute("SELECT mp.id FROM medical_patient mp ")
        ids = [r[0] for r in self._cr.fetchall()]
        patients = self.search([('id', 'in', ids)], limit=limit)
        if patients:
            return patients.name_get()
        if not recs:
            return []

    @api.multi
    @api.onchange('dob')
    def onchange_dob(self):
        c_date = datetime.today().strftime('%Y-%m-%d')
        if self.dob:
            if not (self.dob <= c_date):
                raise UserError(_('Birthdate cannot be After Current Date.'))
        return {}

    @api.multi
    def _patient_age(self):
        def compute_age_from_dates(patient_dob, patient_deceased, patient_dod):
            now = datetime.now()
            if (patient_dob):
                dob = datetime.strptime(patient_dob, '%Y-%m-%d')
                if patient_deceased:
                    dod = datetime.strptime(patient_dod, '%Y-%m-%d %H:%M:%S')
                    delta = relativedelta(dod, dob)
                    deceased = " (deceased)"
                else:
                    delta = relativedelta(now, dob)
                    deceased = ''
                years_months_days = str(delta.years) + "y "

                 # + str(delta.months) + "m " + str(
                 #    delta.days) + "d" + deceased
            else:
                years_months_days = "No DoB !"

            return years_months_days

        for rec in self:
            rec.age = compute_age_from_dates(rec.dob, rec.deceased, rec.dod)

    @api.multi
    def _medical_alert(self):
        for patient_data in self:
            medical_alert = ""
            # if patient_data.q1 == 'YES':
            #     q1 = "Health is Good"
            #     medical_alert = medical_alert + q1 + ','
            if patient_data.q1 == 'NO':
                q1 = "Health is not good"
                medical_alert = medical_alert + q1 + ','
            if patient_data.q2:
                q2 = "Anemia"
                medical_alert = medical_alert + q2 + ','
            if patient_data.q3:
                q3 = "Arthritis, Rheumatism"
                medical_alert = medical_alert + q3 + ','
            if patient_data.q4:
                q4 = "Artificial Joints, Pins"
                medical_alert = medical_alert + q4 + ','
            if patient_data.q5:
                q5 = "Asthma"
                medical_alert = medical_alert + q5 + ','
            if patient_data.q6:
                q6 = "Back pain"
                medical_alert = medical_alert + q6 + ','
            if patient_data.q7:
                q7 = "Cortisone Treatment"
                medical_alert = medical_alert + q7 + ','
            if patient_data.q8:
                q8 = "Cough, Persistent"
                medical_alert = medical_alert + q8 + ','
            if patient_data.q9:
                q9 = "Diabetes"
                medical_alert = medical_alert + q9 + ','
            if patient_data.q10:
                q10 = "Epilepsy"
                medical_alert = medical_alert + q10 + ','
            if patient_data.q11:
                q11 = "Fainting"
                medical_alert = medical_alert + q11 + ','
            if patient_data.q12:
                q12 = "Glaucoma"
                medical_alert = medical_alert + q12 + ','
            if patient_data.q13:
                q13 = "Headaches or Migraine"
                medical_alert = medical_alert + q13 + ','
            if patient_data.q14:
                q14 = "Hemophilia"
                medical_alert = medical_alert + q14 + ','
            if patient_data.q15:
                q15 = "Heart Disease"
                medical_alert = medical_alert + q15 + ','
            if patient_data.q16:
                q16 = "Heart Valve problems"
                medical_alert = medical_alert + q16 + ','
            if patient_data.q17:
                q17 = "Heart Surgery"
                medical_alert = medical_alert + q17 + ','
            if patient_data.q18:
                q18 = "Hepatitis"
                medical_alert = medical_alert + q18 + ','
            if patient_data.q19:
                q19 = "High Blood Pressure"
                medical_alert = medical_alert + q19 + ','
            if patient_data.q20:
                q20 = "HIV"
                medical_alert = medical_alert + q20 + ','
            if patient_data.q21:
                q21 = "Jaw Pain"
                medical_alert = medical_alert + q21 + ','
            if patient_data.q22:
                q22 = "Kidney Disease"
                medical_alert = medical_alert + q22 + ','
            if patient_data.q23:
                q23 = "Pacemaker"
                medical_alert = medical_alert + q23 + ','
            if patient_data.q24:
                q24 = "Prolonged bleeding"
                medical_alert = medical_alert + q24 + ','
            if patient_data.q25:
                q25 = "Respiratory Disease"
                medical_alert = medical_alert + q25 + ','
            if patient_data.q26:
                q26 = "Kidney Problem"
                medical_alert = medical_alert + q26 + ','
            if patient_data.q27:
                q27 = "Liver Problem"
                medical_alert = medical_alert + q27 + ','
            if patient_data.q28:
                q28 = "Thyroid Problem"
                medical_alert = medical_alert + q28 + ','
            if patient_data.q29 == 'YES':
                q29 = "Have Serious illness"
                medical_alert = medical_alert + q29 + '-'
            # elif patient_data.q29 == 'NO':
            #     q29 = "No Serious illness"
            #     medical_alert = medical_alert + q29 + ','
            if patient_data.q30:
                medical_alert = medical_alert + patient_data.q30 + ','
            if patient_data.q31 == 'YES':
                q31 = "Have Other Medical Problems"
                medical_alert = medical_alert + q31 + '-'
            if patient_data.q32:
                q32 = patient_data.q32
                medical_alert = medical_alert + q32 + ','
            if patient_data.q33:
                q33 = "Allergy to Latex"
                medical_alert = medical_alert + q33 + ','
            if patient_data.q34:
                q34 = "Allergy to Local Anesthetic"
                medical_alert = medical_alert + q34 + ','
            if patient_data.q35:
                q35 = "Allergy to Penicillin"
                medical_alert = medical_alert + q35 + ','
            if patient_data.q36:
                q36 = "Allergy to Sulfa"
                medical_alert = medical_alert + q36 + ','
            if patient_data.q37:
                q37 = "Allergy to Aspirin"
                medical_alert = medical_alert + q37 + ','
            if patient_data.q38:
                q38 = "Allergy to Brufen"
                medical_alert = medical_alert + q38 + ','
            if patient_data.q39:
                q39 = "Allergy to Iodine"
                medical_alert = medical_alert + q39 + ','
            # if patient_data.q40:
            #     q40 = "Allergy to NONE"
            #     medical_alert = medical_alert + q40 + ','
            if patient_data.q41:
                q41 = "Other allergies : " + patient_data.q41
                medical_alert = medical_alert + q41 + ','
            if patient_data.q42 == 'YES':
                q42 = "Smoke"
                medical_alert = medical_alert + q42 + ','
            # elif patient_data.q42 == 'NO':
            #     q42 = "Don't Smoke"
            #     medical_alert = medical_alert + q42 + ','
            if patient_data.q43:
                q43 = str(patient_data.q43) + "Cigarettes /day"
                medical_alert = medical_alert + q43 + ','
            if patient_data.q44 == 'YES':
                q44 = "Pregnant"
                medical_alert = medical_alert + q44 + ','
            # elif patient_data.q44 == 'NO':
            #     q44 = " Not Pregnant"
            #     medical_alert = medical_alert + q44 + ','
            if patient_data.q45:
                q45 = patient_data.q45 + "month pregnant"
                medical_alert = medical_alert + q45 + ','
            if patient_data.q46 == 'YES':
                q46 = "Feeling Discomfort"
                medical_alert = medical_alert + q46 + ','
            if patient_data.q47 == 'YES':
                q47 = "Had Serious trouble"
                medical_alert = medical_alert + q47 + ','
            if patient_data.q48 == 'YES':
                q48 = "Take anticoagulants"
                medical_alert = medical_alert + q48 + ','
            if patient_data.q49:
                q49 = "Date of last visit" + patient_data.q49
                medical_alert = medical_alert + q49 + ','
            if patient_data.q50:
                q50 = 'Brushing:' + patient_data.q50
                medical_alert = medical_alert + q50 + ','
            if patient_data.q51:
                q51 = 'Flossing:' + patient_data.q51
                medical_alert = medical_alert + q51 + ','
            if patient_data.q52:
                q52 = 'Mouthwash:' + patient_data.q52
                medical_alert = medical_alert + q52 + ','
            if patient_data.q53 == 'YES':
                q53 = "Treated for gum disease"
                medical_alert = medical_alert + q53 + ','
            # elif patient_data.q53 == 'NO':
            #     q53 = "Treated for gum disease"
            #     medical_alert = medical_alert + q53 + ','
            if patient_data.q54 == 'YES':
                q54 = "Had Medical radiographs"
                medical_alert = medical_alert + q54 + ','
            if patient_data.q55:
                q55 = "On and at:" + patient_data.q55
                medical_alert = medical_alert + q55 + ','
            if patient_data.q56:
                q56 = "Reason for seeking medical care" + patient_data.q56
                medical_alert = medical_alert + q56 + ','
            if patient_data.q57:
                q57 = "Bleeding or sore gums"
                medical_alert = medical_alert + q57 + ','
            if patient_data.q58:
                q58 = "Biting Cheeks/lips"
                medical_alert = medical_alert + q58 + ','
            if patient_data.q59:
                q59 = "Broken filling"
                medical_alert = medical_alert + q59 + ','
            if patient_data.q60:
                q60 = "Clenching/grinding"
                medical_alert = medical_alert + q60 + ','
            if patient_data.q61:
                q61 = "Clicking/Locked Jaw"
                medical_alert = medical_alert + q61 + ','
            if patient_data.q62:
                q62 = "Difficult to open/close"
                medical_alert = medical_alert + q62 + ','
            if patient_data.q63:
                q63 = "Frequent blisters (lips/mouth)"
                medical_alert = medical_alert + q63 + ','
            if patient_data.q64:
                q64 = "Food impaction"
                medical_alert = medical_alert + q64 + ','
            if patient_data.q65:
                q65 = "Food collection in between teeth"
                medical_alert = medical_alert + q65 + ','
            if patient_data.q66:
                q66 = "Root Canal Treatment"
                medical_alert = medical_alert + q66 + ','
            if patient_data.q67:
                q67 = "Loose teeth"
                medical_alert = medical_alert + q67 + ','
            if patient_data.q68:
                q68 = "Swelling or Lumps in mouth"
                medical_alert = medical_alert + q68 + ','
            if patient_data.q69:
                q69 = "Ortho Treatment (braces)"
                medical_alert = medical_alert + q69 + ','
            if patient_data.q70:
                q70 = "Sensitive to hot"
                medical_alert = medical_alert + q70 + ','
            if patient_data.q71:
                q71 = "Sensitive to cold"
                medical_alert = medical_alert + q71 + ','
            if patient_data.q72:
                q72 = "Sensitive to sweet"
                medical_alert = medical_alert + q72 + ','
            if patient_data.q73:
                q73 = "Sensitive to bite"
                medical_alert = medical_alert + q73 + ','
            if patient_data.q74:
                q74 = "Shifting in bite"
                medical_alert = medical_alert + q74 + ','
            if patient_data.q75:
                q75 = "Unpleasant taste/bad breath"
                medical_alert = medical_alert + q75 + ','
            # if patient_data.q76 == 'YES':
            #     q76 = "Pleased with the general appearance of teeth and smile"
            #     medical_alert = medical_alert + q76 + ','
            if patient_data.q77:
                q77 = "Not Pleased with the general appearance of teeth and smile: " + patient_data.q77
                medical_alert = medical_alert + q77
            patient_data.critical_info = medical_alert
            # medical_history = ''
            # for appt in self.apt_id:
            #     if appt.medicl_history:
            #         medical_history = appt.medicl_history + '\n' + medical_history
            # patient_data.medical_history = medical_history

    def _show_only_dr_alert(self):
        for patient in self:
            config_obj = self.env['ir.config_parameter'].sudo()
            show_only_dr_alert = literal_eval(config_obj.get_param('show_only_dr_alert', default='False'))
            patient.update({'show_only_dr_alert': show_only_dr_alert})

    show_only_dr_alert = fields.Boolean(string='Show only Alerts specified by the doctors', compute='_show_only_dr_alert', readonly=True)
    name_tag = fields.Selection([('Mr.', 'Mr.'),
                                 ('Mrs.', 'Mrs.'),
                                 ('Miss', 'Miss'),
                                 ('Ms.', 'Ms.'),
                                 ('Dr.', 'Dr.'),
                                 ('Sh.', 'Sh.'),
                                 ('Sha.', 'Sha.'),
                                 ('Other', 'Other')], 'Name Tag')
    address = fields.Text("Address")
    emergency_name = fields.Char('Name')
    emergency_relation = fields.Char('Relation')
    emergency_phone = fields.Char('Phone')
    patient_name = fields.Char(_("Patient Name"))
    register_signature = fields.Binary(string='Signature')
    name = fields.Many2one('res.partner', 'Patient Partner', required=False, readonly=True,
                           domain=[('is_patient', '=', True)], help="Patient Name")
    qid = fields.Char("QID")
    weight = fields.Float(readonly=False)
    sex = fields.Selection([('m', 'Male'), ('f', 'Female'),('i', 'Intermediate') ], 'Gender')
    invoice_count = fields.Integer(string='# of Invoices', compute='_get_invoiced', readonly=True)
    invoice_ids = fields.Many2many("account.invoice", string='Invoices', compute="_get_invoiced", readonly=True,
                                   copy=False)
    payment_count = fields.Integer(string='# of Payments', compute='_get_payments', readonly=True)
    payment_ids = fields.Many2many("account.payment", string='Payments', compute="_get_payments", readonly=True,
                                   copy=False)
    operation_summary_ids = fields.One2many('operation.summary', 'patient_id', 'Operation Summary', readonly=True)
    finding_ids = fields.One2many("complaint.finding", 'patient_id', "Complaints and findings", readonly=True)
    prescriptions = fields.One2many("prescription.line", 'patient_id', "Prescriptions", readonly=True)
    feedbacks = fields.One2many("patient.feedback", 'patient_id', "Feedbacks")
    language = fields.Selection([('english', 'English'),
                                 ('arabic', 'Arabic')], 'Language')
    register_date = fields.Date('Registration Date')
    amount_due = fields.Char('Outstanding Amount', compute='_get_invoiced')
    amount_advance = fields.Char('Advance Amount', compute='_get_invoiced')

    patient_id = fields.Char('Patient ID', size=64,
                             help="Patient Identifier provided by the Health Center."
                                  " Is not the patient id from the partner form",
                             default=lambda self: _('New'))
    ssn = fields.Char('SSN', size=128, help="Patient Unique Identification Number")
    lastname = fields.Char(related='name.lastname', string='Lastname')
    middle_name = fields.Char(related='name.middle_name', string='Middle Name')
    insurance_ids = fields.One2many('medical.insurance', 'patient_id', "Insurances")
    dob = fields.Date('Date of Birth')
    age = fields.Char(compute='_patient_age', string='Patient Age',
                      help="It shows the age of the patient in years(y), months(m) and days(d).\n"
                           "If the patient has died, the age shown is the age at time of death, "
                           "the age corresponding to the date on the death certificate. "
                           "It will show also \"deceased\" on the field")
    marital_status = fields.Selection(
        [('s', 'Single'), ('m', 'Married'), ('w', 'Widowed'), ('d', 'Divorced'), ('x', 'Separated'), ],
        'Marital Status')
    blood_type = fields.Selection([('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O'), ], 'Blood Type')
    rh = fields.Selection([('+', '+'), ('-', '-'), ], 'Rh')
    user_id = fields.Many2one('res.users', related='name.user_id', string='Doctor',
                              help="Physician that logs in the local Medical system (HIS), on the health center. "
                                   "It doesn't necesarily has do be the same as the Primary Care doctor",
                              store=True)
    critical_info = fields.Text(compute='_medical_alert', string='Medical Alert',
                                help="Write any important information on the patient's disease,"
                                     " surgeries, allergies, ...")
    medical_history = fields.Text(string='Medical History')
    critical_info_fun = fields.Text(compute='_medical_alert', string='Medical Alert',
                                    help="Write any important information on the patient's disease,"
                                         " surgeries, allergies, ...")
    medical_history_fun = fields.Text('Medical History')
    general_info = fields.Text('General Information', help="General information about the patient")
    deceased = fields.Boolean('Deceased', help="Mark if the patient has died")
    dod = fields.Datetime('Date of Death')
    apt_id = fields.Many2many('medical.appointment', 'pat_apt_rel', 'patient', 'apid', 'Appointments', readonly=True)
    attachment_ids = fields.One2many('ir.attachment', 'patient_id', 'attachments')
    attach_count = fields.Integer(string='# of Attachments', compute='_get_attached', readonly=True)
    photo = fields.Binary(related='name.image', string='Picture', store=True)
    report_date = fields.Date("Report Date:", default=fields.Datetime.now)
    occupation_id = fields.Many2one('medical.occupation', 'Occupation')
    primary_doctor_id = fields.Many2one('medical.physician', 'Primary Doctor', )
    referring_doctor_id = fields.Many2one('medical.physician', 'Referring  Doctor', )
    note = fields.Text('Notes', help="Notes and To-Do")
    survey_id = fields.Many2one('patient.survey', 'How did you hear about us?')
    other_survey = fields.Char('Other, Please specify')
    mobile = fields.Char('Mobile', related='name.mobile')
    other_mobile = fields.Char('Other Mobile')
    teeth_treatment_ids = fields.One2many('medical.teeth.treatment', 'patient_id', 'Operations', readonly=True)
    nationality_id = fields.Many2one('patient.nationality', 'Nationality')
    patient_complaint_ids = fields.One2many('patient.complaint', 'patient_id')
    q1 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Is your health good?')
    q2 = fields.Boolean('Anemia')
    q3 = fields.Boolean('Arthritis, Rheumatism')
    q4 = fields.Boolean('Artificial Joints, Pins')
    q5 = fields.Boolean('Asthma')
    q6 = fields.Boolean('Back pain')
    q7 = fields.Boolean('Cortisone Treatment')
    q8 = fields.Boolean('Cough, Persistent')
    q9 = fields.Boolean('Diabetes')
    q10 = fields.Boolean('Epilepsy')
    q11 = fields.Boolean('Fainting')
    q12 = fields.Boolean('Glaucoma')
    q13 = fields.Boolean('Headaches or Migraine')
    q14 = fields.Boolean('Hemophilia')
    q15 = fields.Boolean('Heart Disease')
    q16 = fields.Boolean('Heart Valve problems')
    q17 = fields.Boolean('Heart Surgery')
    q18 = fields.Boolean('Hepatitis')
    q19 = fields.Boolean('High Blood Pressure')
    q20 = fields.Boolean('HIV')
    q21 = fields.Boolean('Jaw Pain')
    q22 = fields.Boolean('Kidney Disease')
    q23 = fields.Boolean('Pacemaker')
    q24 = fields.Boolean('Prolonged bleeding')
    q25 = fields.Boolean('Respiratory Disease')
    q26 = fields.Boolean('Kidney Problem')
    q27 = fields.Boolean('Liver Problem')
    q28 = fields.Boolean('Thyroid Problem')
    q29 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Serious illness or operations?')
    q30 = fields.Char('When')
    q31 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Other Medical Problems?')
    q32 = fields.Char('Please Specify')
    q33 = fields.Boolean('Latex')
    q34 = fields.Boolean('Local Anesthetic')
    q35 = fields.Boolean('Penicillin')
    q36 = fields.Boolean('Sulfa')
    q37 = fields.Boolean('Aspirin')
    q38 = fields.Boolean('Brufen')
    q39 = fields.Boolean('Iodine')
    q40 = fields.Boolean('NONE')
    q41 = fields.Char('Any other allergies')
    q42 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Do you smoke?')
    q43 = fields.Integer(' # of cigarette/day')
    q44 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Are you pregnant?')
    q45 = fields.Char('Month')
    q46 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Are you having discomfort at this time?')
    q47 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Have you ever had any serious trouble?')
    q48 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Are you taking any anticoagulants (blood thinner) ? ')
    q49 = fields.Date('Date of Last Medical Visit?')
    q50 = fields.Char('Brushing')
    q51 = fields.Char('Flossing')
    q52 = fields.Char('Mouthwash')
    q53 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Have you been treated for gum disease?')
    q54 = fields.Selection([('YES', 'YES'), ('NO', 'NO')], 'Have you had any Medical radiographs?')
    q55 = fields.Char('When and where')
    q56 = fields.Char('What is the main reason for seeking Medical care?')
    q57 = fields.Boolean('Bleeding or sore gums')
    q58 = fields.Boolean('Biting Cheeks/lips')
    q59 = fields.Boolean('Broken filling')
    q60 = fields.Boolean('Clenching/grinding')
    q61 = fields.Boolean('Clicking/Locked Jaw')
    q62 = fields.Boolean('Difficult to open/close')
    q63 = fields.Boolean('Frequent blisters (lips/mouth)')
    q64 = fields.Boolean('Food impaction')
    q65 = fields.Boolean('Food collection in between teeth')
    q66 = fields.Boolean('Root Canal Treatment')
    q67 = fields.Boolean('Loose teeth')
    q68 = fields.Boolean('Swelling or Lumps in mouth')
    q69 = fields.Boolean('Ortho Treatment (braces)')
    q70 = fields.Boolean('Sensitive to hot')
    q71 = fields.Boolean('Sensitive to cold')
    q72 = fields.Boolean('Sensitive to sweet')
    q73 = fields.Boolean('Sensitive to bite')
    q74 = fields.Boolean('Shifting in bite')
    q75 = fields.Boolean('Unpleasant taste/bad breath')
    q76 = fields.Selection([('YES', 'YES'), ('NO', 'NO')],
                           'Are you pleased with the general appearance of your teeth and smile?')
    q77 = fields.Char('if no why')
    updated_date = fields.Date('Updated Date')
    arebic = fields.Boolean('Arabic')
    registration_fee_amount = fields.Float('Registration fee')
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid')], 'State', default='draft')
    registration_inv_id = fields.Many2one('account.invoice', 'Registration Invoice')
    treatment_ids = fields.One2many("treatment.invoice", 'patient_id', "Treatment History", readonly=True
                                    , track_visibility='onchange')
    passport_no = fields.Char("Passport Number")
    is_vip = fields.Boolean(string="Is VIP", copy=False, default=False)

    file_index = fields.Integer(compute='compute_file_index', store=True)
    email = fields.Char(string='Email',track_visibility='onchange')

    @api.depends('patient_id')
    def compute_file_index(self):
        for rec in self:
            rec.file_index = rec._get_file_index()

    def _default_company(self):
        return self.env['res.company']._company_default_get('res.partner') or self.env.user.company_id.id

    company_id = fields.Many2one('res.company', 'Company', index=True, default=_default_company)

    @api.constrains('company_id', 'name')
    def _check_same_company_patient(self):
        if self.company_id:
            if self.name.company_id:
                if self.company_id.id != self.name.company_id.id:
                    raise ValidationError(_('Error ! Patient and Patient Partner should be of same company'))

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The Patient already exists'),
        ('patient_id_uniq', 'unique (patient_id)', 'The Patient ID already exists'), ]

    @api.depends('attachment_ids')
    def _get_attached(self):
        for patient in self:
            if patient.attachment_ids:
                attach_count = self.env['ir.attachment'].search_count([('patient_id', '=', patient.id)])
                patient.update({
                    'attach_count': attach_count,
                })
            else:
                patient.update({
                    'attach_count': 0,
                })

    @api.onchange('patient_name')
    def onchange_patient_name(self):
        for rec in self:
            if rec.patient_name and rec.name:
                rec.name.name = rec.patient_name
                rec.name.write({'name': rec.patient_name})

    @api.onchange('mobile')
    def onchange_mobilee(self):
        for rec in self:
            if rec.mobile:
                for appt in rec.apt_id:
                    self._cr.execute('UPDATE medical_appointment SET patient_phone=%s WHERE id=%s',
                                     (rec.mobile, appt.id))

    @api.depends('name')
    def _get_payments(self):
        for patient in self:
            payment_ids = self.env['account.payment'].search([('partner_id', '=', patient.name.id),
                                                              ('partner_type', '=', 'customer')])
            patient.update({
                'payment_count': len(set(payment_ids.ids)),
                'payment_ids': payment_ids.ids
            })

    @api.multi
    @api.depends('patient_name', 'patient_id')
    def name_get(self):
        result = []
        for partner in self:
            name = ""
            if partner.patient_name:
                name = partner.patient_name
            if partner.patient_id:
                name = '[' + partner.patient_id + '] ' + name
            if partner.mobile:
                name = name + " " + partner.mobile
            result.append((partner.id, name))
        return result

    @api.multi
    def add_prescription(self):
        return {
            'name': _('Prescription'),
            'type': 'ir.actions.act_window',
            'res_model': 'prescription.additional',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'nodestroy': False,
            'context': {
                'default_patient_id': self.id,
            }
        }

    @api.multi
    def show_prescriptions(self):
        prescription = self.env['prescription.additional'].search([('patient_id', '=', self.id)])
        action = self.env.ref('pragtech_dental_management.action_prescription_additional').read()[0]
        if len(prescription) >= 1:
            action['domain'] = [('id', 'in', prescription.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.multi
    def attach_registration(self):
        data = {'ids': self.ids}
        data, data_format = self.env.ref('pragtech_dental_management.report_registration').render([1], data=data)
        att_id = self.env['ir.attachment'].create({
            'name': 'Registration_' + self.updated_date,
            'type': 'binary',
            'datas': base64.encodestring(data),
            'datas_fname': self.name.name + '_registration.pdf',
            'res_model': 'medical.patient',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

    @api.multi
    def action_view_payment(self):
        payments = self.mapped('payment_ids')
        action = self.env.ref('account.action_account_payments').read()[0]
        if len(payments) > 1:
            action['domain'] = [('id', 'in', payments.ids)]
        elif len(payments) == 1:
            action['views'] = [(self.env.ref('account.view_account_payment_form').id, 'form')]
            action['res_id'] = payments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def show_attachments(self):
        attachments = self.mapped('attachment_ids')
        action = self.env.ref('pragtech_dental_management.action_attachments').read()[0]
        if len(attachments) > 0:
            action['domain'] = [('id', 'in', attachments.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.depends('name')
    def _get_invoiced(self):
        for patient in self:
            invoice_ids = self.env['account.invoice'].search([('partner_id', '=', patient.name.id),
                                                              ('type', '=', 'out_invoice')])
            amount_due = 0
            for inv in invoice_ids:
                amount_due += inv.residual_signed
            domain = [('account_id', '=', patient.name.property_account_receivable_id.id),
                      ('partner_id', '=', patient.name.id),
                      ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
                      ('amount_residual_currency', '!=', 0.0),
                      ('credit', '>', 0), ('debit', '=', 0)]
            lines = self.env['account.move.line'].search(domain)
            advance = 0
            if len(lines) != 0:
                for line in lines:
                    amount_to_show = line.company_id.currency_id.with_context(date=line.date).compute(
                        abs(line.amount_residual), self.env.user.company_id.currency_id)
                    advance += amount_to_show
            patient.update({
                'invoice_count': len(set(invoice_ids.ids)),
                'invoice_ids': invoice_ids.ids,
                'amount_due': "{:.2f}".format(amount_due),
                'amount_advance': "{:.2f}".format(advance)
            })

    @api.multi
    def show_inv_due(self):
        for patient in self:
            action = self.env.ref('account.action_invoice_tree1').read()[0]
            action['context'] = {'hide_for_service_bill': True, 'show_for_service_bill': True}
            invoice_ids = self.env['account.invoice'].search([('partner_id', '=', patient.name.id),
                                                              ('type', '=', 'out_invoice'),
                                                              ('residual_signed', '>', 0),
                                                              ])
            if len(invoice_ids) > 1:
                action['domain'] = [('id', 'in', invoice_ids.ids)]
            elif len(invoice_ids) == 1:
                action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
                action['res_id'] = invoice_ids.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['context'] = {'hide_for_service_bill': True, 'show_for_service_bill': True}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def get_img(self):
        for rec in self:
            res = {}
            img_lst_ids = []
            imd = self.env['ir.model.data']
            action_view_id = imd.xmlid_to_res_id('action_result_image_view')
            for i in rec.attachment_ids:
                img_lst_ids.append(i.id)
            res['image'] = img_lst_ids

            return {
                'type': 'ir.actions.client',
                'name': 'Patient image',
                'tag': 'result_images',
                'params': {
                    'patient_id': rec.id or False,
                    'model': 'medical.patient',
                    'values': res
                },
            }

    @api.multi
    def create_registration_fee_invoice(self):
        inv_obj = self.env['account.invoice']
        ICPSudo = self.env['ir.config_parameter'].sudo()
        registration_invoice_product_id = literal_eval(
            ICPSudo.get_param('registration_invoice_product_id', default='False'))
        product_obj = self.env['product.product'].browse(registration_invoice_product_id)
        if not registration_invoice_product_id:
            raise Warning('You need to specify Product to be used for Registration Invoice.')
        account_id = None
        if product_obj.property_account_income_id:
            account_id = product_obj.property_account_income_id.id
        else:
            account_id = product_obj.categ_id.property_account_income_categ_id.id

        jr_brw = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('name', '=', 'Customer Invoices'), ('company_id', '=', self.company_id.id)])
        invoice = inv_obj.create({
            'name': 'REGISTRATION INVOICE',
            'origin': 'Registration' + ' ' + self.patient_id,
            'type': 'out_invoice',
            'account_id': self.name.property_account_receivable_id.id,
            'company_id': self.company_id.id,
            'journal_id': jr_brw.id,
            'reference': False,
            'partner_id': self.name.id,
            'is_patient': True,
            'registration_invoice': True,
            'invoice_line_ids': [(0, 0, {
                'name': 'Registration',
                'origin': 'Registration' + ' ' + self.patient_id,
                'account_id': account_id,
                'price_unit': product_obj.lst_price,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': product_obj.uom_id.id,
                'product_id': registration_invoice_product_id,
            })],
            'currency_id': self.name.company_id.currency_id.id,
            'comment': 'Registration Invoice of Patient ' + ' ' + self.name.name,
        })
        for line in self.env['account.invoice.line'].search([('invoice_id', '=', invoice.id)]):
            line._onchange_product_id()
        self.state = 'paid'
        self.registration_inv_id = invoice.id
        invoice.compute_taxes()
        return invoice

    @api.multi
    def view_registartion_invoice(self):
        view_id = self.env.ref('account.invoice_form').id,
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.registration_inv_id.id,
            'views': [(view_id, 'form')],
        }

    @api.model
    def get_patient_history(self, patient_id,
                            appt_id):
        return_list = []
        treatment_by_surface = {}
        return_list.append([])
        if patient_id:
            treatment_obj = self.env['medical.teeth.treatment']
            total_operation = \
                treatment_obj.search([('patient_id', '=', patient_id)])
            extra_history = len(total_operation)
        elif appt_id:
            appt_id_brw = self.env['medical.appointment'].browse(appt_id)
            total_operation = appt_id_brw.operations
            extra_history = len(total_operation)
            for each_patient_operation in self.teeth_treatment_ids:
                if each_patient_operation.description.action_perform == "missing" and \
                                each_patient_operation.appt_id.id < appt_id:
                    total_operation += each_patient_operation
        else:
            total_operation = self.teeth_treatment_ids
            extra_history = len(total_operation)
        history_count = 0
        for each_operation in total_operation:
            desc_list = each_operation.detail_description.split(",")
            for desc in desc_list:
                if desc not in treatment_by_surface:
                    treatment_by_surface[desc] = []
                treatment_by_surface[desc].append({
                    'create_date': each_operation.create_date,
                    'name': each_operation.description.name,
                    'state': each_operation.state.replace("_", " ").title()
                })
            history_count += 1
            current_tooth_id = ""
            for each_teeth_code in each_operation.teeth_code_rel:
                if current_tooth_id:
                    current_tooth_id += ", "
                teeth_obj = self.env['chart.selection'].search([])
                teeth_chart_selection = teeth_obj[-1]
                # if teeth_chart_selection.type == 'palmer':
                #     current_tooth_id += str(each_teeth_code.palmer_name)
                # elif teeth_chart_selection.type == 'iso':
                #     current_tooth_id += str(each_teeth_code.iso)
                # else:
                #     current_tooth_id += str(each_teeth_code.name)
                current_tooth_id += str(each_teeth_code.display_name)
            if each_operation.description:
                desc_brw = self.env['product.product'].browse(each_operation.description.id)
                if desc_brw.action_perform == 'missing':
                    return_list[0].append(current_tooth_id)
                self._cr.execute('select teeth from teeth_code_medical_teeth_treatment_rel '
                                 'where operation = %s' % (each_operation.id,))
                multiple_teeth = self._cr.fetchall()
                multiple_teeth_list = [multiple_teeth_each[0] for multiple_teeth_each in multiple_teeth]
                total_multiple_teeth_list = []
                for each_multiple_teeth_list in multiple_teeth_list:
                    each_multiple_teeth_list_brw = self.env['teeth.code'].browse(each_multiple_teeth_list)
                    total_multiple_teeth_list.append(each_multiple_teeth_list_brw.internal_id)
                    multiple_teeth_list = total_multiple_teeth_list
                other_history = 0
                if history_count > extra_history:
                    other_history = 1

                # uid = self.env['res.users'].search([('partner_id', '=', each_operation.dentist.name.id)], limit=1).id
                uid = self.env['res.users'].search([('partner_id', '=',
                                                     each_operation.dentist.name.id)], limit=1).id
                line_data = {
                    'id': each_operation.id,
                    'dignosis': {
                        'id': each_operation.diagnosis_id.id,
                        'code': each_operation.diagnosis_id.code
                    },
                    'dignosis_description': each_operation.diagnosis_description,
                    'other_history': other_history,
                    'created_date': each_operation.create_date,
                    'status': each_operation.state,
                    'multiple_teeth': multiple_teeth_list,
                    'tooth_id': current_tooth_id,
                    'surface': each_operation.detail_description,
                    'dentist': [uid,
                                each_operation.dentist.name.name,
                                ],
                    'desc': {
                        'name': each_operation.description.name,
                        'id': each_operation.description.id,
                        'action': each_operation.description.action_perform,
                        'highlight_color': each_operation.description.highlight_color
                    },
                    'amount': each_operation.amount,
                    'inv_status': each_operation.inv_status,
                    'initial': each_operation.initial,
                    'child': each_operation.child
                }
                line_data.update(self._update_discount_values(
                    each_operation, each_operation.unit_price))
                return_list.append(line_data)
        for surface in treatment_by_surface:
            treatment_by_surface[surface].sort(
                key=lambda x: datetime.strptime(x['create_date'], DTF),
                reverse=True)
        return [return_list, treatment_by_surface]

    def is_valid_user(self, uid):
        related_partner_of_curr_user = self.env['res.users'].browse(uid).partner_id.id
        physician = self.env['medical.physician'].search([('name', '=', related_partner_of_curr_user)], limit=1).id
        if physician:
            return True
        else:
            return False

    @api.model
    def unlink_treatment(self, line_id):
        """Unlink the given treatment line"""
        if line_id == 'false':
            return False
        try:
            treatment_obj = self.env['medical.teeth.treatment']
            return treatment_obj.search([('id', '=', line_id)]).unlink()
        except:
            pass
        return False

    @api.multi
    def create_lines(self, treatment_lines, patient_id, appt_id):
        config_obj = self.env['ir.config_parameter'].sudo()
        settings_qty_for_teeth = config_obj.get_param('pragtech_dental_management.module_mdc_quantity_paylines')
        medical_teeth_treatment_obj = self.env['medical.teeth.treatment']
        medical_physician_obj = self.env['medical.physician']
        teeth_code_obj = self.env['teeth.code']
        product_obj = self.env['product.product']
        patient = int(patient_id)
        appt_obj = self.env['medical.appointment']
        latest_app = appt_obj.search([
            ('patient', '=', patient),
            ('state', 'in', ['checkin', 'ready'])], order='id asc')
        latest_appt = False
        if latest_app:
            latest_appt = latest_app[-1]
        latest_appt_id = False
        if latest_appt:
            latest_appt_id = latest_appt.id

        for each in treatment_lines:
            if not each.get('line_id'):
                each['line_id'] = 'false'
            if each['line_id'] == 'false':
                if 'teeth_id' not in list(each.keys()):
                    each['teeth_id'] = 'all'
                all_treatment = each.get('values')
                if all_treatment:
                    for each_trt in all_treatment:
                        vals = {}
                        category_id = int(each_trt.get('categ_id'))
                        vals['description'] = category_id
                        vals['patient_id'] = patient
                        desc = ''
                        for each_val in each_trt['values']:
                            if each_val:
                                desc += each_val + ' '
                        vals['detail_description'] = desc.rstrip()
                        res_partner_id = self.env['res.users'].browse(
                            self.env.uid).partner_id
                        if res_partner_id:
                            physician = medical_physician_obj.search([
                                ('name', '=', res_partner_id.id)], limit=1)
                            if physician:
                                vals['dentist'] = physician.id
                        if each.get('status_name'):
                            status_name = each.get('status_name')
                            if status_name == 'in_progress':
                                status = 'in_progress'
                            elif (
                                status_name == 'Planned'
                            ) or (
                                status_name == 'false'
                            ):
                                status = 'planned'
                            elif (
                                        status_name == 'initial_examination'
                                     ) or (
                                         status_name == 'false'
                                     ):
                                status = 'initial_examination'

                            else:
                                status = (str(each.get('status_name')))
                        else:
                            status = 'planned'
                        vals['state'] = status

                        p_brw = product_obj.browse(vals['description'])

                        if each.get('dignosis_code') and \
                                not each.get('dignosis_code') == 'noclass':
                            vals['diagnosis_id'] = each.get('dignosis_code')
                        else:
                            vals['diagnosis_id'] = None

                        if each.get('dignosis_description'):
                            vals['diagnosis_description'] = each.get('dignosis_description')
                        full_mouth = []
                        operate_on_tooth = []
                        actual_teeth_ids_list = []
                        for each_value in each.get('values'):
                            each_value_value = each_value.get('values')
                            for each_v_v in each_value_value:
                                if ',' in each_v_v:
                                    var_each_v_v = each_v_v.split(',')
                                else:
                                    var_each_v_v = [each_v_v]
                                for split_v_v_mouth in var_each_v_v:
                                    if split_v_v_mouth in ['Full_mouth', 'Upper_Jaw', 'Lower_Jaw']:
                                        actual_teeth_ids = teeth_code_obj.search([('code', '=', split_v_v_mouth)],
                                                                                 limit=1)
                                        for actual_teeth in actual_teeth_ids:
                                            if actual_teeth not in actual_teeth_ids_list:
                                                actual_teeth_ids_list.append(actual_teeth)
                                    if '_' in split_v_v_mouth and split_v_v_mouth not in ['Full_mouth', 'Upper_Jaw',
                                                                                          'Lower_Jaw']:
                                        mouth_v_v_0 = split_v_v_mouth.split('_')[0]
                                        mouth_v_v_1 = split_v_v_mouth.split('_')[1]
                                        if mouth_v_v_0.isnumeric():
                                            if mouth_v_v_0 not in full_mouth:
                                                full_mouth.append(mouth_v_v_0)
                                        if mouth_v_v_1.isnumeric():
                                            if mouth_v_v_1 not in full_mouth:
                                                full_mouth.append(mouth_v_v_1)
                                        teeth_obj = self.env['chart.selection'].search([])
                                        teeth_chart_selection = teeth_obj[-1]
                                        if teeth_chart_selection.type == 'palmer':
                                            new_teeth_dom = [
                                                ('palmer_name', 'in', [int(teeth) for teeth in full_mouth])]
                                            # new_teeth_dom = [('palmer_internal_id', 'in', [int(teeth) for teeth in full_mouth])]
                                        elif teeth_chart_selection.type == 'iso':
                                            new_teeth_dom = [('iso', 'in', [int(teeth) for teeth in full_mouth])]
                                            if each['is_child']:
                                                correct_full_mouth = []
                                                for wrong_teeth_no in full_mouth:
                                                    child_correct_teeth_code = self.env['teeth.code'].get_child_correct_teeth_code()
                                                    correct_full_mouth.append(child_correct_teeth_code[wrong_teeth_no])
                                                new_teeth_dom = [('iso', 'in', [int(teeth) for teeth in correct_full_mouth])]
                                        else:
                                            new_teeth_dom = [('name', 'in', [int(teeth) for teeth in full_mouth])]
                                        actual_teeth_ids = teeth_code_obj.search(new_teeth_dom)
                                        for actual_teeth in actual_teeth_ids:
                                            if actual_teeth not in actual_teeth_ids_list:
                                                actual_teeth_ids_list.append(actual_teeth)
                        for actual_teeth in actual_teeth_ids_list:
                            operate_on_tooth.append(actual_teeth.id)
                        # update the amount value from chart to db
                        if not each.get('amount'):
                            vals['amount'] = p_brw.lst_price
                            vals['unit_price'] = p_brw.lst_price
                        else:
                            if settings_qty_for_teeth:
                                if p_brw.apply_quantity_on_payment_lines:
                                    qty_teeth = len(operate_on_tooth)
                                else:
                                    qty_teeth = 1
                                subtotal = float(each['amount'])
                                qty_lst_price = qty_teeth * p_brw.lst_price
                                if subtotal < qty_lst_price:
                                    vals.update(
                                        self._update_discount_values(
                                            each, qty_lst_price))
                                else:
                                    vals['unit_price'] = p_brw.lst_price
                                    vals['discount_fixed_percent'] = False
                                    vals['discount_value'] = 0.0
                                vals['amount'] = float(each['amount'])
                            else:
                                if float(each['amount']) < p_brw.lst_price:
                                    vals.update(
                                        self._update_discount_values(
                                            each, p_brw.lst_price))
                                else:
                                    vals['unit_price'] = float(each['amount'])
                                vals['amount'] = float(each['amount'])
                        if latest_appt_id:
                            vals['appt_id'] = latest_appt_id

                        # update the invoice status
                        if each.get('inv_status'):
                            vals['inv_status'] = each.get('inv_status')
                        if each.get('initial'):
                            vals['initial'] = each.get('initial')
                        vals['child'] = each['is_child']
                        vals['teeth_code_rel'] = [(6, 0, operate_on_tooth)]
                        treatment_id = medical_teeth_treatment_obj.create(vals)
            else:
                line_id = int(each['line_id'])
                treat_obj = medical_teeth_treatment_obj.search([('id', '=', line_id)])
                updated = False
                vals = {}
                vals['appt_id'] = latest_appt_id
                res_partner_id = self.env['res.users'].browse(self.env.uid).partner_id
                treat_obj_diagnosis_id = False
                if treat_obj.diagnosis_id:
                    treat_obj_diagnosis_id = treat_obj.diagnosis_id.id
                if each['dignosis_description'] == '':
                    each['dignosis_description'] = False
                if treat_obj.state != each['status_name']:
                    vals['state'] = each['status_name']
                    if res_partner_id:
                        physician = medical_physician_obj.search([('name', '=', res_partner_id.id)],
                                                                 limit=1)
                        if physician:
                            vals['dentist'] = physician.id
                    updated = True
                if int(treat_obj_diagnosis_id) != int(each['dignosis_code']):
                    vals['diagnosis_id'] = each['dignosis_code']
                    updated = True
                if treat_obj.diagnosis_description != each['dignosis_description']:
                    vals['diagnosis_description'] = each['dignosis_description']
                    updated = True
                if settings_qty_for_teeth:
                    subtotal = float(each['amount'])
                    p_brw = treat_obj.description
                    if p_brw.apply_quantity_on_payment_lines:
                        qty_teeth = len(treat_obj.teeth_code_rel)
                    else:
                        qty_teeth = 1
                    qty_lst_price = qty_teeth * p_brw.lst_price
                    if treat_obj.amount != float(each['amount']):
                        if subtotal < qty_lst_price:
                            vals.update(self._update_discount_values(
                                each, qty_lst_price))
                        else:
                            vals['discount_fixed_percent'] = False
                            vals['discount_value'] = 0.0
                            vals['unit_price'] = p_brw.lst_price
                        vals['amount'] = float(each['amount'])
                        updated = True
                else:
                    if treat_obj.amount != float(each['amount']):
                        p_brw = treat_obj.description
                        if float(each['amount']) < p_brw.lst_price:
                            vals.update(self._update_discount_values(
                                each, p_brw.lst_price))
                        else:
                            vals['unit_price'] = float(each['amount'])
                        vals['amount'] = float(each['amount'])
                        updated = True
                if updated:
                    initial = False
                    if each.get('initial'):
                        initial = True
                    if 'state' in list(vals.keys()) and vals['state'] in ['in_progress', 'completed'] and not initial:
                        inv_id = False
                        invoiced_treatments = self.env['treatment.invoice'].search([('treatment_id', '=', line_id)])
                        if invoiced_treatments or treat_obj.inv_status == "invoiced":
                            pass
                        else:
                            category_id = False
                            desc_note = ''
                            for value in each.get('values'):
                                category_id = int(value.get('categ_id'))
                                for each_val in value['values']:
                                    if each_val:
                                        desc_note += each_val + ' '
                            if patient and latest_appt:
                                if latest_appt.state in ['checkin', 'ready']:
                                    treat_inv_vals = {'appointment_id': latest_appt_id,
                                                      'treatment_id': line_id,
                                                      'description': category_id,
                                                      'note': desc_note,
                                                      }
                                    if line_id:
                                        treatment_tooths = self.env['medical.teeth.treatment'].browse(line_id).teeth_code_rel
                                        if treatment_tooths:
                                            all_teeth_code = []
                                            for treatment_teeth in treatment_tooths:
                                                all_teeth_code.append(treatment_teeth.id)
                                            treat_inv_vals['teeth_code_rel'] = [(6, 0, all_teeth_code)]
                                    prod_browse = product_obj.browse(category_id)
                                    if settings_qty_for_teeth:
                                        if prod_browse.apply_quantity_on_payment_lines:
                                            qty_teeth = len(treat_obj.teeth_code_rel)
                                        else:
                                            qty_teeth = 1
                                        subtotal = float(each['amount'])
                                        qty_lst_price = qty_teeth * prod_browse.lst_price
                                        if treat_obj.amount != float(each['amount']):
                                            if subtotal < qty_lst_price:
                                                treat_inv_vals.update(self._update_discount_values(
                                                    each, prod_browse.lst_price))
                                                # treat_inv_vals['actual_amount'] = prod_browse.lst_price
                                            else:
                                                treat_inv_vals['unit_price'] = float(each['amount'])
                                                treat_inv_vals['discount_fixed_percent'] = False
                                                treat_inv_vals['discount_value'] = 0.0
                                            treat_inv_vals['actual_amount'] = float(each['amount'])
                                        else:
                                            treat_inv_vals['unit_price'] = prod_browse.lst_price
                                            treat_inv_vals['actual_amount'] = float(each['amount'])
                                    else:
                                        if float(each['amount']) < prod_browse.lst_price:
                                            treat_inv_vals.update(
                                                self._update_discount_values(
                                                    each, prod_browse.lst_price))
                                            # treat_inv_vals['actual_amount'] = prod_browse.lst_price
                                        else:
                                            treat_inv_vals['unit_price'] = float(each['unit_price'])
                                            treat_inv_vals['actual_amount'] = float(each['amount'])
                                    treat_inv_vals['amount'] = float(each['amount'])
                                    inv_id = self.env['treatment.invoice'].create(treat_inv_vals)
                        if inv_id:
                            vals['inv_status'] = 'invoiced'
                    treat_obj.write(vals)
                else:
                    if each['line_status'] == 'old' and each['status_name'] == 'in_progress':
                        if res_partner_id:
                            physician = medical_physician_obj.search([('name', '=', res_partner_id.id)],
                                                                     limit=1)
                            if physician:
                                vals['dentist'] = physician.id
                        treat_obj.write(vals)

    def _update_discount_values(self, data, unit_price):
        """
        :param data: line data or line object
        :param unit_price: price before discount
        :return:
        """
        return {
            'discount_fixed_percent': data['discount_fixed_percent'],
            'discount': data['discount'],
            'discount_value': data['discount_value'],
            'unit_price': data['unit_price'],
        }

    @api.multi
    def get_back_address(self, active_patient):
        active_patient = str(active_patient)
        action_rec = self.env['ir.actions.act_window'].search([('res_model', '=', 'medical.patient')])
        action_id = str(action_rec.id)
        address = '/web#id=' + active_patient + '&view_type=form&model=medical.patient&action=' + action_id
        return address

    @api.multi
    def get_date(self, date1, lang):
        new_date = ''
        if date1:
            search_id = self.env['res.lang'].search([('code', '=', lang)])
            new_date = datetime.strftime(datetime.strptime(date1, '%Y-%m-%d %H:%M:%S').date(), search_id.date_format)
        return new_date

    @api.multi
    def write(self, vals):
        patient_vals = {}
        if 'patient_name' in list(vals.keys()):
            patient_vals['patient_name'] = vals['patient_name']
        if 'qid' in list(vals.keys()):
            patient_vals['qid'] = vals['qid']
        if 'mobile' in list(vals.keys()):
            patient_vals['patient_phone'] = vals['mobile']
        if 'sex' in list(vals.keys()):
            patient_vals['sex'] = vals['sex']
        if 'dob' in list(vals.keys()):
            patient_vals['dob'] = vals['dob']
        if 'nationality_id' in list(vals.keys()):
            patient_vals['nationality_id'] = vals['nationality_id']

        for appt in self.apt_id:
            if 'patient_name' in list(vals.keys()):
                self._cr.execute('UPDATE medical_appointment SET patient_name=%s WHERE id=%s', (patient_vals['patient_name'], appt.id))
            if 'mobile' in list(vals.keys()):
                self._cr.execute('UPDATE medical_appointment SET patient_phone=%s WHERE id=%s', (patient_vals['patient_phone'], appt.id))
            if 'qid' in list(vals.keys()):
                self._cr.execute('UPDATE medical_appointment SET qid=%s WHERE id=%s', (patient_vals['qid'], appt.id))
            if 'sex' in list(vals.keys()):
                if patient_vals['sex'] in ('m', 'f'):
                    self._cr.execute('UPDATE medical_appointment SET sex=%s WHERE id=%s', (patient_vals['sex'], appt.id))
                else:
                    self._cr.execute('UPDATE medical_appointment SET sex=%s WHERE id=%s', ('', appt.id))
            if 'dob' in list(vals.keys()):
                if patient_vals['dob'] == False:
                    self._cr.execute('UPDATE medical_appointment SET dob=%s WHERE id=%s', (None, appt.id))
                else:
                    self._cr.execute('UPDATE medical_appointment SET dob=%s WHERE id=%s', (patient_vals['dob'], appt.id))
            if 'nationality_id' in list(vals.keys()):
                if patient_vals['nationality_id'] == False:
                    self._cr.execute('UPDATE medical_appointment SET nationality_id=%s WHERE id=%s', (None, appt.id))
                else:
                    self._cr.execute('UPDATE medical_appointment SET nationality_id=%s WHERE id=%s', (patient_vals['nationality_id'], appt.id))
        if 'critical_info' in list(vals.keys()):
            vals['critical_info_fun'] = vals['critical_info']
        elif 'critical_info_fun' in list(vals.keys()):
            vals['critical_info'] = vals['critical_info_fun']
        if 'medical_history' in list(vals.keys()):
            vals['medical_history_fun'] = vals['medical_history']
        elif 'medical_history_fun' in list(vals.keys()):
            vals['medical_history'] = vals['medical_history_fun']
        return super(MedicalPatient, self).write(vals)

    @api.model
    def create(self, vals):
        if 'name' not in list(vals.keys()):
            if 'patient_name' in list(vals.keys()):
                values_partner = {'name': vals['patient_name'],
                                  'is_patient': True}
                company_id = False
                if 'company_id' in list(vals.keys()):
                    company_id = vals['company_id']
                    company_browse = self.env['res.company'].browse(company_id)
                    values_partner = company_browse.update_partner_receiv_payable(company_id, values_partner)
                if 'email' in vals:
                    values_partner.update({'email':vals.get('email',False)})
                partner_id = self.env['res.partner'].create(values_partner)
                vals['name'] = partner_id.id
        if vals.get('critical_info'):
            vals['critical_info_fun'] = vals['critical_info']
        elif vals.get('critical_info_fun'):
            vals['critical_info'] = vals['critical_info_fun']
        if vals.get('medical_history'):
            vals['medical_history_fun'] = vals['medical_history']
        elif vals.get('medical_history_fun'):
            vals['medical_history'] = vals['medical_history_fun']
        c_date = datetime.today().strftime('%Y-%m-%d')
        result = False
        if 'dob' in list(vals.keys()) and vals['dob']:
            if vals['dob'] > c_date:
                raise ValidationError(_('Birthdate cannot be After Current Date.'))
        if vals.get('patient_id', 'New') == 'New':
            vals['patient_id'] = self.patient_sequence_generation()
        result = super(MedicalPatient, self).create(vals)
        return result

    #     @api.multi
    #     def get_img(self):
    #         for rec in self:
    #             res = {}
    #             img_lst_ids = []
    #             imd = self.env['ir.model.data']
    #             action_view_id = imd.xmlid_to_res_id('action_result_image_view')
    #             for i in rec.attachment_ids:
    #                 img_lst_ids.append(i.id)
    #             res['image'] = img_lst_ids
    #
    #             return {
    #             'type': 'ir.actions.client',
    #             'name': 'Patient image',
    #             'tag': 'result_images',
    #             'params': {
    #                'patient_id':  rec.id  or False,
    #                'model':  'medical.patient',
    #                'values': res
    #             },
    #         }

    @api.multi
    def edit_patient_id(self):
        contextt = {}
        contextt['default_patient_id'] = self.id
        contextt['default_new_patient_id'] = self.env.user.company_id.patient_prefix
        return {
            'name': _('Enter New Patient ID'),
            'view_id': self.env.ref('pragtech_dental_management.view_edit_patient_wizard2').id,
            'type': 'ir.actions.act_window',
            'res_model': 'edit.patient',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': contextt
        }

    @api.multi
    def open_chart(self):
        for rec in self:
            config_obj = self.env['ir.config_parameter'].sudo()
            settings_qty_for_teeth = config_obj.get_param('pragtech_dental_management.module_mdc_quantity_paylines')
            appt_id = ''
            context = dict(self._context or {})
            #             if 'appointment_id_new' in context.keys():
            if 'appointment_id_new' in list(context.keys()):
                appt_id = context['appointment_id_new']
            if context is None:
                context = {}

            imd = self.env['ir.model.data']
            action_view_id = imd.xmlid_to_res_id('action_open_dental_chart')
            teeth_obj = self.env['chart.selection'].search([])
            teeth = teeth_obj[-1]
            if not appt_id:
                appt_id = self._context.get('appointment', '')
            return {
                'type': 'ir.actions.client',
                'name': 'Dental Chart',
                'tag': 'dental_chart',
                'params': {
                    'patient_id': rec.id or False,
                    'appt_id': appt_id,
                    'settings_qty_for_teeth': settings_qty_for_teeth,
                    'model': 'medical.patient',
                    'type': teeth.type,
                    'insurance': context.get('insurance', False),
                    'doctor': context.get('doctor', False),
		    'highlight_color': context.get('highlight_color', 'ff000c')
                },
            }

    digital_signature = fields.Binary(string='Signature')

    @api.multi
    def print_questionnaire_format(self):
        data = {'ids': self.ids}
        return self.env.ref('pragtech_dental_management.quest_format').report_action(self, data=data)


    @api.multi
    def print_questionnaire(self):
        data = {'ids': self.ids}
        data, data_format = self.env.ref('pragtech_dental_management.report_sign2_pdf').render([1], data=data)
        att_id = self.env['ir.attachment'].create({
            'name': 'Questionnaire_' + self.updated_date,
            'type': 'binary',
            'datas': base64.encodestring(data),
            'datas_fname': self.name.name + '_Questionnaire.pdf',
            'res_model': 'medical.patient',
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })

    @api.multi
    def action_approval_wizard(self):
        return {
            'name': _('Sign Form'),
            'type': 'ir.actions.act_window',
            'res_model': 'sign.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'nodestroy': False,
            'context': {
                'default_patient_id': self.id,
            }
        }

    def _get_file_index(self, file_number=None):
        """Convert the file number to an integer value, so that it can be
         used to sort the patient from the tree view"""
        if not file_number:
            file_number = self.patient_id
        if not file_number:
            return 0

        file_number = str(file_number)

        f_index = 0
        for f_v in file_number:
            if f_v.isdigit():
                f_index += f_index * 10 + int(f_v)
            # don't consider letters
            # else:
            #     f_index += ord(f_v)

        return f_index
