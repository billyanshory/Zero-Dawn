import re

with open('masjid-al-hijrah-68 - alternate - ( idcloudhost - fixing fitur absen - Idul Adha Qurban - Fifth Effort).py', 'r') as f:
    content = f.read()

# Fix 1: check_in_time displaying with UTC time in user UI
content = content.replace("user.check_in_time", "user.check_in_time") # Need to see how user check in time is populated
