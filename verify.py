import ast
import sys

def verify_syntax(filepath):
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        print(f"Syntax OK: {filepath}")
        return True
    except SyntaxError as e:
        print(f"Syntax Error in {filepath}: {e}")
        return False

verify_syntax("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py")
