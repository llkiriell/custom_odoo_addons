from odoo import models, fields, api

class VirtualSalePosOrder(models.TransientModel):
    _name = 'virtual.sale.pos.order'
    _description = 'Vista combinada entre Sale Orders y POS Orders'
    _log_access = True  # No se necesita rastrear acceso en modelos transitorios

    # Campos en común entre Sale Order y POS Order
    company_id = fields.Many2one('res.company', string='Company')
    partner_id = fields.Many2one('res.partner', string='Partner')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    user_id = fields.Many2one('res.users', string='Salesperson')
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    currency_rate = fields.Float(string='Currency Rate')
    amount_tax = fields.Float(string='Amount Tax')
    amount_total = fields.Float(string='Amount Total')
    date_order = fields.Datetime(string='Order Date')
    create_date = fields.Datetime(string='Create Date')
    write_date = fields.Datetime(string='Write Date')

    @api.model
    def _get_combined_orders(self):
        """ Obtiene y combina datos de `sale.order` y `pos.order`. """

        # Se obtienen los pedidos sin restricciones innecesarias
        sale_orders = self.env['sale.order'].sudo().search([])
        pos_orders = self.env['pos.order'].sudo().search([])

        combined_orders = []

        for order in sale_orders:
            combined_orders.append({
                'company_id': order.company_id.id,
                'partner_id': order.partner_id.id,
                'pricelist_id': order.pricelist_id.id,
                'user_id': order.user_id.id,
                'fiscal_position_id': order.fiscal_position_id.id,
                'currency_rate': order.currency_rate,
                'amount_tax': order.amount_tax,
                'amount_total': order.amount_total,
                'date_order': order.date_order,
                'create_date': order.create_date,
                'write_date': order.write_date,
            })

        for order in pos_orders:
            combined_orders.append({
                'company_id': order.company_id.id,
                'partner_id': order.partner_id.id,
                'pricelist_id': order.pricelist_id.id,
                'user_id': order.user_id.id,
                'fiscal_position_id': order.fiscal_position_id.id,
                'currency_rate': order.currency_rate,
                'amount_tax': order.amount_tax,
                'amount_total': order.amount_total,
                'date_order': order.date_order,
                'create_date': order.create_date,
                'write_date': order.write_date,
            })

        return combined_orders

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """ Sobrescribe `search()` para devolver datos virtuales en memoria. """
        combined_orders = self._get_combined_orders()

        if count:
            return len(combined_orders)

        # Crear registros virtuales sin persistencia usando `new()`
        records = self.browse([])
        for order_data in combined_orders:
            records += self.new(order_data)

        return records
