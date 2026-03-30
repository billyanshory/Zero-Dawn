import libcst as cst
from libcst.metadata import PositionProvider

with open("backup.py", "r", encoding="utf-8") as f:
    text = f.read()

class FindHTMLVars(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        self.html_vars = []

    def visit_Assign(self, node: cst.Assign):
        if len(node.targets) == 1 and isinstance(node.targets[0].target, cst.Name):
            name = node.targets[0].target.value
            if name in ['STYLES_HTML', 'BASE_LAYOUT', 'FITUR_MASJID_HTML', 'HOME_HTML', 'RAMADHAN_STYLES', 'RAMADHAN_DASHBOARD_HTML', 'IRMA_STYLES', 'IRMA_DASHBOARD_HTML']:
                pos = self.get_metadata(PositionProvider, node)
                self.html_vars.append((name, pos.start.line, pos.end.line))

wrapper = cst.MetadataWrapper(cst.parse_module(text))
visitor = FindHTMLVars()
wrapper.visit(visitor)

print("Found HTML vars:", len(visitor.html_vars))
for m in visitor.html_vars:
    print(m)
