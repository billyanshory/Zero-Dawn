import libcst as cst

with open("backup.py", "r", encoding="utf-8") as f:
    source = f.read()

tree = cst.parse_module(source)

html_vars = []
models = []
routes = []
other = []

for stmt in tree.body:
    if isinstance(stmt, cst.SimpleStatementLine):
        if isinstance(stmt.body[0], cst.Assign):
            assign = stmt.body[0]
            if len(assign.targets) == 1 and isinstance(assign.targets[0].target, cst.Name):
                name = assign.targets[0].target.value
                html_vars.append((name, stmt))
            else:
                other.append(stmt)
        else:
            other.append(stmt)
    elif isinstance(stmt, cst.ClassDef):
        if any(isinstance(base.value, cst.Attribute) and base.value.attr.value == 'Model' for base in stmt.bases):
            models.append((stmt.name.value, stmt))
        else:
            other.append(stmt)
    elif isinstance(stmt, cst.FunctionDef):
        is_route = any(
            isinstance(dec.decorator, cst.Call) and
            isinstance(dec.decorator.func, cst.Attribute) and
            dec.decorator.func.attr.value == 'route'
            for dec in stmt.decorators
        )
        if is_route:
            routes.append((stmt.name.value, stmt))
        else:
            other.append(stmt)
    else:
        other.append(stmt)

print("HTML Vars:", [n for n, _ in html_vars])
print("Models:", [n for n, _ in models])
print("Routes:", len(routes))
