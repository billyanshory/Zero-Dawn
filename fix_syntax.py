import sys

filename = "sekolah-luar-biasa-69 ( idcloudhost - debugging - waktu, save data, warna tab, jadwal medis error, tambah kamus, json file kamus, api modul  - Opus 4.6 ).py"

with open(filename, 'r') as f:
    content = f.read()

# Fix 1: Add missing </style> tag
content = content.replace('        }\n\n"""\n\nBASE_LAYOUT', '        }\n    </style>\n"""\n\nBASE_LAYOUT')

# Fix 2: Handle fetchHijri leftover. The leftover might look like this near `updateDate` or similar. Let's see how `fetchHijri` was deleted.
import re

# Fix 1: Add missing </style> tag
content = content.replace('        }\n\n"""\n\nBASE_LAYOUT', '        }\n    </style>\n"""\n\nBASE_LAYOUT')

# Fix 2: Remove orphaned braces in openModal
# Notice lines 1219 to 1222:
# 1219
# 1220	                }
# 1221	            }
# 1222	        }
# We should replace this with just two closing braces
content = content.replace("""                el.classList.remove('hidden');
                history.pushState({modal: id}, null, "");

                }
            }
        }""", """                el.classList.remove('hidden');
                history.pushState({modal: id}, null, "");
            }
        }""")

# Fix 3: Remove orphaned brace around updateDate. The code reads:
#   1210	            setInterval(updateDate, 1000); // Update every second for real-time clock
#   1211	        }
content = content.replace("""            setInterval(updateDate, 1000); // Update every second for real-time clock
        }""", """            setInterval(updateDate, 1000); // Update every second for real-time clock""")

with open(filename, 'w') as f:
    f.write(content)
