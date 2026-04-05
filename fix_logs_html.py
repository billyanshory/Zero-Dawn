file_path = "kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I see that `epilepsi-logs-container` was not actually inserted into the HTML correctly
# because my previous string replacement failed to match the exact template.
# Let's find where the modal is and replace it.

target_match = """            <h4 class="text-sm font-bold text-gray-800 mb-4 pl-2 border-l-4 border-blue-500">Riwayat Terakhir</h4>
            <div class="space-y-3">
"""
# Let's use regex to replace everything from <div class="space-y-3"> down to {% endfor %} inside the modal-terapi-log block
import re

# find modal-terapi-log
modal_idx = content.find('id="modal-terapi-log"')
if modal_idx != -1:
    h4_idx = content.find('<h4 class="text-sm font-bold text-gray-800 mb-4 pl-2 border-l-4 border-blue-500">Riwayat Terakhir</h4>', modal_idx)
    if h4_idx != -1:
        # Find the next </div> that matches the end of the modal or the end of the space-y-3
        # But wait, there's a {% for log in epilepsi_logs %} block there.
        # Let's search for {% for log in epilepsi_logs %}
        for_idx = content.find('{% for log in epilepsi_logs %}', modal_idx)
        if for_idx != -1:
            endfor_idx = content.find('{% endfor %}', for_idx)
            if endfor_idx != -1:
                # Replace the block
                original_block = content[content.rfind('<div class="space-y-3">', h4_idx, for_idx):endfor_idx + len('{% endfor %}')]
                new_block = """<div class="space-y-3" id="epilepsi-logs-container">
                    <p class="text-center text-gray-400 text-xs py-4">Memuat data rekaman...</p>
                </div>"""
                content = content.replace(original_block, new_block)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
