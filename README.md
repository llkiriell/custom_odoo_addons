Repositorio que contiene aplicaciones o módulos de prueba de Odoo 16.

# Instaladores utilizados

- Python 3.10 ***(python-3.10.0-amd64)***
- PostgreSQL 14.16 ***(postgresql-14.16-1-windows-x64)***
- Microsoft C++ Build Tools 2022 ***(vs_BuildTools)***
- wkhtmltopdf ***(wkhtmltox-0.12.6-1.msvc2015-win64)***
- NodeJS 22.14 instalado con NVM 1.2.2 ***(nvm-windows)***

# Videos de referencia

- https://www.youtube.com/watch?v=MMKQ4qQwa1Q

# Estructura de archivos
Aquí se representa una estructura de directorios y archivos para desarrollar los ejemplos:
```
<directorio>/
├── addons/
│   ├── o16_notes/
│   ├── ...
│   ├── ...
│   └── ...
└── projects/
    ├── odoo16/
    ├── odoo16_default.zip
    └── ...
```

## Descripción de las carpetas y archivos:

- `addons`: Esta carpeta contiene los módulos personalizados creados para Odoo 16. Los módulos en esta carpeta permiten extender y personalizar la funcionalidad de Odoo según las necesidades específicas del proyecto.

- `projects`: En esta carpeta se almacenan los proyectos basados en Odoo. Cada proyecto puede ser de otras versiones, en este caso la versión 16.

- `o16_notes`: Este es un módulo personalizado de ejemplo que está desarrollado para Odoo 16. Este módulo, al igual que otros en la carpeta addons, agrega características específicas que no están incluidas en la versión regular de Odoo.

- `odoo16`: Esta carpeta contiene una copia del código fuente de Odoo 16 obtenida directamente de su repositorio oficial de github. Es la base para todas las personalizaciones y módulos adicionales que se desarrollen y configuren para el entorno de la version 16.

- `odoo16_default.zip`: Este archivo contiene una copia descargada del proyecto de Odoo 16 desde su repositorio oficial en github. Se puede usar para restaurar el proyecto o iniciar uno nuevo de la versión 16.

# Instalación de entorno de desarrollo

- Instalar Python.
- Instalar wkhtmltopdf.
- Microsoft C++ Build Tools 2022.

## 1. Clonar el repositorio

Se clona el repositorio en una carpeta raíz de proyectos.

```bash
git clone -b 16.0 https://github.com/odoo/odoo.git odoo16
```

## 2. Instalar/Actualizar dependencias

Se actualizan algunas dependencias para evitar conflictos

```bash
python -m pip install --upgrade pip setuptools wheel
```

## 3. Instalar librería rtlcss con NPM

```bash
npm i -g rtlcss
```

## 4. Crear un usuario en PostgreSQL desde PgAdmin

Crear un usuario con todos los privilegios.

```
usr: odoo
pwd: odoo
```

## 5. Crear entorno virtual antes de instalar dependencias
Para no tener conflictos o errores al momento de instalar las dependencias de Odoo, se crea un entorno virtual de dependencias de python.

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
    

## 6. Generar un archivo de configuración
Es necesario generar un archivo de configuración `odoo.conf` para especificar las credenciales de PostgreSQL.

```bash
python .\odoo-bin -s
```

### 6.1. Modificar el archivo odoo.conf

```
[options]
addons_path = ...,d:\proyectos-aplicaciones\odoo\addons
...
db_host = 127.0.0.1
...
db_password = odoo
...
db_user = odoo
db_filter = v16.*
```

## 7. Ejecutar Odoo

```bash
python .\odoo-bin -c .\odoo.conf
```

## 8. Instalación en localhost:8069

Seguir el instalador rápido de Odoo, completar :

- Database Name (v16_test_1),
- Language (Spanish / Español) ,
- Country (Peru),
- Email (admin)
- Password (el que se elija).

# Activar modulos por defecto.
Se puede activar el módulo `Sales` o el módulo `Peru_Accounting(l10n_pe)`, pero este último se activa por defecto al activar el primero.