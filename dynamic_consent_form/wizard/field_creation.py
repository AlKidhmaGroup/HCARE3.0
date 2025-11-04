from odoo import api, fields, models, SUPERUSER_ID
import base64
from odoo.exceptions import UserError

# class fieldsmodels(models.Model):
#     _name = "ir.model.fields"

#     @api.model
#     def create(self, vals):
#         print("___________vals",vals)
#         res = super(consent, self).create(vals)
#         return res


class ConsentFieldCreationWizard(models.TransientModel):
    _name = "consent.field.creation"

    @api.depends('boolean_fields_ids')
    def get_bool_line_count(self):
        for rec in self:
            count = 0
            for line in rec.boolean_fields_ids.sorted(key=lambda r: r.field_count):
                count = line.field_count
            rec.bool_line_count = count+1
            
    @api.depends('selection_o2many')
    def get_sele_line_count(self):
        for rec in self:
            count = 0
            for line in rec.selection_o2many.sorted(key=lambda r: r.field_count):
                count = line.field_count
            rec.sele_line_count = count+1
    
    field_name = fields.Char('Field Name', default='x_', required=True)
    field_description = fields.Char('Field Label-English', required=True)
    field_arabic_description = fields.Char('Field Label-Arabic', required=True)
    field_type = fields.Selection([('char', 'Char'), ('date', 'Date'), ('text', 'Text'),
                                   ('html', 'Html'),('boolean', 'Boolean'),('signature', 'Signature'),
                                   ('many2one', 'Many2one'), ('selection', 'Selection'),
                                   ('many2many', 'Many2many'),('one2many', 'One2many')],
                                    string='Field Type', required=True)
    is_readonly = fields.Boolean(string='Readonly')
    is_related = fields.Boolean(string='Related field?')
    patient_doctor_related = fields.Selection([('Patient', 'Patient'), ('Doctor', 'Doctor')] ,string='Relation Type?')
    is_related_relation = fields.Char(string='Relation')
    table_field = fields.Many2one('ir.model', string='Model')
    selection_o2many = fields.One2many('selection.values', 'selection_field_id', string='Selection options')
    model_id = fields.Char('Table', default='consent.wizard', required=True)
    dynamic_sequence = fields.Integer(default=1)
    html_default_content = fields.Html('Html English Default Content')
    html_arabic_default_content = fields.Html('Html Arabic Default Content')

    has_dependency = fields.Boolean(string="Has Dependent Field")
    dependent_value = fields.Char(string="Dependent Value")
    dependent_field = fields.Many2one('ir.model.fields',
                                      string="Dependent Field")
    relation_field = fields.Char(string="Relation Field",default='x_')
    relation_table_field = fields.Many2one('ir.model', string='Relation Model')
    boolean_fields_ids = fields.One2many('boolean.values', 'boolean_field_id', string='Boolean options')
    
    bool_line_count = fields.Integer(compute='get_bool_line_count', string="Bool Line Count", store=True)
    sele_line_count = fields.Integer(compute='get_sele_line_count', string="Sele Line Count", store=True)
    
    

    # def design_view_for_new_field(self, consent_new_field, related_field_id):
    #     view_arch = """
    #     <data>
    #         <field name="consent_detail_id" position="after">
    #             <field name='""" + related_field_id.name + """' invisible="1"/>
    #             <field name='""" + consent_new_field.name + """' attrs="{'invisible': ['|',('""" + related_field_id.name + """', '=', False),('language', '=', 'arabic')]}"/>
    #             <field name='""" + consent_new_field.name + """' string= '""" + consent_new_field.field_arabic_description + """' attrs="{'invisible': ['|' ,('""" + related_field_id.name + """', '=', False),('language', '=', 'english')]}"/>
    #         </field>
    #     </data>
    #     """
    #     if self.field_type == 'signature':
    #        view_arch = """
    #         <data>
    #             <field name="sign_xpath_field_id" position="after">
    #                 <field name='""" + related_field_id.name + """' invisible="1"/>
    #                 <field name='""" + consent_new_field.name + """' widget="signature" attrs="{'invisible': ['|',('""" + related_field_id.name + """', '=', False),('language', '=', 'arabic')]}"/>
    #                 <field name='""" + consent_new_field.name + """' string= '""" + consent_new_field.field_arabic_description + """' widget="signature" attrs="{'invisible': ['|' ,('""" + related_field_id.name + """', '=', False),('language', '=', 'english')]}"/>
    #             </field>
    #         </data>
    #         """
    #     view_id = self.env['ir.ui.view'].browse(self.env['ir.ui.view'].get_view_id('dynamic_consent_form.consent_form_wizard'))
    #     view = self.env['ir.ui.view'].create({
    #         'name': 'Consent Dynamic field ' + self.field_name + ' ' + self.field_description,
    #         'model': self.model_id,
    #         'model_data_id': self.model_id,
    #         'type': 'form',
    #         'mode': 'extension',
    #         'action': True,
    #         'arch': view_arch,
    #         'inherit_id': view_id.id,
    #     })

    @api.onchange('is_related', 'patient_doctor_related')
    def onchange_is_related(self):
        if not self.patient_doctor_related:
            self.is_related_relation = ''
        if self.patient_doctor_related == 'Patient':
            self.is_related_relation = 'patient_id.field_name'
        if self.patient_doctor_related == 'Doctor':
            self.is_related_relation = 'doctor_id.field_name'

    def create_consent_new_field(self, ttype, wizard_model, related_field_id):
        dyn_vals = {
            'name': self.field_name,
            'field_description': self.field_description,
            'field_arabic_description': self.field_arabic_description,
            'ttype': ttype,
            'state': 'manual',
            'model_id': wizard_model.id,
            'model': self.model_id,
            'consent_field': True,
            'readonly': self.is_readonly,
            'dynamic_sequence': self.dynamic_sequence,
            'related_xml_field_id': related_field_id.id,
            'has_dependency': self.has_dependency,
            'dependent_value': self.dependent_value,
            'dependent_field': self.dependent_field.id,
        }
        if self.is_related and self.is_related_relation:
            if self.is_related_relation == 'patient_id.field_name':
                raise UserError('Enter Patient related field name properly')
            if self.is_related_relation == 'doctor_id.field_name':
                raise UserError('Enter Doctor related field name properly')
            dyn_vals['related'] = self.is_related_relation
        if self.field_type in ('many2one', 'many2many'):
            dyn_vals['relation'] = self.table_field.model
        if self.field_type == 'selection':
            if not self.selection_o2many:
                raise UserError('Please provide Selection options')
            select_list = []
            dup_select_list = []
            for select_val in self.selection_o2many:
                select_list.append((select_val.name, select_val.name))
                if select_val.name in dup_select_list:
                    raise UserError('Remove duplicate Selection options')
                dup_select_list.append(select_val.name)
            dyn_vals['selection'] = str(select_list)
        if self.field_type == 'signature':
            dyn_vals['is_sign_field_id'] = True
        if self.field_type == 'html':
            dyn_vals['html_default_content'] = self.html_default_content
            dyn_vals['html_arabic_default_content'] = self.html_arabic_default_content
        if self.field_type == 'one2many':
            dyn_vals_many2one = {
                                   "active":True,
                                   'consent_field': False,
                                   "name":self.relation_field,
                                   "field_description":self.relation_field,
                                   "dynamic_sequence":self.dynamic_sequence,
                                   "store":True,
                                   "on_delete":"set null",
                                   "domain":"[]",
                                   "field_arabic_description":False,
                                   "has_dependency":False,
                                   "dependent_value":False,
                                   "dependent_field":False,
                                   "model_id":self.relation_table_field.id,
                                   # 'related_xml_field_id': related_field_id.id,
                                   "ttype":"many2one",
                                   "help":False,
                                   "html_default_content":"<p><br></p>",
                                   "html_arabic_default_content":"<p><br></p>",
                                   "required":False,
                                   "readonly":False,
                                   "index":False,
                                   "copy":True,
                                   "track_visibility":False,
                                   "relation":wizard_model.model,
                                   "related":False,
                                   "depends":False,
                                   "compute":False,
                                   "groups":[[6,False,[ ]] ]
                                }
            consent_many2one_field = self.env['ir.model.fields'].create(dyn_vals_many2one)
            dyn_vals_one2many = {
                                   "active":True,
                                   'consent_field': True,
                                   "name": self.field_name,
                                   "field_description": self.field_description,
                                   "field_arabic_description": self.field_arabic_description,
                                   "dynamic_sequence":self.dynamic_sequence,
                                   "store":True,
                                   "domain":"[]",
                                   "has_dependency":False,
                                   "dependent_value":False,
                                   "dependent_field":False,
                                   "model_id":wizard_model.id,
                                   "ttype":"one2many",
                                   "help":False,
                                   "html_default_content":"<p><br></p>",
                                   "html_arabic_default_content":"<p><br></p>",
                                   "required":False,
                                   "readonly":False,
                                   "index":False,
                                   "copy":False,
                                   "track_visibility":False,
                                   "relation": self.relation_table_field.model,
                                   'related_xml_field_id': related_field_id.id,
                                   "relation_field": self.relation_field,
                                   "related":False,
                                   "depends":False,
                                   "compute":False,
                                   "groups":[
                                      [
                                         6,
                                         False,
                                         [
                                            
                                         ]
                                      ]
                                   ]
                                }
            consent_new_field = self.env['ir.model.fields'].create(dyn_vals_one2many)
        repeat_field_list = []
        if self.field_type == 'selection' and self.selection_o2many and self.has_dependency:
            field_list = []
            for line in self.selection_o2many:
                if not line.none_field and not line.char_field and not line.text_field or not line.name or not line.field_name:
                    raise UserError('Enter Related Fields Properly')
                # if not line.none_field:
                field_list.append((0,0,{'value':line.name,'related_field_id':self.create_selection_related_field(line,wizard_model,repeat_field_list)}))
            dyn_vals.update({'select_related_field_ids':field_list})
        
        if self.field_type == 'boolean' and self.boolean_fields_ids and self.has_dependency:
            field_list = []
            for line in self.boolean_fields_ids:
                if not line.none_field and not line.char_field and not line.text_field or not line.name or not line.field_name:
                    raise UserError('Enter Related Fields Properly')
                bool_id,text_id = self.create_boolean_related_field(line,wizard_model,repeat_field_list)
                field_list.append((0,0,{'value':line.name,'related_bool_field_id':bool_id and bool_id.id or False,'related_text_field_id':text_id and text_id.id or False,'visible_in':line.visible_in}))
            dyn_vals.update({'boolean_related_field_ids':field_list})
        
        if self.field_type != 'one2many':
            consent_new_field = self.env['ir.model.fields'].create(dyn_vals)
        return consent_new_field
    
    def create_selection_related_field(self,data,wizard_model,repeat_field_list):
        data_field_name= data_field_name = data.field_name.lower()
        if data.none_field:
            return False
        vals = {
                'name': data_field_name+"_sele",
                'field_description': data.name,
                'field_arabic_description': data.arabic_name if data.arabic_name else data.name,
                'ttype': 'text' if data.text_field else 'char',
                'state': 'manual',
                'model_id': wizard_model.id,
                'model': self.model_id,
                'consent_field': True,
                }
        consent_new_field = self.env['ir.model.fields'].create(vals)
        return consent_new_field.id
    
    def create_boolean_related_field(self,data,wizard_model,repeat_field_list):
        consent_new_field = False
        data_field_name = data.field_name.lower()
        if not data.none_field:
            vals = {
                    'name': data_field_name+"_text",
                    'field_description': data.name,
                    'field_arabic_description': data.arabic_name if data.arabic_name else data.name,
                    'ttype': 'text' if data.text_field else 'char',
                    'state': 'manual',
                    'model_id': wizard_model.id,
                    'model': self.model_id,
                    'consent_field': True,
                    }
            consent_new_field = self.env['ir.model.fields'].create(vals)
        vals = {
                'name': data_field_name+"_bool",
                'field_description': data.name,
                'field_arabic_description': data.arabic_name if data.arabic_name else data.name,
                'ttype': 'boolean',
                'state': 'manual',
                'model_id': wizard_model.id,
                'model': self.model_id,
                'consent_field': True,
                }
        consent_bool_field = self.env['ir.model.fields'].create(vals)
        return consent_bool_field,consent_new_field
    
    def create_compute_field(self, wizard_model):
        compute_vals = {
            'name': self.field_name + '_compute',
            'field_description': 'Compute ' + self.field_description,
            'ttype': 'boolean',
            'state': 'manual',
            'model_id': wizard_model.id,
            'model': self.model_id,
            'consent_field': True,
        }
        related_field_id = self.env['ir.model.fields'].create(compute_vals)
        return related_field_id

    @api.multi
    def create_field_wizard(self):
        wizard_model = self.env['ir.model'].search([('model', '=', self.model_id)])
        if not wizard_model:
            raise UserError('Entered table is invalid')
        wizard_field = self.env['ir.model.fields'].search([('model_id', '=', wizard_model.id),('name', '=', self.field_name)])
        if wizard_field:
            raise UserError('Already a field exists with same name.')
        if not self.field_name or self.field_name == 'x_' or self.field_name == 'x':
            raise UserError('Enter field name properly.')
        ttype = self.field_type
        if self.field_type == 'signature':
            ttype = 'binary'
        related_field_id = self.create_compute_field(wizard_model)
        consent_new_field = self.create_consent_new_field(ttype, wizard_model, related_field_id)
        # design_view_for_field = self.design_view_for_new_field(consent_new_field, related_field_id)
        wiz_update_view = self.env['field.view.update'].browse(1)
        wiz_update_view.design_dynamic_field_view()


class SelectionValues(models.TransientModel):
    _name = 'selection.values'

    @api.model
    def default_get(self, field_list):
        res = super(SelectionValues, self).default_get(field_list)
        if self.env.context.get('line_count',False) and self.env.context.get('field_name',False):
           name =  self.env.context.get('field_name') 
           count = self.env.context.get('line_count')
           res.update({'field_name':name+"_"+str(count)}) 
        return res

    name = fields.Char('English Name')
    selection_field_id = fields.Many2one('consent.field.creation')
    char_field = fields.Boolean(string='Text')
    text_field = fields.Boolean(string='Text Area')
    none_field = fields.Boolean(string='None')
    field_name = fields.Char(string='Field Name',default='x_')
    field_count = fields.Float(string='Field Count')
    arabic_name = fields.Char('Arabic Name')
    
    @api.onchange('none_field')
    def onchange_none_field(self):
        for rec in self:
            if rec.none_field:
                rec.text_field = rec.char_field = False
                
    @api.onchange('char_field','text_field')
    def onchange_text_field(self):
        for rec in self:
           if rec.char_field or rec.text_field:
               rec.none_field = False       
                
    
                
class BooleanValues(models.TransientModel):
    _name = 'boolean.values'
    
    @api.model
    def default_get(self, field_list):
        res = super(BooleanValues, self).default_get(field_list)
        if self.env.context.get('line_count',False) and self.env.context.get('field_name',False):
           name =  self.env.context.get('field_name') 
           count = self.env.context.get('line_count')
           res.update({'field_name':name+"_"+str(count)}) 
        return res
    
    name = fields.Char('English Name')
    boolean_field_id = fields.Many2one('consent.field.creation')
    char_field = fields.Boolean(string='Text')
    text_field = fields.Boolean(string='Text Area')
    none_field = fields.Boolean(string='None',default=True)
    visible_in = fields.Boolean(string='Visible In(Tick/Untick)',default=True)
    field_name = fields.Char(string='Field Name',default='x_')
    field_count = fields.Float(string='Field Count')
    arabic_name = fields.Char('Arabic Name')
    
    @api.onchange('char_field','text_field')
    def onchange_text_field(self):
        for rec in self:
           if rec.char_field or rec.text_field:
               rec.none_field = False
    
