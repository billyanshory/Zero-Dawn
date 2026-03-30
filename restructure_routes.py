import re
import ast

filename = 'kampus-stie-samarinda-18 ( idcloudhost - bug fatal - focus di tracer study & pmb digital ).py'
with open(filename, 'r', encoding='utf-8') as f:
    code = f.read()

tree = ast.parse(code)

def get_decorators(node):
    decs = []
    for d in node.decorator_list:
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
            if d.func.value.id == 'app' and d.func.attr == 'route':
                if d.args and isinstance(d.args[0], ast.Constant):
                    decs.append(d.args[0].value)
    return decs

route_funcs = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        routes = get_decorators(node)
        if routes:
            route_funcs.append((node, routes))

# We will classify them into categories:
# 1. Public / Global
# 2. Tata Usaha (TU) -> routes starting with /tu/ or /seed-admin or /donate/update
# 3. Mahasiswa -> routes starting with /mahasiswa/ or /pmb/ (if any PMB routes exist)
# 4. Dosen -> routes starting with /dosen/
# 5. Legacy / Features -> /ramadhan, /irma, /masjid (Wait, there are many legacy endpoints like /finance, /agenda, /zakat)

# Let's map function names to routes to know what to group
for f, r in route_funcs:
    print(f.name, r)
