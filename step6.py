with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    content = f.read()

# 1. Add Toast CSS
toast_css = """
        /* Floating notification */
        @keyframes float-up {
            0% { transform: translateY(100%); opacity: 0; }
            10% { transform: translateY(0); opacity: 1; }
            90% { transform: translateY(0); opacity: 1; }
            100% { transform: translateY(-100%); opacity: 0; }
        }
        .toast-float {
            animation: float-up 3s ease-in-out forwards;
        }
"""
# Replace existing if present to avoid duplication, or append if not.
# It seems there is already a `.toast-float` block in STYLES_HTML from exploration. We will just add the JS function.

# 2. Add Toast JS in BASE_LAYOUT
toast_js = """
    function showToast(msg, type='success') {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-20 left-1/2 transform -translate-x-1/2 z-[1000] px-6 py-3 rounded-full text-white font-bold shadow-2xl toast-float backdrop-blur-md ${type==='error'?'bg-red-500/90':'bg-sky-500/90'}`;
        toast.innerHTML = `<i class="fas ${type==='error'?'fa-exclamation-circle':'fa-check-circle'} mr-2"></i> ${msg}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    // Polling Notification Script
    function pollNotifications() {
        fetch('/api/notifications/poll')
        .then(res => res.json())
        .then(data => {
            if(data && data.length > 0) {
                data.forEach(n => showToast(n.message, 'success'));
            }
        }).catch(err => console.log(err));
    }
    setInterval(pollNotifications, 10000);
"""
content = content.replace("function triggerEmergency() {", toast_js + "\n    function triggerEmergency() {")

# 3. Replace simple alerts
content = content.replace("alert('Gagal memproses persetujuan KRS.');", "showToast('Gagal memproses persetujuan KRS.', 'error');")
content = content.replace("alert('Masukkan kode surat yang valid.');", "showToast('Masukkan kode surat yang valid.', 'error');")
content = content.replace("alert(\"Gagal memuat surat. Periksa koneksi internet.\");", "showToast('Gagal memuat surat. Periksa koneksi internet.', 'error');")

# Also add the skeleton JS trigger
skeleton_js = """
    window.addEventListener('beforeunload', function () {
        document.body.classList.add('skeleton', 'opacity-50', 'pointer-events-none');
    });
"""
content = content.replace("function updateProgress() {", skeleton_js + "\n    function updateProgress() {")

with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "w") as f:
    f.write(content)
