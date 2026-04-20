with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search = """        doc.build(Story)
        buffer.seek(0)
        return Response(buffer, mimetype='application/pdf', headers={'Content-Disposition': f'attachment;filename=IEP_{student_name}.pdf'})"""

replace = """        doc.build(Story)
        buffer.seek(0)
        opaque_token = uuid.uuid4().hex[:12]

        headers = {
            'Content-Disposition': f'attachment;filename=IEP_{opaque_token}.pdf',
            'X-Content-Type-Options': 'nosniff',
            'Cache-Control': 'no-store'
        }
        return Response(buffer, mimetype='application/pdf', headers=headers)"""

if search in text:
    text = text.replace(search, replace)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
