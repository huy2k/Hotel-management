from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime


class Folio(models.Model):
    _name = "hotel1.folio"
    _order = "checkin_date DESC"
    name = fields.Char("Name")

    customer_id = fields.Many2one('res.partner', string='Customer')

    checkin_date = fields.Datetime(
        "Check In",
        required=True,

    )
    checkout_date = fields.Datetime(
        "Check Out",
    )
    room_type_id = fields.Many2one('hotel1.room.type', "Room type")
    room_id = fields.Many2one("hotel1.room")
    service_line_ids = fields.One2many(
        "hotel1.service.line",
        "folio_id",
        readonly=False,
        help="Hotel services details provided to"
             "Customer and it will included in "
             "the main Invoice.",
    )
    hotel_policy = fields.Selection(
        [
            ("draft", "Draft"),
            ("manual", "On Check In"),
            ("picking", "On Checkout"),
            ("done", "Done"),
            ('cancel', "Canceled")
        ],
        default="draft",
        help="Hotel policy for payment that "
             "either the guest has to payment at "
             "booking time or check-in "
             "check-out time.",
    )
    duration = fields.Float(
        "Duration in Days",
        help="Number of days which will automatically "
             "count from the check-in and check-out date. ", compute="_compute__checkin_checkout_dates"
    )
    # hotel_invoice_id = fields.Many2one("account.move", "Invoice", copy=False)
    additional_hours = fields.Integer(
        help="Provide the min hours value for \
                                            check in, checkout days, whatever the \
                                            hours will be provided here based on \
                                            that extra days will be calculated.", default=0
    )
    duration_dummy = fields.Float()
    price_room = fields.Monetary("Price Room", related="room_id.price")
    total_room = fields.Monetary("Total room price", compute="computer_price_room")
    total_service = fields.Monetary("Total service")
    total_price = fields.Monetary("Total", compute="_compute_total_price", store=True)
    is_invoiced = fields.Boolean(copy=False, default=False)
    reservation_id = fields.Many2one(
        "hotel1.reservation", "Reservation", ondelete="restrict"
    )
    option_price = fields.Selection([
        ('day', 'Day'),
        ('hour', 'Hour')
    ], default='day')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        readonly=True,
        store=True
    )

    @api.depends('total_room', 'total_service', 'service_line_ids')
    def _compute_total_price(self):
        total = 0.0
        total_all = 0.0
        for i in self:
            for line in i.service_line_ids:
                total += line.total
            total_all = i.total_room + total
            i.total_price = total_all

    @api.constrains("checkin_date", "checkout_date")
    def _check_dates(self):
        """
        This method is used to validate the checkin_date and checkout_date.
        -------------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        if self.checkin_date >= self.checkout_date:
            raise ValidationError(
                _(
                    """Room line Check In Date Should be """
                    """less than the Check Out Date!"""
                )
            )
        if self.create_date and self.checkin_date:
            if self.checkin_date.date() < self.create_date.date():
                raise ValidationError(
                    _(
                        """Room line check in date should be """
                        """greater than the current date."""
                    )
                )

    # @api.onchange("checkin_date", "checkout_date", 'duration')
    @api.depends("checkin_date", "checkout_date", 'duration')
    # def _onchange_checkin_checkout_dates(self):
    def _compute__checkin_checkout_dates(self):
        """
        When you change checkin_date or checkout_date it will check it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        """
        for record in self:
            configured_addition_hours = record.additional_hours
            myduration = 0
            if record.checkin_date and record.checkout_date:
                dur = record.checkout_date - record.checkin_date
                sec_dur = dur.seconds
                if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                    myduration = dur.days
                else:
                    myduration = dur.days + 1
                #            To calculate additional hours in hotel room as per minutes
                if configured_addition_hours > 0:
                    additional_hours = abs((dur.seconds / 60) / 60)
                    if additional_hours >= configured_addition_hours:
                        myduration += 1
            record.duration = myduration

    @api.depends('duration', 'room_id')
    def computer_price_room(self):
        total = 0.0
        for i in self:
            total = i.price_room * i.duration
            i.total_room = total

    def action_done(self):
        self.hotel_policy = 'done'
        self.room_id.status = 'open'

    def action_checkin(self):
        if self.room_id:
            self.hotel_policy = 'manual'
            self.room_id.status = "booking"
        else:
            raise ValidationError(
                _(
                    """Please select room  """
                )
            )

    def action_checkout(self):
        self.hotel_policy = 'picking'

    def action_canceled(self):
        self.room_id.status = "open"
        self.hotel_policy = 'cancel'

    def write(self, vals):
        if vals and vals.get("duration", False):
            vals["duration"] = vals.get("duration", 0.0)
        if vals.get("duration") and vals.get("room_id"):
            vals["total_room"] = vals.get("duration") * vals.get("price_room")
        res = super(Folio, self).write(vals)
        reservation_line_obj = self.env["hotel1.room.reservation.line"]
        for folio in self:
            reservations = reservation_line_obj.search(
                [("reservation_id", "=", folio.reservation_id.id)]
            )
        return res

    def create_folio_invoice(self):

        list_of_ids = []

        account_invoice_obj = self.env['account.move']

        for folio_req in self:
            if folio_req.is_invoiced:
                raise Warning('All ready Invoiced.')
            sale_journals = self.env['account.journal'].search([('type', '=', 'sale')])
            invoice_vals = {
                'name': self.env['ir.sequence'].next_by_code('hotel1.folio'),
                'invoice_origin': self.customer_id.id or '',
                'move_type': 'out_invoice',
                'ref': False,
                'journal_id': sale_journals and sale_journals[0].id or False,
                'partner_id': folio_req.customer_id.id,
                'currency_id': folio_req.customer_id.currency_id.id,
                'invoice_payment_term_id': False,
                'fiscal_position_id': folio_req.customer_id.property_account_position_id.id,
                'team_id': False,
                'invoice_date': date.today(),
                'company_id': folio_req.customer_id.company_id.id or False,
            }
            res = account_invoice_obj.create(invoice_vals)
            product = folio_req.service_line_ids.service_line_id
            invoice_line_account_id = False

            invoice_line_vals1 = {
                'name': folio_req.room_id.name or '',
                'account_id': invoice_line_account_id,
                'price_unit': folio_req.room_id.room_type.price,
                'quantity': folio_req.duration,
                'product_id': folio_req.room_id.product_id.id,
            }
            invoice_line_vals = {
                'name': folio_req.service_line_ids.service_line_id.name or '',
                'account_id': invoice_line_account_id,
                'price_unit': folio_req.service_line_ids.service_line_id.product_id.list_price,
                'quantity': folio_req.service_line_ids.quantity,
                'product_id': folio_req.service_line_ids.service_line_id.product_id.id,
            }
            res1 = res.write({'invoice_line_ids': ([(0, 0, invoice_line_vals)])})
            res2 = res.write({'invoice_line_ids': ([(0, 0, invoice_line_vals1)])})
            list_of_ids.append(res.id)

            if list_of_ids:
                imd = self.env['ir.model.data']
                write_ids = folio_req.browse(self._context.get('active_id'))
                write_ids.write({'is_invoiced': True})
                action = self.env.ref('account.action_move_out_invoice_type')
                list_view_id = imd._xmlid_to_res_id('account.view_invoice_tree')
                form_view_id = imd._xmlid_to_res_id('account.view_move_form')
                result = {
                    'name': action.name,
                    'help': action.help,
                    'type': action.type,
                    'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
                    'target': action.target,
                    'context': action.context,
                    'res_model': action.res_model,

                }
                if list_of_ids:
                    result['domain'] = "[('id','=',%s)]" % list_of_ids
                return result

    def action_view_invoice_hotel(self):
        """
        """
        return {
            'name': 'Invoices',
            'domain': [('invoice_origin', '=', self.customer_id.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.model
    def create(self, vals):
        vals["name"] = (
                self.env["ir.sequence"].next_by_code("hotel1.folio") or "New"
        )
        room = vals.get("room_id")
        # print(type(room))
        # room = int(room)
        room_obj = self.env["hotel1.room"].search([('id', '=', room)])

        if room_obj.status == 'close':
            raise ValidationError(
                _(
                    """Room close """
                )
            )
        # room_obj.write({
        #     'status': 'booking'
        # })

        # vals['price_room'] = room_obj.list_price * vals.get('duration')
        result = super(Folio, self).create(vals)
        return result

    @api.onchange("room_type_id")
    def on_change_categ(self):
        """
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        -----------------------------------------------------------
        @param self: object pointer
        """
        hotel_room_ids = self.env["hotel1.room"].search(
            [("room_type.id", "=", self.room_type_id.id)]
        )
        room_ids = []
        for room in hotel_room_ids:
            room_ids.append(room.id)
        domain = {"room_id": ['&', ("id", "in", room_ids), ('status', '=', 'open')]}
        return {"domain": domain}


class HotelServiceLine(models.Model):
    _name = "hotel1.service.line"
    _description = "hotel Service line"

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """
        return super(HotelServiceLine, self).copy(default=default)

    service_line_id = fields.Many2one(
        "hotel1.service",
        "Service Line",
        required=True,
    )
    folio_id = fields.Many2one("hotel1.folio", "Booking", ondelete="cascade")
    price = fields.Float(string="price", compute="_compute_price")
    quantity = fields.Integer(default=1)
    total = fields.Float(string="Total")

    @api.depends('service_line_id.price')
    def _compute_price(self):
        for service in self:
            if not service.price:
                service.price = service.service_line_id.product_id.list_price

    @api.onchange('quantity', 'service_line_id')
    def _onchange_price(self):
        total = 0.0
        for i in self:
            total = i.service_line_id.list_price * i.quantity
        self.total = total


class Refund(models.Model):
    _name = "hotel1.refund"
    _description = "hotel refund"
    _order = 'date_refund asc'
    guest = fields.Many2one('res.partner', compute="_compute_guest", string="Guest")
    # email_from = fields.Char(
    #     'Email',
    #     compute='_compute_email_from', readonly=True)
    reservation = fields.Many2one('hotel1.reservation')
    reason = fields.Char("Reason refund")
    status = fields.Selection([('draft', "Draft"), ('approved', 'Approved'),
                               ('declined', 'Declined')], default='draft', string="Status refund")
    date_refund = fields.Datetime("Date refund", default=datetime.today())

    @api.depends('reservation.customer_id')
    def _compute_guest(self):
        for res in self:
            res.guest = res.reservation.customer_id.id

    # @api.model
    # def create(self, vals):
    #     # reservation = vals.get("reservation")
    #     # reservation_obj = self.env["hotel1.reservation"].search([('id', '=', reservation)])
    #     # if vals.get('status') == 'approved':
    #     #     if reservation_obj.state == 'draft' or reservation_obj.state == 'confirm':
    #     #         print("draft")
    #     #         reservation_obj.write({'state': 'cancel'})
    #     #         reservation_obj.cancel_reservation()
    #     result = super(Refund, self).create(vals)
    #     return result

    # @api.model
    # def write(self, vals):
    #     result = super(Refund, self).write(vals)
    #     return result

    # @api.depends('guest.email')
    # def _compute_email_from(self):
    #     for line in self:
    #         if line.guest:
    #             line.email_from = line.guest.email

    def action_approved(self):
        self.status = 'approved'
        reservation_obj = self.env["hotel1.reservation"].search([('id', '=', self.reservation.id)])
        reservation_obj.cancel_reservation()

    def action_declined(self):
        self.status = 'declined'

    def send_accept_refund_function(self):
        template = self.env.ref('Hotel-management.hotel1_refund_email_template').id
        template_id = self.env['mail.template'].browse(template)
        template_id.send_mail(self.id, force_send=True)

    def send_declined_refund_function(self):
        template = self.env.ref('Hotel-management.hotel1_refund_declined_email_template').id
        template_id = self.env['mail.template'].browse(template)
        template_id.send_mail(self.id, force_send=True)
