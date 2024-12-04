import os
from fpdf import FPDF, XPos, YPos
from datetime import datetime
from database import cursor, conn, insert_invoice, insert_budget

class RoundedPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        if self.doc_type == 'Presupuesto':
            self.set_y(-10)
            self.set_font('DejaVu', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, 'Fecha de vencimiento: 15 días a partir de la fecha de emisión', 0, 0, 'C')

    def rounded_rect(self, x, y, w, h, r, style=''):
        k = self.k
        hp = self.h
        if style == 'F':
            op = 'f'
        elif style == 'FD' or style == 'DF':
            op = 'B'
        else:
            op = 'S'
        MyArc = 4 / 3 * (2**0.5 - 1)
        self._out('%.2f %.2f m' % ((x + r) * k, (hp - y) * k))
        self._out('%.2f %.2f l' % ((x + w - r) * k, (hp - y) * k))
        self._out('%.2f %.2f %.2f %.2f %.2f %.2f c' % (
            (x + w - r + r * MyArc) * k, (hp - y) * k,
            (x + w) * k, (hp - (y + r - r * MyArc)) * k,
            (x + w) * k, (hp - (y + r)) * k))
        self._out('%.2f %.2f l' % ((x + w) * k, (hp - (y + h - r)) * k))
        self._out('%.2f %.2f %.2f %.2f %.2f %.2f c' % (
            (x + w) * k, (hp - (y + h - r + r * MyArc)) * k,
            (x + w - r + r * MyArc) * k, (hp - (y + h)) * k,
            (x + w - r) * k, (hp - (y + h)) * k))
        self._out('%.2f %.2f l' % ((x + r) * k, (hp - (y + h)) * k))
        self._out('%.2f %.2f %.2f %.2f %.2f %.2f c' % (
            (x + r - r * MyArc) * k, (hp - (y + h)) * k,
            (x) * k, (hp - (y + h - r + r * MyArc)) * k,
            (x) * k, (hp - (y + h - r)) * k))
        self._out('%.2f %.2f l' % ((x) * k, (hp - (y + r)) * k))
        self._out('%.2f %.2f %.2f %.2f %.2f %.2f c' % (
            (x) * k, (hp - (y + r - r * MyArc)) * k,
            (x + r - r * MyArc) * k, (hp - y) * k,
            (x + r) * k, (hp - y) * k))
        self._out(op)

def add_page_with_header_footer(pdf):
    pdf.add_page()
    pdf.set_font('DejaVu', 'I', 10)
    pdf_width = 210
    text = f'Página {pdf.page_no()}'
    text_width = pdf.get_string_width(text)
    rect_x = pdf_width - 20 - 10
    pdf.set_xy(rect_x + (20 - text_width) / 2, pdf.get_y() + 2)
    pdf.cell(0, 10, text, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
    pdf.ln(10)
    
    # Repetir encabezados de la tabla combinada
    pdf.set_font('DejaVu', 'B', 10)
    margin_left = 10
    table_width = pdf_width - 2 * margin_left
    pdf.set_x(margin_left)
    pdf.cell(table_width * 0.55, 10, 'Producto y Descripción', 1, align='C')  # Columna combinada
    pdf.cell(table_width * 0.15, 10, 'Cantidad', 1, align='C')
    pdf.cell(table_width * 0.15, 10, 'Base', 1, align='C')
    pdf.cell(table_width * 0.15, 10, 'Total', 1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('DejaVu', '', 10)

def create_document(client_id, items, payment_method, doc_type, apply_iva=False, doc_id=None):
    base_total = sum(item['quantity'] * item['price'] for item in items)
    iva_amount = 0
    if apply_iva:
        iva_amount = base_total * 0.21
    total = base_total + iva_amount
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    pdf = RoundedPDF()
    pdf.doc_type = doc_type

    # Configuración de fuentes
    font_path = os.path.join('FONTS', 'DejaVuSans.ttf')
    bold_font_path = os.path.join('FONTS', 'DejaVuSans-Bold.ttf')
    italic_font_path = os.path.join('FONTS', 'DejaVuSans-Oblique.ttf')
    bold_italic_font_path = os.path.join('FONTS', 'DejaVuSans-BoldOblique.ttf')

    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.add_font('DejaVu', 'B', bold_font_path, uni=True)
    pdf.add_font('DejaVu', 'I', italic_font_path, uni=True)
    pdf.add_font('DejaVu', 'BI', bold_italic_font_path, uni=True)

    pdf.add_page()

    # Agregar logo
    logo_path = os.path.join('IMG', 'Logo_Sanchez_Luna.png')
    if os.path.exists(logo_path):
        pdf.image(logo_path, 10, 10, 33)

    pdf.set_xy(10, 50)

    # Información de la empresa
    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(0, 10, 'SANCHEZ LUNA SERVICIOS INTEGRALES S.L', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

    pdf.set_font('DejaVu', '', 12)
    pdf.cell(0, 10, 'www.sanchezlunaserviciosintegrales.com', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    pdf.cell(0, 10, 'sanchezlunaservicios.i.sl@gmail.com', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    pdf.cell(0, 10, '622 438 603', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    if apply_iva:
        pdf.cell(0, 10, 'CIF: B55457287', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

    pdf.ln(20)

    # Título del documento
    pdf.set_font('DejaVu', 'B', 30)
    pdf.set_xy(140, 10)
    pdf.cell(0, 10, doc_type.upper(), align='R')

    # Datos del cliente
    pdf.set_font('DejaVu', 'B', 12)
    pdf.rounded_rect(140, 30, 60, 65, 3, 'D')
    pdf.set_xy(140, 30)
    pdf.cell(0, 10, 'Datos del cliente', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font('DejaVu', '', 10)
    pdf.set_x(140)
    cursor.execute('SELECT name, email, address, phone, dni FROM clients WHERE id = ?', (client_id,))
    client = cursor.fetchone()
    pdf.multi_cell(0, 8, f'{client[0]}', align='L')
    pdf.set_x(140)
    pdf.multi_cell(0, 8, f'{client[2]}', align='L')
    pdf.set_x(140)
    pdf.multi_cell(0, 8, f'{client[3]}', align='L')
    pdf.set_x(140)
    pdf.multi_cell(0, 8, f'{client[1]}', align='L')
    pdf.set_x(140)
    pdf.multi_cell(0, 8, f'DNI: {client[4]}', align='L')

    pdf.ln(10)

    # Pie de página con número de página
    pdf.set_font('DejaVu', 'I', 10)
    pdf_width = 210
    text = f'Página {pdf.page_no()}'
    text_width = pdf.get_string_width(text)
    rect_x = pdf_width - 20 - 10
    pdf.set_y(pdf.get_y() + 10)
    pdf.set_xy(rect_x + (20 - text_width) / 2, pdf.get_y() + 2)
    pdf.cell(0, 10, text, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')

    pdf.ln(10)

    # Información del documento
    pdf.set_font('DejaVu', 'B', 12)
    pdf.rounded_rect(10, pdf.get_y(), 190, 20, 3, 'D')
    pdf.cell(0, 10, f'{doc_type.upper()} Nº: {doc_id}', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f'Fecha: {date.split(" ")[0]}', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)

    # Encabezados de la tabla de detalles del producto
    pdf.set_font('DejaVu', 'B', 10)

    margin_left = 10
    pdf_width = 210
    table_width = pdf_width - 2 * margin_left

    pdf.set_x(margin_left)
    pdf.cell(table_width * 0.55, 10, 'Producto y Descripción', 1, align='C')
    pdf.cell(table_width * 0.15, 10, 'Cantidad', 1, align='C')     # Ancho incrementado
    pdf.cell(table_width * 0.15, 10, 'Base', 1, align='C')
    pdf.cell(table_width * 0.15, 10, 'Total', 1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font('DejaVu', '', 10)
    line_height = pdf.font_size * 2

    for item in items:
        cursor.execute('SELECT name, description FROM products WHERE id = ?', (item['product_id'],))
        product = cursor.fetchone()

        product_name = product[0]
        description = product[1]

        # Combinar Producto y Descripción en una sola cadena
        combined_text = f"{product_name} {description}"  # Puedes cambiar el separador si lo prefieres

        # Calcular líneas necesarias para la columna combinada
        combined_lines = pdf.multi_cell(table_width * 0.55, line_height, combined_text, border=0, align='L', split_only=True)

        # Altura máxima de la fila
        max_lines = len(combined_lines)
        max_line_height = max_lines * line_height

        # Añadir nueva página si es necesario
        if pdf.get_y() + max_line_height > pdf.h - 60:
            add_page_with_header_footer(pdf)
            # Repetir encabezados
            pdf.set_font('DejaVu', 'B', 10)
            pdf.set_x(margin_left)
            pdf.cell(table_width * 0.55, 10, 'Producto y Descripción', 1, align='C')  # Columna combinada
            pdf.cell(table_width * 0.15, 10, 'Cantidad', 1, align='C')
            pdf.cell(table_width * 0.15, 10, 'Base', 1, align='C')
            pdf.cell(table_width * 0.15, 10, 'Total', 1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font('DejaVu', '', 10)

        y_start = pdf.get_y()

        # Celda combinada de Producto y Descripción
        pdf.rect(margin_left, y_start, table_width * 0.55, max_line_height)
        pdf.set_xy(margin_left, y_start)
        pdf.multi_cell(table_width * 0.55, line_height, combined_text, border=0)

        # Celdas de cantidad, base y total
        pdf.set_xy(margin_left + table_width * 0.55, y_start)
        pdf.cell(table_width * 0.15, max_line_height, str(item['quantity']), 1, align='C')
        pdf.cell(table_width * 0.15, max_line_height, f"{item['price']:.2f} €", 1, align='C')
        pdf.cell(table_width * 0.15, max_line_height, f"{item['quantity'] * item['price']:.2f} €", 1, align='C')

        pdf.set_y(y_start + max_line_height)

    pdf.ln(10)

    # Resumen y totales
    pdf.set_y(-60)
    pdf.set_font('DejaVu', 'B', 10)
    pdf.set_x(margin_left)
    pdf.rounded_rect(margin_left, pdf.get_y(), table_width, 40, 3, 'D')

    # Método de pago
    pdf.cell(table_width * 0.25, 10, 'Método de pago:', align='L', border=0)
    pdf.cell(table_width * 0.75, 10, payment_method, align='L', border=0, new_x=XPos.LMARGIN)

    if payment_method == 'Transferencia':
        pdf.ln(10)
        pdf.set_x(margin_left)
        pdf.cell(table_width * 0.25, 10, 'Número de cuenta:', align='L', border=0)
        pdf.cell(table_width * 0.75, 10, 'ES6701826101810201629602', align='L', border=0, new_x=XPos.LMARGIN)

    # Totales
    pdf.set_xy(margin_left + table_width * 0.65, pdf.get_y() - 10 if payment_method == 'Transferencia' else pdf.get_y() + 10)
    pdf.cell(table_width * 0.15, 10, 'Base Imponible', align='R', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(table_width * 0.20, 10, f"{base_total:.2f} €", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if apply_iva:
        pdf.set_x(margin_left + table_width * 0.65)
        pdf.cell(table_width * 0.15, 10, 'IVA (21%)', align='R', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(table_width * 0.20, 10, f"{iva_amount:.2f} €", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(margin_left + table_width * 0.65)
    pdf.cell(table_width * 0.15, 10, 'Total', align='R', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(table_width * 0.20, 10, f"{total:.2f} €", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return pdf, base_total, iva_amount, total

def insert_document(client_id, date, total, payment_method, items, apply_iva, doc_type):
    if doc_type == 'Factura':
        return insert_invoice(client_id, date, total, payment_method, items, apply_iva)
    else:
        return insert_budget(client_id, date, total, payment_method, items, apply_iva)

def create_documents_for_quarter(quarter, year):
    months = {
        "1": ("01", "02", "03"),
        "2": ("04", "05", "06"),
        "3": ("07", "08", "09"),
        "4": ("10", "11", "12")
    }

    start_date = f"{year}-{months[quarter][0]}-01"
    end_date = f"{year}-{months[quarter][2]}-31"

    cursor.execute('''
        SELECT id, client_id, date, total, payment_method
        FROM invoices
        WHERE date BETWEEN ? AND ?
    ''', (start_date, end_date))

    invoices = cursor.fetchall()
    pdfs = []

    for invoice in invoices:
        invoice_id, client_id, date, total, payment_method = invoice
        cursor.execute('''
            SELECT product_id, quantity, price
            FROM invoice_items
            WHERE invoice_id = ?
        ''', (invoice_id,))
        items = cursor.fetchall()
        items = [{'product_id': item[0], 'quantity': item[1], 'price': item[2]} for item in items]

        pdf, _ = create_document(client_id, items, payment_method, 'Factura')
        pdfs.append((pdf, f"Factura_{invoice_id}.pdf"))

    return pdfs

def create_document_from_existing(doc_id, client_id, date, total, payment_method, items, doc_type, apply_iva):
    base_total = sum(item['quantity'] * item['price'] for item in items)
    iva_amount = 0
    if apply_iva:
        iva_amount = base_total * 0.21
    total_calculated = base_total + iva_amount

    pdf = RoundedPDF()
    pdf.doc_type = doc_type

    # Configuración de fuentes
    font_path = os.path.join('FONTS', 'DejaVuSans.ttf')
    bold_font_path = os.path.join('FONTS', 'DejaVuSans-Bold.ttf')
    italic_font_path = os.path.join('FONTS', 'DejaVuSans-Oblique.ttf')
    bold_italic_font_path = os.path.join('FONTS', 'DejaVuSans-BoldOblique.ttf')

    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.add_font('DejaVu', 'B', bold_font_path, uni=True)
    pdf.add_font('DejaVu', 'I', italic_font_path, uni=True)
    pdf.add_font('DejaVu', 'BI', bold_italic_font_path, uni=True)

    pdf.add_page()

    # Agregar logo
    logo_path = os.path.join('IMG', 'Logo_Sanchez_Luna.png')
    if os.path.exists(logo_path):
        pdf.image(logo_path, 10, 10, 33)

    pdf.set_xy(10, 50)

    # Información de la empresa
    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(0, 10, 'SANCHEZ LUNA SERVICIOS INTEGRALES S.L', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

    pdf.set_font('DejaVu', '', 12)
    pdf.cell(0, 10, 'www.sanchezlunaserviciosintegrales.com', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    pdf.cell(0, 10, 'sanchezlunaservicios.i.sl@gmail.com', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    pdf.cell(0, 10, '622 438 603', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    if apply_iva:
        pdf.cell(0, 10, 'CIF: B55457287', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

    pdf.ln(20)

    # Título del documento
    pdf.set_font('DejaVu', 'B', 30)
    pdf.set_xy(140, 10)
    pdf.cell(0, 10, doc_type.upper(), align='R')

    # Datos del cliente
    pdf.set_font('DejaVu', 'B', 12)
    pdf.rounded_rect(140, 30, 60, 65, 3, 'D')
    pdf.set_xy(140, 30)
    pdf.cell(0, 10, 'Datos del cliente', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font('DejaVu', '', 10)
    pdf.set_x(140)
    cursor.execute('SELECT name, email, address, phone, dni FROM clients WHERE id = ?', (client_id,))
    client = cursor.fetchone()
    pdf.multi_cell(0, 8, f'{client[0]}', align='L')
    pdf.set_x(140)
    pdf.multi_cell(0, 8, f'{client[2]}', align='L')
    pdf.set_x(140)
    pdf.multi_cell(0, 8, f'{client[3]}', align='L')
    pdf.set_x(140)
    pdf.multi_cell(0, 8, f'{client[1]}', align='L')
    pdf.set_x(140)
    pdf.multi_cell(0, 8, f'DNI: {client[4]}', align='L')

    pdf.ln(10)

    # Pie de página con número de página
    pdf.set_font('DejaVu', 'I', 10)
    pdf_width = 210
    text = f'Página {pdf.page_no()}'
    text_width = pdf.get_string_width(text)
    rect_x = pdf_width - 20 - 10
    pdf.set_y(pdf.get_y() + 10)
    pdf.set_xy(rect_x + (20 - text_width) / 2, pdf.get_y() + 2)
    pdf.cell(0, 10, text, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')

    pdf.ln(10)

    # Información del documento
    pdf.set_font('DejaVu', 'B', 12)
    pdf.rounded_rect(10, pdf.get_y(), 190, 20, 3, 'D')
    pdf.cell(0, 10, f'{doc_type.upper()} Nº: {doc_id}', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f'Fecha: {date.split(" ")[0]}', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)

    # Encabezados de la tabla de detalles del producto
    pdf.set_font('DejaVu', 'B', 10)

    margin_left = 10
    table_width = pdf_width - 2 * margin_left

    pdf.set_x(margin_left)
    pdf.cell(table_width * 0.55, 10, 'Producto y Descripción', 1, align='C')
    pdf.cell(table_width * 0.15, 10, 'Cantidad', 1, align='C')     # Ancho ajustado
    pdf.cell(table_width * 0.15, 10, 'Base', 1, align='C')
    pdf.cell(table_width * 0.15, 10, 'Total', 1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font('DejaVu', '', 10)
    line_height = pdf.font_size * 2

    for item in items:
        cursor.execute('SELECT name, description FROM products WHERE id = ?', (item['product_id'],))
        product = cursor.fetchone()

        product_name = product[0]
        description = product[1]

        # Combinar Producto y Descripción en una sola cadena
        combined_text = f"{product_name} {description}"  # Puedes cambiar el separador si lo prefieres

        # Calcular líneas necesarias para la columna combinada
        combined_lines = pdf.multi_cell(table_width * 0.55, line_height, combined_text, border=0, align='L', split_only=True)

        # Altura máxima de la fila
        max_lines = len(combined_lines)
        max_line_height = max_lines * line_height

        # Añadir nueva página si es necesario
        if pdf.get_y() + max_line_height > pdf.h - 60:
            add_page_with_header_footer(pdf)
            # Repetir encabezados
            pdf.set_font('DejaVu', 'B', 10)
            pdf.set_x(margin_left)
            pdf.cell(table_width * 0.55, 10, 'Producto y Descripción', 1, align='C')  # Columna combinada
            pdf.cell(table_width * 0.15, 10, 'Cantidad', 1, align='C')
            pdf.cell(table_width * 0.15, 10, 'Base', 1, align='C')
            pdf.cell(table_width * 0.15, 10, 'Total', 1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font('DejaVu', '', 10)

        y_start = pdf.get_y()

        # Celda combinada de Producto y Descripción
        pdf.rect(margin_left, y_start, table_width * 0.55, max_line_height)
        pdf.set_xy(margin_left, y_start)
        pdf.multi_cell(table_width * 0.55, line_height, combined_text, border=0)

        # Celdas de cantidad, base y total
        pdf.set_xy(margin_left + table_width * 0.55, y_start)
        pdf.cell(table_width * 0.15, max_line_height, str(item['quantity']), 1, align='C')
        pdf.cell(table_width * 0.15, max_line_height, f"{item['price']:.2f} €", 1, align='C')
        pdf.cell(table_width * 0.15, max_line_height, f"{item['quantity'] * item['price']:.2f} €", 1, align='C')

        pdf.set_y(y_start + max_line_height)

    pdf.ln(10)

    # Resumen y totales
    pdf.set_y(-60)
    pdf.set_font('DejaVu', 'B', 10)
    pdf.set_x(margin_left)
    pdf.rounded_rect(margin_left, pdf.get_y(), table_width, 40, 3, 'D')

    # Método de pago
    pdf.cell(table_width * 0.25, 10, 'Método de pago:', align='L', border=0)
    pdf.cell(table_width * 0.75, 10, payment_method, align='L', border=0, new_x=XPos.LMARGIN)

    if payment_method == 'Transferencia':
        pdf.ln(10)
        pdf.set_x(margin_left)
        pdf.cell(table_width * 0.25, 10, 'Número de cuenta:', align='L', border=0)
        pdf.cell(table_width * 0.75, 10, 'ES6701826101810201629602', align='L', border=0, new_x=XPos.LMARGIN)

    # Totales
    pdf.set_xy(margin_left + table_width * 0.65, pdf.get_y() - 10 if payment_method == 'Transferencia' else pdf.get_y() + 10)
    pdf.cell(table_width * 0.15, 10, 'Base Imponible', align='R', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(table_width * 0.20, 10, f"{base_total:.2f} €", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if apply_iva:
        pdf.set_x(margin_left + table_width * 0.65)
        pdf.cell(table_width * 0.15, 10, 'IVA (21%)', align='R', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(table_width * 0.20, 10, f"{iva_amount:.2f} €", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(margin_left + table_width * 0.65)
    pdf.cell(table_width * 0.15, 10, 'Total', align='R', border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(table_width * 0.20, 10, f"{total_calculated:.2f} €", align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return pdf, doc_id

def save_invoice(pdf, filename):
    pdf.output(filename)
