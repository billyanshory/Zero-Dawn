import ast

with open("backup.py", "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)

html_vars = []
models = []
routes = []
others = []

for node in tree.body:
    if isinstance(node, ast.Assign):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            # check if it's a multiline string
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                if len(node.value.value) > 200 and ('<' in node.value.value or 'html' in node.value.value.lower() or 'style' in node.value.value.lower()):
                    html_vars.append(var_name)
    elif isinstance(node, ast.ClassDef):
        if any(isinstance(base, ast.Attribute) and base.attr == 'Model' for base in node.bases):
            models.append(node.name)
    elif isinstance(node, ast.FunctionDef):
        is_route = any(isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == 'route' for dec in node.decorator_list)
        if is_route:
            routes.append(node.name)

print("HTML Vars:", html_vars)
print("Models:", models)
print("Routes:", len(routes), routes)
