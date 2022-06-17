from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Room(models.Model):
    _name = "hotel1.room"
    product_id = fields.Many2one(
        "product.product",
        "Product_id",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    room_type = fields.Many2one("hotel1.room.type", "Room type")
    status = fields.Selection([
        ('open', 'Open'),
        ('close', 'Close'),
        ('booking', 'Booking'),
        ('reservation', "Reservation")
    ], default="open")
    # booking_id = fields.Many2one("hotel1.booking")
    capacity = fields.Integer(string="Capacity")
    room_reservation_line_ids = fields.One2many(
        "hotel1.room.reservation.line", "room_id", string="Room Reserve Line"
    )
    price = fields.Monetary(string="Price", compute='_compute_price', readonly=True, store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        readonly=True,
        store=True
    )

    @api.depends('room_type.price')
    def _compute_price(self):
        for room in self:
            room.price = room.room_type.price

    def unlink(self):
        if self.status == "booking":
            raise ValidationError(
                (
                    """Room booking """
                    """You can't delete room."""
                )
            )


class RoomType(models.Model):
    _name = "hotel1.room.type"

    name = fields.Char("Name Room Type")
    limit_person = fields.Integer("Limit Person")
    price = fields.Monetary("price", 'currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
