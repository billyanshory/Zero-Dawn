import re
import ast

def scan_file(filename):
    with open(filename, 'r') as f:
        source = f.read()

    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            is_route = False
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    if dec.func.attr == 'route':
                        is_route = True
                        break

            if is_route:
                has_db = False
                has_try = False
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Attribute) and subnode.attr == 'query':
                        has_db = True
                    if isinstance(subnode, ast.Name) and subnode.id == 'db':
                        has_db = True
                    if isinstance(subnode, ast.Try):
                        has_try = True

                if has_db and not has_try:
                    print(f"Route '{node.name}' (line {node.lineno}) uses DB but lacks try-except.")

scan_file("masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py")
