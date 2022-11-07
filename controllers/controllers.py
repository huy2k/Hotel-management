# -*- coding: utf-8 -*-


from odoo import http
from datetime import datetime
from dateutil import parser


class Hotel(http.Controller):

    @http.route('/index', auth='public', website=True)
    def index1(self, **kw):
        return http.request.render('Hotel-management.index1')

    @http.route('/room-type', auth='public', website=True)
    def index(self, **kw):
        room_types = http.request.env['hotel1.room.type']
        return http.request.render('Hotel-management.index', {
            'room_types': room_types.search([])
        })

    @http.route('/room-type/<model("hotel1.room.type"):room_type>', auth="public",
                website=True)
    def room_type(self, room_type):
        rooms = http.request.env['hotel1.room'].search(['&', ('room_type', '=', room_type.id), ('status', '=', 'open')])
        room_ids = []

        print(rooms)
        return http.request.render('Hotel-management.view_room', {
            'room_type': room_type, 'rooms': rooms
        })

    @http.route('/book-form', auth="public", website=True)
    def booking_form(self, **kw):
        return http.request.render('Hotel-management.booking_form')

    @http.route('/create/booking', auth="public", website=True)
    def create_webbooking(self, **kwargs):
        partner = http.request.env['res.users'].browse(http.request.env.uid).partner_id
        customer = http.request.env['hotel1.customer'].search([('partner_id', '=', partner.id)])
        print(kwargs)
        checkin = parser.parse(kwargs.get('Checkin'))
        # checkin =datetime.strptime(checkin, "%Y/%m/%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
        checkout = parser.parse(kwargs.get('checkout'))
        room = int(kwargs.get('Room'))
        # checkout = datetime.strptime(checkout, "%Y/%m/%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
        print(partner)
        print(customer)
        reverse_vals = {'customer_id': customer.id,
                        'checkin': checkin,
                        'checkout': checkout,
                        'adults': kwargs.get('adults'),
                        'children': kwargs.get('children'),
                        'reservation_line': [
                            [0, 'virtual_24',
                             {'name': False, 'categ_id': kwargs.get('Room_type'), 'reserve': [[room, False, [room]]]}]],
                        # 'reservation_no': 'Re/00006'
                        }
        http.request.env['hotel1.reservation'].sudo().create(reverse_vals)
        return http.request.render('Hotel-management.thank_you_booking')
