# -*- coding: utf-8 -*-

from odoo import fields, models, api


class HotelEmployee(models.Model):
    # ---------------------------------------- Private Attributes ---------------------------------

    _name = "hotel1.employee"
    _description = "hospital doctor"

    # --------------------------------------- Fields Declaration ----------------------------------
    _inherit = ['mail.thread', 'mail.activity.mixin']
    employee_id = fields.Many2one('hr.employee', 'Employees ID',
                                  ondelete="cascade",
                                  delegate=True, required=True,
                                  help='Enter related employee')
    category_id = fields.Many2many('hr.employee.category',
                                   'Doctor_category_rels', 'emp_id',
                                   'categ_id', 'Tags',
                                   help='Select employee category')

    info = fields.Text('Extra Info')


    #
    @api.model
    def create(self, vals):
        """Inherited create method to assign value to users for delegation"""
        em_id = super( HotelEmployee, self).create(vals)
        user_obj = self.env['res.users']
        user_vals = {'name': em_id.name,
                     'login': em_id.work_email,
                     'email': em_id.work_email,
                     }
        ctx_vals = {'doctor_create': True,
                    'hospital_id': em_id.company_id.id}
        user_rec = user_obj.with_context(ctx_vals).create(user_vals)
        em_id.employee_id.write({'user_id': user_rec.id})
        #        if vals.get('is_parent'):
        #            self.parent_crt(teacher_id)
        return em_id

    @api.onchange('user_id')
    def onchange_user(self):
        """Onchange method for user."""
        if self.user_id:
            self.name = self.name or self.user_id.name
            self.work_email = self.user_id.email
            self.image = self.image or self.user_id.image
