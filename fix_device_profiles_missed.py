import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# I missed defining DEVICE_PROFILES when I re-ran the fix earlier.
device_profiles_def = """DEVICE_PROFILES = [
    {
        "viewport": {"width": 1366, "height": 768},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "device_scale_factor": 1.0,
        "is_mobile": False,
        "has_touch": False,
        "Sec-CH-UA-Platform": '"Windows"'
    },
    {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "device_scale_factor": 1.0,
        "is_mobile": False,
        "has_touch": False,
        "Sec-CH-UA-Platform": '"Windows"'
    },
    {
        "viewport": {"width": 412, "height": 915},
        "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "device_scale_factor": 2.625,
        "is_mobile": True,
        "has_touch": True,
        "Sec-CH-UA-Platform": '"Android"'
    }
]"""

content = content.replace("async def scrape_url_with_playwright(url: str) -> str:", f"{device_profiles_def}\n\nasync def scrape_url_with_playwright(url: str) -> str:")

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
