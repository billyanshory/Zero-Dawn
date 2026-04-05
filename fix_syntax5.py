file_path = "kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import re
content = re.sub(r'\n<script>\nasync function refreshCaptcha\(\).*?</script>\n', '', content, flags=re.DOTALL)

html_to_append = """
<script>
async function refreshCaptcha() {
    try {
        const fd = new FormData();
        const csrfToken = document.querySelector('input[name="csrf_token"]');
        if (csrfToken) fd.append('csrf_token', csrfToken.value);
        const res = await fetch('/api/captcha/refresh', {method: 'POST', body: fd});
        const data = await res.json();
        const el = document.getElementById('captcha-question');
        if (el) el.innerText = `Berapa hasil dari ${data.a} + ${data.b}? (CAPTCHA)`;
    } catch(e) { console.error(e); }
}
</script>
"""

content = content.replace('RAMADHAN_DASHBOARD_HTML = """', html_to_append + '\n"""\n\nRAMADHAN_DASHBOARD_HTML = """')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
