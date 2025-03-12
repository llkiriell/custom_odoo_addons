from odoo import models, fields
from odoo.exceptions import ValidationError
from datetime import datetime

class DocumentIssued(models.Model):
    _name = 'document.issued'
    _auto = False  # No es una tabla fisica

    # Definir los campos como en la consulta SQL
    session_id = fields.Many2one('pos.session', string="Session")
    order_id = fields.Many2one('pos.order', string="Order")
    fproceso = fields.Datetime("FProceso")
    cia_socio = fields.Char("CiaSocio")
    cod_alm = fields.Char("CodAlm")
    id_bach = fields.Char("IdBach")
    tdcto = fields.Char("TDocto")
    nro_docto = fields.Char("NroDocto")
    fdocumento = fields.Datetime("FDocumento")
    cliente_ruc = fields.Char("ClienteRUC")
    cliente_nombre = fields.Char("ClienteNombre")
    cliente_direccion = fields.Char("ClienteDireccion")
    cc = fields.Char("CC")
    suc = fields.Char("Suc")
    un = fields.Char("UN")
    mon_docto = fields.Char("MonDocto")
    monto_afecto = fields.Float("MontoAfecto")
    monto_no_afecto = fields.Float("MontoNoAfecto")
    monto_igv = fields.Float("MontoIGV")
    monto_imp = fields.Char("MontoImp")
    monto_total = fields.Float("MontoTotal")
    porc_recargo = fields.Char("PorcRecargo")
    estado = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ], string="Estado")
    detalle_cobranza_flag = fields.Char("DetalleCobranzaFlag")
    tipo_pago = fields.Char("TipoPago")
    moneda_pago = fields.Char("MonedaPago")
    tipo_cambio_pago = fields.Char("TipoCambioPago")
    monto_pago = fields.Float("MontoPago")
    tarjeta_credito_codigo = fields.Char("TarjetaCreditoCodigo")
    documento_referencia = fields.Char("DocumentoReferencia")
    numero_autorizacion = fields.Char("NumeroAutorizacion")
    monto_propina = fields.Float("MontoPropina")
    procesado_flag = fields.Char("ProcesadoFlag")
    fecha_procesado = fields.Datetime("FechaProcesado")
    estado_proceso = fields.Char("EstadoProceso")
    numero_liquidacion = fields.Char("NumeroLiquidacion")
    numero_personas = fields.Integer("NumeroPersonas")
    mozo = fields.Char("Mozo")
    cajero = fields.Many2one('res.users', string="Cajero")
    venta_tienda_flag = fields.Char("VentaTiendaFlag")
    otros_ingresos_flag = fields.Char("OtrosIngresosFlag")
    reservacion_flag = fields.Char("ReservacionFlag")
    numero_adelanto = fields.Char("NumeroAdelanto")

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
                '0' AS "CC", '0' AS "Suc", '0' AS "UN", 
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

        resultados = []
        for po in pos_orders:
            session = po.session_id
            company = po.company_id
            warehouse = company.warehouse_id
            payments = po.payment_ids
            account_move = payments[0].account_move_id if payments else None
            partner = po.partner_id
            currency = account_move.currency_id if account_move else None

            # Construir los resultados como en la consulta SQL
            resultados.append({
                'session_id': session.id,
                'order_id': po.id,
                'fproceso': session.start_at,
                'cia_socio': company.name,
                'cod_alm': warehouse.code,
                'id_bach': f'{warehouse.code}#{po.id}',
                'tdcto': None,
                'nro_docto': None,
                'fdocumento': account_move.invoice_date_due if account_move else None,
                'cliente_ruc': partner.vat,
                'cliente_nombre': partner.name,
                'cliente_direccion': partner.street,
                'cc': '0',
                'suc': '0',
                'un': '0',
                'mon_docto': currency.name if currency else None,
                'monto_afecto': account_move.amount_total if account_move else 0,
                'monto_no_afecto': account_move.amount_untaxed if account_move else 0,
                'monto_igv': account_move.amount_tax if account_move else 0,
                'monto_imp': 'E',
                'monto_total': account_move.amount_total if account_move else 0,
                'porc_recargo': 'E',
                'estado': account_move.payment_state if account_move else 'draft',
                'detalle_cobranza_flag': None,
                'tipo_pago': None,
                'moneda_pago': None,
                'tipo_cambio_pago': None,
                'monto_pago': None,
                'tarjeta_credito_codigo': None,
                'documento_referencia': None,
                'numero_autorizacion': None,
                'monto_propina': None,
                'procesado_flag': None,
                'fecha_procesado': None,
                'estado_proceso': None,
                'numero_liquidacion': session.name,
                'numero_personas': None,
                'mozo': None,
                'cajero': session.user_id.id,
                'venta_tienda_flag': None,
                'otros_ingresos_flag': None,
                'reservacion_flag': None,
                'numero_adelanto': None
            })

        return resultados

    def get_doc_issued_data(self, session_id, start_date, end_date, method='sql'):
        # Elegir entre SQL o ORM
        if method == 'sql':
            return self.get_results_sql(session_id, start_date, end_date)
        elif method == 'orm':
            return self.obtener_resultados_orm(session_id, start_date, end_date)
        else:
            raise ValidationError("Método no reconocido. Use 'sql' o 'orm'.")
