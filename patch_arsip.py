import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Route update for arsip
search_arsip_route = """@app.route('/arsip-portofolio')
def arsip_portofolio():
    portfolios = StudentPortfolio.query.order_by(StudentPortfolio.created_at.desc()).all()"""

replace_arsip_route = """@app.route('/arsip-portofolio')
def arsip_portofolio():
    page = request.args.get('page', 1, type=int)
    pagination = StudentPortfolio.query.order_by(StudentPortfolio.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    portfolios = pagination.items"""

if search_arsip_route in content:
    content = content.replace(search_arsip_route, replace_arsip_route)

# Add pagination controls to arsip html
search_arsip_html = """            {% if not portfolios %}
            <div class="text-center py-20 bg-white rounded-[3rem] shadow-sm border border-rose-100">
                <div class="w-24 h-24 mx-auto bg-rose-50 text-rose-300 rounded-full flex items-center justify-center text-4xl mb-4"><i class="fas fa-folder-open"></i></div>
                <p class="text-gray-500 font-medium text-lg mb-1">Brankas Masih Kosong</p>
                <p class="text-sm text-gray-400">Belum ada portofolio yang diunggah oleh guru.</p>
            </div>
            {% endif %}"""

replace_arsip_html = """            {% if not portfolios %}
            <div class="text-center py-20 bg-white rounded-[3rem] shadow-sm border border-rose-100">
                <div class="w-24 h-24 mx-auto bg-rose-50 text-rose-300 rounded-full flex items-center justify-center text-4xl mb-4"><i class="fas fa-folder-open"></i></div>
                <p class="text-gray-500 font-medium text-lg mb-1">Brankas Masih Kosong</p>
                <p class="text-sm text-gray-400">Belum ada portofolio yang diunggah oleh guru.</p>
            </div>
            {% else %}
            <div class="flex justify-center items-center mt-10 gap-2">
                {% if pagination.has_prev %}
                <a href="{{ url_for('arsip_portofolio', page=pagination.prev_num) }}" class="bg-white border border-rose-200 text-rose-500 px-4 py-2 rounded-xl font-bold hover:bg-rose-50 transition"><i class="fas fa-chevron-left mr-1"></i> Prev</a>
                {% endif %}
                <span class="text-gray-500 text-sm font-medium px-4">Halaman {{ pagination.page }} dari {{ pagination.pages }}</span>
                {% if pagination.has_next %}
                <a href="{{ url_for('arsip_portofolio', page=pagination.next_num) }}" class="bg-white border border-rose-200 text-rose-500 px-4 py-2 rounded-xl font-bold hover:bg-rose-50 transition">Next <i class="fas fa-chevron-right ml-1"></i></a>
                {% endif %}
            </div>
            {% endif %}"""

if search_arsip_html in content:
    content = content.replace(search_arsip_html, replace_arsip_html)

# Add pagination param
content = content.replace("render_template_string(content, is_admin=session.get('is_admin', False), portfolios=portfolios)",
                          "render_template_string(content, is_admin=session.get('is_admin', False), portfolios=portfolios, pagination=pagination)")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
