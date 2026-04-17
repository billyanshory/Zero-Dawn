import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# 1. Extract the inline HTML from handle_exception
# The handler looks like this:
# @app.errorhandler(500)
# @app.errorhandler(Exception)
# def handle_exception(e):
#     ...
#     return """...""", 500

error_html_start = content.find("def handle_exception(e):")
if error_html_start != -1:
    return_start = content.find("return \"\"\"", error_html_start)
    if return_start != -1:
        # the literal is between return """ and """, 500
        # actually, let's just use regex to extract it
        match = re.search(r'return (\'\'\'|""")([\s\S]*?)\1, 500', content[error_html_start:])
        if match:
            literal = match.group(0)
            html_content = match.group(2)
            quote = match.group(1)

            # create the constant
            constant_def = f"# ============================================================\n# TEMPLATE: ERROR_500_HTML\n# CONSUMED BY: handle_exception\n# ============================================================\nERROR_500_HTML = {quote}{html_content}{quote}\n"

            # place it right before the handler
            handler_decorator = content.rfind("@app.errorhandler(500)", 0, error_html_start)
            content = content[:handler_decorator] + constant_def + "\n" + content[handler_decorator:]

            # replace the literal with the constant
            content = content.replace(literal, "return ERROR_500_HTML, 500")

with open(fname, 'w') as f:
    f.write(content)
