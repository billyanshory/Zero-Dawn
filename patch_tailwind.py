import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove tailwind script and config, and replace with linked minified stylesheet
search_tailwind = """    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                emerald: {
                  50: '#ecfdf5',
                  100: '#d1fae5',
                  400: '#34d399',
                  500: '#10b981',
                  600: '#059669',
                },
                amber: {
                  300: '#fcd34d',
                  400: '#fbbf24',
                }
              },
              fontFamily: {
                sans: ['Poppins', 'sans-serif'],
              },
              borderRadius: {
                '3xl': '1.5rem',
              }
            }
          }
        }
    </script>"""

replace_tailwind = """    <link rel="stylesheet" href="/static/tailwind.min.css">"""

if search_tailwind in content:
    content = content.replace(search_tailwind, replace_tailwind)

# There is also one in SW.js caching list, but we can replace it just in case
content = content.replace("'https://cdn.tailwindcss.com'", "'/static/tailwind.min.css'")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("BUG-012 Patched.")
