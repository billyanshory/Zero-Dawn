with open("backup.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

html_var_ranges = []
import ast

tree = ast.parse("".join(lines))
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in ['STYLES_HTML', 'BASE_LAYOUT', 'FITUR_MASJID_HTML', 'HOME_HTML', 'RAMADHAN_STYLES', 'RAMADHAN_DASHBOARD_HTML', 'IRMA_STYLES', 'IRMA_DASHBOARD_HTML']:
            html_var_ranges.append((name, node.lineno - 1, node.end_lineno))

for name, s, e in html_var_ranges:
    print(f"{name}: {s} - {e}")
