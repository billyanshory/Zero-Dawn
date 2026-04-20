with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

# Replace tailwind
text = text.replace('<link href="/static/tailwind.min.css" rel="stylesheet" integrity="sha384-dummy" crossorigin="anonymous">', '<link href="/static/tailwind.min.css" rel="stylesheet">')

# Replace all.min.css (Font awesome)
text = text.replace('<noscript><link href="/static/all.min.css" rel="stylesheet" integrity="sha384-dummy" crossorigin="anonymous"></noscript>', '<noscript><link href="/static/all.min.css" rel="stylesheet"></noscript>')

# Replace confetti
text = text.replace('<script src="/static/confetti.browser.min.js" integrity="sha384-dummy" crossorigin="anonymous"></script>', '<script src="/static/confetti.browser.min.js"></script>')

# Replace dead JIT script with new root CSS vars
search_script = """    <script>tailwind.config = { theme: { extend: { colors: { emerald: { 50: '#ecfdf5', 100: '#d1fae5', 400: '#34d399', 500: '#10b981', 600: '#059669' }, amber: { 300: '#fcd34d', 400: '#fbbf24' } }, fontFamily: { sans: ['Poppins', 'sans-serif'] }, borderRadius: { '3xl': '1.5rem' } } } }</script>
    <style>"""

replace_script = """    <style>
        :root {
            --color-emerald-50: #ecfdf5;
            --color-emerald-100: #d1fae5;
            --color-emerald-400: #34d399;
            --color-emerald-500: #10b981;
            --color-emerald-600: #059669;
            --color-amber-300: #fcd34d;
            --color-amber-400: #fbbf24;
        }
        .bg-emerald-50 { background-color: var(--color-emerald-50); }
        .bg-emerald-100 { background-color: var(--color-emerald-100); }
        .bg-emerald-400 { background-color: var(--color-emerald-400); }
        .bg-emerald-500 { background-color: var(--color-emerald-500); }
        .bg-emerald-600 { background-color: var(--color-emerald-600); }
        .text-emerald-500 { color: var(--color-emerald-500); }
        .text-emerald-600 { color: var(--color-emerald-600); }
        .bg-amber-300 { background-color: var(--color-amber-300); }
        .bg-amber-400 { background-color: var(--color-amber-400); }
        .text-amber-400 { color: var(--color-amber-400); }
        .rounded-3xl { border-radius: 1.5rem; }
        body, html { font-family: 'Poppins', sans-serif; }"""

text = text.replace(search_script, replace_script)

with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
    f.write(text)
