from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv.expression import expression


class HotelFloor(models.Model):
    _name = "hotel1.floor"
    _description = "Floor"
    _order = "sequence"

    name = fields.Char("Floor Name", required=True, index=True)
    sequence = fields.Integer("sequence", default=10)


class Room(models.Model):
    _name = "hotel1.room"
    product_id = fields.Many2one(
        "product.product",
        "Product_id",
        # delegate=True,
        # ondelete="cascade",
    )
    name = fields.Char("name")
    room_type = fields.Many2one("hotel1.room.type", "Room type")
    floor_id = fields.Many2one(
        "hotel1.floor",
        "Floor No",
        help="At which floor the room is located.",
        ondelete="restrict",
    )
    status = fields.Selection([
        ('open', 'Open'),
        ('close', 'Close'),
        ('booking', 'Rental'),
        ('reservation', "Reservation")
    ], default="open")
    room_line_ids = fields.One2many("hotel1.room.reservation.line", inverse_name='room_id')
    capacity = fields.Integer(string="Capacity", related='room_type.limit_person')
    room_reservation_line_ids = fields.One2many(
        "hotel1.room.reservation.line", "room_id", string="Room Reserve Line"
    )
    price = fields.Monetary(string="Price", compute='_compute_price', readonly=True, store=True)
    price_hour = fields.Monetary(string="Price hour", related="room_type.price_hour", readonly=True)

    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        readonly=True,
        store=True
    )
    img_room = fields.Image("Image Room")
    kanbancolor = fields.Integer('Color', compute="set_kanban_color")
    description = fields.Char("Description")

    def set_kanban_color(self):
        for record in self:
            kanban_color = 0
            if record.status == 'open':
                kanban_color = 4
            elif record.status == 'close':
                kanban_color = 1
            elif record.status == 'reservation':
                kanban_color = 2
            elif record.status == 'booking':
                kanban_color = 5
            record.kanbancolor = kanban_color

    @api.depends('room_type.price')
    def _compute_price(self):
        for room in self:
            room.price = room.room_type.price

    @api.model
    def create(self, vals):
        product_obj = self.env["product.product"].create({'name': vals.get('name')})
        vals["product_id"] = product_obj.id
        return super(Room, self).create(vals)
    def unlink(self):
        if self.status == "booking" or self.status == 'reservation':
            raise ValidationError(
                (
                    """Room booking """
                    """You can't delete room."""
                )
            )


class RoomType(models.Model):
    _name = "hotel1.room.type"

    name = fields.Char("Name Room Type")
    max_adults = fields.Integer("Max adults")
    max_children = fields.Integer("Max children")
    limit_person = fields.Integer("Limit Person")
    room_amenities_ids = fields.Many2many(
        "hotel1.room.amenities", string="Room Amenities", help="List of room amenities."
    )
    price = fields.Monetary("price", 'currency_id')
    price_hour = fields.Monetary(string="Price hour")

    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    img_room_type = fields.Image("Image")


class HotelRoomAmenitiesType(models.Model):
    _name = "hotel1.room.amenities.type"
    _description = "amenities Type"

    amenity_id = fields.Many2one("hotel1.room.amenities.type", "Category")
    child_ids = fields.One2many(
        "hotel1.room.amenities.type", "amenity_id", "Amenities Child Categories"
    )
    product_categ_id = fields.Many2one(
        "product.category",
        "Product Category",
        delegate=True,
        required=True,
        copy=False,
        ondelete="restrict",
    )

    @api.model
    def create(self, vals):
        if "amenity_id" in vals:
            amenity_categ = self.env["hotel1.room.amenities.type"].browse(
                vals.get("amenity_id")
            )
            vals.update({"parent_id": amenity_categ.product_categ_id.id})
        return super(HotelRoomAmenitiesType, self).create(vals)

    def write(self, vals):
        if "amenity_id" in vals:
            amenity_categ = self.env["hotel1.room.amenities.type"].browse(
                vals.get("amenity_id")
            )
            vals.update({"parent_id": amenity_categ.product_categ_id.id})
        return super(HotelRoomAmenitiesType, self).write(vals)

    def name_get(self):
        def get_names(cat):
            """Return the list [cat.name, cat.amenity_id.name, ...]"""
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.amenity_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    # @api.model
    # def name_search(self, name, args=None, operator="ilike", limit=100):
    #     if not args:
    #         args = []
    #     if name:
    #         # Be sure name_search is symetric to name_get
    #         category_names = name.split(" / ")
    #         parents = list(category_names)
    #         child = parents.pop()
    #         domain = [("name", operator, child)]
    #         if parents:
    #             names_ids = self.name_search(
    #                 " / ".join(parents),
    #                 args=args,
    #                 operator="ilike",
    #                 limit=limit,
    #             )
    #             category_ids = [name_id[0] for name_id in names_ids]
    #             if operator in expression.NEGATIVE_TERM_OPERATORS:
    #                 categories = self.search([("id", "not in", category_ids)])
    #                 domain = expression.OR(
    #                     [[("amenity_id", "in", categories.ids)], domain]
    #                 )
    #             else:
    #                 domain = expression.AND(
    #                     [[("amenity_id", "in", category_ids)], domain]
    #                 )
    #             for i in range(1, len(category_names)):
    #                 domain = [
    #                     [
    #                         (
    #                             "name",
    #                             operator,
    #                             " / ".join(category_names[-1 - i:]),
    #                         )
    #                     ],
    #                     domain,
    #                 ]
    #                 if operator in expression.NEGATIVE_TERM_OPERATORS:
    #                     domain = expression.AND(domain)
    #                 else:
    #                     domain = expression.OR(domain)
    #         categories = self.search(expression.AND([domain, args]), limit=limit)
    #     else:
    #         categories = self.search(args, limit=limit)
    #     return categories.name_get()


class HotelRoomAmenities(models.Model):
    _name = "hotel1.room.amenities"
    _description = "Room amenities"

    product_id = fields.Many2one(
        "product.product",
        "Room Amenities Product",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    amenities_categ_id = fields.Many2one(
        "hotel1.room.amenities.type",
        "Amenities Category",
        required=True,
        ondelete="restrict",
    )
    product_manager = fields.Many2one("res.users")

    @api.model
    def create(self, vals):
        if "amenities_categ_id" in vals:
            amenities_categ = self.env["hotel1.room.amenities.type"].browse(
                vals.get("amenities_categ_id")
            )
            vals.update({"categ_id": amenities_categ.product_categ_id.id})
        return super(HotelRoomAmenities, self).create(vals)

    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if "amenities_categ_id" in vals:
            amenities_categ = self.env["hotel1.room.amenities.type"].browse(
                vals.get("amenities_categ_id")
            )
            vals.update({"categ_id": amenities_categ.product_categ_id.id})
        return super(HotelRoomAmenities, self).write(vals)
