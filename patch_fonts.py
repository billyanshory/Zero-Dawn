import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove @import
content = content.replace("@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');\n", "")
content = content.replace("        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');\n", "")

# 2. Add <link> to BASE_LAYOUT
search_head = """    <title>Sekolah Luar Biasa</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {{ styles|safe }}
</head>"""

replace_head = """    <title>Sekolah Luar Biasa</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Poppins:wght@300;400;500;600;700&display=swap" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Poppins:wght@300;400;500;600;700&display=swap"></noscript>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"></noscript>
    {{ styles|safe }}
</head>"""

if search_head in content:
    content = content.replace(search_head, replace_head)
else:
    print("head not found")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("BUG-013 & BUG-014 Patched.")
