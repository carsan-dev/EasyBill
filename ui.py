import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
from models import add_new_product, add_new_client
from database import (
    fetch_clients, fetch_products, fetch_all_products, fetch_all_clients,
    fetch_all_documents, get_product_price, get_product_name, get_product_description,
    get_client_name, update_client, update_product, update_budget,
    update_budget_items, update_invoice, update_invoice_items, delete_budget,
    delete_invoice, cursor, conn
)
from pdf_generator import (
    create_document, insert_document, save_invoice,
    create_documents_for_quarter, create_document_from_existing
)
from datetime import datetime
import os
import tempfile
from utils import is_file_in_use
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import ttk

class AutocompleteCombobox(ttk.Combobox):
    def __init__(self, master=None, placeholder="", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.default_fg_color = self['foreground']
        self.placeholder_fg_color = 'grey'
        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)
        self.bind("<KeyRelease>", self._on_keyrelease)
        self._add_placeholder()
        
        # Inicializar el identificador del temporizador
        self.after_id = None

    def _clear_placeholder(self, event=None):
        if self.get() == self.placeholder:
            self.set('')
            self.config(foreground=self.default_fg_color)

    def _add_placeholder(self, event=None):
        if not self.get():
            self.set(self.placeholder)
            self.config(foreground=self.placeholder_fg_color)

    def _on_keyrelease(self, event=None):
        if self.get() == self.placeholder:
            return
        typed = self.get().lower()
        if hasattr(self, 'full_list'):
            filtered = [item for item in self.full_list if typed in item.lower()]
            self['values'] = filtered

            # Cancelar el temporizador anterior si existe
            if self.after_id:
                self.after_cancel(self.after_id)

            if filtered:
                # Establecer un nuevo temporizador para abrir el dropdown después de 1 segundo
                self.after_id = self.after(700, self._open_dropdown)

    def _open_dropdown(self):
        # Generar el evento '<Down>' para abrir el menú desplegable
        self.event_generate('<Down>')
        # Resetear el identificador del temporizador
        self.after_id = None

    def set_completion_list(self, completion_list):
        self.full_list = sorted(completion_list, key=str.lower)
        self['values'] = self.full_list


class Application(tk.Tk):
    SPANISH_MONTHS = [
        "Enero", "Febrero", "Marzo", "Abril",
        "Mayo", "Junio", "Julio", "Agosto",
        "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    def __init__(self):
        super().__init__()
        self.title('Sistema de Facturación Sánchez Luna Servicios Integrales')
        self.geometry('1366x768')

        self.iconbitmap('Logo_Sanchez_Luna.ico')
        
        self.doc_type_filter = tk.StringVar(value="Todos")
        self.month_filter = tk.StringVar(value="Todos")
        
        self.create_widgets()
    
    def create_widgets(self):
        tabControl = ttk.Notebook(self)
        
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
        
        tabControl.add(tab1, text='Productos')
        tabControl.add(tab2, text='Clientes')
        tabControl.add(tab3, text='Documentos')
        
        tabControl.pack(expand=1, fill='both')
        
        self.create_products_tab(tab1)
        self.create_clients_tab(tab2)
        self.create_documents_tab(tab3)
    
    def create_products_tab(self, tab):
        frame = ttk.LabelFrame(tab, text='Agregar Nuevo Producto')
        frame.grid(column=0, row=0, padx=20, pady=20, sticky='nsew')
        
        ttk.Label(frame, text='Nombre:').grid(column=0, row=0, sticky='W')
        self.product_name = ttk.Entry(frame, width=50)
        self.product_name.grid(column=1, row=0, sticky='ew')
        
        ttk.Label(frame, text='Descripción:').grid(column=0, row=1, sticky='W')
        self.product_description = ttk.Entry(frame, width=50)
        self.product_description.grid(column=1, row=1, sticky='ew')
        
        ttk.Label(frame, text='Precio: *').grid(column=0, row=2, sticky='W')
        self.product_price = ttk.Entry(frame, width=50)
        self.product_price.grid(column=1, row=2, sticky='ew')
        
        ttk.Button(frame, text='Agregar', command=self.add_product).grid(column=1, row=3, pady=10, sticky='ew')

        filter_frame = ttk.LabelFrame(tab, text='Buscar Productos')
        filter_frame.grid(column=0, row=1, padx=20, pady=10, sticky='nsew')

        ttk.Label(filter_frame, text='Buscar por Nombre:').grid(column=0, row=0, sticky='W')
        self.product_search_name = ttk.Entry(filter_frame, width=50)
        self.product_search_name.grid(column=1, row=0, sticky='ew')
        self.product_search_name.bind('<KeyRelease>', lambda event: self.load_products_list())

        self.product_list_frame = ttk.Frame(tab)
        self.product_list_frame.grid(column=0, row=2, padx=20, pady=20, sticky='nsew')
        
        self.product_list = ttk.Treeview(self.product_list_frame, columns=('ID', 'Nombre', 'Descripción', 'Precio'), show='headings')
        self.product_list.heading('ID', text='ID')
        self.product_list.heading('Nombre', text='Nombre')
        self.product_list.heading('Descripción', text='Descripción')
        self.product_list.heading('Precio', text='Precio')
        self.product_list.column('ID', width=50)
        self.product_list.column('Nombre', width=150)
        self.product_list.column('Descripción', width=250)
        self.product_list.column('Precio', width=100)
        
        self.product_list_scrollbar = ttk.Scrollbar(self.product_list_frame, orient="vertical", command=self.product_list.yview)
        self.product_list.configure(yscrollcommand=self.product_list_scrollbar.set)
        
        self.product_list.grid(column=0, row=0, sticky='nsew')
        self.product_list_scrollbar.grid(column=1, row=0, sticky='ns')
        
        self.product_list.bind('<Double-1>', self.edit_product)

        self.product_list_frame.grid_columnconfigure(0, weight=1)
        self.product_list_frame.grid_rowconfigure(0, weight=1)
        
        self.load_products_list()
        
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

    def create_clients_tab(self, tab):
        frame = ttk.LabelFrame(tab, text='Agregar Nuevo Cliente')
        frame.grid(column=0, row=0, padx=20, pady=20, sticky='nsew')
        
        ttk.Label(frame, text='Nombre:').grid(column=0, row=0, sticky='W')
        self.client_name = ttk.Entry(frame, width=50)
        self.client_name.grid(column=1, row=0, sticky='ew')
        
        # Eliminamos el asterisco del label de Email
        ttk.Label(frame, text='Email:').grid(column=0, row=1, sticky='W')
        self.client_email = ttk.Entry(frame, width=50)
        self.client_email.grid(column=1, row=1, sticky='ew')
        
        ttk.Label(frame, text='Dirección:').grid(column=0, row=2, sticky='W')
        self.client_address = ttk.Entry(frame, width=50)
        self.client_address.grid(column=1, row=2, sticky='ew')
        
        ttk.Label(frame, text='Teléfono: *').grid(column=0, row=3, sticky='W')
        self.client_phone = ttk.Entry(frame, width=50)
        self.client_phone.grid(column=1, row=3, sticky='ew')
        
        ttk.Label(frame, text='DNI:').grid(column=0, row=4, sticky='W')
        self.client_dni = ttk.Entry(frame, width=50)
        self.client_dni.grid(column=1, row=4, sticky='ew')
        
        ttk.Button(frame, text='Agregar', command=self.add_client).grid(column=1, row=5, pady=10, sticky='ew')

        filter_frame = ttk.LabelFrame(tab, text='Buscar Clientes')
        filter_frame.grid(column=0, row=1, padx=20, pady=10, sticky='nsew')

        ttk.Label(filter_frame, text='Buscar por Nombre:').grid(column=0, row=0, sticky='W')
        self.client_search_name = ttk.Entry(filter_frame, width=50)
        self.client_search_name.grid(column=1, row=0, sticky='ew')
        self.client_search_name.bind('<KeyRelease>', lambda event: self.load_clients_list())

        self.client_list_frame = ttk.Frame(tab)
        self.client_list_frame.grid(column=0, row=2, padx=20, pady=20, sticky='nsew')
        
        self.client_list = ttk.Treeview(self.client_list_frame, columns=('ID', 'Nombre', 'Email', 'Dirección', 'Teléfono', 'DNI'), show='headings')
        self.client_list.heading('ID', text='ID')
        self.client_list.heading('Nombre', text='Nombre')
        self.client_list.heading('Email', text='Email')
        self.client_list.heading('Dirección', text='Dirección')
        self.client_list.heading('Teléfono', text='Teléfono')
        self.client_list.heading('DNI', text='DNI')
        self.client_list.column('ID', width=50)
        self.client_list.column('Nombre', width=150)
        self.client_list.column('Email', width=150)
        self.client_list.column('Dirección', width=200)
        self.client_list.column('Teléfono', width=100)
        self.client_list.column('DNI', width=100)
        
        self.client_list_scrollbar = ttk.Scrollbar(self.client_list_frame, orient="vertical", command=self.client_list.yview)
        self.client_list.configure(yscrollcommand=self.client_list_scrollbar.set)
        
        self.client_list.grid(column=0, row=0, sticky='nsew')
        self.client_list_scrollbar.grid(column=1, row=0, sticky='ns')
        
        self.client_list.bind('<Double-1>', self.edit_client)

        self.client_list_frame.grid_columnconfigure(0, weight=1)
        self.client_list_frame.grid_rowconfigure(0, weight=1)
        
        self.load_clients_list()
        
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)
    
    def create_documents_tab(self, tab):
        # Marco para generar documentos
        frame = ttk.LabelFrame(tab, text='Generar Documento')
        frame.grid(column=0, row=0, padx=10, pady=10, sticky='ew')

        self.doc_type = tk.StringVar()
        self.doc_type.set("Factura")
        ttk.Label(frame, text="Tipo de Documento:").grid(column=0, row=0, sticky='W', padx=5, pady=5)
        ttk.Radiobutton(frame, text="Factura", variable=self.doc_type, value="Factura", command=self.reset_iva_checkbox).grid(column=0, row=1, sticky='W', padx=5)
        ttk.Radiobutton(frame, text="Presupuesto", variable=self.doc_type, value="Presupuesto", command=self.reset_iva_checkbox).grid(column=0, row=2, sticky='W', padx=5)

        right_frame = ttk.Frame(frame)
        right_frame.grid(column=1, row=0, rowspan=3, padx=10, pady=5, sticky='nw')

        self.apply_iva = tk.BooleanVar(value=True)
        self.iva_checkbox = ttk.Checkbutton(right_frame, text='Aplicar IVA (21%)', variable=self.apply_iva)
        self.iva_checkbox.grid(column=0, row=0, sticky='W', pady=(0, 10))

        self.payment_method = tk.StringVar()
        self.payment_method.set("Contado")
        ttk.Label(right_frame, text="Método de Pago:").grid(column=0, row=1, sticky='W')
        ttk.Radiobutton(right_frame, text="Contado", variable=self.payment_method, value="Contado").grid(column=0, row=2, sticky='W')
        ttk.Radiobutton(right_frame, text="Transferencia", variable=self.payment_method, value="Transferencia").grid(column=0, row=3, sticky='W')

        # Reemplazar ttk.Combobox por AutocompleteCombobox con placeholder
        self.client_dropdown = AutocompleteCombobox(frame, placeholder="Selecciona un cliente:")
        self.client_dropdown.grid(column=0, row=3, columnspan=2, pady=10, padx=5, sticky='ew')
        self.load_clients_combobox()

        self.invoice_items = []

        ttk.Button(frame, text='Agregar Productos', command=self.add_invoice_items).grid(column=0, row=4, columnspan=2, pady=5, padx=5, sticky='ew')
        ttk.Button(frame, text='Generar Documento', command=self.generate_document).grid(column=0, row=5, columnspan=2, pady=5, padx=5, sticky='ew')

        # Configuración para la tabla de productos dentro de "Generar Documento"
        self.invoice_item_list_frame = ttk.Frame(frame)
        self.invoice_item_list_frame.grid(column=0, row=6, columnspan=2, padx=10, pady=5, sticky='ew')

        self.invoice_item_list = ttk.Treeview(
            self.invoice_item_list_frame,
            columns=('Producto', 'Descripción', 'Cantidad', 'Precio', 'Total'),
            show='headings',
            height=5
        )
        self.invoice_item_list.heading('Producto', text='Producto')
        self.invoice_item_list.heading('Descripción', text='Descripción')
        self.invoice_item_list.heading('Cantidad', text='Cantidad')
        self.invoice_item_list.heading('Precio', text='Precio')
        self.invoice_item_list.heading('Total', text='Total')
        self.invoice_item_list.column('Producto', width=150, anchor='center')
        self.invoice_item_list.column('Descripción', width=200, anchor='center')
        self.invoice_item_list.column('Cantidad', width=80, anchor='center')
        self.invoice_item_list.column('Precio', width=80, anchor='center')
        self.invoice_item_list.column('Total', width=80, anchor='center')

        self.invoice_item_list_scrollbar = ttk.Scrollbar(self.invoice_item_list_frame, orient="vertical", command=self.invoice_item_list.yview)
        self.invoice_item_list.configure(yscrollcommand=self.invoice_item_list_scrollbar.set)

        self.invoice_item_list.grid(column=0, row=0, sticky='nsew')
        self.invoice_item_list_scrollbar.grid(column=1, row=0, sticky='ns')

        self.invoice_item_list_frame.grid_columnconfigure(0, weight=1)
        self.invoice_item_list_frame.grid_rowconfigure(0, weight=1)

        # Crear un frame para contener la imagen
        image_frame = ttk.Frame(tab)
        image_frame.grid(column=1, row=0, padx=10, pady=10, sticky='nsew')

        # Agregar la imagen al frame
        self.add_transparent_image(image_frame)

        # Marco para los filtros
        filter_frame = ttk.LabelFrame(tab, text='Filtros')
        filter_frame.grid(column=0, row=1, padx=10, pady=5, sticky='ew')

        # Configurar columnas en filter_frame
        for i in range(6):
            filter_frame.columnconfigure(i, weight=1)

        # Filtros
        ttk.Label(filter_frame, text="Tipo de Documento:").grid(column=0, row=0, padx=5, pady=5, sticky='W')
        self.doc_type_filter_combobox = ttk.Combobox(filter_frame, textvariable=self.doc_type_filter, values=["Todos", "Factura", "Presupuesto"], state='readonly')
        self.doc_type_filter_combobox.grid(column=1, row=0, padx=5, pady=5, sticky='ew')

        ttk.Label(filter_frame, text="Mes:").grid(column=2, row=0, padx=5, pady=5, sticky='W')
        self.month_filter_combobox = ttk.Combobox(
            filter_frame,
            textvariable=self.month_filter,
            values=["Todos"] + self.SPANISH_MONTHS,
            state='readonly'
        )
        self.month_filter_combobox.grid(column=3, row=0, padx=5, pady=5, sticky='ew')

        ttk.Label(filter_frame, text="Cliente:").grid(column=0, row=1, padx=5, pady=5, sticky='W')
        self.doc_client_search_name = ttk.Entry(filter_frame)
        self.doc_client_search_name.grid(column=1, row=1, padx=5, pady=5, sticky='ew')

        ttk.Label(filter_frame, text="Producto:").grid(column=2, row=1, padx=5, pady=5, sticky='W')
        self.doc_product_search_name = ttk.Entry(filter_frame)
        self.doc_product_search_name.grid(column=3, row=1, padx=5, pady=5, sticky='ew')

        # Botón para aplicar filtros
        ttk.Button(filter_frame, text='Aplicar Filtros', command=self.load_documents_list).grid(column=4, row=0, rowspan=2, padx=10, pady=5, sticky='nsew')

        # Vincular las entradas de búsqueda con la función de carga
        self.doc_client_search_name.bind('<KeyRelease>', lambda event: self.load_documents_list())
        self.doc_product_search_name.bind('<KeyRelease>', lambda event: self.load_documents_list())

        # Marco para facturas trimestrales
        quarter_frame = ttk.LabelFrame(tab, text='Generar Facturas por Trimestre')
        quarter_frame.grid(column=1, row=1, padx=10, pady=5, sticky='ew')

        self.quarter = tk.StringVar()
        self.quarter.set("1")
        ttk.Label(quarter_frame, text="Trimestre:").grid(column=0, row=0, padx=5, pady=5, sticky='W')
        self.quarter_combobox = ttk.Combobox(quarter_frame, textvariable=self.quarter, values=["1", "2", "3", "4"], state='readonly')
        self.quarter_combobox.grid(column=1, row=0, padx=5, pady=5, sticky='ew')

        self.year = tk.StringVar()
        self.year.set(datetime.now().year)
        ttk.Label(quarter_frame, text="Año:").grid(column=0, row=1, padx=5, pady=5, sticky='W')
        ttk.Entry(quarter_frame, textvariable=self.year).grid(column=1, row=1, padx=5, pady=5, sticky='ew')

        ttk.Button(quarter_frame, text='Generar Facturas', command=self.generate_quarter_invoices).grid(column=0, row=2, columnspan=2, padx=5, pady=5, sticky='ew')

        # Ajustar la tabla de documentos
        self.document_list_frame = ttk.Frame(tab)
        self.document_list_frame.grid(column=0, row=2, columnspan=2, padx=10, pady=(0, 10), sticky='nsew')

        self.document_list = ttk.Treeview(
            self.document_list_frame,
            columns=('ID', 'Cliente', 'Productos', 'Fecha', 'Total', 'Tipo'),
            show='headings',
            height=20,  # Aumentado de 5 a 20
            selectmode='extended'  # Permitir selección múltiple
        )
        self.document_list.heading('ID', text='ID')
        self.document_list.heading('Cliente', text='Cliente')
        self.document_list.heading('Productos', text='Productos')
        self.document_list.heading('Fecha', text='Fecha')
        self.document_list.heading('Total', text='Total')
        self.document_list.heading('Tipo', text='Tipo')
        self.document_list.column('ID', width=50, anchor='center')
        self.document_list.column('Cliente', width=130, anchor='center')  # Ajustado de 150 a 130
        self.document_list.column('Productos', width=180, anchor='center')  # Ajustado de 200 a 180
        self.document_list.column('Fecha', width=150, anchor='center')
        self.document_list.column('Total', width=80, anchor='center')
        self.document_list.column('Tipo', width=100, anchor='center')

        self.document_list_scrollbar = ttk.Scrollbar(self.document_list_frame, orient="vertical", command=self.document_list.yview)
        self.document_list.configure(yscrollcommand=self.document_list_scrollbar.set)

        self.document_list.grid(column=0, row=0, sticky='nsew')
        self.document_list_scrollbar.grid(column=1, row=0, sticky='ns')

        self.document_list_frame.grid_columnconfigure(0, weight=1)
        self.document_list_frame.grid_rowconfigure(0, weight=1)

        # Botón Editar Documento
        ttk.Button(tab, text="Editar Documento", command=self.edit_document).grid(column=0, row=3, padx=10, pady=10, sticky='ew')

        # Botón Eliminar Documento
        ttk.Button(tab, text="Eliminar Documento", command=self.delete_document).grid(column=1, row=3, padx=10, pady=10, sticky='ew')

        self.load_documents_list()

        # Vincula el doble clic en la lista de documentos
        self.document_list.bind('<Double-1>', lambda event: self.on_document_double_click(event))

        # Ajustar la configuración del grid
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=0)  # Las filas superiores no se expanden
        tab.grid_rowconfigure(1, weight=0)
        tab.grid_rowconfigure(2, weight=1)  # La fila de la tabla de documentos se expande
        tab.grid_rowconfigure(3, weight=0)  # Botones inferiores no se expanden

    def on_document_double_click(self, event):
        item = self.document_list.identify_row(event.y)
        if not item:
            return
        doc_id = self.document_list.item(item, 'values')[0]
        doc_type = self.document_list.item(item, 'values')[5]
        self.view_document(doc_id, doc_type)


    def view_document(self, doc_id, doc_type):
        if doc_type == 'Factura':
            cursor.execute('SELECT client_id, date, total, payment_method, apply_iva FROM invoices WHERE id = ?', (doc_id,))
            document = cursor.fetchone()
        elif doc_type == 'Presupuesto':
            cursor.execute('SELECT client_id, date, total, payment_method, apply_iva FROM budgets WHERE id = ?', (doc_id,))
            document = cursor.fetchone()

        if not document:
            messagebox.showerror('Error', 'Documento no encontrado.')
            return

        client_id, date, total, payment_method, apply_iva = document

        if doc_type == 'Factura':
            cursor.execute('SELECT product_id, quantity, price FROM invoice_items WHERE invoice_id = ?', (doc_id,))
        elif doc_type == 'Presupuesto':
            cursor.execute('SELECT product_id, quantity, price FROM budget_items WHERE budget_id = ?', (doc_id,))

        items = cursor.fetchall()
        items = [{'product_id': item[0], 'quantity': item[1], 'price': item[2]} for item in items]

        pdf, _ = create_document_from_existing(doc_id, client_id, date, total, payment_method, items, doc_type, apply_iva)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            pdf.output(temp_pdf.name)
            filename = temp_pdf.name

        os.startfile(filename)

        self.after(1000, lambda: is_file_in_use(filename))

    def edit_product(self, event):
        selected_item = self.product_list.selection()[0]
        product_id = self.product_list.item(selected_item, 'values')[0]
        name = self.product_list.item(selected_item, 'values')[1]
        description = self.product_list.item(selected_item, 'values')[2]
        price = self.product_list.item(selected_item, 'values')[3]

        edit_window = tk.Toplevel(self)
        edit_window.title("Editar Producto")
        edit_window.geometry('400x250')
        edit_window.transient(self)
        edit_window.grab_set()
        self.center_window(edit_window)

        edit_window.iconbitmap('Logo_Sanchez_Luna.ico')  # Añadir el ícono a la ventana

        ttk.Label(edit_window, text='Nombre:').grid(column=0, row=0, sticky='W')
        product_name = ttk.Entry(edit_window, width=50)
        product_name.grid(column=1, row=0, sticky='ew')
        product_name.insert(0, name)
        
        ttk.Label(edit_window, text='Descripción:').grid(column=0, row=1, sticky='W')
        product_description = ttk.Entry(edit_window, width=50)
        product_description.grid(column=1, row=1, sticky='ew')
        product_description.insert(0, description)
        
        ttk.Label(edit_window, text='Precio: *').grid(column=0, row=2, sticky='W')
        product_price = ttk.Entry(edit_window, width=50)
        product_price.grid(column=1, row=2, sticky='ew')
        product_price.insert(0, price)

        def update_product_details():
            new_name = product_name.get()
            new_description = product_description.get()
            new_price = product_price.get()

            if not self.validate_text(new_name):
                messagebox.showerror('Error', 'El nombre del producto no es válido.')
                return

            if not self.validate_price(new_price):
                messagebox.showerror('Error', 'El precio del producto no es válido.')
                return

            update_product(product_id, new_name, new_description, float(new_price))
            messagebox.showinfo('Éxito', 'Producto actualizado correctamente')
            self.load_products_list()
            edit_window.destroy()

        ttk.Button(edit_window, text='Actualizar', command=update_product_details).grid(column=1, row=3, pady=10, sticky='ew')

    def edit_client(self, event):
        selected_item = self.client_list.selection()[0]
        client_id = self.client_list.item(selected_item, 'values')[0]
        name = self.client_list.item(selected_item, 'values')[1]
        email = self.client_list.item(selected_item, 'values')[2]
        address = self.client_list.item(selected_item, 'values')[3]
        phone = self.client_list.item(selected_item, 'values')[4]
        dni = self.client_list.item(selected_item, 'values')[5]

        edit_window = tk.Toplevel(self)
        edit_window.title("Editar Cliente")
        edit_window.geometry('400x300')
        edit_window.transient(self)
        edit_window.grab_set()
        self.center_window(edit_window)

        edit_window.iconbitmap('Logo_Sanchez_Luna.ico')

        ttk.Label(edit_window, text='Nombre:').grid(column=0, row=0, sticky='W')
        client_name = ttk.Entry(edit_window, width=50)
        client_name.grid(column=1, row=0, sticky='ew')
        client_name.insert(0, name)

        ttk.Label(edit_window, text='Email:').grid(column=0, row=1, sticky='W')
        client_email = ttk.Entry(edit_window, width=50)
        client_email.grid(column=1, row=1, sticky='ew')
        client_email.insert(0, email)

        ttk.Label(edit_window, text='Dirección:').grid(column=0, row=2, sticky='W')
        client_address = ttk.Entry(edit_window, width=50)
        client_address.grid(column=1, row=2, sticky='ew')
        client_address.insert(0, address)

        ttk.Label(edit_window, text='Teléfono: *').grid(column=0, row=3, sticky='W')
        client_phone = ttk.Entry(edit_window, width=50)
        client_phone.grid(column=1, row=3, sticky='ew')
        client_phone.insert(0, phone)

        ttk.Label(edit_window, text='DNI:').grid(column=0, row=4, sticky='W')
        client_dni = ttk.Entry(edit_window, width=50)
        client_dni.grid(column=1, row=4, sticky='ew')
        client_dni.insert(0, dni)

        def update_client_details():
            new_name = client_name.get()
            new_email = client_email.get()
            new_address = client_address.get()
            new_phone = client_phone.get()
            new_dni = client_dni.get()

            if not self.validate_text(new_name):
                messagebox.showerror('Error', 'El nombre del cliente no es válido.')
                return

            if not self.validate_phone(new_phone):
                messagebox.showerror('Error', 'El teléfono del cliente no es válido.')
                return

            update_client(client_id, new_name, new_email, new_address, new_phone, new_dni)
            messagebox.showinfo('Éxito', 'Cliente actualizado correctamente')
            self.load_clients_list()
            self.load_documents_list()
            edit_window.destroy()

        ttk.Button(edit_window, text='Actualizar', command=update_client_details).grid(column=1, row=5, pady=10, sticky='ew')
    
    def edit_document(self):
        selected_items = self.document_list.selection()
        if not selected_items:
            messagebox.showerror('Error', 'Debe seleccionar un documento para editar.')
            return

        if len(selected_items) > 1:
            messagebox.showwarning('Advertencia', 'Por favor, seleccione solo un documento para editar.')
            return

        selected_item = selected_items[0]
        doc_id = self.document_list.item(selected_item, 'values')[0]
        doc_type = self.document_list.item(selected_item, 'values')[5]
        
        # Obtenemos los detalles del documento seleccionado
        if doc_type == 'Factura':
            cursor.execute('SELECT client_id, date, total, payment_method, apply_iva FROM invoices WHERE id = ?', (doc_id,))
        elif doc_type == 'Presupuesto':
            cursor.execute('SELECT client_id, date, total, payment_method, apply_iva FROM budgets WHERE id = ?', (doc_id,))
        
        document = cursor.fetchone()
        
        if not document:
            messagebox.showerror('Error', 'Documento no encontrado.')
            return

        client_id, date, total, payment_method, apply_iva = document

        # Obtenemos los items asociados al documento
        if doc_type == 'Factura':
            cursor.execute('SELECT product_id, quantity, price FROM invoice_items WHERE invoice_id = ?', (doc_id,))
        elif doc_type == 'Presupuesto':
            cursor.execute('SELECT product_id, quantity, price FROM budget_items WHERE budget_id = ?', (doc_id,))

        items = cursor.fetchall()
        items = [{'product_id': item[0], 'quantity': item[1], 'price': item[2]} for item in items]

        # Abrimos una ventana emergente para editar el documento
        self.open_edit_document_window(doc_id, doc_type, client_id, date, total, payment_method, apply_iva, items)

    def open_edit_document_window(self, doc_id, doc_type, client_id, date, total, payment_method, apply_iva, items):
        edit_window = tk.Toplevel(self)
        edit_window.title(f"Editar {doc_type}")
        edit_window.geometry('600x600')
        edit_window.transient(self)
        edit_window.grab_set()
        self.center_window(edit_window)

        # Agregar el ícono de la app
        edit_window.iconbitmap('Logo_Sanchez_Luna.ico')

        # Almacena el tipo de documento en una variable StringVar
        self.edit_doc_type = tk.StringVar(value=doc_type)

        # Tipo de Documento
        ttk.Label(edit_window, text="Tipo de Documento:").grid(column=0, row=0, sticky='W', padx=10, pady=10)
        ttk.Radiobutton(edit_window, text="Factura", variable=self.edit_doc_type, value="Factura").grid(column=1, row=0, sticky='W', padx=10)
        ttk.Radiobutton(edit_window, text="Presupuesto", variable=self.edit_doc_type, value="Presupuesto").grid(column=1, row=1, sticky='W', padx=10)

        # Cliente
        ttk.Label(edit_window, text="Cliente:").grid(column=0, row=2, sticky='W', padx=10, pady=10)
        self.edit_client_dropdown = AutocompleteCombobox(edit_window, placeholder="Selecciona un cliente:")
        self.edit_client_dropdown.grid(column=1, row=2, pady=10, padx=10, sticky='ew')

        # Cargar todos los clientes en el combobox
        clients = fetch_all_clients()  # Obtener todos los clientes de la base de datos
        client_list = [f"{client[0]} - {client[1]}" for client in clients]  # Formato "id - nombre"
        self.edit_client_dropdown.set_completion_list(client_list)
        self.edit_client_dropdown.set(f"{client_id} - {get_client_name(client_id)}")

        # Método de pago
        ttk.Label(edit_window, text="Método de pago:").grid(column=0, row=3, sticky='W', padx=10, pady=10)
        self.edit_payment_method = tk.StringVar()
        ttk.Radiobutton(edit_window, text="Contado", variable=self.edit_payment_method, value="Contado").grid(column=1, row=3, sticky='W', padx=10)
        ttk.Radiobutton(edit_window, text="Transferencia", variable=self.edit_payment_method, value="Transferencia").grid(column=1, row=4, sticky='W', padx=10)
        self.edit_payment_method.set(payment_method)

        # Aplicar IVA
        self.edit_apply_iva = tk.BooleanVar(value=apply_iva)
        self.edit_iva_checkbox = ttk.Checkbutton(edit_window, text='Aplicar IVA (21%)', variable=self.edit_apply_iva)
        self.edit_iva_checkbox.grid(column=0, row=5, sticky='W', padx=10, pady=10)

        # Tabla para editar productos
        self.product_list_frame_edit = ttk.Frame(edit_window)
        self.product_list_frame_edit.grid(column=0, row=6, columnspan=2, padx=10, pady=10, sticky='nsew')

        self.product_list_edit = ttk.Treeview(
            self.product_list_frame_edit,
            columns=('Producto', 'Descripción', 'Cantidad', 'Precio', 'Total'),
            show='headings'
        )
        self.product_list_edit.heading('Producto', text='Producto')
        self.product_list_edit.heading('Descripción', text='Descripción')
        self.product_list_edit.heading('Cantidad', text='Cantidad')
        self.product_list_edit.heading('Precio', text='Precio')
        self.product_list_edit.heading('Total', text='Total')
        self.product_list_edit.column('Producto', width=150, anchor='center')
        self.product_list_edit.column('Descripción', width=200, anchor='center')
        self.product_list_edit.column('Cantidad', width=80, anchor='center')
        self.product_list_edit.column('Precio', width=80, anchor='center')
        self.product_list_edit.column('Total', width=80, anchor='center')

        self.product_list_edit_scrollbar = ttk.Scrollbar(self.product_list_frame_edit, orient="vertical", command=self.product_list_edit.yview)
        self.product_list_edit.configure(yscrollcommand=self.product_list_edit_scrollbar.set)

        self.product_list_edit.grid(column=0, row=0, sticky='nsew')
        self.product_list_edit_scrollbar.grid(column=1, row=0, sticky='ns')

        self.product_list_frame_edit.grid_columnconfigure(0, weight=1)
        self.product_list_frame_edit.grid_rowconfigure(0, weight=1)

        # Botones para añadir o eliminar productos
        ttk.Button(
            edit_window,
            text='Añadir Producto',
            command=lambda: self.add_product_to_invoice(edit_window, self.product_list_edit, self.edit_invoice_items)
        ).grid(column=0, row=7, pady=10, sticky='ew')
        ttk.Button(edit_window, text='Eliminar Producto', command=self.remove_product_from_invoice).grid(column=1, row=7, pady=10, sticky='ew')

        # Guardar cambios
        ttk.Button(
            edit_window,
            text="Guardar Cambios",
            command=lambda: self.save_edited_document(edit_window, doc_id, self.edit_doc_type.get())
        ).grid(column=0, row=8, columnspan=2, pady=20, padx=10, sticky='ew')

        # Centrado de la ventana
        self.center_window(edit_window)

        # Cargar los productos existentes en la tabla
        self.edit_invoice_items = items
        self.load_edit_invoice_item_list()

        # Configuración de la grid
        edit_window.grid_columnconfigure(0, weight=1)
        edit_window.grid_columnconfigure(1, weight=1)
        edit_window.grid_rowconfigure(6, weight=1)

    def delete_document(self):
        selected_items = self.document_list.selection()
        if not selected_items:
            messagebox.showerror('Error', 'Debe seleccionar al menos un documento para eliminar.')
            return

        confirm = messagebox.askyesno('Confirmar Eliminación', f'¿Está seguro que desea eliminar los documentos seleccionados?')
        if not confirm:
            return

        for selected_item in selected_items:
            doc_id = self.document_list.item(selected_item, 'values')[0]
            doc_type = self.document_list.item(selected_item, 'values')[5]  # La columna Tipo está en la posición 5

            if doc_type == 'Factura':
                delete_invoice(doc_id)
            elif doc_type == 'Presupuesto':
                delete_budget(doc_id)
            else:
                messagebox.showerror('Error', f'Tipo de documento desconocido para el documento con ID {doc_id}.')
                continue

        messagebox.showinfo('Éxito', 'Documentos eliminados correctamente.')
        self.load_documents_list()

    def load_edit_invoice_item_list(self):
        for row in self.product_list_edit.get_children():
            self.product_list_edit.delete(row)
        for item in self.edit_invoice_items:
            product_name = get_product_name(item['product_id'])
            product_description = get_product_description(item['product_id'])
            
            self.product_list_edit.insert('', 'end', values=(
                product_name,
                product_description,
                item['quantity'], 
                f"{item['price']} €", 
                f"{item['quantity'] * item['price']} €"
            ))

    def add_product_to_invoice(self, parent_window, treeview, items_list):
        # Crear la ventana para añadir productos
        top = tk.Toplevel(parent_window)
        top.title('Añadir Productos a la Factura/Presupuesto')
        top.geometry('600x400')
        top.transient(parent_window)
        top.grab_set()

        # Añadir el ícono de la app
        top.iconbitmap('Logo_Sanchez_Luna.ico')

        self.center_window(top)  # Centrar la ventana

        # Lista temporal para los productos que se van añadiendo
        temp_added_products = []

        # Etiqueta para el título de la ventana
        ttk.Label(top, text="Añadir Producto", font=("Arial", 14, "bold")).grid(column=0, row=0, columnspan=3, padx=10, pady=10)

        # Etiqueta y Combobox para seleccionar el producto con placeholder
        ttk.Label(top, text="Producto:").grid(column=0, row=1, padx=10, pady=5, sticky='W')
        product_dropdown = AutocompleteCombobox(top, placeholder="Selecciona un producto:")
        product_dropdown.grid(column=1, row=1, padx=10, pady=5, sticky='ew')
        self.load_products_combobox(product_dropdown)  # Cargar productos en el dropdown

        # Etiqueta y Entry para introducir la cantidad
        ttk.Label(top, text="Cantidad:").grid(column=0, row=2, padx=10, pady=5, sticky='W')
        quantity_entry = ttk.Entry(top, width=10)
        quantity_entry.grid(column=1, row=2, padx=10, pady=5, sticky='w')

        # Añadir una cantidad por defecto en el campo de cantidad
        quantity_entry.insert(0, "1")

        # Botón para añadir el producto a la lista temporal
        add_button = ttk.Button(
            top,
            text="Añadir",
            command=lambda: self.add_to_temp_list(product_dropdown, quantity_entry, temp_added_products, temp_treeview)
        )
        add_button.grid(column=2, row=2, padx=10, pady=5, sticky='ew')

        # Treeview para mostrar los productos añadidos
        columns = ('Producto', 'Descripción', 'Cantidad', 'Precio', 'Total')
        temp_treeview = ttk.Treeview(top, columns=columns, show='headings', height=10)
        temp_treeview.heading('Producto', text='Producto')
        temp_treeview.heading('Descripción', text='Descripción')
        temp_treeview.heading('Cantidad', text='Cantidad')
        temp_treeview.heading('Precio', text='Precio')
        temp_treeview.heading('Total', text='Total')
        temp_treeview.column('Producto', width=150, anchor='center')
        temp_treeview.column('Descripción', width=200, anchor='center')
        temp_treeview.column('Cantidad', width=80, anchor='center')
        temp_treeview.column('Precio', width=80, anchor='center')
        temp_treeview.column('Total', width=80, anchor='center')

        temp_treeview.grid(column=0, row=3, columnspan=3, padx=10, pady=10, sticky='nsew')

        temp_scrollbar = ttk.Scrollbar(top, orient="vertical", command=temp_treeview.yview)
        temp_treeview.configure(yscrollcommand=temp_scrollbar.set)
        temp_scrollbar.grid(column=3, row=3, sticky='ns')

        # Botón para confirmar todos los productos añadidos
        confirm_button = ttk.Button(
            top,
            text="Confirmar Todos",
            command=lambda: self.confirm_temp_products(temp_added_products, items_list, treeview, top)
        )
        confirm_button.grid(column=0, row=4, columnspan=3, padx=10, pady=10, sticky='ew')

        # Configurar grid
        top.grid_columnconfigure(1, weight=1)
        top.grid_rowconfigure(3, weight=1)

    def add_to_temp_list(self, product_dropdown, quantity_entry, temp_added_products, temp_treeview):
        # Obtener el texto del producto y la cantidad
        product_text = product_dropdown.get()
        quantity_text = quantity_entry.get()

        # Validaciones
        if not product_text or product_text == "Selecciona un producto:":
            messagebox.showerror('Error', 'Debe seleccionar un producto.')
            return

        if not quantity_text or quantity_text == "Introduce la cantidad":
            messagebox.showerror('Error', 'Debe introducir una cantidad.')
            return

        try:
            product_id = int(product_text.split(' ')[0])
            quantity = int(quantity_text)
        except ValueError:
            messagebox.showerror('Error', 'Cantidad inválida.')
            return

        price = get_product_price(product_id)
        product_name = get_product_name(product_id)
        product_description = get_product_description(product_id)

        total = quantity * price

        # Insertar en el Treeview temporal
        temp_treeview.insert('', 'end', values=(product_name, product_description, quantity, f"{price} €", f"{total} €"))

        # Añadir al lista temporal
        temp_added_products.append({
            'product_id': product_id,
            'quantity': quantity,
            'price': price
        })

        # Resetear los campos
        product_dropdown.set('Selecciona un producto:')
        quantity_entry.delete(0, tk.END)
        quantity_entry.insert(0, "1")

    def confirm_temp_products(self, temp_added_products, items_list, main_treeview, top):
        if not temp_added_products:
            messagebox.showerror('Error', 'No hay productos añadidos para confirmar.')
            return

        # Añadir cada producto a la main items_list
        for product in temp_added_products:
            items_list.append(product)
            product_name = get_product_name(product['product_id'])
            product_description = get_product_description(product['product_id'])
            quantity = product['quantity']
            price = product['price']
            total = quantity * price

            main_treeview.insert('', 'end', values=(product_name, product_description, quantity, f"{price} €", f"{total} €"))

        messagebox.showinfo('Éxito', 'Productos añadidos correctamente.')
        top.destroy()

    def confirm_add_product_to_invoice(self, product_dropdown, quantity_entry, top, treeview, items_list):
        # Obtener el texto del producto y la cantidad
        product_text = product_dropdown.get()
        quantity_text = quantity_entry.get()

        # Validaciones
        if not product_text or product_text == "Selecciona un producto:":
            messagebox.showerror('Error', 'Debe seleccionar un producto.')
            return

        if not quantity_text or quantity_text == "Introduce la cantidad":
            messagebox.showerror('Error', 'Debe introducir una cantidad.')
            return

        try:
            product_id = int(product_text.split(' ')[0])
            quantity = int(quantity_text)
        except ValueError:
            messagebox.showerror('Error', 'Cantidad inválida.')
            return

        price = get_product_price(product_id)
        product_name = get_product_name(product_id)
        product_description = get_product_description(product_id)

        # Insertar en el Treeview pasado como parámetro
        treeview.insert('', 'end', values=(product_name, product_description, quantity, f"{price} €", f"{quantity * price} €"))
        items_list.append({
            'product_id': product_id,
            'quantity': quantity,
            'price': price
        })

        # Resetear los campos
        product_dropdown.set('Selecciona un producto:')
        quantity_entry.delete(0, tk.END)
        quantity_entry.insert(0, "Introduce la cantidad")

    def remove_product_from_invoice(self):
        selected_item = self.product_list_edit.selection()
        if not selected_item:
            messagebox.showerror('Error', 'Debe seleccionar un producto para eliminar.')
            return
        product_name = self.product_list_edit.item(selected_item, 'values')[0]
        
        # Buscar el producto en la lista de items
        for item in self.edit_invoice_items:
            if get_product_name(item['product_id']) == product_name:
                self.edit_invoice_items.remove(item)
                break
        
        self.load_edit_invoice_item_list()  # Recargar la tabla

    def save_edited_document(self, window, doc_id, new_doc_type):
        # Obtener la selección del cliente
        client_selection = self.edit_client_dropdown.get()
        if not client_selection or client_selection == "Selecciona un cliente:":
            messagebox.showerror('Error', 'Debe seleccionar un cliente.')
            return

        try:
            client_id = int(client_selection.split(' ')[0])  # Obtener el id del cliente seleccionado
        except ValueError:
            messagebox.showerror('Error', 'Selección de cliente inválida.')
            return

        payment_method = self.edit_payment_method.get()
        apply_iva = self.edit_apply_iva.get()

        base_total = sum(item['quantity'] * item['price'] for item in self.edit_invoice_items)
        iva_amount = base_total * 0.21 if apply_iva else 0
        total = base_total + iva_amount

        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Determinar si es necesario cambiar el tipo de documento
        if new_doc_type == "Factura":
            update_invoice(doc_id, client_id, date, total, payment_method, apply_iva)
            update_invoice_items(doc_id, self.edit_invoice_items)  # Actualizar productos de la factura

        elif new_doc_type == "Presupuesto":
            update_budget(doc_id, client_id, date, total, payment_method, apply_iva)
            update_budget_items(doc_id, self.edit_invoice_items)  # Actualizar productos del presupuesto

        conn.commit()

        messagebox.showinfo('Éxito', f'{new_doc_type} actualizado correctamente.')
        self.load_documents_list()  # Recargar la lista de documentos
        window.destroy()

    def update_client_name_in_documents(self, client_id, new_name):
        for item in self.document_list.get_children():
            values = self.document_list.item(item, 'values')
            doc_id, client_name, date, total, doc_type = values
            current_client_id = int(client_id)

            # Comparar el nombre actual con el nombre nuevo y actualizar si es necesario
            if client_name != new_name:
                self.document_list.item(item, values=(doc_id, new_name, date, total, doc_type))

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def add_transparent_image(self, parent_frame):
        canvas = tk.Canvas(parent_frame, highlightthickness=0)
        canvas.grid(column=0, row=0, sticky='nsew')

        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(0, weight=1)

        image = Image.open('IMG/Background_image.png')
        image = image.resize((400, 200), Image.LANCZOS)  # Image.Resampling.LANCZOS puede no estar disponible en versiones antiguas de PIL

        self.tk_image = ImageTk.PhotoImage(image)

        def center_image(event):
            canvas.delete("all")
            canvas_width = event.width
            canvas_height = event.height
            img_width = self.tk_image.width()
            img_height = self.tk_image.height()
            x = (canvas_width // 2) - (img_width // 2)
            y = (canvas_height // 3.5) - (img_height // 3.5)
            canvas.create_image(x, y, anchor='nw', image=self.tk_image)

        canvas.bind('<Configure>', center_image)

    def reset_iva_checkbox(self):
        if self.doc_type.get() == 'Factura':
            self.apply_iva.set(True)
        else:
            self.apply_iva.set(False)

    def load_documents_list(self):
        for row in self.document_list.get_children():
            self.document_list.delete(row)

        # Usa las nuevas variables de búsqueda en lugar de las antiguas
        search_client_name = self.doc_client_search_name.get().lower()
        search_product_name = self.doc_product_search_name.get().lower()

        documents = fetch_all_documents()

        months = {
            "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04",
            "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08",
            "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
        }

        filtered_documents = []
        for document in documents:
            doc_id, client_name, date, total, doc_type, products = document
            
            # Filtro por tipo de documento
            if self.doc_type_filter.get() != "Todos" and doc_type != self.doc_type_filter.get():
                continue

            # Filtro por mes
            if self.month_filter.get() != "Todos":
                try:
                    document_month = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%m')
                except ValueError:
                    # Manejar formato de fecha diferente si es necesario
                    continue
                selected_month = months.get(self.month_filter.get(), "00")
                if document_month != selected_month:
                    continue

            # Filtro por nombre de cliente
            if search_client_name and search_client_name not in client_name.lower():
                continue

            # Filtro por nombre de producto
            if search_product_name and search_product_name not in products.lower():
                continue

            filtered_documents.append(document)
        
        for document in filtered_documents:
            doc_id, client_name, date, total, doc_type, products = document
            self.document_list.insert('', 'end', values=(doc_id, client_name, products, date, f"{total:.2f} €", doc_type))

    def create_view_text(self, doc_id, doc_type, action_text):
        item_id = self.document_list.get_children()[-1]
        self.document_list.item(item_id, tags=(item_id,))
        self.document_list.tag_bind(item_id, '<Double-1>', lambda event, id=doc_id, type=doc_type: self.view_document(id, type))

    def load_clients_combobox(self):
        clients = fetch_all_clients()
        client_list = [f"{client[0]} - {client[1]}" for client in clients]
        self.client_dropdown.set_completion_list(client_list)
        if not self.client_dropdown.get():
            self.client_dropdown.set("Selecciona un cliente:")

    def load_products_combobox(self, combobox):
        products = fetch_products()
        product_list = [f"{product[0]} - {product[1]}" for product in products]
        combobox.set_completion_list(product_list)
        if not combobox.get():
            combobox.set("Selecciona un producto...")

    def load_products_list(self):
        for row in self.product_list.get_children():
            self.product_list.delete(row)
        products = fetch_all_products()
        search_name = self.product_search_name.get().lower()
        filtered_products = [product for product in products if search_name in product[1].lower()]
        for product in filtered_products:
            self.product_list.insert('', 'end', values=product)

    def load_clients_list(self):
        for row in self.client_list.get_children():
            self.client_list.delete(row)
        clients = fetch_all_clients()
        search_name = self.client_search_name.get().lower()
        filtered_clients = [client for client in clients if search_name in client[1].lower()]
        for client in filtered_clients:
            self.client_list.insert('', 'end', values=client)

    def update_invoice_item_list(self):
        for row in self.invoice_item_list.get_children():
            self.invoice_item_list.delete(row)
        for item in self.invoice_items:
            product_name = get_product_name(item['product_id'])
            product_description = get_product_description(item['product_id'])
            
            self.invoice_item_list.insert('', 'end', values=(
                product_name,
                product_description,
                item['quantity'], 
                f"{item['price']} €", 
                f"{item['quantity'] * item['price']} €"
            ))

    def validate_text(self, text):
        if text.strip():
            return True
        return False

    def validate_price(self, price):
        try:
            float(price)
            return True
        except ValueError:
            return False

    def validate_email(self, email):
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return True
        return False

    def validate_phone(self, phone):
        if re.match(r"^\d{9}$", phone):
            return True
        return False

    def add_product(self):
        name = self.product_name.get()
        description = self.product_description.get()
        price = self.product_price.get()
        
        if not self.validate_text(name):
            messagebox.showerror('Error', 'El nombre del producto no es válido.')
            return
        
        if not self.validate_price(price):
            messagebox.showerror('Error', 'El precio del producto no es válido.')
            return
        
        add_new_product(name, description, float(price))
        messagebox.showinfo('Información', 'Producto agregado con éxito')
        
        self.product_name.delete(0, tk.END)
        self.product_description.delete(0, tk.END)
        self.product_price.delete(0, tk.END)
        self.load_products_list()

    def add_client(self):
        name = self.client_name.get()
        email = self.client_email.get()
        address = self.client_address.get()
        phone = self.client_phone.get()
        dni = self.client_dni.get()
        
        if not self.validate_text(name):
            messagebox.showerror('Error', 'El nombre del cliente no es válido.')
            return
        
        if not self.validate_phone(phone):
            messagebox.showerror('Error', 'El teléfono del cliente no es válido.')
            return
        
        add_new_client(name, email, address, phone, dni)
        messagebox.showinfo('Información', 'Cliente agregado con éxito')
        
        self.client_name.delete(0, tk.END)
        self.client_email.delete(0, tk.END)
        self.client_address.delete(0, tk.END)
        self.client_phone.delete(0, tk.END)
        self.client_dni.delete(0, tk.END)
        self.load_clients_combobox()
        self.load_clients_list()

    def add_invoice_items(self):
        top = tk.Toplevel(self)
        top.title('Agregar Productos a la Factura')
        top.geometry('750x400')
        top.transient(self)
        top.grab_set()
        self.center_window(top)

        top.iconbitmap('Logo_Sanchez_Luna.ico')  # Añadir el ícono a la ventana

        self.invoice_item_entries = []

        frame = ttk.Frame(top)
        frame.pack(fill=tk.BOTH, expand=True)

        product_dropdown = AutocompleteCombobox(frame, placeholder="Selecciona un producto:")
        product_dropdown.grid(column=0, row=0, padx=10, pady=10, sticky='ew')
        self.load_products_combobox(product_dropdown)

        quantity_entry = ttk.Entry(frame)
        quantity_entry.grid(column=1, row=0, padx=10, pady=10, sticky='ew')

        # Placeholder para cantidad
        quantity_entry.insert(0, "Introduce la cantidad")
        quantity_entry.config(foreground='grey')
        quantity_entry.bind("<FocusIn>", lambda event: self.clear_placeholder(event, quantity_entry, "Introduce la cantidad"))
        quantity_entry.bind("<FocusOut>", lambda event: self.add_placeholder(event, quantity_entry, "Introduce la cantidad"))

        add_button = ttk.Button(
            frame,
            text="Añadir",
            command=lambda: self.add_item_to_list(product_dropdown, quantity_entry)
        )
        add_button.grid(column=2, row=0, padx=10, pady=10)

        columns = ('Producto', 'Descripción', 'Cantidad', 'Precio', 'Total')
        self.invoice_item_temp_list = ttk.Treeview(frame, columns=columns, show='headings')
        self.invoice_item_temp_list.heading('Producto', text='Producto')
        self.invoice_item_temp_list.heading('Descripción', text='Descripción')
        self.invoice_item_temp_list.heading('Cantidad', text='Cantidad')
        self.invoice_item_temp_list.heading('Precio', text='Precio')
        self.invoice_item_temp_list.heading('Total', text='Total')
        self.invoice_item_temp_list.column('Producto', width=150)
        self.invoice_item_temp_list.column('Descripción', width=200)
        self.invoice_item_temp_list.column('Cantidad', width=80)
        self.invoice_item_temp_list.column('Precio', width=80)
        self.invoice_item_temp_list.column('Total', width=80)

        self.invoice_item_temp_list_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.invoice_item_temp_list.yview)
        self.invoice_item_temp_list.configure(yscrollcommand=self.invoice_item_temp_list_scrollbar.set)

        self.invoice_item_temp_list.grid(column=0, row=1, columnspan=2, padx=10, pady=10, sticky='nsew')
        self.invoice_item_temp_list_scrollbar.grid(column=2, row=1, sticky='ns')

        confirm_button = ttk.Button(
            frame,
            text="Confirmar Productos",
            command=lambda: self.confirm_items(top)
        )
        confirm_button.grid(column=0, row=2, columnspan=3, padx=10, pady=10, sticky='ew')

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(1, weight=1)

    def confirm_items(self, top):
        if not self.invoice_item_entries:
            messagebox.showerror('Error', 'Debe añadir al menos un producto antes de confirmar.')
            return
        self.invoice_items.extend(self.invoice_item_entries)
        self.update_invoice_item_list()
        top.destroy()

    def add_item_to_list(self, product_dropdown, quantity_entry):
        product_text = product_dropdown.get()
        quantity_text = quantity_entry.get()

        if product_text == "Selecciona un producto:" or not product_text:
            messagebox.showerror('Error', 'Debe seleccionar un producto.')
            return

        if not quantity_text or quantity_text == "Introduce la cantidad":
            messagebox.showerror('Error', 'Debe introducir una cantidad.')
            return

        try:
            product_id = int(product_text.split(' ')[0])
            quantity = int(quantity_text)
        except ValueError:
            messagebox.showerror('Error', 'Cantidad inválida.')
            return

        price = get_product_price(product_id)
        product_name = get_product_name(product_id)
        product_description = get_product_description(product_id)

        self.invoice_item_temp_list.insert('', 'end', values=(product_name, product_description, quantity, f"{price} €", f"{quantity * price} €"))
        self.invoice_item_entries.append({
            'product_id': product_id,
            'quantity': quantity,
            'price': price
        })

        # Resetear los campos
        product_dropdown.set('Selecciona un producto:')
        quantity_entry.delete(0, tk.END)
        quantity_entry.insert(0, "Introduce la cantidad")

    def generate_document(self):
        client_selection = self.client_dropdown.get()
        if not client_selection or client_selection == "Selecciona un cliente:":
            messagebox.showerror('Error', 'Debe seleccionar un cliente.')
            return

        if not self.invoice_items:
            messagebox.showerror('Error', 'Debe añadir al menos un producto.')
            return
        try:
            client_id = int(self.client_dropdown.get().split(' ')[0])
        except ValueError:
            messagebox.showerror('Error', 'Selección de cliente inválida.')
            return

        items = self.invoice_items[:]
        self.invoice_items = []

        client_name = get_client_name(client_id)
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        date_str = datetime.now().strftime('%Y%m%d')

        doc_type = self.doc_type.get()
        apply_iva = self.apply_iva.get()

        base_total = sum(item['quantity'] * item['price'] for item in items)
        iva_amount = base_total * 0.21 if apply_iva else 0
        total = base_total + iva_amount

        doc_id = insert_document(client_id, date, total, self.payment_method.get(), items, apply_iva, doc_type)

        pdf, _, _, _ = create_document(client_id, items, self.payment_method.get(), doc_type, apply_iva, doc_id)

        default_filename = f"{doc_type}_{doc_id}_{client_name}_{date_str}.pdf"
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default_filename, filetypes=[("PDF files", "*.pdf")])

        if filename:
            save_invoice(pdf, filename)
            messagebox.showinfo('Información', f'{doc_type} generado con éxito')
        else:
            cursor.execute(f"DELETE FROM {'invoices' if doc_type == 'Factura' else 'budgets'} WHERE id = ?", (doc_id,))
            conn.commit()
            messagebox.showwarning('Advertencia', 'Generación de documento cancelada')
        
        self.client_dropdown.set('Selecciona un cliente:')
        self.update_invoice_item_list()
        self.load_documents_list()
        self.apply_iva.set(True)

    def generate_quarter_invoices(self):
        quarter = self.quarter.get()
        year = self.year.get()

        pdfs = []
        months = {
            "1": ("01", "02", "03"),
            "2": ("04", "05", "06"),
            "3": ("07", "08", "09"),
            "4": ("10", "11", "12")
        }

        start_date = f"{year}-{months[quarter][0]}-01"
        end_date = f"{year}-{months[quarter][2]}-31"

        cursor.execute('''
            SELECT id, client_id, date, total, payment_method, apply_iva
            FROM invoices
            WHERE date BETWEEN ? AND ?
        ''', (start_date, end_date))

        invoices = cursor.fetchall()

        for invoice in invoices:
            invoice_id, client_id, date, total, payment_method, apply_iva = invoice
            cursor.execute('SELECT product_id, quantity, price FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
            items = cursor.fetchall()
            items = [{'product_id': item[0], 'quantity': item[1], 'price': item[2]} for item in items]

            cursor.execute('SELECT name FROM clients WHERE id = ?', (client_id,))
            client_name = cursor.fetchone()[0]

            pdf, _ = create_document_from_existing(invoice_id, client_id, date, total, payment_method, items, 'Factura', apply_iva)
            formatted_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')
            filename = f"Factura_{invoice_id}_{client_name}_{formatted_date}.pdf"
            pdfs.append((pdf, filename))

        if not pdfs:
            messagebox.showinfo('Información', 'No hay facturas para el trimestre seleccionado')
            return

        folder_name = f"Facturas_{quarter}_Trimestre_{year}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        for pdf, filename in pdfs:
            pdf.output(os.path.join(folder_name, filename))

        messagebox.showinfo('Información', f'Facturas generadas con éxito en el directorio {folder_name}')