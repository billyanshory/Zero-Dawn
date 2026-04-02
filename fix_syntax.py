with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'email_body = f"Halo {user_pmb.nama},' in line:
        lines[i] = '                email_body = f"Halo {user_pmb.nama},\\n\\nPembayaran {tagihan.jenis_tagihan} sebesar Rp {tagihan.jumlah} telah dikonfirmasi LUNAS.\\n\\nTerima kasih."\n'
        lines[i+1] = ''
        lines[i+2] = ''
        lines[i+3] = ''
        lines[i+4] = ''

with open('kampus-stie-samarinda-35 ( idcloudhost - Ninth Layer of Quality Control ).py', 'w') as f:
    f.writelines(lines)
