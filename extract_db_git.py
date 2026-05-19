#!/usr/bin/env python3
"""Extraer BD de git sin procesar."""
import subprocess
import sys
import os

# Obtener el contenido del blob de git de forma bruta
result = subprocess.run(
    ['git', 'cat-file', 'blob', '74f9646:instance/app.db'],
    capture_output=True,
    text=False  # Obtener bytes, no texto
)

blob_data = result.stdout

print(f"Tamaño del blob desde git: {len(blob_data)} bytes")
print(f"Primeros 32 bytes: {blob_data[:32]}")

# El problema parece ser que git está guardando archivos binarios en UTF-16LE
# Vamos a intentar obtener la lista de objetos git
print("\nInvestigando archivos en git...")
result2 = subprocess.run(
    ['git', 'ls-tree', '-r', '74f9646', '--', 'instance/app.db'],
    capture_output=True,
    text=True
)
print(result2.stdout)

# Buscar en el historial
print("\nHistorial de la BD:")
result3 = subprocess.run(
    ['git', 'log', '--name-status', '--oneline', '--', 'instance/app.db'],
    capture_output=True,
    text=True
)
print(result3.stdout)
