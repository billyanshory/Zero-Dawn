import ast

with open("backup.py", "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)

# Let's see all top-level statements
for i, node in enumerate(tree.body):
    if isinstance(node, ast.Assign):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            print(f"{i} Assign: {node.targets[0].id}")
    else:
        print(f"{i} {type(node).__name__}")
