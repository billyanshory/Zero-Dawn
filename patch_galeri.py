import re

filepath = "sekolah-luar-biasa-55 ( idcloudhost - Layer of Quality Cyber Security - Third Effort ).py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Route update for galeri
search_galeri_route = """@app.route('/galeri')
def galeri_karya():
    karya = GaleriKarya.query.order_by(GaleriKarya.created_at.desc()).all()"""

replace_galeri_route = """@app.route('/galeri')
def galeri_karya():
    page = request.args.get('page', 1, type=int)
    pagination = GaleriKarya.query.order_by(GaleriKarya.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    karya = pagination.items"""

if search_galeri_route in content:
    content = content.replace(search_galeri_route, replace_galeri_route)

# Add pagination controls to galeri html
search_galeri_html = """            {% if not karya %}
            <div class="text-center py-16">
                <div class="w-20 h-20 mx-auto bg-gray-50 text-gray-300 rounded-full flex items-center justify-center text-3xl mb-4"><i class="fas fa-images"></i></div>
                <p class="text-gray-500 font-medium">Belum ada karya yang diunggah.</p>
            </div>
            {% endif %}"""

replace_galeri_html = """            {% if not karya %}
            <div class="text-center py-16">
                <div class="w-20 h-20 mx-auto bg-gray-50 text-gray-300 rounded-full flex items-center justify-center text-3xl mb-4"><i class="fas fa-images"></i></div>
                <p class="text-gray-500 font-medium">Belum ada karya yang diunggah.</p>
            </div>
            {% else %}
            <div class="flex justify-center items-center mt-10 gap-2">
                {% if pagination.has_prev %}
                <a href="{{ url_for('galeri_karya', page=pagination.prev_num) }}" class="bg-white border border-rose-200 text-rose-500 px-4 py-2 rounded-xl font-bold hover:bg-rose-50 transition"><i class="fas fa-chevron-left mr-1"></i> Prev</a>
                {% endif %}
                <span class="text-gray-500 text-sm font-medium px-4">Halaman {{ pagination.page }} dari {{ pagination.pages }}</span>
                {% if pagination.has_next %}
                <a href="{{ url_for('galeri_karya', page=pagination.next_num) }}" class="bg-white border border-rose-200 text-rose-500 px-4 py-2 rounded-xl font-bold hover:bg-rose-50 transition">Next <i class="fas fa-chevron-right ml-1"></i></a>
                {% endif %}
            </div>
            {% endif %}"""

if search_galeri_html in content:
    content = content.replace(search_galeri_html, replace_galeri_html)

# Add pagination param
content = content.replace("render_template_string(content, is_admin=session.get('is_admin', False), karya=karya)",
                          "render_template_string(content, is_admin=session.get('is_admin', False), karya=karya, pagination=pagination)")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
