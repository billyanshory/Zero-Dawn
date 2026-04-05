file_path = "kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's insert it inside the <script> block in HOME_HTML
# We know there is a function openModal(id) in HOME_HTML
# We'll just insert it right before function openModal(id)

js_to_insert = """
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

"""

content = content.replace("function openModal(id) {", js_to_insert + "function openModal(id) {", 1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
