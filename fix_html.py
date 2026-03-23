with open('klinik-delima-dalam-39 ( IdCloudHost - Tata Letak Lay Out & Hierarki Visual Tampilan Interface UI-UX ).py', 'r') as f:
    text = f.read()

idx1 = text.find('HTML_DASHBOARD =')
idx2 = text.find('"""', idx1 + 20)
print("Dashboard ends at:", idx2)

# Wait! The string was not properly closed when I extracted it!
# I used match = re.search(r'(HTML_DASHBOARD\s*=\s*\"\"\".*?\"\"\")', text, flags=re.DOTALL)
# BUT there are OTHER """ inside the HTML_DASHBOARD string?! NO, but maybe it matched the first """ it found?
# Yes! `.*?` is non-greedy, it stops at the FIRST `"""` it encounters!
# So my extraction cut off HTML_DASHBOARD at the first `"""` it found!
