from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class TreatmentInvoice(models.Model):
    _name = "treatment.invoice"

    def _get_treatment_dom_id(self):
        company = self.env['res.company']._company_default_get('res.partner') or self.env.user.company_id.id
        if self.appointment_id.company_id:
            company = self.appointment_id.company_id
        if self.appointment_id.insurance_id:
            doc_ids = []
            for coverage_treatmts in self.appointment_id.insurance_id.company_id.treatment_ids:
                doc_ids.append(coverage_treatmts.id)
            for non_coverage_treatmts in self.appointment_id.insurance_id.company_id.non_coverage_treatment_ids:
                doc_ids.append(non_coverage_treatmts.id)
            for consultation_treatmts in self.appointment_id.insurance_id.company_id.consultation_treatment_ids:
                doc_ids.append(consultation_treatmts.id)
            domain = [('id', 'in', doc_ids), ('is_treatment', '=', True),
                      ('company_id', '=', company.id)]
        else:
            domain = [('is_treatment', '=', True), ('is_clinic_treatment', '=', True),
                      ('company_id', '=', company.id)]
        return domain

    @api.onchange('description')
    def onchange_treatment_ids(self):
        domain = self._get_treatment_dom_id()
        return {
            'domain': {'description': domain}
        }

    appointment_id = fields.Many2one("medical.appointment", "Appointment", required=True)
    # changes by mubaris
    qty = fields.Integer('Quantity', default=1)
    teeth_code_rel = fields.Many2many(comodel_name='teeth.code', string='teeth')
    diagnosis_id = fields.Many2one('diagnosis', 'Diagnosis')
    treatment_id = fields.Many2one("medical.teeth.treatment", "Treatment")
    description = fields.Many2one('product.product', 'Treatment', required=True, domain=_get_treatment_dom_id)
    note = fields.Char("Description")
    amount_edit = fields.Boolean('Amount Edit?', related='description.amount_edit')
    amount = fields.Float("After Discount")
    actual_amount = fields.Float('Actual Amt', compute='_get_actual_amount')
    unit_price = fields.Float('Actual Amt')
    patient_id = fields.Many2one("medical.patient", "Patient", related='appointment_id.patient')
    date = fields.Datetime('Date', compute='_compute_date')
    is_doctor_user = fields.Boolean(string="Is Doctor", compute='get_user')
    discount_fixed_percent = fields.Selection([('Fixed', 'Fixed'), ('Percent', 'Percent')],
                                              string='Disc Fixed/Percent', default=False, track_visibility='always')
    discount = fields.Float(string='Disc (%)', digits=dp.get_precision('Discount'), default=0.0,
                            track_visibility='always')
    discount_value = fields.Float(string='Disc Amt', track_visibility='always')
    insurance_approved_amount = fields.Float('Approved Amount',default=0.00)

    @api.onchange('discount', 'discount_value', 'unit_price')
    def _onchange_discount_value(self):
        qty = 1
        if self.description.apply_quantity_on_payment_lines:
            qty = len(self.teeth_code_rel)
        if qty == 0:
            qty = 1
        if self.discount_fixed_percent == 'Fixed':
            if self.discount_value > (self.actual_amount * qty):
                raise UserError(_('Please Enter Discount properly.'))
        if self.discount_fixed_percent == 'Percent':
            if self.discount > 100:
                raise UserError(_('Discount Percentage should not be greater than 100'))
        if self.description:
            qty = 1
            if self.description.apply_quantity_on_payment_lines:
                qty = len(self.teeth_code_rel)
            if qty == 0:
                qty = 1
            unit_price = self._fetch_unit_price()
            lst_price = unit_price * qty
            if self.discount_fixed_percent == 'Fixed':
                if self.discount_value > lst_price:
                    raise UserError(_('Please Enter Discount properly.'))
                else:
                    discount_value = 0
                    if self.discount_value:
                        discount_value = self.discount_value
                    self.amount = lst_price - discount_value
            elif self.discount_fixed_percent == 'Percent':
                if self.discount > 100:
                    raise UserError(_('Discount Percentage should not be greater than 100'))
                else:
                    discount_value = 0
                    if self.discount:
                        discount_value = (self.discount * lst_price) / 100
                    self.amount = lst_price - discount_value
            else:
                self.amount = lst_price
        else:
            self.amount = 0
            self.unit_price = 0
            self.actual_amount = 0
            self.discount_fixed_percent = False
            self.discount = 0
            self.discount_value = 0

    @api.onchange('discount_fixed_percent')
    def _onchange_discount_fixed_percent(self):
        if not self.discount_fixed_percent:
            self.discount = ""
            self.discount_value = ""
        if self.discount_fixed_percent == 'Fixed':
            self.discount = ""
        if self.discount_fixed_percent == 'Percent':
            self.discount_value = ""

    def get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('pragtech_dental_management.group_dental_doc_menu'):
            for rec in self:
                rec.is_doctor_user = True
        else:
            for rec in self:
                rec.is_doctor_user = False

    @api.depends('appointment_id', 'appointment_id.appointment_sdate')
    def _compute_date(self):
        for record in self:
            if record.appointment_id:
                record.date = record.appointment_id.appointment_sdate

    @api.depends('description')
    def _get_actual_amount(self):
        for appt in self.filtered(lambda t: t.description):
            unit_price = appt._fetch_unit_price()
            if appt.discount_fixed_percent:
                appt.update({
                    'actual_amount': unit_price,
                })
            else:
                val_treat_inv = {
                    'unit_price': unit_price,
                    'actual_amount': unit_price,
                    'discount_fixed_percent': False,
                    'discount': False,
                    'discount_value': False
                }
                # if not appt.amount:
                qty = 1
                if appt.description.apply_quantity_on_payment_lines:
                    qty = len(appt.teeth_code_rel)
                if qty == 0:
                    qty = 1
                val_treat_inv['amount'] = unit_price * qty
                appt.update(val_treat_inv)

    @api.onchange('treatment_id')
    def onchange_treatment_id(self):
        if self.treatment_id:
            self.description = self.treatment_id.description

    @api.onchange('description')
    def onchange_description(self):
        if self.description:
            self.amount = self.description.lst_price
            self.unit_price = self.description.lst_price

    @api.model
    def create(self, values):
        doc = self.env['res.users'].has_group(
            'pragtech_dental_management.group_dental_doc_menu')
        keep_zero_price = self._context.get('keep_zero_price', False)
        if (not keep_zero_price and values.get('description') and not
                values.get('amount') and not doc):
            product_price = self.env['product.product'].browse(values.get('description')).lst_price
            full_discount = 0
            if values.get('discount_fixed_percent') == 'Fixed' and values.get('discount_value') == product_price:
                full_discount = 1
            if values.get('discount_fixed_percent') == 'Percent' and values.get('discount') == 100:
                full_discount = 1
            if not full_discount:
                values['amount'] = product_price
        line = super(TreatmentInvoice, self).create(values)
        msg = "<b> Created New Payment Lines:</b><ul>"
        if values.get('description'):
            msg += "<li>" + _("Treatment") + ": %s<br/>" % (line.description.name)
        if values.get('note'):
            msg += "<li>" + _("Description") + ": %s  <br/>" % (line.note)
        if values.get('actual_amount'):
            msg += "<li>" + _("Actual Amt") + ": %s  <br/>" % (line.actual_amount)
        if values.get('amount'):
            msg += "<li>" + _("After Discount Amt") + ": %s  <br/>" % (line.amount)
        msg += "</ul>"
        line.appointment_id.message_post(body=msg)
        return line

    @api.multi
    def write(self, values):
        doc = self.env['res.users'].has_group('pragtech_dental_management.group_dental_doc_menu')
        if values.get('description') and not values.get('amount') and not doc:
            product_price = self.env['product.product'].browse(values.get('description')).lst_price
            full_discount = 0
            if values.get('discount_fixed_percent') == 'Fixed' and values.get('discount_value') == product_price:
                full_discount = 1
            if values.get('discount_fixed_percent') == 'Percent' and values.get('discount') == 100:
                full_discount = 1
            if not full_discount:
                values['amount'] = product_price
        appoints = self.mapped('appointment_id')
        for apps in appoints:
            order_lines = self.filtered(lambda x: x.appointment_id == apps)
            msg = "<b> Updated Payment Lines :</b><ul>"
            for line in order_lines:
                if values.get('description'):
                    msg += "<li>" + _("Treatment") + ": %s -> %s <br/>" % (
                        line.description.name, self.env['product.product'].browse(values['description']).name,)
                if values.get('note'):
                    msg += "<li>" + _("Description") + ": %s -> %s <br/>" % (line.note, values['note'],)
                if values.get('actual_amount'):
                    msg += "<li>" + _("Actual Amt") + ": %s -> %s <br/>" % (
                        line.actual_amount, values['actual_amount'],)
                if values.get('amount'):
                    msg += "<li>" + _("After Discount Amt") + ": %s -> %s <br/>" % (line.amount, values['amount'],)
            msg += "</ul>"
            apps.message_post(body=msg)
        result = super(TreatmentInvoice, self).write(values)
        return result

    @api.multi
    def unlink(self):
        for rec in self:
            msg = "<b> Deleted Payment Lines with Values:</b><ul>"
            if rec.description:
                msg += "<li>" + _("Treatment") + ": %s <br/>" % (rec.description.name,)
            if rec.note:
                msg += "<li>" + _("Description") + ": %s  <br/>" % (rec.note,)
            if rec.actual_amount:
                msg += "<li>" + _("Actual Amt") + ": %s  <br/>" % (rec.actual_amount,)
            if rec.amount:
                msg += "<li>" + _("After Discount Amt") + ": %s  <br/>" % (rec.amount,)
            msg += "</ul>"
            rec.appointment_id.message_post(body=msg)
        return super(TreatmentInvoice, self).unlink()

    def _fetch_unit_price(self):
        unit_price = self.unit_price
        return unit_price and unit_price or (self.description and
                                             self.description.lst_price or 0)
