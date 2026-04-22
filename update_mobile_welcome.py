import re

with open("masjid-al-hijrah-61 ( idcloudhost - tombol akses, page, & first fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# We need to add the mobile-visible welcome section (since the previous welcome is desktop only: `hidden md:block`).
# For mobile users, the prompt said:
# "Transitioning to our mobile, Android, and iOS users, your directive is to execute a clean, permanent removal of that same redundant 'Idul Adha Mode Portal' banner, as screen real estate on mobile devices is a critical priority. In its place, at the very zenith of the mobile viewport, you must position the dynamic prayer times card as the primary focal point."
# The prayer times card is currently in `RIGHT COLUMN` which will render AFTER the `LEFT COLUMN` on mobile if it was visible, but since LEFT is hidden, the prayer card is the only thing visible at the top!
# Wait! "Below this primary header layer, for both desktop and mobile views, you must meticulously organize the primary functional buttons: 'Menu Qurban'..."
# Wait, did it ask for the text and buttons to be on mobile too?
# "Below this primary header layer, for both desktop and mobile views, you must meticulously organize the primary functional buttons: 'Menu Qurban', the time-gated 'Absen Panitia' ..."
# Let me re-read: "For desktop and wide-screen users, you must re-engineer the top section of the Idul Adha dashboard to mirror the sophisticated dual-panel layout found on our primary home and Ramadhan pages. On the left panel, craft a spiritually resonant welcoming interface featuring a greeting... On the right... prayer times card"
# "Transitioning to our mobile... at the very zenith of the mobile viewport, you must position the dynamic prayer times card as the primary focal point. ... Below this primary header layer, for both desktop and mobile views, you must meticulously organize the primary functional buttons: 'Menu Qurban'..."
# This implies the greeting and the 'Lihat Agenda' / 'Infaq Sekarang' buttons are DESKTOP ONLY, or if they are on mobile, they should be below the prayer card but ABOVE the Menu Qurban.
# However, "Below this primary header layer, for both desktop and mobile views, you must meticulously organize the primary functional buttons: 'Menu Qurban'..."
# This strongly implies the mobile view *only* has the Prayer Card at the top, and then goes straight to 'Menu Qurban', skipping the long text and 'Lihat Agenda' / 'Infaq Sekarang' buttons to save screen real estate! "as screen real estate on mobile devices is a critical priority."
# Wait, no. "On the left panel, craft a spiritually resonant welcoming interface featuring a greeting... Immediately beneath this adapted greeting, ensure the two functional call-to-action buttons... to the right of this greeting panel..."
# Let's check `HOME_HTML`.
