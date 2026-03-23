with open('klinik-delima-dalam-39 ( IdCloudHost - Tata Letak Lay Out & Hierarki Visual Tampilan Interface UI-UX ).py') as f:
    text = f.read()

idx = text.find('HTML_DASHBOARD =')
print("START:\n", text[idx:idx+150])
print("\nEND:\n", text[idx+7800:idx+8000])
