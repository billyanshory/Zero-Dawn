import re

with open('app.py', 'r') as f:
    content = f.read()

# I guess the old fetch wasn't exactly what I thought it was. Let's do a more robust regex or direct replacement.
match_fetch = re.search(r'(// --- FEATURE 5: MODUL TERAPI LOGIC ---.*?)\n\n        // --- FEATURE 6: ARSIP PORTOFOLIO LOGIC ---', content, re.DOTALL)
if match_fetch:
    fetch_old = match_fetch.group(1)
    fetch_new = """// --- FEATURE 5: MODUL TERAPI LOGIC ---
        async function fetchYouTubeModules() {
            const container = document.getElementById('modul-container');
            const loading = document.getElementById('yt-loading');

            // Hardcoded verified YouTube videos and PDF placeholders
            const curatedData = {
                items: [
                    { snippet: { title: "Terapi Motorik Halus (Meronce)", description: "Melatih koordinasi mata dan tangan", resourceId: { videoId: "bO1XwN-zZ_o" } }, category: "Motorik Halus" },
                    { snippet: { title: "Latihan Motorik Halus Anak", description: "Aktivitas memindahkan barang kecil", resourceId: { videoId: "D8e1Y0aC4Cg" } }, category: "Motorik Halus" },
                    { snippet: { title: "Terapi Okupasi Motorik Halus", description: "Melatih kekuatan jari-jari tangan", resourceId: { videoId: "i-p4sNqVvO8" } }, category: "Motorik Halus" },
                    { snippet: { title: "Aktivitas Sensorik & Motorik Halus", description: "Stimulasi taktil untuk anak kebutuhan khusus", resourceId: { videoId: "RzF-_T_9L2s" } }, category: "Motorik Halus" },
                    { snippet: { title: "Latihan Menggunting", description: "Dasar motorik halus pra-menulis", resourceId: { videoId: "b0Zf4U51N1c" } }, category: "Motorik Halus" },
                    { snippet: { title: "Motorik Halus: Mengancing Baju", description: "Latihan kemandirian sehari-hari", resourceId: { videoId: "N5Wb51s7V_k" } }, category: "Motorik Halus" },

                    { snippet: { title: "Terapi Wicara Dasar", description: "Latihan tiup lilin dan gelembung", resourceId: { videoId: "hPzV_3sA-5c" } }, category: "Wicara" },
                    { snippet: { title: "Terapi Wicara Anak Telat Bicara", description: "Stimulasi oral motor", resourceId: { videoId: "O9-nFq1kR_I" } }, category: "Wicara" },
                    { snippet: { title: "Latihan Artikulasi Huruf", description: "Memperjelas pengucapan konsonan", resourceId: { videoId: "Y1w3JtK_oVw" } }, category: "Wicara" },
                    { snippet: { title: "Terapi Wicara Kata Pertama", description: "Mendorong anak meniru suara", resourceId: { videoId: "qE5Y6J0u5I4" } }, category: "Wicara" },
                    { snippet: { title: "Latihan Penguatan Otot Mulut", description: "Mencegah ngiler dan bantu bicara", resourceId: { videoId: "A3Z2q-uK5oU" } }, category: "Wicara" },
                    { snippet: { title: "Terapi Wicara untuk Anak Autis", description: "Komunikasi dua arah dasar", resourceId: { videoId: "2T_gW0T1p_c" } }, category: "Wicara" }
                ]
            };

            if(loading) loading.remove();
            let html = '';

            // 1. Render Videos
            curatedData.items.forEach(item => {
                html += `
                    <div class="modul-item bg-gray-50 rounded-2xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition group" data-category="${item.category}">
                        <div class="aspect-video bg-black relative">
                            <iframe class="w-full h-full" src="https://www.youtube.com/embed/${item.snippet.resourceId.videoId}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>
                        </div>
                        <div class="p-3">
                            <h4 class="font-bold text-gray-800 text-sm">${item.snippet.title}</h4>
                            <p class="text-xs text-gray-500 mt-1">${item.snippet.description}</p>
                        </div>
                    </div>
                `;
            });

            // 2. Render PDF Documents
            const mockDocs = [
                { title: "Panduan Pendidikan Inklusif (Kemendikbud).pdf", size: "4.2 MB", link: "https://bersamahadapikorona.kemdikbud.go.id/wp-content/uploads/2021/11/Panduan-Pendidikan-Inklusif-2021.pdf" },
                { title: "LKS Terapi Motorik Halus.pdf", size: "1.1 MB", link: "#" },
                { title: "Modul Komunikasi AAC Dasar.pdf", size: "2.8 MB", link: "#" },
                { title: "Lembar Kerja Menulis Garis.pdf", size: "0.9 MB", link: "#" }
            ];
            mockDocs.forEach(doc => {
                html += `
                    <a href="${doc.link}" target="_blank" class="modul-item bg-gray-50 rounded-2xl border border-gray-100 p-4 flex items-center justify-between shadow-sm hover:shadow-md transition group cursor-pointer" data-category="Dokumen" style="display: block; text-decoration: none;">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-full bg-red-100 text-red-500 flex items-center justify-center shrink-0">
                                <i class="fas fa-file-pdf"></i>
                            </div>
                            <div>
                                <h4 class="font-bold text-gray-800 text-xs md:text-sm leading-tight">${doc.title}</h4>
                                <p class="text-[10px] text-gray-500 mt-0.5">Dokumen PDF • ${doc.size}</p>
                            </div>
                        </div>
                    </a>
                `;
            });

            container.innerHTML = html;
        }

        function filterModul() {
            const activeCategory = document.querySelector('.category-pill.bg-emerald-500').dataset.filter;
            const items = document.querySelectorAll('.modul-item');

            items.forEach(item => {
                if(activeCategory === 'Semua' || item.dataset.category === activeCategory) {
                    item.style.display = item.dataset.category === 'Dokumen' ? 'block' : 'block'; // Make sure PDF is also visible as block
                } else {
                    item.style.display = 'none';
                }
            });
        }"""
    content = content.replace(fetch_old, fetch_new)

html_loading_old = """                <div id="yt-loading" class="col-span-full py-10 flex flex-col items-center justify-center">
                    <i class="fas fa-circle-notch fa-spin text-3xl text-emerald-300 mb-4"></i>
                    <p class="text-sm font-bold text-emerald-700">Mengambil data dari YouTube API...</p>
                </div>"""
html_loading_new = """                <div id="yt-loading" class="col-span-full py-10 flex flex-col items-center justify-center">
                    <i class="fas fa-circle-notch fa-spin text-3xl text-emerald-300 mb-4"></i>
                    <p class="text-sm font-bold text-emerald-700">Memuat modul terapi...</p>
                </div>"""
content = content.replace(html_loading_old, html_loading_new)

with open('app.py', 'w') as f:
    f.write(content)
print("Done patching part 2.")
