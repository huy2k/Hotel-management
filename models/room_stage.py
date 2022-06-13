from odoo import fields, models, api


class RoomStage(models.Model):
    _name = 'hotel1.room.status'
    _order = 'sequence'
    _description = 'Description'

    name = fields.Char("Name", required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
