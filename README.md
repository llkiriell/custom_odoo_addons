Repositorio que contiene aplicaciones o módulos de prueba de Odoo 16.

### Instaladores

- Python 3.10 ***(python-3.10.0-amd64)***
- PostgreSQL 14.16 ***(postgresql-14.16-1-windows-x64)***
- Microsoft C++ Build Tools 2022 ***(vs_BuildTools)***
- wkhtmltopdf ***(wkhtmltox-0.12.6-1.msvc2015-win64)***
- NodeJS 22.14 instalado con NVM 1.2.2 ***(nvm-windows)***

### Instalar/Actualizar dependencias que dan conflicto

```bash
python -m pip install --upgrade pip setuptools wheel
```

### **Crear entorno virtual antes de instalar dependencias**:

1. Crea un entorno virtual en la raíz del proyecto:
    
    ```bash
    python -m venv odooenv
    ```
    
2. Activar entorno:
    
    ```bash
    .\odooenv\Scripts\activate
    ```
    
3. Instala las dependencias:
    
    ```bash
    pip install -r requirements.txt
    ```
    

### Video de referencia

https://www.youtube.com/watch?v=MMKQ4qQwa1Q