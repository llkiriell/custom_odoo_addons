from odoo import models, tools, modules, fields, api
import json
from io import BytesIO
import base64, os, io
import xml.etree.ElementTree as ET
import xml.dom.minidom
import zipfile

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
        template_path = os.path.join(modules.get_module_path('o16_pos_sales_export_pre'), 'data', 'templates', 'xml', file_name)

        # Verificación de archivo
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"La plantilla XML '{file_name}' no existe en la ruta especificada.")

        # Cargar la plantilla
        tree = ET.parse(template_path)
        root = tree.getroot()

        # Eliminar contenido
        for elem in root.findall("CabeceraDocumentosEmitidos"):
            root.remove(elem)

        # Agregar datos a la plantilla dinamicamente
        for data in data_array:
            cabecera_element = ET.Element("CabeceraDocumentosEmitidos")
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
        xml_string = reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

        # print(xml_string)
        # Nombre del archivo
        file_name = f"ventas_session_{self.name}.xml"

        return file_name, xml_string

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
        # Datos de la sesion POS
        session_data = [
            {
                'id': self.id,
                'name': self.name,
                'start_at': self.start_at,
                'stop_at': self.stop_at,
                'user_id': self.user_id.name,
                'config_id': self.config_id.name,
                'state': self.state,
            }
        ]

        # Datos a json
        json_data = json.dumps(session_data, default=str, indent=4)

        # Nombre del archivo
        file_name = f"ventas_session_{self.name}.json"

        # Archivo adjunto
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(json_data.encode('utf-8')),
            'mimetype': 'application/json',
        })

        # Devuelve una acción de descarga
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self'
        }
