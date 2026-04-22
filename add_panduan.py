import re

filename = "masjid-al-hijrah-62 ( idcloudhost - fixing lay out - Idul Adha Qurban ).py"
with open(filename, "r") as f:
    content = f.read()

html_content = """

IDUL_ADHA_PANDUAN_HTML = '''
<div class="min-h-screen bg-[#F5F0E8] font-sans pb-20 flex flex-col items-center p-4">
    <div class="w-full max-w-3xl bg-white rounded-3xl shadow-2xl overflow-hidden relative mt-8">
        <!-- Header -->
        <div class="bg-[#1B4332] text-white p-6 md:p-8 relative">
            <a href="/idul-adha" class="absolute top-4 left-4 bg-white/20 hover:bg-white text-white hover:text-[#1B4332] w-8 h-8 rounded-full flex items-center justify-center text-xs transition-colors backdrop-blur-sm">
                <i class="fas fa-arrow-left"></i>
            </a>
            <div class="text-center mt-6 relative z-10">
                <h2 class="text-2xl md:text-3xl font-bold text-[#D4A017] mb-2">Panduan & Fikih Qurban</h2>
                <p class="text-xs md:text-sm text-[#F5F0E8]/80 max-w-md mx-auto">Ensiklopedia Fikih Qurban Masjid Al-Hijrah & Kalkulator Patungan Sesuai Syariat</p>
            </div>
        </div>

        <div class="p-6 md:p-8 space-y-10">

            <!-- CALCULATOR SECTION -->
            <div class="bg-[#1B4332]/5 rounded-3xl p-6 md:p-8 border border-[#1B4332]/10">
                <h3 class="text-xl font-bold text-[#1B4332] mb-4 flex items-center gap-2 border-b border-[#1B4332]/10 pb-3">
                    <i class="fas fa-calculator text-[#D4A017]"></i> Kalkulator Patungan Hewan
                </h3>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Jenis Hewan</label>
                        <select id="calc-type" class="w-full bg-white border border-gray-200 rounded-xl p-4 text-sm font-bold focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]" onchange="runCalculator()">
                            <option value="Sapi">Sapi</option>
                            <option value="Kambing">Kambing / Domba</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-600 mb-1">Harga Total Hewan (Rp)</label>
                        <input type="number" id="calc-price" value="21000000" min="0" class="w-full bg-white border border-gray-200 rounded-xl p-4 text-sm font-mono font-bold focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]" oninput="runCalculator()">
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-xs font-bold text-gray-600 mb-1">Jumlah Peserta Patungan</label>
                        <input type="number" id="calc-participants" value="7" min="1" class="w-full bg-white border border-gray-200 rounded-xl p-4 text-sm font-mono font-bold focus:border-[#D4A017] focus:ring-1 focus:ring-[#D4A017]" oninput="runCalculator()">
                    </div>
                </div>

                <!-- Result / Warning Display -->
                <div id="calc-result-box" class="bg-white rounded-xl p-6 text-center border border-gray-100 shadow-sm transition-colors duration-300">
                    <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Biaya Per Orang</p>
                    <h2 id="calc-result-val" class="text-3xl md:text-4xl font-bold text-[#1B4332] font-mono">Rp 3.000.000</h2>
                </div>

                <div id="calc-warning" class="hidden mt-4 bg-[#8B2635]/10 border border-[#8B2635]/30 rounded-xl p-4 flex items-start gap-3">
                    <div class="text-[#8B2635] mt-0.5"><i class="fas fa-exclamation-circle"></i></div>
                    <p id="calc-warning-text" class="text-sm font-bold text-[#8B2635] leading-relaxed"></p>
                </div>
            </div>

            <!-- ENCYCLOPEDIA SECTION -->
            <div class="prose prose-sm md:prose-base max-w-none text-[#F5F0E8] bg-white text-gray-800">
                <div class="text-center mb-8 border-b-2 border-[#1B4332] pb-6">
                    <h2 class="text-2xl font-bold text-[#1B4332] mb-2 uppercase tracking-wide">PANDUAN SYARIAT QURBAN — MASJID AL-HIJRAH</h2>
                    <p class="text-sm italic text-gray-500">Disusun dengan merujuk pada Al-Qur'an Al-Karim, Hadis Sahih, dan Fatwa Majelis Ulama Indonesia (MUI)</p>
                </div>

                <div class="mb-8">
                    <h3 class="text-lg font-bold text-[#1B4332] flex items-center gap-2 mb-3 border-b border-[#1B4332]/10 pb-2">
                        <i class="fas fa-leaf text-[#D4A017]"></i> Syarat Hewan Qurban yang Sah
                    </h3>
                    <p class="leading-relaxed text-gray-700 text-justify">
                        Hewan yang akan dijadikan qurban haruslah memenuhi sejumlah syarat yang ditetapkan oleh syariat. Pertama, hewan tersebut harus termasuk dalam kategori binatang ternak (bahîmah al-an'âm), yaitu unta, sapi, kerbau, domba, atau kambing. Kedua, hewan harus telah mencapai usia yang disyaratkan: untuk kambing dan domba minimal berusia satu tahun penuh (atau domba yang sudah berganti gigi susu meskipun belum genap satu tahun); untuk sapi dan kerbau minimal dua tahun; untuk unta minimal lima tahun. Ketiga, hewan harus dalam kondisi sehat dan bebas dari cacat yang dapat mengurangi kualitasnya — tidak buta sebelah, tidak pincang parah, tidak sangat kurus hingga tulangnya menonjol, dan tidak dalam keadaan sakit yang nyata. Hewan yang sedikit kurang sempurna namun tidak tergolong cacat berat tetap sah untuk diqurbankan, meskipun lebih utama memilih hewan yang paling gemuk, paling sehat, dan paling sempurna fisiknya sebagai bentuk kesungguhan ibadah.
                    </p>
                </div>

                <div class="mb-8">
                    <h3 class="text-lg font-bold text-[#1B4332] flex items-center gap-2 mb-3 border-b border-[#1B4332]/10 pb-2">
                        <i class="fas fa-users text-[#D4A017]"></i> Ketentuan Patungan (Ishtirâk) dalam Qurban
                    </h3>
                    <p class="leading-relaxed text-gray-700 text-justify">
                        Seekor sapi atau kerbau dapat dijadikan qurban bagi maksimal tujuh orang, sesuai dengan hadis yang diriwayatkan oleh Imam Muslim dari Jabir bin Abdillah radhiyallahu 'anhu: <em>"Kami menyembelih bersama Rasulullah ﷺ pada tahun Hudaibiyah, seekor unta untuk tujuh orang dan seekor sapi untuk tujuh orang."</em> Adapun seekor kambing atau domba hanya sah untuk satu orang beserta keluarganya yang ia nafkahi. Pahala qurban tersebut dapat diniatkan untuk diri sendiri dan seluruh anggota keluarga dalam satu rumah tangga, sebagaimana praktik yang dicontohkan oleh Nabi Muhammad ﷺ. Penting untuk dicatat bahwa seluruh peserta patungan harus menyepakati niat qurban sejak awal; tidak dibenarkan mencampurkan niat qurban dengan niat akikah atau konsumsi biasa dalam satu hewan yang sama.
                    </p>
                </div>

                <div class="mb-8">
                    <h3 class="text-lg font-bold text-[#1B4332] flex items-center gap-2 mb-3 border-b border-[#1B4332]/10 pb-2">
                        <i class="fas fa-clock text-[#D4A017]"></i> Waktu Penyembelihan yang Sah
                    </h3>
                    <p class="leading-relaxed text-gray-700 text-justify">
                        Penyembelihan qurban dimulai setelah pelaksanaan shalat Idul Adha dan dua khutbah selesai, tepatnya pada tanggal 10 Dzulhijjah. Waktu penyembelihan berlangsung hingga terbenamnya matahari pada tanggal 13 Dzulhijjah (akhir hari-hari Tasyrik). Berdasarkan ini, panitia masjid memiliki waktu selama empat hari penuh untuk menyelesaikan seluruh proses penyembelihan. Penyembelihan yang dilakukan sebelum shalat Id selesai tidak dianggap sah sebagai qurban, melainkan hanya sembelihan biasa. Hal ini berdasarkan hadis yang diriwayatkan oleh Imam Bukhari dan Muslim dari Al-Bara' bin 'Azib radhiyallahu 'anhu.
                    </p>
                </div>

                <div class="mb-8">
                    <h3 class="text-lg font-bold text-[#1B4332] flex items-center gap-2 mb-3 border-b border-[#1B4332]/10 pb-2">
                        <i class="fas fa-hand-holding-heart text-[#D4A017]"></i> Tata Cara Penyembelihan yang Benar dan Penuh Adab
                    </h3>
                    <p class="leading-relaxed text-gray-700 text-justify">
                        Sebelum memulai penyembelihan, panitia dan penyembelih (juru sembelih halal) hendaknya mempersiapkan diri dengan niat yang tulus dan alat sembelih yang benar-benar tajam, karena mempertajam pisau sebelum menyembelih adalah bagian dari ihsân (berbuat baik) yang diperintahkan Rasulullah ﷺ. Pisau yang tajam meminimalkan rasa sakit pada hewan dan memastikan kematian yang cepat dan manusiawi. Hewan dibaringkan dengan lembut ke sisi kirinya, menghadap kiblat. Dianjurkan bagi penyembelih untuk meletakkan kakinya dengan ringan di sisi leher hewan agar hewan tidak bergerak berlebihan — bukan dengan tekanan menyakiti, melainkan dengan ketenangan yang menenangkan. Penyembelihan dilakukan dengan memotong tiga saluran sekaligus: saluran napas (tenggorokan), saluran makan (kerongkongan), dan kedua urat nadi leher — dengan satu tarikan pisau yang tegas dan cepat. Penyembelih tidak boleh memutus kepala hewan secara sekaligus saat penyembelihan, dan tidak boleh mulai menguliti atau memotong bagian tubuh hewan sebelum hewan benar-benar diam dan dipastikan telah tiada, demi menjaga kehormatan dan kemanusiaan dalam proses ini.
                    </p>
                </div>

                <div class="mb-8">
                    <h3 class="text-lg font-bold text-[#1B4332] flex items-center gap-2 mb-4 border-b border-[#1B4332]/10 pb-2">
                        <i class="fas fa-book-open text-[#D4A017]"></i> Bacaan Doa Penyembelihan Qurban
                    </h3>
                    <p class="leading-relaxed text-gray-700 mb-4 text-justify">
                        Sebelum pisau menyentuh leher hewan, penyembelih mengucapkan doa berikut. Doa ini diriwayatkan dalam berbagai hadis sahih dan merupakan sunnah yang sangat dianjurkan:
                    </p>

                    <div class="bg-[#F5F0E8] p-5 rounded-2xl mb-4 border border-[#D4A017]/30">
                        <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Apabila menyembelih untuk diri sendiri dan keluarga:</p>
                        <p class="text-2xl md:text-3xl text-right font-arabic leading-[2.5] mb-4 text-[#1B4332]" style="font-family: 'Amiri', serif;" dir="rtl">بِسْمِ اللهِ وَاللهُ أَكْبَرُ، اللَّهُمَّ هَذَا مِنْكَ وَلَكَ، هَذَا عَنِّي وَعَنْ أَهْلِ بَيْتِي</p>
                        <p class="text-[#8B2635] italic text-sm md:text-base mb-2 font-medium">Bismillâhi wallâhu akbar, Allâhumma hâdzâ minka wa laka, hâdzâ 'annî wa 'an ahli baytî.</p>
                        <p class="text-gray-700 text-sm leading-relaxed border-t border-[#D4A017]/20 pt-2">Artinya: "Dengan nama Allah, dan Allah Maha Besar. Ya Allah, ini adalah dari-Mu dan untuk-Mu. Ini dariku dan dari keluargaku."</p>
                    </div>

                    <div class="bg-[#F5F0E8] p-5 rounded-2xl mb-4 border border-[#D4A017]/30">
                        <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Apabila menyembelih atas nama Sohibul Qurban (orang lain):</p>
                        <p class="text-2xl md:text-3xl text-right font-arabic leading-[2.5] mb-4 text-[#1B4332]" style="font-family: 'Amiri', serif;" dir="rtl">بِسْمِ اللهِ وَاللهُ أَكْبَرُ، اللَّهُمَّ هَذَا مِنْكَ وَلَكَ، هَذَا عَنْ [nama Sohibul Qurban]</p>
                        <p class="text-[#8B2635] italic text-sm md:text-base mb-2 font-medium">Bismillâhi wallâhu akbar, Allâhumma hâdzâ minka wa laka, hâdzâ 'an [nama Sohibul Qurban].</p>
                        <p class="text-gray-700 text-sm leading-relaxed border-t border-[#D4A017]/20 pt-2">Artinya: "Dengan nama Allah, dan Allah Maha Besar. Ya Allah, ini adalah dari-Mu dan untuk-Mu. Ini atas nama [nama Sohibul Qurban]."</p>
                    </div>

                    <div class="bg-[#F5F0E8] p-5 rounded-2xl border border-[#D4A017]/30">
                        <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Setelah selesai menyembelih, dianjurkan pula untuk membaca:</p>
                        <p class="text-2xl md:text-3xl text-right font-arabic leading-[2.5] mb-4 text-[#1B4332]" style="font-family: 'Amiri', serif;" dir="rtl">اللَّهُمَّ تَقَبَّلْ مِنِّي (أَوْ مِنْ فُلَانٍ)</p>
                        <p class="text-[#8B2635] italic text-sm md:text-base mb-2 font-medium">Allâhumma taqabbal minnî (atau: min fulân).</p>
                        <p class="text-gray-700 text-sm leading-relaxed border-t border-[#D4A017]/20 pt-2">Artinya: "Ya Allah, terimalah [qurban ini] dariku (atau: dari si Fulan)."</p>
                    </div>
                </div>

                <div class="mb-8">
                    <h3 class="text-lg font-bold text-[#1B4332] flex items-center gap-2 mb-4 border-b border-[#1B4332]/10 pb-2">
                        <i class="fas fa-balance-scale text-[#D4A017]"></i> Hukum-Hukum Penting bagi Panitia Qurban
                    </h3>
                    <p class="leading-relaxed text-gray-700 mb-4 text-justify">
                        Berikut adalah beberapa ketentuan fikih yang sangat penting untuk dipahami oleh seluruh panitia, agar pelaksanaan qurban tidak hanya sah secara teknis tetapi juga bersih secara syariat:
                    </p>

                    <ul class="space-y-4">
                        <li class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span class="font-bold text-[#8B2635] block mb-1">Pertama:</span> <strong>larangan menjadikan bagian hewan qurban sebagai upah (ujrah) bagi juru sembelih atau panitia.</strong> Berdasarkan hadis yang diriwayatkan oleh Imam Bukhari dan Muslim dari Ali bin Abi Thalib radhiyallahu 'anhu, Rasulullah ﷺ memerintahkan beliau untuk mengurus unta-unta qurban dan menyedekahkan seluruh daging, kulit, serta pelana-pelananya, tanpa memberikan sedikitpun kepada juru sembelih sebagai bayaran. Juru sembelih boleh diberikan upah dari sumber dana lain (misalnya dari kas masjid atau biaya operasional yang sudah dianggarkan), tetapi tidak boleh diambil dari daging, kulit, atau bagian manapun dari hewan qurban itu sendiri. Panitia yang terlibat dalam proses qurban boleh menerima daging sebagai hadiah atau sedekah biasa — bukan sebagai imbalan jasa.
                        </li>
                        <li class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span class="font-bold text-[#8B2635] block mb-1">Kedua:</span> <strong>larangan menjual kulit, tanduk, atau bagian apapun dari hewan qurban.</strong> Semua bagian hewan qurban — termasuk kulitnya — tidak boleh diperjualbelikan. Kulit boleh dimanfaatkan oleh masjid untuk keperluan ibadah (seperti dijadikan sajadah atau tempat wudhu), diberikan kepada mustahik sebagai hibah, atau didonasikan kepada lembaga sosial. Namun menjualnya dan memasukkan hasilnya ke kas masjid adalah tidak dibenarkan menurut mayoritas ulama.
                        </li>
                        <li class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span class="font-bold text-[#8B2635] block mb-1">Ketiga:</span> <strong>ketentuan pembagian daging qurban.</strong> Para ulama membagi distribusi daging qurban menjadi tiga bagian: sepertiga untuk Sohibul Qurban dan keluarganya, sepertiga untuk dihadiahkan kepada kerabat, tetangga, dan teman, serta sepertiga untuk disedekahkan kepada fakir miskin dan mustahik. Meskipun pembagian ini bersifat anjuran (sunnah) dan bukan wajib menurut jumhur ulama, namun mengamalkannya merupakan bentuk mengikuti sunnah Nabi ﷺ yang paling sempurna. Yang wajib menurut syariat adalah bahwa minimal sebagian dari daging qurban itu harus disedekahkan; Sohibul Qurban tidak diperkenankan mengambil seluruh dagingnya untuk diri sendiri tanpa menyedekahkan apapun.
                        </li>
                        <li class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span class="font-bold text-[#8B2635] block mb-1">Keempat:</span> <strong>Sohibul Qurban yang berniat berqurban dianjurkan untuk tidak memotong rambut, kuku, dan kulit tubuhnya</strong> sejak memasuki bulan Dzulhijjah hingga hewan qurbannya selesai disembelih. Ini berdasarkan hadis sahih yang diriwayatkan oleh Imam Muslim dari Ummu Salamah radhiyallahu 'anha. Larangan ini bersifat makruh tahrim menurut sebagian ulama, dan hanya berlaku bagi Sohibul Qurban — bukan bagi panitia penyembelih.
                        </li>
                        <li class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span class="font-bold text-[#8B2635] block mb-1">Kelima:</span> <strong>niat qurban harus sudah ditentukan sejak hewan diserahkan</strong> kepada panitia. Jika Sohibul Qurban telah menyerahkan hewannya dengan niat qurban, kemudian hewan tersebut sakit atau mati sebelum disembelih tanpa kelalaian panitia, maka kewajiban qurban Sohibul Qurban dianggap gugur dan ia tidak wajib menggantinya — kecuali jika kematian atau kerusakan tersebut disebabkan oleh kelalaian panitia, maka panitia bertanggung jawab untuk menggantinya.
                        </li>
                    </ul>
                </div>

            </div>
        </div>
    </div>
</div>

<script>
    function runCalculator() {
        const type = document.getElementById('calc-type').value;
        const price = parseFloat(document.getElementById('calc-price').value) || 0;
        const participants = parseInt(document.getElementById('calc-participants').value) || 1;

        const resultBox = document.getElementById('calc-result-box');
        const resultVal = document.getElementById('calc-result-val');
        const warningBox = document.getElementById('calc-warning');
        const warningText = document.getElementById('calc-warning-text');

        let isValid = true;
        let warningMsg = "";

        // Validation Rules
        if (type === "Sapi" && participants > 7) {
            isValid = false;
            warningMsg = "Sapi hanya dapat diperuntukkan bagi maksimal 7 orang sesuai syariat Islam.";
        } else if (type === "Kambing" && participants > 1) {
            isValid = false;
            warningMsg = "Kambing atau domba hanya sah untuk 1 orang (beserta keluarga yang dinafkahinya) sesuai syariat Islam.";
        }

        if (!isValid) {
            // Show Warning, Hide Result
            warningText.innerText = warningMsg;
            warningBox.classList.remove('hidden');
            resultBox.classList.remove('border-gray-100');
            resultBox.classList.add('border-[#8B2635]', 'bg-[#8B2635]/5');
            resultVal.innerText = "-";
            resultVal.classList.replace('text-[#1B4332]', 'text-[#8B2635]');
        } else {
            // Show Result, Hide Warning
            warningBox.classList.add('hidden');
            resultBox.classList.remove('border-[#8B2635]', 'bg-[#8B2635]/5');
            resultBox.classList.add('border-gray-100');
            resultVal.classList.replace('text-[#8B2635]', 'text-[#1B4332]');

            if (participants > 0) {
                const costPerPerson = price / participants;
                resultVal.innerText = "Rp " + Math.round(costPerPerson).toLocaleString('id-ID');
            } else {
                resultVal.innerText = "Rp 0";
            }
        }
    }

    // Initial run
    window.addEventListener('DOMContentLoaded', runCalculator);
</script>
'''

"""

routes = """
@app.route('/idul-adha/panduan')
def idul_adha_panduan():
    rendered_content = render_template_string(IDUL_ADHA_PANDUAN_HTML, settings=get_settings())
    return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content=rendered_content, is_admin=session.get('is_admin', False), settings=get_settings())
"""


insert_target = 'HOME_HTML = """'
if insert_target in content:
    content = content.replace(insert_target, html_content + insert_target)

# Routes
insert_target_r = "if __name__ == '__main__':"
if insert_target_r in content:
    content = content.replace(insert_target_r, routes + "\n" + insert_target_r)

with open(filename, "w") as f:
    f.write(content)

print("Injected panduan html and logic")
