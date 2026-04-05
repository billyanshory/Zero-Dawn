file_path = "kampus-stie-samarinda-41 ( idcloudhost - Twelfth Layer of Quality Control - Extreme QC ).py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure we are no longer passing epilepsi_logs to content_kwargs
content = content.replace(", 'epilepsi_logs': logs_display", "")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
