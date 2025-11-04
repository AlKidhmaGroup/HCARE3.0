# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class TeethCode(models.Model):
    _description = "teeth code"
    _name = "teeth.code"

    name = fields.Char('Name', size=128, required=True)
    code = fields.Char('Code', size=128, required=True)
    palmer_name = fields.Char('palmer_name', size=128, required=True)
    palmer_internal_id = fields.Integer('Palmar Internam ID')
    iso = fields.Char('iso', size=128, required=True)
    internal_id = fields.Integer('Internal IDS')

    @api.multi
    def write(self, vals):
        for rec in self:
            #             if vals.has_key('palmer_name'):
            if 'palmer_name' in vals:
                lst = self.search([('palmer_internal_id', '=', rec.palmer_internal_id)])
                #                 lst.write({'palmer_name': vals['palmer_name']})
                super(TeethCode, lst).write({'palmer_name': vals['palmer_name']})
        return super(TeethCode, self).write(vals)

    @api.model
    def name_get(self):
        res = []
        teeth_obj = self.env['chart.selection'].search([])
        obj = teeth_obj[-1]
        for each in self:
            name = each.name
            if obj.type == 'palmer':
                name = str(each.palmer_internal_id)
                if each.internal_id <= 8:
                    name += '-1x'
                elif each.internal_id <= 16:
                    name += '-2x'
                elif each.internal_id <= 24:
                    name += '-3x'
                else:
                    name += '-4x'
            elif obj.type == 'iso':
                name = each.iso
            res.append((each.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            res = []
            teeth_obj = self.env['chart.selection'].search([])
            obj = teeth_obj[-1]
            if obj.type == 'palmer':
                domain = [('palmer_name', operator, name)]
            elif obj.type == 'iso':
                domain = [('iso', operator, name)]
            else:
                domain = [('name', operator, name)]

            partner = self.search(domain + args, limit=limit)
            return partner.name_get()
        return super(TeethCode, self).name_search(name, args=args, operator=operator, limit=limit)

    @api.multi
    def get_teeth_code(self):
        l1 = []
        d1 = {}
        teeth_ids = self.env['teeth.code'].search([])
        teeth_obj = self.env['chart.selection'].search([])
        teeth_type = teeth_obj[-1]
        for teeth in teeth_ids.filtered(lambda t: t.internal_id):
            if teeth_type.type == 'palmer':
                d1[int(teeth.internal_id)] = teeth.palmer_name
            elif teeth_type.type == 'iso':
                d1[int(teeth.internal_id)] = teeth.iso
            else:
                d1[int(teeth.internal_id)] = teeth.name
        x = d1.keys()
        x = sorted(x)
        for i in x:
            l1.append(d1[i])
        return l1

    @api.multi
    def get_child_correct_teeth_code(self):
        dict_teeth_no = {}
        teeth_obj = self.env['chart.selection'].search([])
        teeth_type = teeth_obj[-1]
        if teeth_type.type == 'iso':
            dict_teeth_no = {
                '18': '55',
				'17': '54',
				'16': '53',
				'15': '52',
				'14': '51',
				'13': '61',
				'12': '62',
				'11': '63',
				'21': '64',
				'22': '65',
				'23': '75',
				'24': '74',
				'25': '73',
				'26': '72',
				'27': '71',
				'28': '81',
				'38': '82',
				'37': '83',
				'36': '84',
				'35': '85',
            }
        return dict_teeth_no
