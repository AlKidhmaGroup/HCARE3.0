# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ChartSelection(models.Model):
    _description = "teeth chart selection"
    _name = "chart.selection"

    type = fields.Selection(
        # [('universal', 'Universal Numbering System'), ('palmer', 'Palmer Method'), ('iso', 'ISO FDI Numbering System')],
        [('universal', 'Universal Numbering System'), ('iso', 'ISO FDI Numbering System')],
        'Select Chart Type', default='universal')

    def convert_to_next_chart_type(self, surface_part, old_type, new_type):
        if surface_part:
            search_name = 'name'
            if old_type == 'universal':
               search_name = 'name'
            if old_type == 'palmer':
                search_name = 'palmer_name'
            if old_type == 'iso':
                search_name = 'iso'
            if ',' in surface_part:
                var_surface_part = surface_part.split(',')
            else:
                var_surface_part = [surface_part]
            for split_v_v_mouth in var_surface_part:
                if '_' in split_v_v_mouth:
                # if '_' in split_v_v_mouth and split_v_v_mouth not in ['Full_mouth', 'Upper_Jaw',
                #                                                       'Lower_Jaw']:
                    mouth_v_v_0 = split_v_v_mouth.split('_')[0]
                    mouth_v_v_1 = split_v_v_mouth.split('_')[1]
                    old_name = ""
                    new_name = ""
                    if mouth_v_v_0.isnumeric():
                        teeth_exists = self.env['teeth.code'].search([(search_name, '=', mouth_v_v_0)])
                        if teeth_exists:
                            teeth_exists = teeth_exists[0]
                            old_name = mouth_v_v_0
                    if mouth_v_v_1.isnumeric():
                        teeth_exists = self.env['teeth.code'].search([(search_name, '=', mouth_v_v_1)])
                        if teeth_exists:
                            teeth_exists = teeth_exists[0]
                            old_name = mouth_v_v_1
                    if mouth_v_v_0.isnumeric() or mouth_v_v_1.isnumeric():
                        if teeth_exists:
                            new_name = teeth_exists.name
                            if new_type == 'universal':
                                new_name = teeth_exists.name
                            if new_type == 'palmer':
                                new_name = teeth_exists.palmer_name
                            if new_type == 'iso':
                                new_name = teeth_exists.iso
                    if new_name and old_name:
                        new_split_v_v_mouth = split_v_v_mouth.replace(old_name, new_name)
                        surface_part = surface_part.replace(split_v_v_mouth, new_split_v_v_mouth)
        return surface_part

    @api.multi
    def write(self, vals):
        if 'type' in vals:
            old_type = self.type
            new_type = vals['type']
            med_teeth_treatment = self.env['medical.teeth.treatment'].search([])
            for operation in med_teeth_treatment:
                old_surface_part = operation.detail_description
                new_surface_part = self.convert_to_next_chart_type(old_surface_part, old_type, new_type)
                if new_surface_part and operation.teeth_code_rel and operation.detail_description != new_surface_part:
                    operation.write({'detail_description': new_surface_part})
            treatment_invoice = self.env['treatment.invoice'].search([])
            for treatment_inv in treatment_invoice:
                old_surface_part = treatment_inv.note
                new_surface_part = self.convert_to_next_chart_type(old_surface_part, old_type, new_type)
                if new_surface_part and treatment_inv.teeth_code_rel and treatment_inv.note != new_surface_part:
                    treatment_inv.write({'note': new_surface_part})
            account_invoice = self.env['account.invoice.line'].search([])
            for account_inv in account_invoice:
                old_surface_part = account_inv.name
                new_surface_part = self.convert_to_next_chart_type(old_surface_part, old_type, new_type)
                if new_surface_part and account_inv.teeth_code_rel and account_inv.name != new_surface_part:
                    account_inv.write({'name': new_surface_part})
        result = super(ChartSelection, self).write(vals)
        return result
