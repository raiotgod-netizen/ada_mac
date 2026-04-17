from pathlib import Path

root = Path(__file__).resolve().parent.parent
print('Proyecto ADA:', root)
print('Contenido raíz:')
for item in sorted(root.iterdir()):
    print('-', item.name)
