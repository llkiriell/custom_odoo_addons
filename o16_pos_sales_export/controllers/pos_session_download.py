import json
import base64
from io import BytesIO
import base64, os, io
from odoo import http, modules
from odoo.http import request, Response
import xml.etree.ElementTree as ET
import xml.dom.minidom
import zipfile

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

        session_data = [{"FProceso": "2024-02-26"}]

        documentos =[
            {
                'nombreArchivo':'CabeceraDocumentosEmitidos',
                'datos': session_data,
            },
            {
                'nombreArchivo':'CierreCaja',
                'datos': session_data,
            },
            {
                'nombreArchivo':'DetalleDocumentosFacturacion',
                'datos': session_data,
            },
            {
                'nombreArchivo':'DetalleDocumentosInventario',
                'datos': session_data,
            },
            {
                'nombreArchivo':'DetalleDocumentosCobranza',
                'datos': session_data,
            },
        ]
        
        # Buffer para el zip
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in documentos:
                xml_name, xml_content = self.generate_xml(doc['nombreArchivo'],doc['datos'])
                zip_file.writestr(xml_name, xml_content)


        # Generar JSON y XML
        # json_name, json_content = self.generate_json(data_array)
        # xml_name, xml_content = self.generate_xml('CabeceraDocumentosEmitidos.xml',data_array)
        
        # Traer contenido del ZIP
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()

        # Nombre del archivo
        zip_name = f"session_{session_id}.zip"

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
                sub_element.text = str(value)
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

        return f"test_{file_name}.xml", xml_string
