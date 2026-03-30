import ast

with open("backup.py", "r", encoding="utf-8") as f:
    source = f.read()

lines = source.split("\n")

tree = ast.parse(source)

for node in tree.body:
    if isinstance(node, ast.ClassDef):
        print(f"Class {node.name}: {node.lineno} - {node.end_lineno}")
    elif isinstance(node, ast.FunctionDef):
        print(f"Func {node.name}: {node.lineno} - {node.end_lineno}")
    elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id in ['STYLES_HTML', 'BASE_LAYOUT', 'FITUR_MASJID_HTML', 'HOME_HTML', 'RAMADHAN_STYLES', 'RAMADHAN_DASHBOARD_HTML', 'IRMA_STYLES', 'IRMA_DASHBOARD_HTML']:
            print(f"HTML {node.targets[0].id}: {node.lineno} - {node.end_lineno}")
