from odoo import models, fields
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class DocumentIssued(models.Model):
    _name = 'document.issued'
    _auto = False  # No es una tabla fisica

    # Define fields as in SQL query
    session_id = fields.Many2one('pos.session', string="Session")
    order_id = fields.Many2one('pos.order', string="Order")
    process_date = fields.Datetime("FProceso")
    partner_company = fields.Char("CiaSocio")
    warehouse_code = fields.Char("CodAlm")
    batch_id = fields.Char("IdBach")
    doc_type = fields.Char("TDocto")
    doc_number = fields.Char("NroDocto")
    document_date = fields.Datetime("FDocumento")
    customer_vat = fields.Char("ClienteRUC")
    customer_name = fields.Char("ClienteNombre")
    customer_address = fields.Char("ClienteDireccion")
    cost_center = fields.Char("CC")
    branch = fields.Char("Suc")
    business_unit = fields.Char("UN")
    doc_currency = fields.Char("MonDocto")
    taxable_amount = fields.Float("MontoAfecto")
    non_taxable_amount = fields.Float("MontoNoAfecto")
    vat_amount = fields.Float("MontoIGV")
    tax_type = fields.Char("MontoImp")
    total_amount = fields.Float("MontoTotal")
    surcharge_percentage = fields.Char("PorcRecargo")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ], string="Estado")
    collection_detail_flag = fields.Char("DetalleCobranzaFlag")
    payment_type = fields.Char("TipoPago")
    payment_currency = fields.Char("MonedaPago")
    payment_exchange_rate = fields.Char("TipoCambioPago")
    payment_amount = fields.Float("MontoPago")
    credit_card_code = fields.Char("TarjetaCreditoCodigo")
    reference_document = fields.Char("DocumentoReferencia")
    authorization_number = fields.Char("NumeroAutorizacion")
    tip_amount = fields.Float("MontoPropina")
    processed_flag = fields.Char("ProcesadoFlag")
    processed_date = fields.Datetime("FechaProcesado")
    process_state = fields.Char("EstadoProceso")
    settlement_number = fields.Char("NumeroLiquidacion")
    number_of_people = fields.Integer("NumeroPersonas")
    waiter = fields.Char("Mozo")
    cashier = fields.Many2one('res.users', string="Cajero")
    store_sale_flag = fields.Char("VentaTiendaFlag")
    other_income_flag = fields.Char("OtrosIngresosFlag")
    reservation_flag = fields.Char("ReservacionFlag")
    advance_number = fields.Char("NumeroAdelanto")

    def get_results_sql(self, session_id, start_date, end_date):
        # Consulta SQL con parámetros
        query = """
            SELECT 
                po.session_id, po.id AS "order_id", 
                TO_CHAR(ps.start_at AT TIME ZONE 'America/Bogota', 'YYYY-MM-DD"T"HH24:MI:SSOF:00') AS "FProceso",
                rc.name AS "CiaSocio", sw.code AS "CodAlm",
                CONCAT(sw.code, '#', po.id) AS "IdBach", 
                NULL AS "TDocto", NULL AS "NroDocto", 
                TO_CHAR(am.invoice_date_due AT TIME ZONE 'America/Bogota', 'YYYY-MM-DD"T"00:00:00-05:00') AS "FDocumento",
                rp.vat AS "ClienteRUC", rp.name AS "ClienteNombre", 
                CONCAT(rp.street) AS "ClienteDireccion", 
                NULL AS "CC", NULL AS "Suc", NULL AS "UN", 
                rcy.name AS "MonDocto", am.amount_total AS "MontoAfecto", 
                am.amount_untaxed AS "MontoNoAfecto", am.amount_tax AS "MontoIGV", 
                'E' AS "MontoImp", am.amount_total AS "MontoTotal", 
                'E' AS "PorcRecargo", am.payment_state AS "Estado", 
                NULL AS "DetalleCobranzaFlag", NULL AS "TipoPago", 
                NULL AS "MonedaPago", NULL AS "TipoCambioPago", 
                NULL AS "MontoPago", NULL AS "TarjetaCreditoCodigo", 
                NULL AS "DocumentoReferencia", NULL AS "NumeroAutorizacion", 
                NULL AS "MontoPropina", NULL AS "ProcesadoFlag", 
                NULL AS "FechaProcesado", NULL AS "EstadoProceso", 
                ps.name AS "NumeroLiquidacion", NULL AS "NumeroPersonas", 
                NULL AS "Mozo", ps.user_id AS "Cajero", 
                NULL AS "VentaTiendaFlag", NULL AS "OtrosIngresosFlag", 
                NULL AS "ReservacionFlag", NULL AS "NumeroAdelanto"
            FROM public.pos_order po
            INNER JOIN public.pos_session ps ON ps.id = po.session_id
            INNER JOIN public.res_company rc ON rc.id = po.company_id
            INNER JOIN public.stock_warehouse sw ON rc.id = sw.company_id
            INNER JOIN public.pos_payment pp ON po.id = pp.pos_order_id
            INNER JOIN public.account_move am ON am.id = pp.account_move_id
            INNER JOIN public.res_partner rp ON rp.id = po.partner_id
            INNER JOIN public.res_currency rcy ON am.currency_id = rcy.id
            WHERE po.session_id = %s
            AND po.date_order BETWEEN %s AND %s;
        """
        self.env.cr.execute(query, (session_id, start_date, end_date))
        return self.env.cr.fetchall()

    def get_results_orm(self, session_id, start_date, end_date):
        # Usar el ORM de Odoo para obtener resultados
        pos_orders = self.env['pos.order'].search([
            ('session_id', '=', session_id),
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date)
        ])

        result = []
        for po in pos_orders:
            try:
                session = po.session_id
                company = po.company_id
                warehouse = company.warehouse_id
                if not warehouse:
                    continue  # Skip if no warehouse found
                payments = po.payment_ids
                if not payments:
                    continue  # Skip if no payments found
                account_move = payments[0].account_move_id
                if not account_move:
                    continue  # Skip if no account move found
                partner = po.partner_id
                currency = account_move.currency_id if account_move else None

                # Construir los resultados como en la consulta SQL
                result.append({
                    'session_id': session.id,
                    'order_id': po.id,
                    'FProceso': session.start_at,
                    'CiaSocio': company.name,
                    'CodAlm': warehouse.code,
                    'IdBach': f'{warehouse.code}#{po.id}',
                    'TDocto': None,
                    'NroDocto': None,
                    'FDocumento': account_move.invoice_date_due if account_move else None,
                    'ClienteRUC': partner.vat,
                    'ClienteNombre': partner.name,
                    'ClienteDireccion': partner.street,
                    'CC': None,
                    'Suc': None,
                    'UN': None,
                    'MonDocto': currency.name if currency else None,
                    'MontoAfecto': account_move.amount_total if account_move else 0,
                    'MontoNoAfecto': account_move.amount_untaxed if account_move else 0,
                    'MontoIGV': account_move.amount_tax if account_move else 0,
                    'MontoImp': 'E',
                    'MontoTotal': account_move.amount_total if account_move else 0,
                    'PorcRecargo': 'E',
                    'Estado': account_move.payment_state if account_move else 'draft',
                    'DetalleCobranzaFlag': None,
                    'TipoPago': None,
                    'MonedaPago': None,
                    'TipoCambioPago': None,
                    'MontoPago': None,
                    'TarjetaCreditoCodigo': None,
                    'DocumentoReferencia': None,
                    'NumeroAutorizacion': None,
                    'MontoPropina': None,
                    'ProcesadoFlag': None,
                    'FechaProcesado': None,
                    'EstadoProceso': None,
                    'NumeroLiquidacion': session.name,
                    'NumeroPersonas': None,
                    'Mozo': None,
                    'Cajero': session.user_id.id,
                    'VentaTiendaFlag': None,
                    'OtrosIngresosFlag': None,
                    'ReservacionFlag': None,
                    'NumeroAdelanto': None
                })
            except Exception as e:
                _logger.error(f"Error processing order {po.id}: {str(e)}")
                continue

        return result

    def get_doc_issued_data(self, session_id, start_date, end_date, method='sql'):
        if not session_id or not start_date or not end_date:
            raise ValidationError("Session ID, start date and end date are required")

        # Elegir entre SQL o ORM
        if method == 'sql':
            return self.get_results_sql(session_id, start_date, end_date)
        elif method == 'orm':
            return self.get_results_orm(session_id, start_date, end_date)
        else:
            raise ValidationError("Método no reconocido. Use 'sql' o 'orm'.")
