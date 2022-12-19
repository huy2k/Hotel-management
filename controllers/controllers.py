# -*- coding: utf-8 -*-

from odoo import http, _
from datetime import datetime, timedelta
from dateutil import parser
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import ValidationError


class Hotel(http.Controller):

    @http.route('/index', type='http', auth='public', website=True)
    def index1(self):
        room_types = http.request.env['hotel1.room.type'].sudo().search([])
        return http.request.render('Hotel-management.index2', {
            'room_types': room_types
        })

    @http.route('/room-types/<model("hotel1.room.type"):room_type>', auth='public', website=True)
    def room_type_website(self, room_type):
        rooms = http.request.env['hotel1.room'].sudo().search(
            ['&', ('room_type', '=', room_type.id), ('status', '=', 'open')])
        return http.request.render('Hotel-management.room_type_website', {
            'room_type': room_type, 'rooms': rooms
        })

    @http.route('/room-type', auth='public', website=True)
    def index(self):
        room_types = http.request.env['hotel1.room.type'].sudo().search([])
        return http.request.render('Hotel-management.index', {
            'room_types': room_types
        })

    @http.route('/room-type/<model("hotel1.room.type"):room_type>', auth="public",
                website=True)
    def room_type(self, room_type):
        rooms = http.request.env['hotel1.room'].sudo().search(
            ['&', ('room_type', '=', room_type.id), ('status', '=', 'open')])
        room_ids = []

        print(rooms)
        return http.request.render('Hotel-management.view_room', {
            'room_type': room_type, 'rooms': rooms
        })

    @http.route('/rooms/<model("hotel1.room"):room>', auth="public",
                website=True)
    def room_type(self, room):
        return http.request.render('Hotel-management.view_detail_room', {
            'room': room
        })

    @http.route('/book-form', auth="public", website=True)
    def booking_form(self, **kw):
        return http.request.render('Hotel-management.booking_form')

    @http.route('/create/booking', auth="public", website=True)
    def create_webbooking(self, **kwargs):
        if http.request.env.user.id == http.request.env.ref('base.public_user').id:
            return http.request.render('web.login', {})
        partner = http.request.env['res.users'].browse(http.request.env.uid).partner_id
        print(kwargs)
        checkin = parser.parse(kwargs.get('Checkin'))
        checkout = parser.parse(kwargs.get('checkout'))
        room = int(kwargs.get('Room'))

        identification = kwargs.get('identification')
        # checkout = datetime.strptime(checkout, "%Y/%m/%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
        print(partner)

        reverse_vals = {'customer_name': kwargs.get('name'),
                        'customer_id': partner.id,
                        'identification': identification,
                        'checkin': checkin,
                        'checkout': checkout,
                        'adults': kwargs.get('adults'),
                        'children': kwargs.get('children'),
                        'reservation_line': [
                            [0, 'virtual_24',
                             {'name': False, 'categ_id': kwargs.get('Room_type'), 'reserve': [[6, False, [room]]]}]],
                        }
        room_state_vals = {
            'status': 'reservation'
        }
        http.request.env['hotel1.reservation'].sudo().create(reverse_vals)
        http.request.env['hotel1.room'].sudo().search([('id', '=', room)]).write(room_state_vals)
        return http.request.render('Hotel-management.thank_you_booking')

    @http.route('/searchs', auth="public", website=True)
    def search_rooms(self, **kwargs):
        return http.request.render('Hotel-management.search_rooms')

    @http.route('/search/room', auth="public", website=True)
    def search_room(self, **kwargs):
        print(kwargs)

        if not kwargs:
            checkin = datetime.today()
            checkout = datetime.today() + timedelta(days=1)
        else:
            if kwargs.get('checkin') == "":
                raise ValidationError("Invalid validate")
            if kwargs.get('checkout') == "":
                raise ValidationError("Invalid validate")
            checkin = parser.parse(kwargs.get('checkin'))
            checkout = parser.parse(kwargs.get('checkout'))

        # get room open
        rooms = http.request.env['hotel1.room'].sudo().search([('status', '=', 'open')])

        reservation_obj = http.request.env["hotel1.reservation"].sudo().search([])
        print(reservation_obj)
        for reservation in reservation_obj:

            reserv_checkin = checkin
            reserv_checkout = checkout
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
                            # print(room.id)
                            print(room.name)
                            print(room_bool)
                        if not room_bool:
                            room_open = http.request.env["hotel1.room"].search([('id', '=', room.id)])
                            rooms += room_open

        # print("so phong trong sau check ngay", len(set(rooms)))
        # rooms = set(rooms)

        return http.request.render('Hotel-management.search_rooms', {
            'check_in': checkin, 'check_out': checkout, 'rooms': rooms, 'count_room': len(set(rooms))
        })

    @http.route('/room/<model("hotel1.room"):room>', auth='user', website=True)
    def roomtype_website(self, room):
        room = http.request.env['hotel1.room'].sudo().browse(room.id)
        return http.request.render('Hotel-management.view_detail_room', {
            'room': room
        })

    @http.route('/hotel/folio/', auth='user', website=True)
    def display_subjects(self, sortby=None, **kw):
        partner = http.request.env.user.partner_id
        reservation = http.request.env['hotel1.reservation'].search([('customer_id', '=', partner.id)])
        return http.request.render('Hotel-management.portal_hotel_reservation', {
            'reservations': reservation,
            'page_name': 'reservation',
            # 'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })

    @http.route('/reservation/<model("hotel1.reservation"):reservation>/', auth='user', website=True)
    def display_reservation_detail(self, reservation):
        reservation_line = http.request.env['hotel1.reservation.line'].sudo().search([('line_id', '=', reservation.id)])
        room_ids = []
        for room in reservation_line.reserve:
            if room.room_reservation_line_ids:
                for reserv in room.room_reservation_line_ids.search(
                        [
                            ("room_id", "=", room.id),
                        ]):
                    room_ids += http.request.env["hotel1.room.reservation.line"].sudo().search(
                        [('room_id', '=', room.id)])
        room_ids = set(room_ids)
        return http.request.render('Hotel-management.reservation_details',
                                   {'reservation': reservation,
                                    'room_reservation': room_ids,
                                    'page_name': 'Reservation'})

    @http.route('/refund/<model("hotel1.reservation"):reservation>/', auth='user', website=True)
    def refund_reservation(self, reservation):
        if reservation.state == 'cancel':
            raise ValidationError(
                _(
                    "Room have refund \n"
                )
            )
        return http.request.render('Hotel-management.refund_booking', {'reservation': reservation})

    @http.route('/refund-reservation', auth='user', website=True)
    def form_refund_reservation(self, **kw):
        reason = kw.get("reason")
        reservation = kw.get("reservation")
        reservation_obj = http.request.env['hotel1.reservation'].sudo().search(
            [('id', '=', reservation)])
        if reservation_obj.state == 'cancel' or reservation_obj.state == 'done':
            raise ValidationError(
                _(
                    "Room cannot have cancel \n"
                )
            )
        else:
            refund_obj = http.request.env['hotel1.refund'].sudo().search([('reservation', '=', reservation)])
            print(refund_obj.reservation)
            if not refund_obj:
                refund_obj.create({'reservation': reservation, 'reason': reason})
            else:
                refund_obj.write({'reservation': reservation, 'reason': reason})
        return http.request.render('Hotel-management.thank_you_booking')


class HotelCustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        Reservations = http.request.env['hotel1.reservation']
        partner = http.request.env.user.partner_id

        if 'count_reservation' in counters:
            values['count_reservation'] = Reservations.search_count([('customer_id', '=', partner.id)])
            # values['count_reservation'] = Reservations.search_count(self._prepare_reservation_domain(partner))\
            #  if Reservations.check_access_rights('read', raise_exception=False) else 0

        print(values)
        return values

    def _prepare_reservation_domain(self, partner):
        return [
            ('customer_id', 'child_of', [partner.commercial_partner_id.id]),
        ]
