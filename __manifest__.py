# -*- coding: utf-8 -*-
{
    'name': "Hotel huy",

    'summary': """
       Hotel management """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Huy",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website_sale', 'account', 'hr', 'portal', 'base', 'mail'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hotel_customer_sequence.xml',
        'data/hotel_sequence.xml',
        'data/hotel_reservation_sequence.xml',
        'data/hotel_folio_sequence.xml',
        'data/email_refund_template.xml',
        'data/email_booking_template.xml',
        'views/data.xml',
        'views/room_view.xml',
        'views/service_views.xml',
        'views/roomtype_views.xml',
        'views/hotel_room_amenities.xml',
        'views/service_type_views.xml',
        'views/customer_view.xml',
        'views/employee_view.xml',
        'views/folio_view.xml',
        'views/hotel_reservation_view.xml',
        'views/refund.xml',
        'views/web-form.xml',
        'views/invoices.xml',
        'views/frontend/home.xml',
        'views/frontend/bookform.xml',
        'views/frontend/roomtype_website.xml',
        'views/frontend/search_booking.xml',
        'views/frontend/portal.xml',
        'views/frontend/reservation_detail.xml',
        'views/frontend/refund_booking.xml',
        'views/menu_views.xml',
    ],
    # 'assets': {
    #     'web.assets_frontend': [
    #         'Hotel-management/static/css/all.css',
    #         'Hotel-management/static/css/bootstrap.min.css',
    #         'Hotel-management/static/css/bootstrap-icons.css',
    #         'Hotel-management/static/css/boxicons.min.css',
    #         'Hotel-management/static/css/jquery-ui.css',
    #         'Hotel-management/static/css/jquery.fancybox.min.css',
    #         'Hotel-management/static/css/slick-theme.css',
    #         'Hotel-management/static/css/slick.css',
    #         'Hotel-management/static/css/magnific-popup.css',
    #         'Hotel-management/static/css/nice-select.css',
    #         'Hotel-management/static/css/swiper-bundle.min.css',
    #         'Hotel-management/static/css/odometer.css',
    #         'Hotel-management/static/css/style.css',
    #     ]
    # }
}
