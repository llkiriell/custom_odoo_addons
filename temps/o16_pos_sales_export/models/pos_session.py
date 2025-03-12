from odoo import models, tools, modules, fields, api,http
from odoo.http import request
import json
from io import BytesIO
import base64, os, io
import xml.etree.ElementTree as ET
import xml.dom.minidom
import zipfile
import logging

_logger = logging.getLogger(__name__)

class PosSession(models.Model):
    _inherit = 'pos.session'
    
    # Metodo general de descarga directa de archivos
    def action_download_archive(self):
        # Datos de la sesión a exportar
        session_data = [
            {
                "FProceso": "2024-02-26",
                "CiaSocio": "ABC Corp",
                "CodAlm": "A001",
                "IdBach": "12345",
                "TDocto": "Factura",
                "NroDocto": "F0001",
                "FDocumento": "2024-02-25",
                "ClienteRUC": "20123456789",
                "ClienteNombre": "Juan Pérez",
                "ClienteDireccion": "Av. Principal 123",
                "MontoTotal": "150.50"
            }
        ]

        # Genera el archivo adjunto Odoo
        # attachment = self.generate_json(session_data)
        # attachment = self.generate_xml('CabeceraDocumentosEmitidos.xml',session_data)
        attachment = self.generate_zip(session_data)

        # Devuelve la acción de descarga
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self'
        }

    # Metodo para crear un registro de archivo adjunto
    def create_attachment(self, file_name, file_content, mimetype):
        # Convertir a base64 si es necesario
        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")

        return self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(file_content),
            'mimetype': mimetype,
        })
    
    # Metodo para generar un archivo JSON
    def generate_json(self, data):
        # Convierte los datos a JSON
        json_data = json.dumps(data, default=str, indent=4)

        # Nombre del archivo
        file_name = f"ventas_session_{self.name}.json"

        return file_name, json_data 
    
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
    
    # Metodo para generar un archivo ZIP
    def generate_zip(self, data_array):
        # Generar JSON y XML
        json_name, json_content = self.generate_json(data_array)
        xml_name, xml_content = self.generate_xml('CabeceraDocumentosEmitidos.xml',data_array)

        # Buffer para el zip
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(json_name, json_content)
            zip_file.writestr(xml_name, xml_content)
        
        # Traer contenido del ZIP
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()

        # Nombre del archivo
        zip_name = f"ventas_session_{self.name}.zip"

        return self.create_attachment(zip_name, zip_content, "application/zip")

    # H - Metodo para descargar JSON
    def action_download_json(self):
        # Asegura tomar un solo elemento
        self.ensure_one()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/pos_session/download_zip/{self.id}',
            'target': 'new'
        }
    
    def action_message(self):
        # return self.action_download_json()
        return self.action_download_zip()

    # Metodo para generar un archivo ZIP
    def generate_zip2(self):
        # Identificador de la sesion
        session = request.env['pos.session'].sudo().browse(self.id)
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

        # Traer contenido del ZIP
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()

        # Nombre del archivo
        zip_name = f"session_{self.name}.zip"

        return self.create_attachment(zip_name, zip_content, "application/zip")

    # Metodo general de descarga directa de archivos
    def action_download_zip(self):
        # Asegura tomar un solo elemento
        self.ensure_one()

        try:
            # Asumiendo que tienes el attachment
            self.message_post(
                body=f"""Se descargó el archivo ZIP de la sesión {self.name}
                Fecha de descarga: {fields.Datetime.now()}
                Usuario: {self.env.user.name}""",
                message_type='notification',
                subtype_id=self.env.ref('mail.mt_note').id
            )
        except Exception as e:
            _logger.error(f"Error al registrar el mensaje en el chatter: {str(e)}")

        # Devuelve la acción de descarga
        return {
            'type': 'ir.actions.act_url',
            'url': f'/pos_session/download_zip/{self.id}',
            'target': 'new'
        }
