from odoo import api, fields, models, _


class BaseExtended(models.AbstractModel):
    _inherit = "base"

    @api.multi
    def get_preview_messages(self):
        """
        return the messages that should be displayed
        when opening the form view of a record.
        This preview will be triggered when opening the form view
        for the first time. i.e, when it is initialised(note that it will not be
        triggered when switching the form view using navigation controls
        and re-opening the form view using breadcrumbs.)

        :return: list containing dictionaries with content to be displayed
        The title and content will accept html content also.
        Each element of the returned list will be shown as separate popups
        in the given order.
        """
        # sample:
        # result = [{
        #   'main_title': "",
        #   'sections': [{'title': "", 'content': ""}, ..,]
        # }, {
        #   ...,
        #   }]
        return []


class ResUsers(models.Model):
    _inherit = "res.users"

    room_ids = fields.Many2many('medical.hospital.oprating.room', 'user_room_rel',
                                'room_id', 'user_id', "Allowed Room Columns")
    physician_ids = fields.Many2many('medical.physician', 'physician_room_rel',
                                     'physician_id', 'user_id', "Allowed Doctor Columns")
