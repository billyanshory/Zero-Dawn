import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

old_pdf_footer = """        footer_text = (f"<i>Disclaimer: This report was generated automatically by GambitHunter. "
                       f"Report ID: {html.escape(str(scan_data.get('scan_id')))}<br/>"
                       f"SHA-256 Integrity Hash: {report_hash}</i>")
        elements.append(Paragraph(footer_text, normal_style))"""

new_pdf_footer = """        elements.append(Paragraph(f"<font size=8>SHA-256: {report_hash}</font>", normal_style))
        footer_text = (f"<i>Disclaimer: This report was generated automatically by GambitHunter. "
                       f"Report ID: {html.escape(str(scan_data.get('scan_id')))}<br/>"
                       f"SHA-256 Integrity Hash: {report_hash}</i>")
        elements.append(Paragraph(footer_text, normal_style))"""

content = content.replace(old_pdf_footer, new_pdf_footer)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
