import re

with open('kampus-stie-samarinda-4 ( idcloudhost - dashboard home utama - debugging & 6 fitur utama home ).py', 'r') as f:
    content = f.read()

# Make sure that the icons and buttons are present and working as expected.
print(content.find('modal-terapi-audio'))
print(content.find('modal-waris'))
