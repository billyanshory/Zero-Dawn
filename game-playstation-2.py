import io
import os
import zipfile
import math
import sqlite3
from flask import Flask, request, send_file, render_template_string, jsonify, send_from_directory, redirect, url_for, session, flash
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from werkzeug.utils import secure_filename

# --- KONFIGURASI FLASK ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB Limit
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg', 'mp3', 'wav', 'ogg', 'mp4', 'm4a', 'flac', 'srt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tabulasi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    no_urut TEXT,
                    nama_lengkap TEXT,
                    nik TEXT,
                    jenis_kelamin TEXT,
                    tempat_lahir TEXT,
                    tanggal_lahir TEXT,
                    agama TEXT,
                    pendidikan TEXT,
                    jenis_pekerjaan TEXT,
                    golongan_darah TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --- GAME DATA HELPER ---
def get_games_data():
    return [
        {
            "id": "game1", "title": "Horizon Zero Dawn", "price": "Rp 729.000", "available": True,
            "desc_en": "In a post-apocalyptic era where nature has reclaimed the ruins of a forgotten civilization, humanity is no longer the dominant species. Colossal machines, evolving with terrifying biological mimicry, roam the landscapes. This is not merely a survival story, but a profound scientific inquiry into the consequences of unchecked technological advancement and the resilience of life itself.\n\nYou inhabit the soul of Aloy, an outcast shunned by her tribe, carrying the heavy burden of an unknown lineage. Her journey is a deeply emotional odyssey of self-discovery, driven by a primal need for acceptance and truth. Every step through the lush, vibrant wilderness is a testament to the human spirit's refusal to fade into oblivion, even when faced with mechanical gods.\n\nThe narrative weaves a complex tapestry of ancient mysteries and futuristic despair. As you unravel the secrets of 'Zero Dawn,' you are confronted with the heartbreaking choices of those who came before. It is a poignant reminder of our fragility and the enduring legacy of hope that persists, even after the end of the world.",
            "desc_id": "Di era pasca-apokaliptik di mana alam telah merebut kembali reruntuhan peradaban yang terlupakan, umat manusia tidak lagi menjadi spesies dominan. Mesin-mesin raksasa, yang berevolusi dengan mimikri biologis yang menakutkan, berkeliaran di lanskap. Ini bukan sekadar kisah bertahan hidup, melainkan penyelidikan ilmiah mendalam tentang konsekuensi kemajuan teknologi yang tidak terkendali dan ketahanan kehidupan itu sendiri.\n\nAnda menghuni jiwa Aloy, seorang buangan yang dijauhi oleh sukunya, memikul beban berat garis keturunan yang tidak diketahui. Perjalanannya adalah pengembaraan emosional yang mendalam tentang penemuan jati diri, didorong oleh kebutuhan mendasar akan penerimaan dan kebenaran. Setiap langkah melalui hutan belantara yang subur dan hidup adalah bukti penolakan jiwa manusia untuk memudar dalam ketiadaan, bahkan saat berhadapan dengan dewa-dewa mekanis.\n\nNarasi ini menjalin permadani kompleks dari misteri kuno dan keputusasaan futuristik. Saat Anda mengungkap rahasia 'Zero Dawn,' Anda dihadapkan pada pilihan memilukan dari mereka yang datang sebelumnya. Ini adalah pengingat pedih akan kerapuhan kita dan warisan harapan abadi yang bertahan, bahkan setelah akhir dunia."
        },
        {
            "id": "game2", "title": "The Last Of Us Part I", "price": "Rp 1.029.000", "available": True,
            "desc_en": "Rooted in terrifying biological plausibility, the Cordyceps brain infection has decimated civilization, stripping humanity of its infrastructure and its morality. The world is a brutal, overgrown husk where survival is a daily negotiation with death. This scientific horror serves as the backdrop for a raw, unfiltered examination of the human condition under extreme duress.\n\nAt its core, this is a heart-wrenching study of the bond between Joel, a hardened survivor haunted by loss, and Ellie, a girl who represents a glimmer of impossible hope. Their journey across a fractured America is an emotional tour de force, exploring the fierce, sometimes destructive nature of paternal love and the trauma of growing up in a world without innocence.\n\nThe narrative challenges the binary of right and wrong, forcing players to confront the gray areas of morality. Every choice carries weight; every violent act leaves a scar on the soul. It is a masterpiece of storytelling that asks a haunting question: how far would you go to save the one thing that gives your life meaning in a godless world?",
            "desc_id": "Berakar pada kemungkinan biologis yang menakutkan, infeksi otak Cordyceps telah memusnahkan peradaban, melucuti infrastruktur dan moralitas umat manusia. Dunia adalah sekam brutal yang ditumbuhi tanaman liar di mana bertahan hidup adalah negosiasi harian dengan kematian. Horor ilmiah ini menjadi latar belakang bagi pemeriksaan mentah dan tanpa filter terhadap kondisi manusia di bawah tekanan ekstrem.\n\nPada intinya, ini adalah studi yang menyayat hati tentang ikatan antara Joel, seorang penyintas keras yang dihantui oleh kehilangan, dan Ellie, seorang gadis yang mewakili secercah harapan yang mustahil. Perjalanan mereka melintasi Amerika yang retak adalah tour de force emosional, mengeksplorasi sifat cinta kebapakan yang ganas dan terkadang merusak serta trauma tumbuh di dunia tanpa kepolosan.\n\nNarasi ini menantang biner benar dan salah, memaksa pemain untuk menghadapi area abu-abu moralitas. Setiap pilihan memiliki bobot; setiap tindakan kekerasan meninggalkan bekas luka pada jiwa. Ini adalah mahakarya penceritaan yang mengajukan pertanyaan menghantui: seberapa jauh Anda akan pergi untuk menyelamatkan satu hal yang memberi hidup Anda makna di dunia tanpa tuhan?"
        },
        {
            "id": "game3", "title": "Resident Evil 2 Remake", "price": "Rp 559.000", "available": True,
            "desc_en": "A catastrophic viral outbreak has transformed the bustling metropolis of Raccoon City into a nightmare of biological distortion. The G-Virus represents the pinnacle of corporate scientific hubris, a terrifying force that warps flesh and mind. The atmosphere is thick with the scent of decay and the oppressive dread of an unseen, mutating predator stalking the halls.\n\nLeon S. Kennedy and Claire Redfield are thrust into this chaos, their survival instincts pushed to the breaking point. The game masterfully manipulates fear and tension, creating an emotional rollercoaster where every shadow holds a threat. It captures the raw, visceral panic of being hunted, forcing players to manage scarce resources while their heart races in sync with the characters.\n\nBeneath the gore lies a tragic narrative of the Birkin family, destroyed by their own creation. It serves as a cautionary tale about the ethics of genetic manipulation and the cost of ambition. The reimagined experience elevates the horror to a poignant level, making the struggle for survival feel intimate, desperate, and utterly compelling.",
            "desc_id": "Wabah virus yang membawa bencana telah mengubah kota metropolis Raccoon City yang ramai menjadi mimpi buruk distorsi biologis. G-Virus mewakili puncak keangkuhan ilmiah korporat, kekuatan mengerikan yang membelokkan daging dan pikiran. Atmosfernya kental dengan aroma pembusukan dan ketakutan menindas akan predator tak terlihat yang bermutasi mengintai di lorong-lorong.\n\nLeon S. Kennedy dan Claire Redfield terdorong ke dalam kekacauan ini, naluri bertahan hidup mereka didorong hingga titik puncaknya. Game ini dengan ahli memanipulasi ketakutan dan ketegangan, menciptakan rollercoaster emosional di mana setiap bayangan menyimpan ancaman. Ini menangkap kepanikan mentah dan mendalam saat diburu, memaksa pemain untuk mengelola sumber daya yang langka sementara jantung mereka berpacu selaras dengan karakter.\n\nDi balik pertumpahan darah terdapat narasi tragis keluarga Birkin, yang dihancurkan oleh ciptaan mereka sendiri. Ini berfungsi sebagai kisah peringatan tentang etika manipulasi genetik dan harga dari ambisi. Pengalaman yang dirancang ulang ini mengangkat horor ke tingkat yang pedih, membuat perjuangan untuk bertahan hidup terasa intim, putus asa, dan sangat memikat."
        },
        {
            "id": "game4", "title": "Uncharted 4", "price": "Rp 450.000", "available": True,
            "desc_en": "Nathan Drake returns in a narrative masterpiece that balances high-octane adventure with the weary melancholy of a man confronting his past. The pursuit of Captain Avery's long-lost pirate treasure is more than a treasure hunt; it is a scientific exploration of history's shadows and the obsessions that drive men to ruin. The breathtaking landscapes hide ancient mechanisms and secrets that defy time.\n\nThis final chapter is a deeply emotional farewell, examining the bonds of brotherhood and the cost of legacy. The interplay between Nathan and his long-lost brother Sam adds a layer of desperate urgency and poignant nostalgia. Every cliff scaled and puzzle solved brings them closer not just to gold, but to the heartbreaking realization that some treasures are best left buried.\n\nIn the end, it is a story about moving on. The lush jungles and crumbling ruins serve as a metaphor for the memories we cling to and the future we fear to embrace. It is a cinematic experience that captures the thrill of discovery and the quiet, aching beauty of letting go.",
            "desc_id": "Nathan Drake kembali dalam mahakarya naratif yang menyeimbangkan petualangan beroktan tinggi dengan melankolia lelah seorang pria yang menghadapi masa lalunya. Pengejaran harta karun bajak laut Kapten Avery yang telah lama hilang lebih dari sekadar perburuan harta karun; ini adalah eksplorasi ilmiah tentang bayang-bayang sejarah dan obsesi yang mendorong manusia menuju kehancuran. Lanskap yang menakjubkan menyembunyikan mekanisme kuno dan rahasia yang menantang waktu.\n\nBab terakhir ini adalah perpisahan emosional yang mendalam, memeriksa ikatan persaudaraan dan harga dari sebuah warisan. Interaksi antara Nathan dan saudaranya yang telah lama hilang, Sam, menambahkan lapisan urgensi putus asa dan nostalgia yang pedih. Setiap tebing yang dipanjat dan teka-teki yang dipecahkan membawa mereka lebih dekat bukan hanya pada emas, tetapi pada kesadaran memilukan bahwa beberapa harta sebaiknya dibiarkan terkubur.\n\nPada akhirnya, ini adalah kisah tentang melangkah maju. Hutan rimbun dan reruntuhan yang runtuh berfungsi sebagai metafora untuk kenangan yang kita pegang teguh dan masa depan yang kita takut untuk rangkul. Ini adalah pengalaman sinematik yang menangkap sensasi penemuan dan keindahan sunyi yang menyakitkan dari melepaskan."
        },
        {
            "id": "game5", "title": "Bloodborne", "price": "Rp 399.000", "available": False,
            "desc_en": "Yharnam is a gothic nightmare born from medical hubris, a city drowning in the blood of its own citizens. The game delves into cosmic horror and biological transcendence, exploring themes of evolution gone wrong. The scourge of beasts is not just a disease, but a symptom of humanity's attempt to commune with the eldritch truths of the cosmos.\n\nThe atmosphere is thick with dread and melancholy, a visceral experience that preys on primal fears. As a Hunter, you navigate a world where the line between man and beast is blurred by madness. The combat is a frantic dance of death, requiring precision and courage, mirroring the desperate struggle to maintain one's sanity in the face of the unknown.\n\nBeneath the gothic spires lies a tragic tale of scholars and clerics who sought enlightenment but found only madness. It is a haunting reflection on the limits of human understanding and the terrifying price of forbidden knowledge. The silence of the night is broken only by the screams of the damned.",
            "desc_id": "Yharnam adalah mimpi buruk gotik yang lahir dari keangkuhan medis, sebuah kota yang tenggelam dalam darah warganya sendiri. Game ini mendalami horor kosmik dan transendensi biologis, mengeksplorasi tema evolusi yang salah arah. Wabah binatang buas bukan hanya penyakit, tetapi gejala dari upaya manusia untuk berkomunikasi dengan kebenaran eldritch dari kosmos.\n\nAtmosfernya kental dengan ketakutan dan melankolia, pengalaman mendalam yang memangsa ketakutan purba. Sebagai Pemburu, Anda menavigasi dunia di mana batas antara manusia dan binatang dikaburkan oleh kegilaan. Pertarungan adalah tarian kematian yang panik, membutuhkan ketepatan dan keberanian, mencerminkan perjuangan putus asa untuk mempertahankan kewarasan seseorang di hadapan hal yang tidak diketahui.\n\nDi bawah menara gotik terdapat kisah tragis para sarjana dan ulama yang mencari pencerahan tetapi hanya menemukan kegilaan. Ini adalah refleksi yang menghantui tentang batas pemahaman manusia dan harga mengerikan dari pengetahuan terlarang. Keheningan malam hanya dipecahkan oleh jeritan mereka yang terkutuk."
        },
        {
            "id": "game6", "title": "GTA V", "price": "Rp 590.000", "available": True,
            "desc_en": "Los Santos is a satirical mirror of modern society, a sun-soaked metropolis built on vanity, greed, and the pursuit of the almighty dollar. The game is a sociologically astute playground, examining the decay of the American Dream through the eyes of three distinct criminals. It is a chaotic simulation of life on the edge, governed by physics but driven by chaos.\n\nMichael, Franklin, and Trevor represent different facets of the criminal psyche: regret, ambition, and unhinged anarchy. Their intertwining stories create a narrative that is both hilarious and deeply cynical, exploring the emptiness of wealth and the bonds forged in the fires of adversity. It is an emotional ride through a world that loves you one minute and chews you up the next.\n\nThe sheer scale of the world is a technical marvel, a living, breathing ecosystem of traffic, weather, and human interaction. Beneath the violence and heist mechanics lies a biting commentary on celebrity culture, government corruption, and the absurdity of modern life. It is the ultimate escapist fantasy, grounded in a gritty, uncomfortable reality.",
            "desc_id": "Los Santos adalah cermin satir masyarakat modern, kota metropolis yang bermandikan matahari yang dibangun di atas kesombongan, keserakahan, dan pengejaran dolar yang mahakuasa. Game ini adalah taman bermain yang cerdas secara sosiologis, memeriksa pembusukan Impian Amerika melalui mata tiga penjahat yang berbeda. Ini adalah simulasi kacau kehidupan di tepi jurang, diatur oleh fisika tetapi didorong oleh kekacauan.\n\nMichael, Franklin, dan Trevor mewakili sisi berbeda dari jiwa kriminal: penyesalan, ambisi, dan anarki yang tidak terkendali. Kisah-kisah mereka yang saling terkait menciptakan narasi yang lucu sekaligus sangat sinis, mengeksplorasi kekosongan kekayaan dan ikatan yang ditempa dalam api kesulitan. Ini adalah perjalanan emosional melalui dunia yang mencintai Anda satu menit dan mengunyah Anda di menit berikutnya.\n\nSkala dunia yang sangat besar adalah keajaiban teknis, ekosistem lalu lintas, cuaca, dan interaksi manusia yang hidup dan bernapas. Di balik kekerasan dan mekanisme perampokan terdapat komentar tajam tentang budaya selebriti, korupsi pemerintah, dan absurditas kehidupan modern. Ini adalah fantasi pelarian pamungkas, yang berakar pada kenyataan yang berpasir dan tidak nyaman."
        },
        {
            "id": "game7", "title": "God of War IV", "price": "Rp 729.000", "available": True,
            "desc_en": "Kratos returns, not as the rage-fueled destroyer of Olympus, but as a weary father seeking redemption in the harsh realm of Norse mythology. This is a profound shift in narrative tone, replacing vengeance with a deeply emotional exploration of parenthood and legacy. The journey to spread a wife's ashes becomes a touching odyssey of bonding and letting go.\n\nThe relationship between Kratos and Atreus is the heart of the experience, a delicate interplay of discipline and love. The boy represents Kratos's lost humanity, a beacon of hope in a brutal world of gods and monsters. Watching their bond evolve is a poignant reminder that even the hardest hearts can be softened by the love for a child.\n\nVisually and technically, the continuous camera shot immerses players in a seamless flow of action and storytelling. The world of Midgard is rendered with breathtaking detail, a landscape of snow, ancient runes, and sleeping giants. It is a masterpiece that redefines a legend, proving that we are not defined by our past, but by who we choose to be for those we love.",
            "desc_id": "Kratos kembali, bukan sebagai penghancur Olympus yang dipicu kemarahan, tetapi sebagai ayah yang lelah mencari penebusan di alam mitologi Nordik yang keras. Ini adalah pergeseran nada naratif yang mendalam, menggantikan balas dendam dengan eksplorasi emosional yang mendalam tentang orang tua dan warisan. Perjalanan untuk menyebarkan abu seorang istri menjadi pengembaraan yang menyentuh tentang ikatan dan melepaskan.\n\nHubungan antara Kratos dan Atreus adalah inti dari pengalaman ini, interaksi yang halus antara disiplin dan cinta. Bocah itu mewakili kemanusiaan Kratos yang hilang, secercah harapan di dunia brutal para dewa dan monster. Menyaksikan ikatan mereka berkembang adalah pengingat pedih bahwa hati yang paling keras pun dapat dilunakkan oleh cinta untuk seorang anak.\n\nSecara visual dan teknis, bidikan kamera berkelanjutan membenamkan pemain dalam aliran aksi dan penceritaan yang mulus. Dunia Midgard dirender dengan detail yang menakjubkan, lanskap salju, rune kuno, dan raksasa tidur. Ini adalah mahakarya yang mendefinisikan kembali legenda, membuktikan bahwa kita tidak didefinisikan oleh masa lalu kita, tetapi oleh siapa yang kita pilih untuk menjadi bagi mereka yang kita cintai."
        },
        {
            "id": "game8", "title": "Assassin's Creed Syndicate", "price": "Rp 350.000", "available": True,
            "desc_en": "Industrial Revolution London comes alive as a smog-choked labyrinth of progress and poverty. The game is a historical simulation that captures the stark contrast between the wealthy elite and the struggling working class. It explores the scientific acceleration of the era, where steam and steel began to reshape the world, often at the cost of human dignity.\n\nJacob and Evie Frye lead a revolution not just for territory, but for the soul of the city. Their bond as twins adds a layer of familial loyalty and emotional depth to the fight against the Templar order. It is a story of liberation, fighting to reclaim the streets from gang rule and corporate tyranny.\n\nThe mechanics of the rope launcher and carriage combat introduce a new dynamism to the gameplay, reflecting the rapid pace of industrial change. Scaling the soot-stained brickwork of factories and palaces, players witness history in motion. It is a thrilling, atmospheric dive into a pivotal moment in human evolution.",
            "desc_id": "London Revolusi Industri menjadi hidup sebagai labirin kemajuan dan kemiskinan yang tercekik asap. Game ini adalah simulasi sejarah yang menangkap kontras tajam antara elit kaya dan kelas pekerja yang berjuang. Ini mengeksplorasi percepatan ilmiah zaman itu, di mana uap dan baja mulai membentuk kembali dunia, seringkali dengan mengorbankan martabat manusia.\n\nJacob dan Evie Frye memimpin revolusi bukan hanya untuk wilayah, tetapi untuk jiwa kota. Ikatan mereka sebagai saudara kembar menambahkan lapisan kesetiaan keluarga dan kedalaman emosional dalam perjuangan melawan ordo Templar. Ini adalah kisah pembebasan, berjuang untuk merebut kembali jalanan dari kekuasaan geng dan tirani korporat.\n\nMekanika peluncur tali dan pertempuran kereta memperkenalkan dinamisme baru pada gameplay, yang mencerminkan laju cepat perubahan industri. Memanjat bata pabrik dan istana yang bernoda jelaga, pemain menyaksikan sejarah yang bergerak. Ini adalah penyelaman atmosfer yang mendebarkan ke dalam momen penting dalam evolusi manusia."
        },
        {
            "id": "game9", "title": "Ghost of Tsushima", "price": "Rp 879.000", "available": True,
            "desc_en": "Tsushima Island is a breathtaking canvas of feudal Japan, painted with falling cherry blossoms and blood-soaked steel. The game is a visual poem, balancing the serene beauty of nature with the brutal reality of the Mongol invasion. It is a study of honor, tradition, and the agonizing sacrifices required to protect one's homeland.\n\nJin Sakai's transformation from honorable samurai to the Ghost is a tragic emotional arc. He is forced to abandon the rigid code that defined his life to save his people, becoming an outcast in the process. The narrative explores the conflict between duty and morality, asking if the ends truly justify the means when the price is your soul.\n\nThe guiding wind mechanics and lack of HUD immerse players completely in the world, creating a meditative experience amidst the chaos of war. Every duel is a dance of lethal precision, every haiku a moment of reflection. It is a masterpiece of atmosphere and storytelling, a poignant tribute to the spirit of the samurai.",
            "desc_id": "Pulau Tsushima adalah kanvas menakjubkan dari Jepang feodal, dilukis dengan bunga sakura yang berguguran dan baja yang berlumuran darah. Game ini adalah puisi visual, menyeimbangkan keindahan alam yang tenang dengan kenyataan brutal invasi Mongol. Ini adalah studi tentang kehormatan, tradisi, dan pengorbanan menyiksa yang diperlukan untuk melindungi tanah air seseorang.\n\nTransformasi Jin Sakai dari samurai terhormat menjadi The Ghost adalah busur emosional yang tragis. Dia dipaksa untuk meninggalkan kode kaku yang mendefinisikan hidupnya untuk menyelamatkan rakyatnya, menjadi orang buangan dalam prosesnya. Narasi ini mengeksplorasi konflik antara tugas dan moralitas, menanyakan apakah tujuan benar-benar membenarkan cara ketika harganya adalah jiwamu.\n\nMekanika angin penuntun dan kurangnya HUD membenamkan pemain sepenuhnya di dunia, menciptakan pengalaman meditatif di tengah kekacauan perang. Setiap duel adalah tarian presisi yang mematikan, setiap haiku adalah momen refleksi. Ini adalah mahakarya atmosfer dan penceritaan, penghormatan yang pedih bagi semangat samurai."
        },
        {
            "id": "game10", "title": "It Takes Two", "price": "Rp 569.000", "available": True,
            "desc_en": "A whimsical yet profound exploration of relationships, this game turns the concept of couples therapy into a magical, cooperative adventure. It is a psychological journey manifested as a chaotic platformer, where the world shifts to reflect the emotional state of Cody and May. The game scientifically deconstructs the mechanics of partnership: communication, trust, and shared effort.\n\nThe narrative is surprisingly touching, delving into the pain of divorce and its impact on a child. As the couple navigates microscopic worlds in their own backyard, they rediscover the spark that once brought them together. It is a heartwarming reminder that love is work, and that repairing a broken bond requires facing challenges hand in hand.\n\nThe gameplay variety is astounding, constantly reinventing itself to match the story's beats. From riding frogs to piloting planes made of underwear, the creativity is boundless. It is a joyful, emotional rollercoaster that proves gaming is a powerful medium for exploring the complexities of the human heart.",
            "desc_id": "Eksplorasi hubungan yang aneh namun mendalam, game ini mengubah konsep terapi pasangan menjadi petualangan kooperatif yang ajaib. Ini adalah perjalanan psikologis yang dimanifestasikan sebagai platformer yang kacau, di mana dunia bergeser untuk mencerminkan keadaan emosional Cody dan May. Game ini secara ilmiah mendekonstruksi mekanisme kemitraan: komunikasi, kepercayaan, dan upaya bersama.\n\nNarasinya secara mengejutkan menyentuh, menggali rasa sakit perceraian dan dampaknya pada seorang anak. Saat pasangan itu menavigasi dunia mikroskopis di halaman belakang mereka sendiri, mereka menemukan kembali percikan yang pernah menyatukan mereka. Ini adalah pengingat yang mengharukan bahwa cinta adalah pekerjaan, dan bahwa memperbaiki ikatan yang rusak membutuhkan menghadapi tantangan bergandengan tangan.\n\nVariasi gameplaynya mencengangkan, terus-menerus menciptakan kembali dirinya sendiri untuk mencocokkan ketukan cerita. Dari menunggang katak hingga mengemudikan pesawat yang terbuat dari celana dalam, kreativitasnya tidak terbatas. Ini adalah rollercoaster emosional yang menyenangkan yang membuktikan game adalah media yang kuat untuk mengeksplorasi kompleksitas hati manusia."
        },
        {
            "id": "game11", "title": "Splinter Cell: Blacklist", "price": "Rp 250.000", "available": False,
            "desc_en": "Sam Fisher returns in a high-stakes geopolitical thriller that emphasizes stealth, precision, and the weight of command. The Blacklist attacks are a ticking clock, a calculated terror campaign that forces Fourth Echelon to operate in the shadows. The game is a tactical simulation of modern warfare, where information is the most lethal weapon.\n\nThe narrative explores the burden of leadership and the moral compromises required to protect national security. Sam is older, more cynical, carrying the scars of a lifetime of service. His interactions with his team reveal a man who has sacrificed everything for the mission, isolated by his own competence and the secrets he keeps.\n\nThe gameplay offers freedom of approach, from ghost-like stealth to lethal aggression, reflecting the adaptability required of a top-tier operative. The tension of infiltrating heavily guarded compounds is palpable, a test of nerves and strategy. It is a gripping, intelligent action game that respects the player's intelligence.",
            "desc_id": "Sam Fisher kembali dalam thriller geopolitik berisiko tinggi yang menekankan pada siluman, presisi, dan bobot komando. Serangan Blacklist adalah jam yang berdetak, kampanye teror terhitung yang memaksa Fourth Echelon beroperasi dalam bayang-bayang. Game ini adalah simulasi taktis perang modern, di mana informasi adalah senjata paling mematikan.\n\nNarasi ini mengeksplorasi beban kepemimpinan dan kompromi moral yang diperlukan untuk melindungi keamanan nasional. Sam lebih tua, lebih sinis, membawa bekas luka dari pengabdian seumur hidup. Interaksinya dengan timnya mengungkapkan seorang pria yang telah mengorbankan segalanya untuk misi, terisolasi oleh kompetensinya sendiri dan rahasia yang disimpannya.\n\nGameplay menawarkan kebebasan pendekatan, dari siluman seperti hantu hingga agresi mematikan, yang mencerminkan kemampuan beradaptasi yang dituntut dari agen tingkat atas. Ketegangan menyusup ke kompleks yang dijaga ketat sangat terasa, ujian saraf dan strategi. Ini adalah game aksi yang mencekam dan cerdas yang menghormati kecerdasan pemain."
        },
        {
            "id": "game12", "title": "Life is Strange", "price": "Rp 300.000", "available": True,
            "desc_en": "Arcadia Bay is a picturesque coastal town hiding dark secrets, the setting for a supernatural coming-of-age story that resonates with raw emotional power. Max Caulfield's ability to rewind time is not just a gameplay mechanic, but a metaphor for the universal desire to fix mistakes and change the past. It is a scientific fantasy grounded in the turbulence of adolescence.\n\nThe relationship between Max and Chloe is the emotional anchor, a poignant exploration of rekindled friendship, loss, and destiny. The game tackles heavy themes like bullying, suicide, and the butterfly effect with sensitivity and grace. Every choice ripples through time, leading to consequences that are often heartbreaking and unforeseen.\n\nThe indie-folk soundtrack and hand-painted art style create a nostalgic, dreamlike atmosphere. It is a narrative experience that lingers long after the credits roll, forcing players to confront the reality that some things cannot be changed, and that growing up means learning to live with our choices.",
            "desc_id": "Arcadia Bay adalah kota pesisir yang indah yang menyembunyikan rahasia gelap, latar untuk kisah kedewasaan supranatural yang bergema dengan kekuatan emosional mentah. Kemampuan Max Caulfield untuk memundurkan waktu bukan hanya mekanika gameplay, tetapi metafora untuk keinginan universal untuk memperbaiki kesalahan dan mengubah masa lalu. Ini adalah fantasi ilmiah yang berakar pada turbulensi masa remaja.\n\nHubungan antara Max dan Chloe adalah jangkar emosional, eksplorasi pedih tentang persahabatan yang dinyalakan kembali, kehilangan, dan takdir. Game ini menangani tema-tema berat seperti intimidasi, bunuh diri, dan efek kupu-kupu dengan kepekaan dan keanggunan. Setiap pilihan beriak melalui waktu, mengarah pada konsekuensi yang seringkali memilukan dan tak terduga.\n\nSoundtrack indie-folk dan gaya seni lukisan tangan menciptakan suasana nostalgia yang seperti mimpi. Ini adalah pengalaman naratif yang bertahan lama setelah kredit bergulir, memaksa pemain untuk menghadapi kenyataan bahwa beberapa hal tidak dapat diubah, dan bahwa tumbuh dewasa berarti belajar hidup dengan pilihan kita."
        },
        {
            "id": "game13", "title": "Batman Arkham Knight", "price": "Rp 280.000", "available": True,
            "desc_en": "Gotham City is a rain-slicked monument to crime and madness, and this finale to the Arkham trilogy is a spectacular descent into the Dark Knight's psyche. The Scarecrow's fear toxin turns the city into a hallucinogenic nightmare, a scientific weaponization of terror. Batman faces his ultimate challenge, battling not just external threats, but the demons within his own mind.\n\nThe narrative dissects the Batman mythos, questioning the consequences of his crusade and the blurred line between hero and vigilante. The inclusion of the Joker as a mental projection adds a layer of psychological horror, a constant, mocking commentary on Batman's failures. It is an emotional deconstruction of the man behind the mask.\n\nThe Batmobile introduces a tank-like power fantasy, while the fluid combat and stealth remain the gold standard. Gliding over the neon-lit skyline of Gotham feels empowering yet lonely. It is a dark, cinematic conclusion that honors the legacy of the character, delivering a powerful message about fear and the will to overcome it.",
            "desc_id": "Gotham City adalah monumen kejahatan dan kegilaan yang basah oleh hujan, dan final trilogi Arkham ini adalah turunan spektakuler ke dalam jiwa Dark Knight. Racun ketakutan Scarecrow mengubah kota menjadi mimpi buruk halusinogen, persenjataan teror ilmiah. Batman menghadapi tantangan utamanya, bertarung bukan hanya ancaman eksternal, tetapi iblis di dalam pikirannya sendiri.\n\nNarasi ini membedah mitos Batman, mempertanyakan konsekuensi dari perang salibnya dan batas yang kabur antara pahlawan dan main hakim sendiri. Dimasukkannya Joker sebagai proyeksi mental menambahkan lapisan horor psikologis, komentar yang terus-menerus dan mengejek tentang kegagalan Batman. Ini adalah dekonstruksi emosional dari pria di balik topeng.\n\nBatmobile memperkenalkan fantasi kekuatan seperti tank, sementara pertempuran cair dan siluman tetap menjadi standar emas. Meluncur di atas cakrawala Gotham yang diterangi neon terasa memberdayakan namun sepi. Ini adalah kesimpulan sinematik yang gelap yang menghormati warisan karakter, menyampaikan pesan yang kuat tentang ketakutan dan keinginan untuk mengatasinya."
        },
        {
            "id": "game14", "title": "Dying Light", "price": "Rp 320.000", "available": True,
            "desc_en": "Harran is a quarantine zone overrun by the infected, a playground of parkour and survival horror. The game masterfully blends fast-paced movement with visceral combat, creating a rhythmic flow of adrenaline. The day-night cycle is a scientific stress test; by day you are the hunter, but by night, the Volatiles emerge, and you become the prey.\n\nKyle Crane's mission evolves from a covert operation to a desperate fight for the survival of the city's remnants. The narrative explores themes of altruism in the face of annihilation, as Crane bonds with the survivors and questions his orders. It is a story of human resilience, finding hope in a hopeless place.\n\nThe verticality of the world offers a sense of freedom amidst the claustrophobia of the zombie horde. Leaping across rooftops while the sun sets and the screams begin is a terrifyingly beautiful experience. It is a game that makes you feel the physical exertion of survival, a heart-pounding rush from start to finish.",
            "desc_id": "Harran adalah zona karantina yang dibanjiri oleh mereka yang terinfeksi, taman bermain parkour dan horor bertahan hidup. Game ini dengan ahli memadukan gerakan cepat dengan pertempuran mendalam, menciptakan aliran adrenalin yang berirama. Siklus siang-malam adalah uji stres ilmiah; di siang hari Anda adalah pemburu, tetapi di malam hari, Volatiles muncul, dan Anda menjadi mangsa.\n\nMisi Kyle Crane berevolusi dari operasi rahasia menjadi pertarungan putus asa untuk kelangsungan hidup sisa-sisa kota. Narasi ini mengeksplorasi tema altruisme dalam menghadapi pemusnahan, saat Crane menjalin ikatan dengan para penyintas dan mempertanyakan perintahnya. Ini adalah kisah ketahanan manusia, menemukan harapan di tempat tanpa harapan.\n\nVertikalitas dunia menawarkan rasa kebebasan di tengah klaustrofobia gerombolan zombie. Melompat melintasi atap saat matahari terbenam dan jeritan dimulai adalah pengalaman yang sangat indah namun menakutkan. Ini adalah game yang membuat Anda merasakan pengerahan tenaga fisik untuk bertahan hidup, aliran yang memacu jantung dari awal hingga akhir."
        },
        {
            "id": "game15", "title": "Infamous Second Son", "price": "Rp 299.000", "available": False,
            "desc_en": "Seattle serves as a wet, neon-soaked backdrop for a superhero origin story that deals with discrimination and control. Delsin Rowe is a conduit, labeled a bio-terrorist by a society that fears what it doesn't understand. The game is a visual spectacle of particle effects and powers, representing the chaotic potential of genetic mutation.\n\nThe narrative is a classic allegory for civil rights and personal freedom. Delsin's journey from delinquent to savior (or villain) is shaped by his choices and his relationship with his brother Reggie. It is an emotional tale of brotherhood and responsibility, asking what you would do if you had the power to change everything.\n\nThe sense of speed and fluidity in traversing the city is exhilarating. Whether soaring as smoke or dashing as neon light, the gameplay empowers players to own the environment. It is a rebellious, punk-rock infused adventure that celebrates individuality and the fight against oppression.",
            "desc_id": "Seattle berfungsi sebagai latar belakang yang basah dan basah kuyup neon untuk kisah asal pahlawan super yang berhubungan dengan diskriminasi dan kontrol. Delsin Rowe adalah saluran, dicap sebagai bio-teroris oleh masyarakat yang takut pada apa yang tidak dipahaminya. Game ini adalah tontonan visual dari efek partikel dan kekuatan, mewakili potensi kacau mutasi genetik.\n\nNarasi ini adalah alegori klasik untuk hak-hak sipil dan kebebasan pribadi. Perjalanan Delsin dari anak nakal menjadi penyelamat (atau penjahat) dibentuk oleh pilihannya dan hubungannya dengan saudaranya Reggie. Ini adalah kisah emosional tentang persaudaraan dan tanggung jawab, menanyakan apa yang akan Anda lakukan jika Anda memiliki kekuatan untuk mengubah segalanya.\n\nRasa kecepatan dan fluiditas dalam melintasi kota sangat mengasyikkan. Baik melambung sebagai asap atau berlari sebagai cahaya neon, gameplay memberdayakan pemain untuk memiliki lingkungan. Ini adalah petualangan pemberontak, yang diresapi punk-rock yang merayakan individualitas dan perjuangan melawan penindasan."
        },
        {
            "id": "game16", "title": "The Witcher III: Wild Hunt", "price": "Rp 450.000", "available": True,
            "desc_en": "The Continent is a vast, war-torn expanse where monsters are often less terrifying than the humans who hire you to kill them. Geralt of Rivia's search for Ciri is a sprawling epic that transcends the fantasy genre, grounding its magic in a gritty, realistic medieval world. It is a scientific study of folklore and ecology, where every creature has a weakness and every curse a cause.\n\nThe storytelling is unparalleled, weaving complex political intrigues with intimate, personal dramas. Every side quest feels like a short story, rich with tragedy and humor. The bond between Geralt and Ciri is the emotional core, a depiction of fatherhood by choice that is both tender and fiercely protective.\n\nThe world feels alive, indifferent to the player's presence yet reactive to their choices. From the swamps of Velen to the peaks of Skellige, the atmosphere is heavy with history and melancholy. It is a landmark achievement in role-playing games, a journey that leaves an indelible mark on the soul.",
            "desc_id": "The Continent adalah hamparan luas yang dilanda perang di mana monster seringkali kurang menakutkan daripada manusia yang menyewa Anda untuk membunuh mereka. Pencarian Geralt of Rivia untuk Ciri adalah epik luas yang melampaui genre fantasi, membumikan sihirnya di dunia abad pertengahan yang berpasir dan realistis. Ini adalah studi ilmiah tentang cerita rakyat dan ekologi, di mana setiap makhluk memiliki kelemahan dan setiap kutukan memiliki penyebab.\n\nPenceritaannya tidak tertandingi, menenun intrik politik yang kompleks dengan drama pribadi yang intim. Setiap misi sampingan terasa seperti cerita pendek, kaya dengan tragedi dan humor. Ikatan antara Geralt dan Ciri adalah inti emosional, penggambaran peran ayah berdasarkan pilihan yang lembut namun sangat protektif.\n\nDunia terasa hidup, acuh tak acuh terhadap kehadiran pemain namun reaktif terhadap pilihan mereka. Dari rawa-rawa Velen hingga puncak Skellige, atmosfernya berat dengan sejarah dan melankolia. Ini adalah pencapaian penting dalam permainan peran, sebuah perjalanan yang meninggalkan bekas yang tak terhapuskan pada jiwa."
        },
        {
            "id": "game17", "title": "Outlast 2", "price": "Rp 270.000", "available": True,
            "desc_en": "Deep in the Arizona desert, investigative journalism turns into a desperate flight from religious fanaticism. This game pushes the boundaries of psychological horror, exploring the darkest corners of the human mind and the corrupting power of blind faith. It is a visceral, disturbing experience that assaults the senses with gore and taboo imagery.\n\nBlake Langermann's search for his wife Lynn is a descent into madness, haunted by traumatic memories of his childhood. The narrative blurs the line between reality and hallucination, forcing players to question their own sanity. It is an emotional ordeal, stripping away power and leaving only the primal instinct to run and hide.\n\nThe use of the camcorder as a survival tool creates a unique perspective, filtering the horror through a grainy, night-vision lens. The sound design is terrifyingly immersive, amplifying every creak and whisper. It is a relentless, uncompromising journey into hell that tests the player's endurance.",
            "desc_id": "Jauh di gurun Arizona, jurnalisme investigasi berubah menjadi pelarian putus asa dari fanatisme agama. Game ini mendorong batas-batas horor psikologis, mengeksplorasi sudut-sudut tergelap pikiran manusia dan kekuatan korup dari keyakinan buta. Ini adalah pengalaman mendalam dan mengganggu yang menyerang indra dengan darah kental dan citra tabu.\n\nPencarian Blake Langermann untuk istrinya Lynn adalah turunan menuju kegilaan, dihantui oleh kenangan traumatis masa kecilnya. Narasi ini mengaburkan batas antara kenyataan dan halusinasi, memaksa pemain untuk mempertanyakan kewarasan mereka sendiri. Ini adalah cobaan emosional, melucuti kekuatan dan hanya menyisakan naluri purba untuk lari dan bersembunyi.\n\nPenggunaan camcorder sebagai alat bertahan hidup menciptakan perspektif yang unik, menyaring horor melalui lensa penglihatan malam yang berbutir. Desain suaranya sangat imersif, memperkuat setiap derit dan bisikan. Ini adalah perjalanan tanpa henti dan tanpa kompromi ke neraka yang menguji daya tahan pemain."
        },
        {
            "id": "game18", "title": "Alien Isolation", "price": "Rp 380.000", "available": True,
            "desc_en": "Sevastopol Station is a decaying monolith of retro-futuristic technology, a perfect trap for the ultimate organism. The Xenomorph is not just an enemy; it is a dynamic, unscripted intelligence that learns and hunts. This survival horror game is a masterclass in tension, capturing the aesthetic and atmosphere of the original film with scientific precision.\n\nAmanda Ripley's search for her mother's flight recorder is a terrifying game of cat and mouse. The emotional weight of her quest adds vulnerability to her character, making her survival feel crucial. The isolation is palpable, a suffocating silence broken only by the hiss of steam and the thud of heavy footsteps.\n\nThe AI of the Alien creates a constant state of dread, where no place is safe and every noise could be your last. It forces players to think, adapt, and hold their breath. It is the definitive Alien experience, a terrifying tribute to the perfection of a killing machine.",
            "desc_id": "Stasiun Sevastopol adalah monolit teknologi retro-futuristik yang membusuk, perangkap sempurna bagi organisme pamungkas. Xenomorph bukan hanya musuh; ini adalah kecerdasan dinamis dan tidak tertulis yang belajar dan berburu. Game horor bertahan hidup ini adalah kelas master dalam ketegangan, menangkap estetika dan suasana film orisinal dengan presisi ilmiah.\n\nPencarian Amanda Ripley untuk perekam penerbangan ibunya adalah permainan kucing dan tikus yang menakutkan. Beban emosional pencariannya menambah kerentanan pada karakternya, membuat kelangsungan hidupnya terasa krusial. Isolasi itu sangat terasa, keheningan menyesakkan yang hanya dipecahkan oleh desis uap dan bunyi langkah kaki yang berat.\n\nAI Alien menciptakan keadaan ketakutan yang konstan, di mana tidak ada tempat yang aman dan setiap suara bisa menjadi yang terakhir bagi Anda. Ini memaksa pemain untuk berpikir, beradaptasi, dan menahan napas. Ini adalah pengalaman Alien yang definitif, penghormatan yang menakutkan bagi kesempurnaan mesin pembunuh."
        },
        {
            "id": "game19", "title": "Bully", "price": "Rp 150.000", "available": True,
            "desc_en": "Bullworth Academy is a microcosm of societal hierarchy, a satirical playground where adolescents clash for dominance. Jimmy Hopkins is the ultimate anti-hero, navigating the treacherous waters of cliques, teachers, and pranks. The game is a sociological experiment, exploring the cruelty and camaraderie of boarding school life with biting humor.\n\nThe narrative is a coming-of-age story wrapped in rebellion. Jimmy's quest to bring peace to the school is surprisingly noble, despite his rough methods. It captures the awkwardness and intensity of teenage years, an emotional mix of frustration, first loves, and the desire to belong.\n\nThe variety of classes and mini-games adds depth to the school simulation, making the world feel lived-in and authentic. The soundtrack is iconic, setting a mischievous tone. It is a unique, charming, and subversively smart game that remains a cult classic.",
            "desc_id": "Akademi Bullworth adalah mikrokosmos hierarki masyarakat, taman bermain satir di mana remaja bentrok untuk mendominasi. Jimmy Hopkins adalah anti-hero pamungkas, menavigasi perairan berbahaya dari klik, guru, dan lelucon. Game ini adalah eksperimen sosiologis, mengeksplorasi kekejaman dan persahabatan kehidupan sekolah asrama dengan humor yang tajam.\n\nNarasi ini adalah kisah kedewasaan yang dibungkus dengan pemberontakan. Upaya Jimmy untuk membawa perdamaian ke sekolah secara mengejutkan mulia, meskipun metodenya kasar. Ini menangkap kecanggunggan dan intensitas masa remaja, campuran emosional dari frustrasi, cinta pertama, dan keinginan untuk menjadi bagian.\n\nVariasi kelas dan mini-game menambah kedalaman simulasi sekolah, membuat dunia terasa hidup dan otentik. Soundtrack-nya ikonik, menetapkan nada nakal. Ini adalah game yang unik, menawan, dan cerdas secara subversif yang tetap menjadi klasik kultus."
        },
        {
            "id": "game20", "title": "Red Dead Redemption 2", "price": "Rp 680.000", "available": True,
            "desc_en": "The twilight of the Wild West is rendered with aching beauty and tragic inevitability. Arthur Morgan's journey with the Van der Linde gang is a slow-burn epic about loyalty, betrayal, and the death of an era. The world is a stunningly detailed simulation of frontier life, where every mud puddle and sunset feels real.\n\nArthur is a complex protagonist, a man of violence grappling with his own mortality and morality. His redemption arc is deeply moving, a quiet struggle to do one good thing before the end. The bonds he forms and breaks are the emotional sinew of the story, leaving players devastated by the inevitable conclusion.\n\nThe pace is deliberate, inviting players to live in the world rather than just play through it. Hunting, fishing, and camping are as integral as gunfights. It is a masterpiece of immersion and character study, a sad, beautiful song of the dying West.",
            "desc_id": "Senja Wild West dirender dengan keindahan yang menyakitkan dan keniscayaan tragis. Perjalanan Arthur Morgan dengan geng Van der Linde adalah epik yang membakar perlahan tentang kesetiaan, pengkhianatan, dan kematian sebuah era. Dunia adalah simulasi kehidupan perbatasan yang sangat detail, di mana setiap genangan lumpur dan matahari terbenam terasa nyata.\n\nArthur adalah protagonis yang kompleks, seorang pria kekerasan yang bergulat dengan kematian dan moralitasnya sendiri. Busur penebusannya sangat mengharukan, perjuangan diam untuk melakukan satu hal baik sebelum akhir. Ikatan yang dia bentuk dan putuskan adalah otot emosional cerita, meninggalkan pemain hancur oleh kesimpulan yang tak terelakkan.\n\nTemponya disengaja, mengundang pemain untuk hidup di dunia daripada hanya memainkannya. Berburu, memancing, dan berkemah sama pentingnya dengan baku tembak. Ini adalah mahakarya imersi dan studi karakter, lagu sedih dan indah dari Barat yang sekarat."
        },
        {
            "id": "game21", "title": "Cyberpunk 2077", "price": "Rp 620.000", "available": True,
            "desc_en": "Night City is a dazzling, dystopian megalopolis obsessed with power, glamour, and body modification. V's struggle for survival with the digital ghost of Johnny Silverhand in their head is a high-tech thriller about identity and the soul. The game explores transhumanism and corporate control, painting a dark future where humanity is a commodity.\n\nThe relationship between V and Johnny is the driving force, a clash of personalities that evolves into a grudging respect. The narrative choices are meaningful, leading to multiple endings that reflect the player's values. It is an emotional ride through a world of chrome and neon, where dreams go to die.\n\nThe density and verticality of the city are overwhelming, a visual feast of futuristic architecture and street life. The combat and hacking mechanics offer diverse playstyles. Despite its flaws, it is an ambitious, immersive experience that asks what it means to be human in a world of machines.",
            "desc_id": "Night City adalah megalopolis distopia yang mempesona yang terobsesi dengan kekuatan, pesona, dan modifikasi tubuh. Perjuangan V untuk bertahan hidup dengan hantu digital Johnny Silverhand di kepala mereka adalah thriller teknologi tinggi tentang identitas dan jiwa. Game ini mengeksplorasi transhumanisme dan kontrol korporat, melukiskan masa depan yang gelap di mana kemanusiaan adalah komoditas.\n\nHubungan antara V dan Johnny adalah kekuatan pendorong, bentrokan kepribadian yang berkembang menjadi rasa hormat yang enggan. Pilihan naratif bermakna, mengarah ke beberapa akhir yang mencerminkan nilai-nilai pemain. Ini adalah perjalanan emosional melalui dunia krom dan neon, di mana mimpi pergi untuk mati.\n\nKepadatan dan vertikalitas kota sangat luar biasa, pesta visual arsitektur futuristik dan kehidupan jalanan. Mekanika pertempuran dan peretasan menawarkan gaya bermain yang beragam. Terlepas dari kekurangannya, ini adalah pengalaman yang ambisius dan imersif yang menanyakan apa artinya menjadi manusia di dunia mesin."
        },
        {
            "id": "game22", "title": "Elden Ring", "price": "Rp 799.000", "available": True,
            "desc_en": "The Lands Between is a sprawling fantasy realm of decay and majesty, crafted by the minds of Hidetaka Miyazaki and George R.R. Martin. As a Tarnished, you are guided by grace to brandish the power of the Elden Ring and become an Elden Lord. The game is a masterclass in open-world design, encouraging exploration and discovery without hand-holding.\n\nThe lore is deep and cryptic, hidden in item descriptions and environmental storytelling. Every boss encounter is a test of skill and determination, a brutal dance that demands perfection. The sense of scale is awe-inspiring, from the golden Erdtree to the depths of the underground cities.\n\nIt is a journey of solitude and triumph, a challenge that rewards curiosity and perseverance. The freedom to forge your own path creates a unique adventure for every player. It is a monumental achievement that redefines what an open-world RPG can be.",
            "desc_id": "The Lands Between adalah ranah fantasi luas dari pembusukan dan keagungan, dibuat oleh pikiran Hidetaka Miyazaki dan George R.R. Martin. Sebagai Tarnished, Anda dibimbing oleh anugerah untuk menggunakan kekuatan Elden Ring dan menjadi Elden Lord. Game ini adalah kelas master dalam desain dunia terbuka, mendorong eksplorasi dan penemuan tanpa pegangan tangan.\n\nLore-nya dalam dan samar, tersembunyi dalam deskripsi item dan penceritaan lingkungan. Setiap pertemuan bos adalah ujian keterampilan dan tekad, tarian brutal yang menuntut kesempurnaan. Rasa skalanya sangat menginspirasi, dari Erdtree emas hingga kedalaman kota bawah tanah.\n\nIni adalah perjalanan kesendirian dan kemenangan, tantangan yang menghargai rasa ingin tahu dan ketekunan. Kebebasan untuk menempa jalan Anda sendiri menciptakan petualangan unik bagi setiap pemain. Ini adalah pencapaian monumental yang mendefinisikan kembali apa yang bisa menjadi RPG dunia terbuka."
        },
        {
            "id": "game23", "title": "Marvel's Spider-Man", "price": "Rp 529.000", "available": True,
            "desc_en": "New York City is your playground, a vibrant urban jungle perfect for web-swinging. Peter Parker is an experienced Spider-Man, balancing his chaotic personal life with his responsibilities as a hero. The game captures the joy of movement and the thrill of being a superhero with incredible polish and cinematic flair.\n\nThe narrative digs deep into Peter's relationships with MJ, Aunt May, and his mentors turned villains. It is an emotionally resonant story about mentorship, loss, and the cost of doing the right thing. The duality of Peter and Spider-Man is explored with heart and humor.\n\nThe combat is acrobatic and improvisational, making you feel powerful and agile. The city feels alive, filled with landmarks and crimes to stop. It is the definitive Spider-Man experience, a love letter to the character that sets a new standard for superhero games.",
            "desc_id": "Kota New York adalah taman bermain Anda, hutan kota yang hidup dan sempurna untuk berayun jaring. Peter Parker adalah Spider-Man yang berpengalaman, menyeimbangkan kehidupan pribadinya yang kacau dengan tanggung jawabnya sebagai pahlawan. Game ini menangkap kegembiraan gerakan dan sensasi menjadi pahlawan super dengan polesan luar biasa dan bakat sinematik.\n\nNarasi menggali jauh ke dalam hubungan Peter dengan MJ, Bibi May, dan mentornya yang berubah menjadi penjahat. Ini adalah kisah yang bergema secara emosional tentang bimbingan, kehilangan, dan harga melakukan hal yang benar. Dualitas Peter dan Spider-Man dieksplorasi dengan hati dan humor.\n\nPertarungannya akrobatik dan improvisasi, membuat Anda merasa kuat dan gesit. Kota terasa hidup, dipenuhi dengan landmark dan kejahatan untuk dihentikan. Ini adalah pengalaman Spider-Man yang definitif, surat cinta untuk karakter yang menetapkan standar baru untuk game superhero."
        },
        {
            "id": "game24", "title": "Final Fantasy VII Remake", "price": "Rp 699.000", "available": False,
            "desc_en": "Midgar is a city of mako energy and steel, a cyberpunk metropolis ruled by the Shinra Electric Power Company. Cloud Strife, a mercenary with a clouded past, joins Avalanche in a fight for the planet. The game reimagines a classic RPG with modern visuals and a hybrid combat system that is both strategic and action-packed.\n\nThe characters are fleshed out with incredible depth, their interactions full of charm and emotion. The story expands on the original, diving deeper into the motivations of Avalanche and the citizens of the slums. It is a nostalgic yet fresh experience, blending beloved memories with new surprises.\n\nThe visuals are stunning, bringing the grime and glory of Midgar to life. The soundtrack is a masterpiece of arrangement, evoking powerful emotions. It is a bold first step in a new saga, honoring the legacy of the original while charting a new course.",
            "desc_id": "Midgar adalah kota energi mako dan baja, metropolis cyberpunk yang diperintah oleh Perusahaan Tenaga Listrik Shinra. Cloud Strife, seorang tentara bayaran dengan masa lalu yang mendung, bergabung dengan Avalanche dalam perjuangan untuk planet ini. Game ini membayangkan kembali RPG klasik dengan visual modern dan sistem pertarungan hibrida yang strategis dan penuh aksi.\n\nKarakter-karakternya disempurnakan dengan kedalaman yang luar biasa, interaksi mereka penuh pesona dan emosi. Ceritanya memperluas yang asli, menyelam lebih dalam ke motivasi Avalanche dan warga daerah kumuh. Ini adalah pengalaman nostalgia namun segar, memadukan kenangan tercinta dengan kejutan baru.\n\nVisualnya memukau, menghidupkan kotoran dan kemuliaan Midgar. Soundtrack-nya adalah mahakarya aransemen, membangkitkan emosi yang kuat. Ini adalah langkah pertama yang berani dalam saga baru, menghormati warisan yang asli sambil memetakan arah baru."
        }
    ]

# --- ROUTES ---

def render_page(content, **kwargs):
    # Inject fragments before rendering to allow Jinja to process them
    content = content.replace('{{ styles|safe }}', STYLES_HTML)
    content = content.replace('{{ navbar|safe }}', NAVBAR_HTML)
    return render_template_string(content, **kwargs)

@app.route('/')
def index():
    # Scan for game images for all 24 games
    game_images = {}
    for i in range(1, 25):
        found = None
        for ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'svg', 'ico']:
             fname = f"game{i}.{ext}"
             if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname)):
                 found = fname
                 break
        game_images[f'game{i}'] = found if found else 'default_game.jpg' 
    
    games = get_games_data()
    return render_page(HTML_GAME_LIST, game_images=game_images, games=games)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/wallpaper-blur')
def wallpaper_blur():
    return redirect(url_for('index'))

@app.route('/wallpaper-blur/upload', methods=['POST'])
def wallpaper_upload():
    if 'background' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['background']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        with open('bg_config.txt', 'w') as f:
            f.write(filename)
            
    return redirect(url_for('index'))

@app.route('/list-game-playstation')
def list_game_playstation():
    # Identical to index now
    game_images = {}
    for i in range(1, 25):
        found = None
        for ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'svg', 'ico']:
             fname = f"game{i}.{ext}"
             if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname)):
                 found = fname
                 break
        game_images[f'game{i}'] = found if found else 'default_game.jpg' 
        
    games = get_games_data()
    return render_page(HTML_GAME_LIST, game_images=game_images, games=games)

@app.route('/list-game-playstation/upload/<game_id>', methods=['POST'])
def upload_game_image(game_id):
    # Allow game1 to game24
    allowed_ids = [f'game{i}' for i in range(1, 25)]
    if game_id not in allowed_ids:
        return "Invalid Game ID", 400

    if 'game_image' not in request.files:
        return redirect(url_for('list_game_playstation'))
    
    file = request.files['game_image']
    if file and file.filename != '' and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        # Remove old images for this game_id
        for e in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'svg', 'ico']:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{game_id}.{e}")
            if os.path.exists(old_path):
                os.remove(old_path)
                
        new_filename = f"{game_id}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        
    return redirect(url_for('list_game_playstation'))

@app.route('/wallpaper-blur/delete-audio/<filename>')
def delete_audio(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('index'))

@app.route('/wallpaper-blur/rename-audio', methods=['POST'])
def rename_audio():
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')
    
    if old_name and new_name:
        safe_old = secure_filename(old_name)
        safe_new = secure_filename(new_name)
        
        # Keep extension
        if '.' in safe_old:
            ext = safe_old.rsplit('.', 1)[1]
            if not safe_new.endswith(f'.{ext}'):
                safe_new += f'.{ext}'
        
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_old)
        new_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_new)
        
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)
            # Update config if active
            if os.path.exists('audio_config.txt'):
                with open('audio_config.txt', 'r') as f:
                    curr = f.read().strip()
                if curr == safe_old:
                    with open('audio_config.txt', 'w') as f:
                        f.write(safe_new)
                        
    return redirect(url_for('index'))

@app.route('/wallpaper-blur/upload-audio', methods=['POST'])
def audio_upload():
    if 'audio' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['audio']
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        with open('audio_config.txt', 'w') as f:
            f.write(filename)
            
    return redirect(url_for('index'))


# --- FRONTEND FRAGMENTS ---

NAVBAR_HTML = """
    <style>
        .navbar {
            background-color: rgba(0, 0, 0, 0.6) !important;
            backdrop-filter: blur(15px) saturate(120%);
            -webkit-backdrop-filter: blur(15px) saturate(120%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        .navbar-brand {
            font-weight: 800;
            font-size: 1.8rem;
            color: white !important;
            letter-spacing: -1px;
            text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
        }
        .brand-verse {
            color: #00f3ff;
            text-shadow: 0 0 5px #00f3ff, 0 0 10px #00f3ff, 0 0 20px #00f3ff;
            font-style: italic;
        }
        .nav-link {
            color: rgba(255, 255, 255, 0.8) !important;
            font-weight: 500;
            margin-right: 15px;
            transition: color 0.3s;
        }
        .nav-link:hover {
            color: white !important;
            text-shadow: 0 0 8px rgba(255,255,255,0.5);
        }
        .join-btn {
            border: 1px solid #00f3ff;
            color: #00f3ff !important;
            border-radius: 5px;
            padding: 5px 15px;
            box-shadow: 0 0 5px rgba(0, 243, 255, 0.2);
            transition: all 0.3s;
        }
        .join-btn:hover {
            background: rgba(0, 243, 255, 0.1);
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.4);
        }
        /* Mobile Menu Toggler White Fix */
        .navbar-toggler {
            border-color: rgba(255,255,255,0.5) !important;
        }
        .navbar-toggler-icon {
            filter: brightness(0) invert(1) !important;
        }

        /* Mobile Menu Acrylic Box */
        @media (max-width: 991px) {
            .navbar-collapse {
                background: rgba(0, 0, 0, 0.85);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 20px;
                margin-top: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }
        }
    </style>
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container">
            <a class="navbar-brand" href="/">Game<span class="brand-verse">Verse</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon" style="filter: brightness(0) invert(1);"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#">Popular Games</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#">New Releases</a>
                    </li>
                </ul>
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item">
                        <a class="nav-link join-btn" href="#">Join Community</a>
                    </li>
                    <li class="nav-item ms-3">
                        <button type="button" class="btn btn-outline-light btn-sm" onclick="toggleLanguage()" id="lang-btn">ID</button>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
"""

STYLES_HTML = """
    <style>
        :root {
            --brand-color: #E5322D;
            --brand-hover: #c41b17;
            --bg-light: #f4f7fa;
            --card-bg: #ffffff;
            --text-dark: #333333;
            --text-muted: #666666;
            --neon-blue: #00f3ff;
        }
        /* Keep existing variable definitions */
        [data-bs-theme="dark"] {
            --bg-light: #1a1a1a;
            --card-bg: #2d2d2d;
            --text-dark: #f1f1f1;
            --text-muted: #aaaaaa;
        }
        body {
            font-family: 'Inter', sans-serif;
        }
        html {
            scroll-behavior: smooth;
        }

        .text-blue-neon {
            color: var(--neon-blue);
            text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
        }

        .btn-cyan-neon {
            background: transparent;
            border: 2px solid var(--neon-blue);
            color: var(--neon-blue);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.2);
            transition: all 0.3s;
        }
        .btn-cyan-neon:hover {
            background: var(--neon-blue);
            color: black;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.6);
            transform: translateY(-2px);
        }
    </style>
"""

HTML_GAME_LIST = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GameVerse Store</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        body {
            background-color: #050505;
            background-image: url('https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=2070&auto=format&fit=crop');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: white;
        }
        .acrylic-overlay-page {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(20px);
            z-index: -1;
        }

        /* Hero Section */
        .hero-section {
            padding: 80px 20px;
            position: relative;
        }
        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.2;
            text-shadow: 0 4px 20px rgba(0,0,0,0.8);
        }
        .hero-subtitle {
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.8);
            max-width: 600px;
            margin: 0 auto;
        }

        /* Section Header */
        .section-header h2 {
            font-size: 2rem;
            margin-bottom: 20px;
            display: inline-block;
        }

        /* Grid Layout */
        .games-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }

        /* Responsive tweaks */
        @media (max-width: 1400px) { .games-grid { grid-template-columns: repeat(4, 1fr); } }
        @media (max-width: 992px) { .games-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 768px) { .games-grid { grid-template-columns: repeat(2, 1fr); } }

        /* Mini Card */
        .mini-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
            display: flex;
            flex-direction: column;
        }
        .mini-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border-color: rgba(255, 255, 255, 0.3);
        }
        .mini-poster {
            width: 100%;
            aspect-ratio: 1/1;
            object-fit: cover;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .mini-info {
            padding: 12px;
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .mini-title {
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 5px;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .mini-status {
            font-size: 0.75rem;
            margin-bottom: 3px;
        }
        .status-avail { color: #4cd137; }
        .status-unavail { color: #ff4757; }
        .mini-price {
            font-size: 0.85rem;
            font-weight: 700;
            color: rgba(255,255,255,0.9);
        }

        /* Modal Overlay (Acrylic Blur) */
        .game-modal-overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(25px); /* Strong blur */
            -webkit-backdrop-filter: blur(25px);
            z-index: 2000;
            display: none; /* Hidden by default */
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .game-modal-overlay.active {
            display: flex;
            opacity: 1;
        }
        .modal-card {
            background: rgba(20, 20, 20, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            width: 90%;
            max-width: 1000px;
            max-height: 90vh;
            display: flex;
            flex-direction: row; /* Horizontal layout */
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            position: relative;
        }
        @media (max-width: 992px) {
            .modal-card { flex-direction: column; overflow-y: auto; }
        }

        .modal-poster-container {
            width: 40%;
            position: relative;
            background: black;
        }
        @media (max-width: 992px) { .modal-poster-container { width: 100%; height: 300px; } }

        .modal-poster {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .modal-info {
            width: 60%;
            padding: 40px;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }
        @media (max-width: 992px) { .modal-info { width: 100%; padding: 25px; } }

        .modal-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 20px;
            text-shadow: 0 0 10px rgba(0,0,0,0.5);
        }
        .modal-desc {
            font-size: 1rem;
            line-height: 1.7;
            color: rgba(255,255,255,0.85);
            font-weight: 300;
            margin-bottom: 30px;
        }
        .modal-desc p { margin-bottom: 15px; }

        .modal-price {
            font-size: 2rem;
            font-weight: 700;
            color: #4cd137;
            margin-top: auto;
            text-align: right;
        }

        .close-modal-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.5);
            border: none;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-size: 1.2rem;
            cursor: pointer;
            transition: 0.2s;
            z-index: 10;
        }
        .close-modal-btn:hover { background: rgba(255,255,255,0.2); }

        /* Upload Button in Modal */
        .upload-btn-modal {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: 0.2s;
        }
        .upload-btn-modal:hover { background: var(--brand-color); }

        /* Footer Styling */
        footer.acrylic-footer {
            margin-top: 80px;
            color: rgba(255,255,255,0.6);
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding: 40px 0;
            text-align: center;
        }
        .footer-logo {
            font-weight: 800;
            font-size: 1.5rem;
            color: white;
            margin-bottom: 10px;
        }
        .footer-logo span {
            color: #00f3ff;
            text-shadow: 0 0 5px #00f3ff;
            font-style: italic;
        }
        .social-icons {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        .social-icon {
            color: rgba(255,255,255,0.6);
            font-size: 1.5rem;
            transition: 0.3s;
            cursor: pointer;
        }
        .social-icon:hover { color: white; transform: scale(1.1); text-shadow: 0 0 10px white; }

        /* Language Toggle Classes */
        .lang-id, .lang-en { display: none; }
        body.lang-mode-id div.lang-id, body.lang-mode-id span.lang-id { display: block; }
        body.lang-mode-id span.lang-id { display: inline; }
        body.lang-mode-en div.lang-en, body.lang-mode-en span.lang-en { display: block; }
        body.lang-mode-en span.lang-en { display: inline; }
    </style>
</head>
<body class="lang-mode-id">
    <div class="acrylic-overlay-page"></div>

    {{ navbar|safe }}

    <div class="container container-xl py-5">

        <!-- HERO SECTION -->
        <div class="hero-section text-center mb-5">
            <h1 class="hero-title">Temukan Petualangan <br> <span class="text-blue-neon">Baru Anda</span></h1>
            <p class="hero-subtitle mt-3">Jelajahi ribuan game dari berbagai genre. Petualangan tanpa batas menanti!</p>
            <button class="btn btn-cyan-neon mt-4 px-5 py-2 rounded-pill" onclick="scrollToPopular()">Mulai Jelajah</button>
        </div>

        <!-- POPULAR HEADER -->
        <div class="section-header mb-4" id="popular-games">
            <h2 class="fw-bold">Game Populer <span class="text-blue-neon" style="border-bottom: 3px solid #00f3ff;">Saat Ini</span></h2>
        </div>

        <!-- GRID -->
        <div class="games-grid">
            {% for game in games %}
            <div class="mini-card" onclick="openModal('{{ game.id }}')">
                {% if game_images[game.id] != 'default_game.jpg' %}
                    <img src="/uploads/{{ game_images[game.id] }}" class="mini-poster" alt="{{ game.title }}">
                {% else %}
                    <div class="mini-poster" style="background: #1e1e1e; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.1); font-size:2rem;"><i class="fas fa-gamepad"></i></div>
                {% endif %}
                <div class="mini-info">
                    <div class="mini-title">{{ game.title }}</div>
                    <div class="mini-status">
                        {% if game.available %}
                            <span class="status-avail"><i class="fas fa-check-circle me-1"></i> <span class="lang-id">Tersedia</span><span class="lang-en">Available</span></span>
                        {% else %}
                            <span class="status-unavail"><i class="fas fa-times-circle me-1"></i> <span class="lang-id">Tidak Tersedia</span><span class="lang-en">Unavailable</span></span>
                        {% endif %}
                    </div>
                    <div class="mini-price">{{ game.price }}</div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- NEW RELEASES SECTION -->
        <div class="section-header mt-5 mb-4">
            <h2 class="fw-bold">Rilisan <span class="text-blue-neon" style="border-bottom: 3px solid #00f3ff;">Terbaru</span></h2>
        </div>
        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-4 g-4 mb-5">
            <!-- Placeholder New Release 1 -->
            <div class="col">
                <div class="mini-card h-100">
                     <div class="mini-poster" style="background: linear-gradient(45deg, #1e1e1e, #2d2d2d); display:flex; align-items:center; justify-content:center; color:white; font-size:1.5rem;">GTA VI</div>
                     <div class="mini-info">
                        <div class="mini-title">Grand Theft Auto VI</div>
                        <div class="mini-status"><span class="text-info"><i class="fas fa-clock me-1"></i> Pre-Order</span></div>
                        <div class="mini-price">Rp 1.150.000</div>
                     </div>
                </div>
            </div>
            <!-- Placeholder New Release 2 -->
             <div class="col">
                <div class="mini-card h-100">
                     <div class="mini-poster" style="background: linear-gradient(45deg, #1e1e1e, #2d2d2d); display:flex; align-items:center; justify-content:center; color:white; font-size:1.5rem;">Witcher 4</div>
                     <div class="mini-info">
                        <div class="mini-title">The Witcher: Polaris</div>
                        <div class="mini-status"><span class="text-info"><i class="fas fa-clock me-1"></i> Coming Soon</span></div>
                        <div class="mini-price">Rp 899.000</div>
                     </div>
                </div>
            </div>
        </div>

        <footer class="acrylic-footer">
            <div class="container">
                <div class="footer-logo">Game<span>Verse</span></div>
                <p>&copy; 2026 GameVerse. All rights reserved.</p>
                <div class="social-icons">
                    <i class="fab fa-facebook social-icon"></i>
                    <i class="fab fa-twitter social-icon"></i>
                    <i class="fab fa-instagram social-icon"></i>
                    <a href="https://wa.me/6281241865310" target="_blank" style="text-decoration:none;"><i class="fab fa-whatsapp social-icon"></i></a>
                    <a href="https://maps.app.goo.gl/BsCQBk3NYK3ARL6p7" target="_blank" style="text-decoration:none;"><i class="fas fa-map-marker-alt social-icon"></i></a>
                </div>
            </div>
        </footer>
    </div>

    <!-- Hidden Modals Structure -->
    <div id="modal-overlay" class="game-modal-overlay">
        <div class="modal-card" onclick="event.stopPropagation()">
            <button class="close-modal-btn" onclick="closeModal()"><i class="fas fa-times"></i></button>

            <div class="modal-poster-container">
                <img id="m-poster" src="" class="modal-poster">
                <!-- Upload Form hidden overlay -->
                <form id="m-upload-form" method="post" enctype="multipart/form-data" style="display:none">
                    <input type="file" name="game_image" id="m-file-input" onchange="this.form.submit()" accept="image/*">
                </form>
                <div class="upload-btn-modal" onclick="triggerUpload()">
                    <i class="fas fa-camera me-1"></i> Change Cover
                </div>
            </div>

            <div class="modal-info">
                <h2 class="modal-title" id="m-title">Title</h2>
                <div class="modal-desc">
                    <div class="lang-id" id="m-desc-id"></div>
                    <div class="lang-en" id="m-desc-en"></div>
                </div>
                <div class="modal-price" id="m-price">Price</div>
            </div>
        </div>
    </div>

    <!-- Data dump for JS -->
    <script>
        const gamesData = {{ games|tojson }};
        const gameImages = {{ game_images|tojson }};
        let currentGameId = null;

        function openModal(id) {
            currentGameId = id;
            const game = gamesData.find(g => g.id === id);
            const imgPath = gameImages[id] !== 'default_game.jpg' ? '/uploads/' + gameImages[id] : '';

            // Populate data
            document.getElementById('m-title').innerText = game.title;
            document.getElementById('m-desc-id').innerHTML = formatDesc(game.desc_id);
            document.getElementById('m-desc-en').innerHTML = formatDesc(game.desc_en);
            document.getElementById('m-price').innerText = game.price;

            const posterImg = document.getElementById('m-poster');
            if (imgPath) {
                posterImg.src = imgPath;
                posterImg.style.display = 'block';
            } else {
                posterImg.src = ''; // Or placeholder
                posterImg.style.background = '#1e1e1e';
            }

            // Setup Upload Form
            const form = document.getElementById('m-upload-form');
            form.action = '/list-game-playstation/upload/' + id;

            // Show Overlay
            const overlay = document.getElementById('modal-overlay');
            overlay.classList.add('active');

            // Re-apply current language display
            toggleLanguage(true);
        }

        function closeModal() {
            const overlay = document.getElementById('modal-overlay');
            overlay.classList.remove('active');
        }

        // Smooth scroll function
        function scrollToPopular() {
            const el = document.getElementById('popular-games');
            if(el) {
                el.scrollIntoView({ behavior: 'smooth' });
            }
        }

        // Close on click outside
        document.getElementById('modal-overlay').addEventListener('click', closeModal);

        function triggerUpload() {
            document.getElementById('m-file-input').click();
        }

        function formatDesc(text) {
            // Convert newlines to <p>
            return text.split('\\n\\n').map(p => `<p>${p}</p>`).join('');
        }

        // Theme and Lang logic
        function setTheme(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        }
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
        })();

        // Language Toggle
        function toggleLanguage(retainState = false) {
            const body = document.body;
            const btn = document.getElementById('lang-btn');

            if (retainState) {
                 // Just ensure UI matches current class
                 btn.textContent = body.classList.contains('lang-mode-id') ? 'ID' : 'EN';
                 return;
            }

            if (body.classList.contains('lang-mode-id')) {
                body.classList.remove('lang-mode-id');
                body.classList.add('lang-mode-en');
                btn.textContent = 'EN';
            } else {
                body.classList.remove('lang-mode-en');
                body.classList.add('lang-mode-id');
                btn.textContent = 'ID';
            }
        }
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

HTML_WALLPAPER = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wallpaper Blur Akrilik | ilikepdf</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    {{ styles|safe }}
    <style>
        body, html {
            height: 100%;
            margin: 0;
            overflow: hidden; /* Prevent scrolling if possible */
        }
        .wallpaper-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('/uploads/{{ bg_image }}');
            background-size: cover;
            background-position: center;
            z-index: -2;
        }
        .acrylic-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            /* Config: [dark] r=0 g=0 b=0 a=120 -> rgba(0, 0, 0, 0.47) */
            background-color: rgba(0, 0, 0, 0.47);
            backdrop-filter: blur(20px) saturate(125%);
            -webkit-backdrop-filter: blur(20px) saturate(125%);
            z-index: -1;
        }
        .content-wrapper {
            position: relative;
            z-index: 1;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .center-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
            width: 100%;
        }
        .upload-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            max-width: 600px;
            width: 90%;
            margin-bottom: 20px;
        }
        .upload-card h2 {
            color: white !important;
        }
        .controls-container {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
            margin-bottom: 30px;
        }
        .acrylic-btn {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            transition: 0.3s;
            text-decoration: none;
            cursor: pointer;
            display: inline-block;
            white-space: nowrap;
        }
        .acrylic-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            color: white;
        }
        .audio-player {
            position: fixed;
            bottom: 50px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 30px;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            z-index: 100;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
            width: 90%;
            max-width: 800px;
        }
        .player-row-top {
            width: 100%;
            padding: 0 5px;
        }
        .player-row-bottom {
            display: grid;
            grid-template-columns: 1fr auto 1fr; /* Left, Center (Play), Right */
            align-items: center;
            width: 100%;
        }
        .player-left {
            display: flex;
            align-items: center;
            gap: 15px;
            justify-content: flex-start;
        }
        .player-center {
            display: flex;
            align-items: center;
            gap: 20px;
            justify-content: center;
        }
        .player-right {
            display: flex;
            align-items: center;
            gap: 15px;
            justify-content: flex-end;
        }
        
        .player-btn {
            background: transparent;
            border: none;
            color: rgba(255,255,255,0.8);
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 1rem;
        }
        .player-btn:hover {
            color: white;
            transform: scale(1.1);
        }
        .player-btn.active {
            color: var(--brand-color);
        }
        .play-btn-large {
            width: 50px;
            height: 50px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            font-size: 1.4rem;
            color: white;
        }
        .play-btn-large:hover {
            background: white;
            color: black;
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(255,255,255,0.3);
        }

        /* Range Slider */
        input[type=range] {
            -webkit-appearance: none;
            width: 100%;
            background: transparent;
        }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 14px;
            width: 14px;
            border-radius: 50%;
            background: white;
            cursor: pointer;
            margin-top: -5px;
            box-shadow: 0 0 5px rgba(0,0,0,0.3);
        }
        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: rgba(255,255,255,0.2);
            border-radius: 2px;
        }
        
        .time-display, .db-display {
            font-size: 0.85rem;
            color: rgba(255,255,255,0.7);
            font-variant-numeric: tabular-nums;
            min-width: 40px;
        }
        
        #visualizer {
            position: absolute;
            top: 50%;
            left: 0;
            width: 100%;
            height: 300px;
            transform: translateY(-50%);
            z-index: 0;
            pointer-events: none;
            filter: blur(2px); /* Soft aesthetic blur */
        }
        
        /* Playlist Panel */
        .playlist-panel {
            position: fixed;
            bottom: 160px; /* Above player */
            right: 50px;
            width: 300px;
            max-height: 400px;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 15px;
            z-index: 101;
            display: none; /* Hidden by default */
            overflow-y: auto;
            color: white;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        .playlist-header {
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 10px;
            margin-bottom: 10px;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
        }
        .playlist-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            border-radius: 5px;
            cursor: pointer;
            transition: 0.2s;
            font-size: 0.9rem;
        }
        .playlist-item:hover {
            background: rgba(255,255,255,0.1);
        }
        .playlist-item.active {
            background: rgba(229, 50, 45, 0.2);
            color: var(--brand-color);
        }
        .playlist-actions {
            display: flex;
            gap: 5px;
        }
        .action-btn {
            background: transparent;
            border: none;
            color: rgba(255,255,255,0.5);
            cursor: pointer;
            font-size: 0.8rem;
        }
        .action-btn:hover { color: white; }
        .action-btn.delete:hover { color: #ff4444; }
    </style>
</head>
<body>
    <div class="wallpaper-bg"></div>
    <div class="acrylic-overlay"></div>

    <div class="content-wrapper">
        {{ navbar|safe }}
        
        <div class="center-content">
            <div class="controls-container">
                <!-- Wallpaper Upload -->
                <form action="/wallpaper-blur/upload" method="post" enctype="multipart/form-data" id="form-wall">
                    <input type="file" name="background" id="file-wall" hidden onchange="document.getElementById('form-wall').submit()" accept="image/*">
                    <button type="button" class="acrylic-btn" onclick="document.getElementById('file-wall').click()">
                        <i class="fas fa-image me-2"></i> Set Wallpaper
                    </button>
                </form>

                <!-- Audio Upload -->
                <form action="/wallpaper-blur/upload-audio" method="post" enctype="multipart/form-data" id="form-audio">
                    <input type="file" name="audio" id="file-audio" hidden onchange="document.getElementById('form-audio').submit()" accept="audio/*">
                    <button type="button" class="acrylic-btn" onclick="document.getElementById('file-audio').click()">
                        <i class="fas fa-music me-2"></i> Set Audio
                    </button>
                </form>
            </div>
            
            {% if audio_file %}
            <!-- Visualizer Overlay -->
            <canvas id="visualizer"></canvas>

            <div class="audio-player">
                <audio id="main-audio" crossorigin="anonymous">
                    <source src="/uploads/{{ audio_file }}" id="audio-source">
                </audio>
                
                <!-- Top Row: Progress -->
                <div class="player-row-top">
                    <input type="range" id="seek-slider" min="0" max="100" value="0">
                </div>
                
                <!-- Bottom Row: Controls -->
                <div class="player-row-bottom">
                    <!-- Left Section: Time, Shuffle, Repeat -->
                    <div class="player-left">
                        <span class="time-display" id="time-display">00:00</span>
                        <button class="player-btn" onclick="toggleShuffle()" title="Shuffle" id="btn-shuffle"><i class="fas fa-random"></i></button>
                        <button class="player-btn" onclick="toggleRepeat()" title="Repeat" id="btn-repeat"><i class="fas fa-redo"></i></button>
                    </div>
                    
                    <!-- Center Section: Stop, Prev, PLAY, Next -->
                    <div class="player-center">
                        <button class="player-btn" onclick="stopAudio()" title="Stop"><i class="fas fa-stop"></i></button>
                        <button class="player-btn" onclick="skip(-5)"><i class="fas fa-backward"></i></button>
                        <button class="player-btn play-btn-large" onclick="togglePlay()"><i class="fas fa-play" id="play-icon"></i></button>
                        <button class="player-btn" onclick="skip(5)"><i class="fas fa-forward"></i></button>
                    </div>
                    
                    <!-- Right Section: Volume, Playlist -->
                    <div class="player-right">
                        <i class="fas fa-volume-up" id="vol-icon" style="color:rgba(255,255,255,0.7)"></i>
                        <div style="width: 80px;">
                            <input type="range" id="vol-slider" min="0" max="1" step="0.01" value="1">
                        </div>
                        <span class="db-display" id="db-display">0 dB</span>
                        <button class="player-btn" onclick="togglePlaylist()" title="Playlist" id="btn-playlist"><i class="fas fa-list"></i></button>
                    </div>
                </div>
            </div>

            <!-- Playlist Modal -->
            <div class="playlist-panel" id="playlist-panel">
                <div class="playlist-header">
                    <span>Playlist</span>
                    <i class="fas fa-times" onclick="togglePlaylist()" style="cursor:pointer"></i>
                </div>
                <div id="playlist-items">
                    <!-- Items injected by JS -->
                </div>
            </div>

            <form id="rename-form" action="/wallpaper-blur/rename-audio" method="post" style="display:none">
                <input type="hidden" name="old_name" id="rename-old">
                <input type="hidden" name="new_name" id="rename-new">
            </form>

            <script>
                const audio = document.getElementById('main-audio');
                const sourceEl = document.getElementById('audio-source');
                const playIcon = document.getElementById('play-icon');
                const seekSlider = document.getElementById('seek-slider');
                const timeDisplay = document.getElementById('time-display');
                const volSlider = document.getElementById('vol-slider');
                const dbDisplay = document.getElementById('db-display');
                const btnShuffle = document.getElementById('btn-shuffle');
                const btnRepeat = document.getElementById('btn-repeat');
                const playlistPanel = document.getElementById('playlist-panel');
                
                // Audio List logic
                let playlist = {{ audio_files|tojson }};
                let currentFile = "{{ audio_file }}";
                let isShuffle = false;
                let isRepeat = false;

                // --- VISUALIZER ---
                const canvas = document.getElementById('visualizer');
                const ctx = canvas.getContext('2d');
                let audioCtx, analyser, source;
                let initialized = false;

                function resizeCanvas() {
                    canvas.width = window.innerWidth;
                    canvas.height = 300;
                }
                window.addEventListener('resize', resizeCanvas);
                resizeCanvas();

                function initAudio() {
                    if (!initialized) {
                        initialized = true;
                        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        analyser = audioCtx.createAnalyser();
                        source = audioCtx.createMediaElementSource(audio);
                        source.connect(analyser);
                        analyser.connect(audioCtx.destination);
                        analyser.fftSize = 2048;
                        drawVisualizer();
                    }
                    if (audioCtx && audioCtx.state === 'suspended') {
                        audioCtx.resume();
                    }
                }

                function drawVisualizer() {
                    requestAnimationFrame(drawVisualizer);
                    const bufferLength = analyser.frequencyBinCount;
                    const dataArray = new Uint8Array(bufferLength);
                    analyser.getByteTimeDomainData(dataArray);
                    
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.lineWidth = 3;
                    ctx.strokeStyle = 'rgba(220, 220, 220, 0.6)';
                    ctx.shadowBlur = 10;
                    ctx.shadowColor = "white";
                    
                    ctx.beginPath();
                    const sliceWidth = canvas.width * 1.0 / bufferLength;
                    let x = 0;
                    
                    for(let i = 0; i < bufferLength; i++) {
                        const v = dataArray[i] / 128.0;
                        const y = v * canvas.height / 2;
                        if(i === 0) ctx.moveTo(x, y);
                        else ctx.lineTo(x, y);
                        x += sliceWidth;
                    }
                    ctx.lineTo(canvas.width, canvas.height/2);
                    ctx.stroke();
                }

                // --- PLAYER LOGIC ---
                function togglePlay() {
                    initAudio();
                    if (audio.paused) {
                        audio.play();
                        playIcon.classList.remove('fa-play');
                        playIcon.classList.add('fa-pause');
                    } else {
                        audio.pause();
                        playIcon.classList.add('fa-play');
                        playIcon.classList.remove('fa-pause');
                    }
                }

                function stopAudio() {
                    audio.pause();
                    audio.currentTime = 0;
                    playIcon.classList.add('fa-play');
                    playIcon.classList.remove('fa-pause');
                }

                function skip(seconds) {
                    audio.currentTime += seconds;
                }

                function toggleRepeat() {
                    isRepeat = !isRepeat;
                    btnRepeat.classList.toggle('active', isRepeat);
                    audio.loop = isRepeat;
                }

                function toggleShuffle() {
                    isShuffle = !isShuffle;
                    btnShuffle.classList.toggle('active', isShuffle);
                }

                function loadTrack(filename) {
                    currentFile = filename;
                    sourceEl.src = "/uploads/" + filename;
                    audio.load();
                    togglePlay();
                    renderPlaylist(); // Update active state
                }

                // --- PLAYLIST LOGIC ---
                function togglePlaylist() {
                    if(playlistPanel.style.display === 'block') {
                        playlistPanel.style.display = 'none';
                    } else {
                        playlistPanel.style.display = 'block';
                        renderPlaylist();
                    }
                }

                function renderPlaylist() {
                    const container = document.getElementById('playlist-items');
                    container.innerHTML = '';
                    
                    if(playlist.length === 0) {
                        container.innerHTML = '<div style="text-align:center; padding:10px; color:rgba(255,255,255,0.5)">No audio files</div>';
                        return;
                    }

                    playlist.forEach(file => {
                        const div = document.createElement('div');
                        div.className = `playlist-item ${file === currentFile ? 'active' : ''}`;
                        div.innerHTML = `
                            <span onclick="loadTrack('${file}')" style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${file}</span>
                            <div class="playlist-actions">
                                <button class="action-btn" onclick="renameTrack('${file}')"><i class="fas fa-pencil-alt"></i></button>
                                <button class="action-btn delete" onclick="deleteTrack('${file}')"><i class="fas fa-trash"></i></button>
                            </div>
                        `;
                        container.appendChild(div);
                    });
                }

                function deleteTrack(filename) {
                    if(confirm('Delete ' + filename + '?')) {
                        window.location.href = `/wallpaper-blur/delete-audio/${filename}`;
                    }
                }

                function renameTrack(filename) {
                    const newName = prompt('Rename ' + filename + ' to:', filename);
                    if(newName && newName !== filename) {
                        document.getElementById('rename-old').value = filename;
                        document.getElementById('rename-new').value = newName;
                        document.getElementById('rename-form').submit();
                    }
                }

                // Auto next track
                audio.addEventListener('ended', () => {
                    if (!isRepeat && playlist.length > 0) {
                        if (isShuffle) {
                            let nextIndex = Math.floor(Math.random() * playlist.length);
                            loadTrack(playlist[nextIndex]);
                        } else {
                            let idx = playlist.indexOf(currentFile);
                            let nextIdx = (idx + 1) % playlist.length;
                            loadTrack(playlist[nextIdx]);
                        }
                    }
                });

                // Update Progress & Time
                audio.addEventListener('timeupdate', () => {
                    if(audio.duration) {
                        const val = (audio.currentTime / audio.duration) * 100;
                        seekSlider.value = val;
                        
                        let mins = Math.floor(audio.currentTime / 60);
                        let secs = Math.floor(audio.currentTime % 60);
                        if(secs < 10) secs = '0' + secs;
                        if(mins < 10) mins = '0' + mins;
                        timeDisplay.textContent = `${mins}:${secs}`;
                    }
                });

                seekSlider.addEventListener('input', () => {
                    if(audio.duration) {
                        const seekTime = (seekSlider.value / 100) * audio.duration;
                        audio.currentTime = seekTime;
                    }
                });

                // Volume & Decibels
                volSlider.addEventListener('input', (e) => {
                    const val = parseFloat(e.target.value);
                    audio.volume = val;
                    
                    // Convert linear 0-1 to approx dB
                    // Typically 0 is -inf, 1 is 0dB. 
                    // Formula: 20 * log10(val)
                    let db = -Infinity;
                    if(val > 0) {
                        db = 20 * Math.log10(val);
                    }
                    
                    // Clamp display
                    if(db < -60) dbDisplay.innerText = "Mute";
                    else dbDisplay.innerText = Math.round(db) + " dB";
                });
            </script>
            {% endif %}
        </div>
        
        <footer style="background: transparent; border: none; color: rgba(255,255,255,0.7);">
            <div class="container">
                <p>&copy; 2025 ourtools - Python 3.13.5 Powered. "We Making The Time"</p>
            </div>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Minimal theme logic for navbar compatibility
        function setTheme(theme) {
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        }
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
        })();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
