import json
import base64
from io import BytesIO
import base64, os, io
from datetime import datetime
from odoo import http, modules
from odoo.http import request, Response
import xml.etree.ElementTree as ET
import xml.dom.minidom
import zipfile
from pprint import pformat
import logging
from ..models.document_issued import DocumentIssued

_logger = logging.getLogger(__name__)

class PosSessionDownload(http.Controller):
    @http.route('/pos_session/download_json/<int:session_id>', type='http', auth='user', methods=['GET'])
    def download_json(self, session_id, **kwargs):
        # Identificador de la sesion
        session = request.env['pos.session'].sudo().browse(session_id)
        if not session.exists():
            return request.not_found()

        session_data = [{
            'id': session.id,
            'name': session.name,
            'start_at': session.start_at,
            'stop_at': session.stop_at,
            'user_id': session.user_id.name,
            'config_id': session.config_id.name,
            'state': session.state,
        }]

        # Conversion a json
        json_data = json.dumps(session_data, default=str, indent=4)

        # Nombre del archivo
        file_name = f"ventas_session_{session.name}.json"

        # Encabezado del response
        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Disposition', f'attachment; filename="{file_name}"')
        ]
        return request.make_response(json_data, headers=headers)

    @http.route('/pos_session/download_zip/<int:session_id>', type='http', auth='user', methods=['GET'])
    def generate_zip(self, session_id, **kwargs):
        # Identificador de la sesion
        session = request.env['pos.session'].sudo().browse(session_id)
        if not session.exists():
            return request.not_found()

        # Obtener y decodificar los parámetros JSON
        params_json = kwargs.get('params', '{}')
        try:
            params = json.loads(params_json)
            _logger.info('\n\n=== PARÁMETROS RECIBIDOS ===\n%s\n========================\n', 
                        pformat(params))
        except json.JSONDecodeError as e:
            _logger.error('Error al decodificar JSON: %s', str(e))
            params = {}

        # Extraer datos de los parámetros
        date_start = params.get('date_start')
        date_end = params.get('date_end')
        all_dates = params.get('all_dates', False)
        documentos_config = params.get('documentos', {})
        formato = params.get('formato', 'xml')
        envio_correo = params.get('envio_correo', {})


        # cabecera_documentos_emitidos = self.get_doc_issued_data(session_id, date_start, date_end)


        session_data = [{"FProceso": "2024-02-26"}]  # Datos por defecto en caso de error

        # Preparar e inicializa los documentos documentos para el ZIP
        documentos = []
        for nombre, incluir in documentos_config.items():
            if incluir:
                session_data = self.get_document_data(nombre, session_id, date_start, date_end)
                documentos.append({
                    'nombreArchivo': nombre,
                    'datos': session_data,
                })
        
        # Buffer para el zip
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in documentos:
                xml_name, xml_content = self.generate_xml(doc['nombreArchivo'], doc['datos'])
                zip_file.writestr(xml_name, xml_content)

        # Traer contenido del ZIP
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()

        # Obtener la fecha actual en formato YYYYMMDD
        fecha_actual = datetime.now().strftime('%Y%m%d')
        # Constante para el nombre del archivo
        codigo_constante = 'MUVESM200000234'
        # Nombre del archivo
        zip_name = f"{fecha_actual}-{codigo_constante}.zip"

        # Agregar mensaje al chatter
        try:
            session.message_post(
                body=f"""<b>Descarga de archivos de la sesión</b><br/>
                <ul>
                    <li><b>Nombre del archivo:</b> {zip_name}</li>
                    <li><b>Fecha de descarga:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><b>Usuario:</b> {request.env.user.name}</li>
                    <li><b>Documentos incluidos:</b> {', '.join([doc['nombreArchivo'] for doc in documentos])}</li>
                    <li><b>Rango de fechas:</b> {date_start or 'No especificado'} - {date_end or 'No especificado'}</li>
                </ul>""",
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        except Exception as e:
            _logger.error(f"Error al registrar el mensaje en el chatter: {str(e)}")

        headers = [
            ('Content-Type', 'application/zip'),
            ('Content-Disposition', f'attachment; filename="{zip_name}"')
        ]
        return request.make_response(zip_content, headers=headers)

    # Metodo para generar un archivo XML
    def generate_xml(self, file_name, data_array):
        # Ruta absoluta de la plantilla
        template_path = os.path.join(modules.get_module_path('o16_pos_sales_export'), 'data', 'templates', 'xml', file_name + '.xml')

        etiqueta_padre = file_name;

        # Verificación de archivo
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"La plantilla XML '{file_name}' no existe en la ruta especificada.")

        # Cargar la plantilla
        tree = ET.parse(template_path)
        root = tree.getroot()

        # Eliminar contenido
        for elem in root.findall(etiqueta_padre):
            root.remove(elem)

        # Agregar datos a la plantilla dinamicamente
        for data in data_array:
            cabecera_element = ET.Element(etiqueta_padre)
            # Cada clave corresponde a una etiqueta
            for key, value in data.items():
                sub_element = ET.Element(key)
                # Si el valor no es None, convertirlo a string y eliminar solo espacios en blanco al inicio y final
                if value is not None:
                    sub_element.text = str(value).lstrip(' ').rstrip(' ')
                cabecera_element.append(sub_element)
            # Agregar al XML
            root.append(cabecera_element)  

        # Codificacion de XML
        rough_string = ET.tostring(root, encoding='utf-8')
        reparsed = xml.dom.minidom.parseString(rough_string)
        xml_string = "\n".join([line for line in reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8").split("\n") if line.strip()])


        # print(xml_string)
        # Nombre del archivo
        # file_name = f"test_{file_name}.xml"

        # Obtener la fecha actual en formato YYYYMMDD
        fecha_actual = datetime.now().strftime('%Y%m%d')
        # Constante para el nombre del archivo
        codigo_constante = 'MUVESM200000234'
        # Generar el nombre del archivo con el nuevo patrón
        file_name = f"{fecha_actual}-{codigo_constante}-{file_name}.xml"

        return file_name, xml_string


    # ANCHOR Q2 - Documentos Emitidos
    def get_doc_issued_data(self, session_id, start_date, end_date):
        # Consulta SQL con parámetros
        query = """
            SELECT 
                -- po.session_id, po.id AS "order_id", 
                TO_CHAR(
                    (ps.start_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"HH24:MI:SS-05:00'
                ) AS "FProceso",
                rpc.company_registry as "CiaSocio",
                sw.code as "CodAlm",
                CONCAT(sw.code,'#',po.id) as "IdBach",
                lnldt.doc_code_prefix as "TDocto",
                am.name as "NroDocto",
                TO_CHAR(
                    (am.invoice_date_due AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"00:00:00-05:00'
                ) as "FDocumento",
                rp.vat as "ClienteRUC",
                rp.name as "ClienteNombre",
                CONCAT(rp.street) as "ClienteDireccion",
                null as "CC",
                null as "Suc",
                null as "UN",
                CASE
                    WHEN rcy.name = 'PEN' THEN 'LO'
                    WHEN rcy.name = 'USD' THEN 'EX'
                    ELSE rcy.name -- Para cualquier otro valor, se mantendrá el valor original
                END AS "MonDocto",
                am.amount_total as "MontoAfecto",
                am.amount_untaxed as "MontoNoAfecto",
                am.amount_tax as "MontoIGV",
                null as "MontoImp",
                am.amount_total as "MontoTotal",
                null as "PorcRecargo",
                am.payment_state as "Estado",
                null as "DetalleCobranzaFlag",
                null as "TipoPago",
                null as "MonedaPago",
                null as "TipoCambioPago",
                null as "MontoPago",
                null as "TarjetaCreditoCodigo",
                null as "DocumentoReferencia",
                null as "NumeroAutorizacion",
                null as "MontoPropina",
                null as "ProcesadoFlag",
                null as "FechaProcesado",
                null as "EstadoProceso",
                ps.name as "NumeroLiquidacion",
                null as "NumeroPersonas",
                null as "Mozo",
                he.barcode as "Cajero",
                null as "VentaTiendaFlag",
                null as "OtrosIngresosFlag",
                null as "ReservacionFlag",
                null as "NumeroAdelanto"
                from
                public.pos_order po
                inner join public.pos_session ps on ps.id = po.session_id
                inner join public.res_company rc on rc.id = po.company_id
                inner join public.stock_warehouse sw on rc.id = sw.company_id
                inner join public.pos_payment pp on po.id = pp.pos_order_id
                inner join public.account_move am on am.id = po.account_move
                inner join public.res_partner rp on rp.id = po.partner_id
                inner join public.res_partner rpc on rpc.id = rc.partner_id
                inner join public.res_currency rcy ON am.currency_id = rcy.id
                inner join public.hr_employee he on po.pos_user_id = he.user_id
                inner join public.l10n_latam_document_type lnldt on am.l10n_latam_document_type_id = lnldt.id
            WHERE po.session_id = %s
            AND TO_CHAR((po.date_order AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima','YYYY-MM-DD"T"HH24:MI:SS-05:00') BETWEEN %s AND %s;
        """
        request.env.cr.execute(query, (session_id, start_date, end_date))
        return request.env.cr.dictfetchall()
    
    # ANCHOR Q1 - Documento de cierre de caja
    def get_doc_cash_closing_data(self, session_id, start_date, end_date):
        # Consulta SQL con parámetros
        query = """
            SELECT
                TO_CHAR(
                    (ps.start_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"HH24:MI:SS-05:00'
                ) AS "FProceso",
                rpc.company_registry as "CiaSocio",
                sw.code as "AlmCod",
                CONCAT(sw.code,'#',po.id) as "IdBach",
                ps.name as "NumeroLiquidacion",
                TO_CHAR(
                    (ps.start_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"HH24:MI:SS-05:00'
                ) AS "FApertura",
                TO_CHAR(
                    (ps.stop_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"HH24:MI:SS-05:00'
                ) AS "FCierre",
                null as "RespNro",
                he.barcode as "Cajero",
                null as "FdoIniMonLoc",
                null as "FdoIniMonExt",
                null as "ProcFlag",
                null as "FProc",
                null as "EstProc"
            FROM
                public.pos_order po
            INNER JOIN public.pos_session ps ON ps.id = po.session_id
            INNER JOIN public.res_company rc ON rc.id = po.company_id
            INNER JOIN public.stock_warehouse sw ON rc.id = sw.company_id
            INNER JOIN public.res_partner rpc ON rpc.id = rc.partner_id
            INNER JOIN public.hr_employee he ON po.pos_user_id = he.user_id
            WHERE po.session_id = %s
            AND TO_CHAR((po.date_order AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima','YYYY-MM-DD"T"HH24:MI:SS-05:00') BETWEEN %s AND %s;
        """
        request.env.cr.execute(query, (session_id, start_date, end_date))
        return request.env.cr.dictfetchall()
    
    # ANCHOR Q3 - Documento detalle de cobranza
    def get_doc_collection_detail_data(self, session_id, start_date, end_date):
        # Consulta SQL con parámetros
        query = """
            SELECT
                TO_CHAR(
                    (ps.start_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"HH24:MI:SS-05:00'
                ) AS "FProceso",
                rpc.company_registry as "CiaSocio",
                sw.code as "AlmCod",
                CONCAT(sw.code,'#',po.id) as "IdBach",
                lnldt.doc_code_prefix as "TDocto",
                am.name as "NroDocto",
                po.sequence_number as "Sec",
                null as "TPago",
                CASE
                    WHEN rcy.name = 'PEN' THEN 'LO'
                    WHEN rcy.name = 'USD' THEN 'EX'
                    ELSE rcy.name -- Para cualquier otro valor, se mantendrá el valor original
                END AS "MonPago",
                po.currency_rate as "TCPago",
                po.amount_total as "MontoPago",
                '-' as "TarCredCod",
                '-' as "DoctoRef",
                null as "NroAutor",
                null as "Propina",
                null as "ProcFlag",
                null as "FProc",
                null as "EstProc",
                null as "NroAdel"
            FROM
                public.pos_order po
            INNER JOIN public.pos_session ps ON ps.id = po.session_id
            INNER JOIN public.res_company rc ON rc.id = po.company_id
            INNER JOIN public.stock_warehouse sw ON rc.id = sw.company_id
            INNER JOIN public.account_move am ON am.id = po.account_move
            INNER JOIN public.res_partner rpc ON rpc.id = rc.partner_id
            INNER JOIN public.res_currency rcy ON am.currency_id = rcy.id
            INNER JOIN public.l10n_latam_document_type lnldt ON am.l10n_latam_document_type_id = lnldt.id
            WHERE po.session_id = %s
            AND TO_CHAR((po.date_order AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima','YYYY-MM-DD"T"HH24:MI:SS-05:00') BETWEEN %s AND %s;
        """
        request.env.cr.execute(query, (session_id, start_date, end_date))
        return request.env.cr.dictfetchall()

    # ANCHOR Q4 - Documento facturacion
    def get_doc_factoring_data(self, session_id, start_date, end_date):
        # Consulta SQL con parámetros
        query = """
            SELECT
                TO_CHAR(
                    (ps.start_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"HH24:MI:SS-05:00'
                ) AS "FProceso",
                rpc.company_registry as "CiaSocio",
                sw.code as "AlmCod",
                CONCAT(sw.code, '#', po.id) as "IdBach",
                lnldt.doc_code_prefix as "TDocto",
                am.name as "NroDocto",
                po.sequence_number as "Sec",
                CASE
                    WHEN pt.detailed_type = 'consu' THEN 'CM'
                    WHEN pt.detailed_type = 'service' THEN 'SE'
                    ELSE pt.detailed_type
                END AS "TDet",
                pt.default_code as "ItemCodigo",
                pol.qty as "Cant",
                null as "CVta",
                pol.pe_affectation_code as "IGVExon",
                (price_subtotal / pol.qty) as "PUnitario",
                pol.price_subtotal as "PrecioTotal",
                null as "ProcFlag",
                null as "FProc",
                null as "EstProc",
                TO_CHAR(
                    (pol.create_date AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"HH24:MI:SS-05:00'
                ) AS "HComand",
                null as "OrigComand",
                pol.price_unit as "PrecioUnitarioFinal",
                pol.price_subtotal_incl as "PrecioTotalFinal",
                lnldt.doc_code_prefix as "DoctoRelTDocto",
                am.name as "DoctoRelNroDocto",
                null as "ValeNro",
                null as "Notas"
            FROM
                public.pos_order po
            INNER JOIN public.pos_session ps ON ps.id = po.session_id
            INNER JOIN public.res_company rc ON rc.id = po.company_id
            INNER JOIN public.stock_warehouse sw ON rc.id = sw.company_id
            INNER JOIN public.account_move am ON am.id = po.account_move
            INNER JOIN public.res_partner rpc ON rpc.id = rc.partner_id
            INNER JOIN public.res_currency rcy ON am.currency_id = rcy.id
            INNER JOIN public.l10n_latam_document_type lnldt ON am.l10n_latam_document_type_id = lnldt.id
            INNER JOIN public.pos_order_line pol ON po.id = pol.order_id
            INNER JOIN public.product_product ppd ON ppd.id = pol.product_id
            INNER JOIN public.product_template pt ON pt.id = ppd.product_tmpl_id
            WHERE po.session_id = %s
            AND TO_CHAR((po.date_order AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima','YYYY-MM-DD"T"HH24:MI:SS-05:00') BETWEEN %s AND %s;
        """
        request.env.cr.execute(query, (session_id, start_date, end_date))
        return request.env.cr.dictfetchall()

    # ANCHOR Q5 - Documento Inventario
    def get_doc_inventory_data(self, session_id, start_date, end_date):
        # Consulta SQL con parámetros
        query = """
            SELECT
                TO_CHAR(
                    (ps.start_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima', 
                    'YYYY-MM-DD"T"HH24:MI:SS-05:00'
                ) AS "FProceso",
                rpc.company_registry as "CiaSocio",
                sw.code as "AlmCod",
                CONCAT(sw.code, '#', po.id) as "IdBach",
                lnldt.doc_code_prefix as "TDocto",
                am.name as "NroDocto",
                po.sequence_number as "Sec",
                null as "Linea",
                null as "TDet",
                pt.default_code  as "ItemCodigo",
                pol.qty as "Cant",
                null as "CVta",
                null as "IGVExon",
                null as "PUnitario",
                null as "PTotal",
                null as "ProcFlag",
                null as "FProc",
                null as "EstProc",
                null as "Estado",
                null as "Notas"
            FROM
                public.pos_order po
            INNER JOIN public.pos_session ps ON ps.id = po.session_id
            INNER JOIN public.res_company rc ON rc.id = po.company_id
            INNER JOIN public.stock_warehouse sw ON rc.id = sw.company_id
            INNER JOIN public.account_move am ON am.id = po.account_move
            INNER JOIN public.res_partner rpc ON rpc.id = rc.partner_id
            INNER JOIN public.l10n_latam_document_type lnldt ON am.l10n_latam_document_type_id = lnldt.id
            INNER JOIN public.pos_order_line pol ON po.id = pol.order_id
            INNER JOIN public.product_product ppd ON ppd.id = pol.product_id
            INNER JOIN public.product_template pt ON pt.id = ppd.product_tmpl_id
            WHERE po.session_id = %s
            AND TO_CHAR((po.date_order AT TIME ZONE 'UTC') AT TIME ZONE 'America/Lima','YYYY-MM-DD"T"HH24:MI:SS-05:00') BETWEEN %s AND %s;
        """
        request.env.cr.execute(query, (session_id, start_date, end_date))
        return request.env.cr.dictfetchall()


    def get_document_data(self, name, session_id, date_start, date_end):
        # Mapeo de nombres de documentos a métodos
        document_methods = {
            'CabeceraDocumentosEmitidos': self.get_doc_issued_data,
            'CierreCaja': self.get_doc_cash_closing_data,
            'DetalleDocumentosFacturacion': self.get_doc_factoring_data,
            'DetalleDocumentosInventario': self.get_doc_inventory_data,
            'DetalleDocumentosCobranza': self.get_doc_collection_detail_data
        }

        # Obtener el método correspondiente al documento
        method = document_methods.get(name)
        if method:
            result = method(session_id, date_start, date_end)
            return result if result else []
        
        return []  # Retornar lista vacía si el documento no está en el mapeo