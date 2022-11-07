# See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelReservation(models.Model):
    _name = "hotel1.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = "reservation_no desc"
    _inherit = ["mail.thread"]

    def _compute_folio_count(self):
        for res in self:
            res.update({"no_of_folio": len(res.customer_id.ids)})

    reservation_no = fields.Char("Reservation No", readonly=True, copy=False)
    date_order = fields.Datetime(
        "Date Ordered",
        readonly=True,
        required=True,
        index=True,
        default=lambda self: fields.Datetime.now(),
    )

    customer_id = fields.Many2one(
        "hotel1.customer",
        "Guest Name",
        index=True,
        required=True

    )

    # partner_invoice_id = fields.Many2one(
    #     "res.partner",
    #     "Invoice Address",
    #     readonly=True,
    #     states={"draft": [("readonly", False)]},
    #     help="Invoice address for " "current reservation.",
    # )

    checkin = fields.Datetime(
        "Expected-Date-Arrival",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    checkout = fields.Datetime(
        "Expected-Date-Departure",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    adults = fields.Integer(
        "Adults",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="List of adults there in guest list. ",
    )
    children = fields.Integer(
        "Children",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Number of children there in guest list.",
    )
    reservation_line = fields.One2many(
        "hotel1.reservation.line",
        "line_id",
        string="Reservation Line",
        help="Hotel room reservation details.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("cancel", "Cancel"),
            ("done", "Done"),
        ],
        "State",
        readonly=True,
        default="draft",
    )
    folio_id = fields.Many2many(
        "hotel1.folio",
        "hotel1_folio_reservation_rel",
        string="Folio",
    )
    no_of_folio = fields.Integer("No. Folio", compute="_compute_folio_count")

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        lines_of_moves_to_post = self.filtered(
            lambda reserv_rec: reserv_rec.state != "draft"
        )
        if lines_of_moves_to_post:
            raise ValidationError(
                _("Sorry, you can only delete the reservation when it's draft!")
            )
        return super(HotelReservation, self).unlink()

    @api.constrains("reservation_line", "adults", "children")
    def _check_reservation_rooms(self):
        """
        This method is used to validate the reservation_line.
        -----------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        """
        ctx = dict(self._context) or {}
        for reservation in self:
            cap = 0
            for rec in reservation.reservation_line:
                if len(rec.reserve) == 0:
                    raise ValidationError(_("Please Select Rooms For Reservation."))
                cap += sum(room.capacity for room in rec.reserve)

            if not ctx.get("duplicate"):
                if (reservation.adults + reservation.children) > cap:
                    raise ValidationError(
                        _(
                            "Room Capacity Exceeded \n"
                            " Please Select Rooms According to"
                            " Members Accomodation." + str(cap)
                        )
                    )
            if reservation.adults <= 0:
                raise ValidationError(_("Adults must be more than 0"))

    @api.constrains("checkin", "checkout")
    def check_in_out_dates(self):
        """
        When date_order is less than check-in date or
        Checkout date should be greater than the check-in date.
        """
        if self.checkout and self.checkin:
            if self.checkin < self.date_order:
                raise ValidationError(
                    _(
                        """Check-in date should be greater than """
                        """the current date."""
                    )
                )
            if self.checkout < self.checkin:
                raise ValidationError(
                    _("""Check-out date should be greater """ """than Check-in date.""")
                )

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        vals["reservation_no"] = (
            self.env["ir.sequence"].next_by_code("hotel1.reservation")
        )
        print(vals)
        return super(HotelReservation, self).create(vals)

    def write(self, vals):
        print(vals)
        res = super(HotelReservation, self).write(vals)
        return res

    def check_overlap(self, date1, date2):
        delta = date2 - date1
        return {date1 + timedelta(days=i) for i in range(delta.days + 1)}

    def confirmed_reservation(self):
        """
        This method create a new record set for hotel room reservation line
        -------------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel room reservation line.
        """
        reservation_line_obj = self.env["hotel1.room.reservation.line"]
        for reservation in self:
            reserv_checkin = reservation.checkin
            reserv_checkout = reservation.checkout
            room_bool = False
            for line_id in reservation.reservation_line:
                for room in line_id.reserve:
                    if room.room_reservation_line_ids:
                        for reserv in room.room_reservation_line_ids.search(
                                [
                                    ("status", "in", ("confirm", "done")),
                                    ("room_id", "=", room.id),
                                ]
                        ):
                            check_in = reserv.check_in
                            check_out = reserv.check_out
                            if check_in <= reserv_checkin <= check_out:
                                room_bool = True
                            if check_in <= reserv_checkout <= check_out:
                                room_bool = True
                            if (
                                    reserv_checkin <= check_in
                                    and reserv_checkout >= check_out
                            ):
                                room_bool = True
                            r_checkin = reservation.checkin.date()
                            r_checkout = reservation.checkout.date()
                            check_intm = reserv.check_in.date()
                            check_outtm = reserv.check_out.date()
                            range1 = [r_checkin, r_checkout]
                            range2 = [check_intm, check_outtm]
                            overlap_dates = self.check_overlap(
                                *range1
                            ) & self.check_overlap(*range2)
                            if room_bool:
                                raise ValidationError(
                                    _(
                                        "You tried to Confirm "
                                        "Reservation with room"
                                        " those already "
                                        "reserved in this "
                                        "Reservation Period. "
                                        "Overlap Dates are "
                                        "%s"
                                    )
                                    % overlap_dates
                                )
                            else:
                                self.state = "confirm"
                                vals = {
                                    "room_id": room.id,
                                    "check_in": reservation.checkin,
                                    "check_out": reservation.checkout,
                                    "state": "assigned",
                                    "reservation_id": reservation.id,
                                }
                                room.write({"status": "booking"})
                        else:
                            self.state = "confirm"
                            vals = {
                                "room_id": room.id,
                                "check_in": reservation.checkin,
                                "check_out": reservation.checkout,
                                "state": "assigned",
                                "reservation_id": reservation.id,
                            }
                            room.write({"status": "booking"})
                    else:
                        self.state = "confirm"
                        vals = {
                            "room_id": room.id,
                            "check_in": reservation.checkin,
                            "check_out": reservation.checkout,
                            "state": "assigned",
                            "reservation_id": reservation.id,
                        }
                        room.write({"status": "booking"})
                    reservation_line_obj.create(vals)
        return True

    def cancel_reservation(self):
        """
        This method cancel record set for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for hotel room reservation line.
        """
        room_res_line_obj = self.env["hotel1.room.reservation.line"]
        hotel_res_line_obj = self.env["hotel1.reservation.line"]
        self.state = "cancel"
        room_reservation_line = room_res_line_obj.search(
            [("reservation_id", "in", self.ids)]
        )
        room_reservation_line.write({"state": "unassigned"})
        room_reservation_line.unlink()
        reservation_lines = hotel_res_line_obj.search([("line_id", "in", self.ids)])
        for reservation_line in reservation_lines:
            reservation_line.reserve.write({"status": "open"})
        return True

    def set_to_draft_reservation(self):
        self.update({"state": "draft"})

    def create_folio(self):
        """
        This method is for create new hotel folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for hotel folio.
        """

        for reservation in self:
            for line in reservation.reservation_line:
                hotel_folio_obj = self.env["hotel1.folio"]
                for r in line.reserve:
                    checkin_date = reservation["checkin"]
                    checkout_date = reservation["checkout"]
                    duration_vals = self._onchange_check_dates(
                        checkin_date=checkin_date,
                        checkout_date=checkout_date,
                        duration=False,
                    )
                    duration = duration_vals.get("duration") or 0.0
                    folio_vals = {
                        "customer_id": reservation.customer_id.id,
                        "checkin_date": reservation.checkin,
                        "checkout_date": reservation.checkout,
                        "duration": duration,
                        "reservation_id": reservation.id,
                        "room_id": r.id and r.id,
                        "name": reservation["reservation_no"],
                        'hotel_policy': "manual"
                    }
                    print(hotel_folio_obj)
                    r.write({"status": "booking"})
                    folio = hotel_folio_obj.create(folio_vals)
                    self.write({"folio_id": [(6, 0, folio.ids)], "state": "done"})

        return True

    def _onchange_check_dates(
            self, checkin_date=False, checkout_date=False, duration=False
    ):
        """
        This method gives the duration between check in checkout if
        customer will leave only for some hour it would be considered
        as a whole day. If customer will checkin checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        """
        value = {}
        configured_addition_hours = 0.0
        duration = 0
        if checkin_date and checkout_date:
            dur = checkout_date - checkin_date
            duration = dur.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs(dur.seconds / 60)
                if additional_hours <= abs(configured_addition_hours * 60):
                    duration -= 1
        value.update({"duration": duration})
        return value

    # def open_folio_view(self):
    #     folios = self.mapped("folio_id")
    #     action = self.env.ref("hotel.open_hotel_folio1_form_tree_all").read()[0]
    #     if len(folios) > 1:
    #         action["domain"] = [("id", "in", folios.ids)]
    #     elif len(folios) == 1:
    #         action["views"] = [(self.env.ref("hotel.view_hotel_folio_form").id, "form")]
    #         action["res_id"] = folios.id
    #     else:
    #         action = {"type": "ir.actions.act_window_close"}
    #     return action


class HotelReservationLine(models.Model):
    _name = "hotel1.reservation.line"
    _description = "Reservation Line"

    name = fields.Char("Name")
    line_id = fields.Many2one("hotel1.reservation")
    reserve = fields.Many2many(
        "hotel1.room",
        # "hotel1_reservation_line_room_rel",
        "hotel1_reservation_line_id",
        "room_id",
        domain="[('room_type','=',categ_id)]",
    )
    categ_id = fields.Many2one("hotel1.room.type", "Room Type")

    @api.onchange("categ_id")
    def on_change_categ(self):
        """
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        -----------------------------------------------------------
        @param self: object pointer
        """
        if not self.line_id.checkin and self.line_id.state != "draft":
            raise ValidationError(
                _(
                    """Before choosing a room,\n You have to """
                    """select a Check in date or a Check out """
                    """ date in the reservation form."""
                )
            )
        hotel_room_ids = self.env["hotel1.room"].search(
            [("room_type.id", "=", self.categ_id.id)]
        )

        room_ids = []
        for room in hotel_room_ids:
            assigned = False
            for line in room.room_reservation_line_ids.filtered(
                    lambda l: l.status != "cancel"
            ):
                if self.line_id.checkin and line.check_in and self.line_id.checkout:
                    if (
                            self.line_id.checkin <= line.check_in <= self.line_id.checkout
                    ) or (
                            self.line_id.checkin <= line.check_out <= self.line_id.checkout
                    ):
                        assigned = True
                    elif (line.check_in <= self.line_id.checkin <= line.check_out) or (
                            line.check_in <= self.line_id.checkout <= line.check_out
                    ):
                        assigned = True
                    hotel_room_folio = self.env["hotel1.folio"].search(
                        [("room_id.id", "=", room.id), ("checkout_date", ">", self.line_id.checkin)]
                    )
                    if len(hotel_room_folio) > 0:
                        assigned = True
                    else:
                        assigned = False

            if not assigned:
                room_ids.append(room.id)
        domain = {"reserve": [("id", "in", room_ids)]}
        return {"domain": domain}

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        hotel_room_reserv_line_obj = self.env["hotel1.room.reservation.line"]
        for reserv_rec in self:
            for rec in reserv_rec.reserve:
                myobj = hotel_room_reserv_line_obj.search(
                    [
                        ("room_id", "=", rec.id),
                        ("reservation_id", "=", reserv_rec.line_id.id),
                    ]
                )
                if myobj:
                    rec.write({"status": "open"})
                    myobj.unlink()
        return super(HotelReservationLine, self).unlink()


class HotelRoomReservationLine(models.Model):
    _name = "hotel1.room.reservation.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one("hotel1.room", string="Room id")
    check_in = fields.Datetime("Check In Date", required=True)
    check_out = fields.Datetime("Check Out Date", required=True)
    state = fields.Selection(
        [("assigned", "Assigned"), ("unassigned", "Unassigned")], "Room Status"
    )
    reservation_id = fields.Many2one("hotel1.reservation", "Reservation")
    status = fields.Selection(string="state", related="reservation_id.state")
