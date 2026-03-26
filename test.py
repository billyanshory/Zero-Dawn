import re

with open('kampus-stie-samarinda-4 ( idcloudhost - dashboard home utama - debugging & 6 fitur utama home ).py', 'r') as f:
    content = f.read()

# Search for the button definitions of the 12 features that need to be brought back.
# Or where they used to be located

match = content.find('Terapi Suara')
if match != -1:
    print(content[match-1000:match+1000])

print("---")
match2 = content.find('modal-waris')
if match2 != -1:
    print(content[match2-500:match2+500])
