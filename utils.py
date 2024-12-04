import os
import time

def is_file_in_use(filepath, max_attempts=10):
    attempts = 0
    while attempts < max_attempts:
        try:
            os.remove(filepath)
            break
        except PermissionError:
            attempts += 1
            time.sleep(1)
    if attempts == max_attempts:
        print(f"Error: No se pudo eliminar el archivo {filepath} después de {max_attempts} intentos.")
