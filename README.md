# Sistema de Facturación y Presupuestos

**Autor:** Carlos Sánchez Román  
**Inicio del proyecto:** Julio 2024  
**Estado:** En desarrollo

## Descripción

Este proyecto es una plataforma integral para la creación y gestión de facturas y presupuestos. Diseñada con un enfoque en la facilidad de uso, permite almacenar información de clientes y productos, generar documentos personalizados, aplicar IVA, y gestionar facturas trimestrales de forma eficiente.

## Características principales

- **Gestión de productos**: Agregar, editar y eliminar productos con descripciones y precios.
- **Gestión de clientes**: Almacenar y actualizar información detallada de los clientes.
- **Creación de documentos**: Generar facturas y presupuestos, con opciones para aplicar IVA.
- **Informes trimestrales**: Generación de facturas trimestrales agrupadas.
- **Exportación a PDF**: Crear documentos en formato PDF con diseños claros y profesionales.
- **Filtros avanzados**: Buscar y gestionar documentos por cliente, tipo, mes o producto.

## Tecnologías utilizadas

- **Backend**: Python (SQLite para la base de datos)
- **Frontend**: Tkinter (interfaz gráfica de usuario)
- **Exportación de documentos**: FPDF para la generación de archivos PDF

## Estructura del proyecto

- **`app.py`**: Punto de entrada principal de la aplicación.
- **`database.py`**: Módulo de gestión de base de datos (creación y operaciones CRUD).
- **`models.py`**: Abstracciones y funciones de lógica empresarial.
- **`pdf_generator.py`**: Generación de documentos PDF.
- **`ui.py`**: Lógica de la interfaz de usuario.
- **`utils.py`**: Utilidades y funciones de apoyo.

## Instalación y configuración

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu_usuario/nombre_del_repositorio.git
   ```
2. Asegúrate de tener Python 3.8 o superior instalado.
3. Instala las dependencias requeridas:
   ```bash
   pip install -r requirements.txt
   ```
4. Ejecuta el archivo `app.py` para iniciar la aplicación:
   ```bash
   python app.py
   ```

## Uso

- **Productos**: Desde la pestaña correspondiente, agrega y gestiona productos para usar en facturas y presupuestos.
- **Clientes**: Almacena la información de tus clientes para una fácil selección al generar documentos.
- **Facturas y presupuestos**: Genera documentos personalizados con opción de aplicar IVA y exportarlos en PDF.
- **Facturas trimestrales**: Genera facturas agrupadas por trimestre y año.

## Contribuciones

Este proyecto está en desarrollo activo y cualquier sugerencia o contribución es bienvenida. Si deseas colaborar:

1. Haz un fork del repositorio.
2. Crea una rama para tu funcionalidad o corrección:
   ```bash
   git checkout -b nombre_de_tu_rama
   ```
3. Realiza tus cambios y envía un Pull Request.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

**Contacto**  
Carlos Sánchez Román  
Correo: [csroman.dev@gmail.com](mailto:csroman.dev@gmail.com)

