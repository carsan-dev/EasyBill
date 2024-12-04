import os
import sqlite3

if not os.path.exists('DB'):
    os.makedirs('DB')

if not os.path.exists('IMG'):
    os.makedirs('IMG')

conn = sqlite3.connect(os.path.join('DB', 'billing.db'))
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    address TEXT,
    phone TEXT,
    dni TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    date TEXT,
    total REAL,
    payment_method TEXT,
    apply_iva INTEGER DEFAULT 0,
    FOREIGN KEY(client_id) REFERENCES clients(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY,
    client_id INTEGER,
    date TEXT,
    total REAL,
    payment_method TEXT,
    apply_iva INTEGER DEFAULT 0,
    FOREIGN KEY(client_id) REFERENCES clients(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY,
    invoice_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS budget_items (
    id INTEGER PRIMARY KEY,
    budget_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY(budget_id) REFERENCES budgets(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
''')

conn.commit()

def add_product(name, description, price):
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
    conn.commit()

def add_client(name, email, address, phone, dni):
    cursor.execute('INSERT INTO clients (name, email, address, phone, dni) VALUES (?, ?, ?, ?, ?)', (name, email, address, phone, dni))
    conn.commit()

def update_product(product_id, name, description, price):
    cursor.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', (name, description, price, product_id))
    conn.commit()

def update_client(client_id, name, email, address, phone, dni):
    cursor.execute('UPDATE clients SET name = ?, email = ?, address = ?, phone = ?, dni = ? WHERE id = ?', (name, email, address, phone, dni, client_id))
    conn.commit()

def update_invoice(invoice_id, client_id, date, total, payment_method, apply_iva):
    cursor.execute('''
        UPDATE invoices
        SET client_id = ?, date = ?, total = ?, payment_method = ?, apply_iva = ?
        WHERE id = ?
    ''', (client_id, date, total, payment_method, apply_iva, invoice_id))
    conn.commit()

def update_budget(budget_id, client_id, date, total, payment_method, apply_iva):
    cursor.execute('''
        UPDATE budgets
        SET client_id = ?, date = ?, total = ?, payment_method = ?, apply_iva = ?
        WHERE id = ?
    ''', (client_id, date, total, payment_method, apply_iva, budget_id))
    conn.commit()

def update_invoice_items(invoice_id, items):
    # Primero elimina todos los items de la factura existente
    cursor.execute('DELETE FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
    # Luego inserta los nuevos items
    for item in items:
        cursor.execute('INSERT INTO invoice_items (invoice_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', 
                       (invoice_id, item['product_id'], item['quantity'], item['price']))
    conn.commit()

def update_budget_items(budget_id, items):
    # Primero elimina todos los items del presupuesto existente
    cursor.execute('DELETE FROM budget_items WHERE budget_id = ?', (budget_id,))
    # Luego inserta los nuevos items
    for item in items:
        cursor.execute('INSERT INTO budget_items (budget_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', 
                       (budget_id, item['product_id'], item['quantity'], item['price']))
    conn.commit()


def get_client_name(client_id):
    cursor.execute('SELECT name FROM clients WHERE id = ?', (client_id,))
    return cursor.fetchone()[0]

def get_product_price(product_id):
    cursor.execute('SELECT price FROM products WHERE id = ?', (product_id,))
    price = cursor.fetchone()[0]
    return price

def get_product_description(product_id):
    cursor.execute('SELECT description FROM products WHERE id = ?', (product_id,))
    return cursor.fetchone()[0]

def fetch_clients():
    cursor.execute('SELECT id, name FROM clients')
    return cursor.fetchall()

def fetch_products():
    cursor.execute('SELECT id, name FROM products')
    return cursor.fetchall()

def fetch_all_products():
    cursor.execute('SELECT * FROM products ORDER BY name COLLATE NOCASE ASC')
    return cursor.fetchall()

def fetch_all_clients():
    cursor.execute('SELECT * FROM clients ORDER BY name COLLATE NOCASE ASC')
    return cursor.fetchall()

def fetch_all_documents():
    cursor.execute('''
        SELECT invoices.id, clients.name, invoices.date, invoices.total, 'Factura' AS doc_type, 
        (SELECT GROUP_CONCAT(products.name, ', ') 
         FROM invoice_items 
         JOIN products ON invoice_items.product_id = products.id 
         WHERE invoice_items.invoice_id = invoices.id) AS products
        FROM invoices
        JOIN clients ON invoices.client_id = clients.id
        UNION ALL
        SELECT budgets.id, clients.name, budgets.date, budgets.total, 'Presupuesto' AS doc_type, 
        (SELECT GROUP_CONCAT(products.name, ', ') 
         FROM budget_items 
         JOIN products ON budget_items.product_id = products.id 
         WHERE budget_items.budget_id = budgets.id) AS products
        FROM budgets
        JOIN clients ON budgets.client_id = clients.id
    ''')
    return cursor.fetchall()

def insert_invoice(client_id, date, total, payment_method, items, apply_iva):
    cursor.execute('INSERT INTO invoices (client_id, date, total, payment_method, apply_iva) VALUES (?, ?, ?, ?, ?)', (client_id, date, total, payment_method, apply_iva))
    invoice_id = cursor.lastrowid
    for item in items:
        cursor.execute('INSERT INTO invoice_items (invoice_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', 
                       (invoice_id, item['product_id'], item['quantity'], item['price']))
    conn.commit()
    return invoice_id

def insert_budget(client_id, date, total, payment_method, items, apply_iva):
    cursor.execute('INSERT INTO budgets (client_id, date, total, payment_method, apply_iva) VALUES (?, ?, ?, ?, ?)', (client_id, date, total, payment_method, apply_iva))
    budget_id = cursor.lastrowid
    for item in items:
        cursor.execute('INSERT INTO budget_items (budget_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', 
                       (budget_id, item['product_id'], item['quantity'], item['price']))
    conn.commit()
    return budget_id

def delete_invoice(invoice_id):
    # Primero elimina todos los items asociados a la factura
    cursor.execute('DELETE FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
    # Luego elimina la factura
    cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
    conn.commit()

def delete_budget(budget_id):
    # Primero elimina todos los items asociados al presupuesto
    cursor.execute('DELETE FROM budget_items WHERE budget_id = ?', (budget_id,))
    # Luego elimina el presupuesto
    cursor.execute('DELETE FROM budgets WHERE id = ?', (budget_id,))
    conn.commit()

def get_product_name(product_id):
    cursor.execute('SELECT name FROM products WHERE id = ?', (product_id,))
    return cursor.fetchone()[0]
