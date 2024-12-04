from database import add_product, add_client

def add_new_product(name, description, price):
    add_product(name, description, price)

def add_new_client(name, email, address, phone, dni):
    add_client(name, email, address, phone, dni)
