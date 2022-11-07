# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HotelCustomer(models.Model):
    # ---------------------------------------- Private Attributes ---------------------------------

    _name = "hotel1.customer"
    _description = "Customer"
    _order = "name"
    _rec_name = "partner_id"

    # --------------------------------------- Fields Declaration ----------------------------------

    # Basic -------
    name = fields.Char(string='Customer code', readonly=True, copy=False)
    birthday = fields.Date(string="Date of birth")
    place_of_birth = fields.Char('Place of Birth')
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'),
                               ('other', 'Other')], string="Gender")

    workplace = fields.Char(string="Workplace")
    identification_id = fields.Char(string='Identification No')
    passport_id = fields.Char('Passport No')
    info = fields.Text(string="Extra Info")

    # Relational ----------
    partner_id = fields.Many2one('res.partner', string='customer', index=True, required=True)

    country_id = fields.Many2one("res.country", string="Nationality (Country)")
    # diseases_ids = fields.One2many("hospital.diseases", "customer_id", string="Diseases")

    # Computed ----------
    phone = fields.Char('Phone', compute='_compute_phone', inverse='_inverse_phone', readonly=False,
                        store=True)
    mobile = fields.Char('Mobile', compute='_compute_mobile', inverse='_inverse_mobile',
                         readonly=False, store=True)
    email = fields.Char('Email', compute='_compute_email', inverse='_inverse_email', readonly=False,
                        store=True)
    avatar = fields.Binary(string="Avatar", compute='_compute_avatar', inverse='_inverse_avatar',
                           readonly=True)
    # Address fields
    street = fields.Char('Street', compute='_compute_partner_address_values',
                         inverse='_inverse_partner_address_values',
                         readonly=False, store=True)
    street2 = fields.Char('Street2', compute='_compute_partner_address_values',
                          inverse='_inverse_partner_address_values', readonly=False, store=True)
    zip = fields.Char('Zip', change_default=True, compute='_compute_partner_address_values',
                      inverse='_inverse_partner_address_values', readonly=False, store=True)
    city = fields.Char('City', compute='_compute_partner_address_values', readonly=False,
                       store=True)
    state_id = fields.Many2one(
        "res.country.state", string='State',
        compute='_compute_partner_address_values',
        inverse='_inverse_partner_address_values',
        readonly=False, store=True,
        domain="[('country_id', '=?', address_country_id)]")
    address_country_id = fields.Many2one(
        'res.country', string='Country',
        compute='_compute_partner_address_values',
        inverse='_inverse_partner_address_values',
        readonly=False, store=True)

    @api.depends('partner_id')
    def _compute_partner_address_values(self):
        for customer in self:
            customer.street = customer.partner_id.street
            customer.street2 = customer.partner_id.street2
            customer.zip = customer.partner_id.zip
            customer.city = customer.partner_id.city
            customer.state_id = customer.partner_id.state_id
            customer.address_country_id = customer.partner_id.country_id

    def _inverse_partner_address_values(self):
        for customer in self:
            if customer.partner_id.street != customer.street:
                customer.partner_id.street = customer.street
            if customer.partner_id.street2 != customer.street2:
                customer.partner_id.street2 = customer.street2
            if customer.partner_id.city != customer.city:
                customer.partner_id.city = customer.city
            if customer.partner_id.zip != customer.zip:
                customer.partner_id.zip = customer.zip
            if customer.partner_id.state_id != customer.state_id:
                customer.partner_id.state_id = customer.state_id
            if customer.partner_id.country_id != customer.address_country_id:
                customer.partner_id.country_id = customer.address_country_id

    @api.depends('partner_id.phone')
    def _compute_phone(self):
        for customer in self:
            if not customer.phone or customer.partner_id.phone:
                customer.phone = customer.partner_id.phone

    def _inverse_phone(self):
        for customer in self:
            customer.partner_id.phone = customer.phone

    @api.depends('partner_id.mobile')
    def _compute_mobile(self):
        for customer in self:
            if not customer.mobile or customer.partner_id.mobile:
                customer.mobile = customer.partner_id.mobile

    def _inverse_mobile(self):
        for customer in self:
            customer.partner_id.mobile = customer.mobile

    @api.depends('partner_id.email')
    def _compute_email(self):
        for customer in self:
            if not customer.email or customer.partner_id.email:
                customer.email = customer.partner_id.email

    def _inverse_email(self):
        for customer in self:
            customer.partner_id.email = customer.email

    @api.depends('partner_id.avatar_128')
    def _compute_avatar(self):
        for customer in self:
            customer.avatar = customer.partner_id.avatar_128

    def _inverse_avatar(self):
        for customer in self:
            customer.partner_id.avatar_128 = customer.avatar

    # ----------------------------------- Constrains and Onchanges --------------------------------

    # on create method
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hotel1.customer.seq')
        result = super(HotelCustomer, self).create(vals)
        return result


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Res Partner'

    identification_id = fields.Char(string='Identification No')
    passport_id = fields.Char('Passport No')
    info = fields.Text(string="Extra Info")

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        company_id = res.company_id.id
        return res
