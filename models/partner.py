from odoo import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'
    partner_hotel = fields.Boolean(string="Is a Hotel Partner")











