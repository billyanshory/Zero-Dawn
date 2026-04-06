import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. BUG-019 (backdrop-filter) & BUG-020 (will-change) in STYLES_HTML
search_css = """        .glass-nav {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .glass-bottom {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(0,0,0,0.05);
        }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:active { transform: scale(0.98); }
        .pb-safe { padding-bottom: env(safe-area-inset-bottom, 20px); }

        /* NEUMORPHISM & CORK BOARD EFFECTS */
        .cork-board {
            background-color: #e5d1b8;
            background-image: radial-gradient(#d3bfa2 15%, transparent 16%), radial-gradient(#d3bfa2 15%, transparent 16%);
            background-size: 8px 8px;
            background-position: 0 0, 4px 4px;
            box-shadow: inset 0 0 40px rgba(100, 70, 40, 0.4);
            border-radius: 2.5rem;
            position: relative;
        }

        .acrylic-card {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.8);
            border-top: 2px solid rgba(255, 255, 255, 1);
            border-left: 2px solid rgba(255, 255, 255, 0.9);
            box-shadow:
                8px 12px 20px rgba(0, 0, 0, 0.25),
                inset -2px -2px 10px rgba(0,0,0,0.05),
                inset 2px 2px 10px rgba(255,255,255,1);
            border-radius: 1.5rem;
            transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
            transform-origin: center center;
            position: relative;
            z-index: 10;
            will-change: transform, box-shadow;
        }"""

replace_css = """        .glass-nav {
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .glass-bottom {
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.05);
            border-top: 1px solid rgba(0,0,0,0.05);
        }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:active { transform: scale(0.98); }
        .pb-safe { padding-bottom: env(safe-area-inset-bottom, 20px); }

        /* NEUMORPHISM & CORK BOARD EFFECTS */
        .cork-board {
            background-color: #e5d1b8;
            background-image: radial-gradient(#d3bfa2 15%, transparent 16%), radial-gradient(#d3bfa2 15%, transparent 16%);
            background-size: 8px 8px;
            background-position: 0 0, 4px 4px;
            box-shadow: inset 0 0 40px rgba(100, 70, 40, 0.4);
            border-radius: 2.5rem;
            position: relative;
        }

        .acrylic-card {
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.8);
            border-top: 2px solid rgba(255, 255, 255, 1);
            border-left: 2px solid rgba(255, 255, 255, 0.9);
            box-shadow:
                8px 12px 20px rgba(0, 0, 0, 0.25),
                inset -2px -2px 10px rgba(0,0,0,0.05),
                inset 2px 2px 10px rgba(255,255,255,1);
            border-radius: 1.5rem;
            transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
            transform-origin: center center;
            position: relative;
            z-index: 10;
        }
        @supports (backdrop-filter: blur(1px)) {
            @media (min-resolution: 2dppx) {
                .acrylic-card {
                    backdrop-filter: blur(16px);
                    -webkit-backdrop-filter: blur(16px);
                }
            }
        }
        .acrylic-card:hover, .acrylic-card:focus-within {
            will-change: transform, box-shadow;
        }"""

if search_css in content:
    content = content.replace(search_css, replace_css)

search_btn = """        .neumorphic-btn {
            background: #f8fafc;
            border-radius: 1.5rem;
            box-shadow:
                6px 6px 12px rgba(163, 177, 198, 0.6),
                -6px -6px 12px rgba(255, 255, 255, 0.9),
                inset 1px 1px 2px rgba(255, 255, 255, 0.8),
                inset -1px -1px 2px rgba(163, 177, 198, 0.2);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.4);
            will-change: transform, box-shadow;
        }"""

replace_btn = """        .neumorphic-btn {
            background: #f8fafc;
            border-radius: 1.5rem;
            box-shadow:
                6px 6px 12px rgba(163, 177, 198, 0.6),
                -6px -6px 12px rgba(255, 255, 255, 0.9),
                inset 1px 1px 2px rgba(255, 255, 255, 0.8),
                inset -1px -1px 2px rgba(163, 177, 198, 0.2);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.4);
        }
        .neumorphic-btn:hover, .neumorphic-btn:active {
            will-change: transform, box-shadow;
        }"""

if search_btn in content:
    content = content.replace(search_btn, replace_btn)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("BUG-019 & 020 Patched.")
