# -*- coding: utf-8 -*-

from odoo import models, fields, api
from collections import defaultdict
import xml.etree.ElementTree as ET
import json

class PosOrder(models.Model):
    _inherit = "pos.order"

    def show_message_test(self):
        raise models.ValidationError("Hola Mundo")

    def get_pos_sales(self):
        # Obtener todas las órdenes de venta que no están en estado 'draft'
        orders = self.search([
            ('state', '!=', 'draft')
        ], order='create_date desc')

        sales_by_session = defaultdict(list)


        for order in orders:
          	# Metodos de pago y sesiones (joins)
            payment_methods = order.payment_ids.mapped('payment_method_id.name')
            session_name = order.session_id.name if order.session_id else 'Sin sesión'

            order_data = {
                'order_id': order.id,
                'order_name': order.name,
                'order_date': order.create_date,
                'customer_name': order.partner_id.name if order.partner_id else 'Sin cliente',
                'user_name': order.user_id.login if order.user_id else 'Desconocido', 
                'order_state': order.state,
                'total_amount': order.amount_total,
                'payment_methods': ', '.join(payment_methods),
            }

            sales_by_session[session_name].append(order_data)

        # Formatear el diccionario con plantilla json
        grouped_sales = [{
            'session_name': session_name,
            'sales': sales
        } for session_name, sales in sales_by_session.items()]

        return grouped_sales
    
    def dict_to_json(self, data):
        pos_orders_json = json.dumps(data, default=str)
        return pos_orders_json
    
    def dict_to_xml(self, data):
        root = ET.Element('sales')

        for session in data:
            session_element = ET.SubElement(root, 'session', name=session['session_name'])

            for sale in session['sales']:
                sale_element = ET.SubElement(session_element, 'sale', order_id=str(sale['order_id']))
                ET.SubElement(sale_element, 'order_name').text = sale['order_name']
                ET.SubElement(sale_element, 'order_date').text = str(sale['order_date'])
                ET.SubElement(sale_element, 'customer_name').text = sale['customer_name']
                ET.SubElement(sale_element, 'user_name').text = sale['user_name']
                ET.SubElement(sale_element, 'order_state').text = sale['order_state']
                ET.SubElement(sale_element, 'total_amount').text = str(sale['total_amount'])
                ET.SubElement(sale_element, 'payment_methods').text = sale['payment_methods']

        return ET.tostring(root, encoding='unicode')
    
    def init(self):
        pos_orders = self.get_pos_sales()

        pos_orders_json = self.dict_to_json(pos_orders)
        pos_orders_xml = self.dict_to_xml(pos_orders)
        print('============================================ json ============================================')
        print(pos_orders_json) 
        print('============================================ json ============================================')
        print('============================================ xml ============================================')
        print(pos_orders_xml) 
        print('============================================ xml ============================================')
