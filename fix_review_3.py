import re

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "r") as f:
    content = f.read()

# Fix error handler for peta admin
err_old = """        app.logger.error(f"Error in admin peta distribusi: {e}")
        return "Internal Server Error", 500"""

err_new = """        app.logger.error(f"Error in admin peta distribusi: {e}")
        return render_template_string(BASE_LAYOUT, styles=STYLES_HTML, active_page='idul-adha', content="<div class='min-h-screen flex items-center justify-center p-4 pt-24 md:pt-28'><div class='bg-white p-8 rounded-3xl shadow-xl max-w-md text-center'><i class='fas fa-exclamation-triangle text-4xl text-red-500 mb-4'></i><h3 class='text-xl font-bold text-gray-800 mb-2'>Kesalahan Sistem</h3><p class='text-gray-600 mb-4'>Data peta distribusi belum dikonfigurasi atau terjadi kesalahan database.</p><a href='/idul-adha' class='inline-block bg-[#1B4332] text-white px-6 py-2 rounded-xl font-bold'>Kembali ke Dashboard</a></div></div>", is_admin=True, settings=get_settings())"""

if "return \"Internal Server Error\", 500" in content:
    content = content.replace(err_old, err_new)
    print("Replaced error handler")

with open("masjid-al-hijrah-64 ( idcloudhost - fixing 4 fitur - Idul Adha Qurban ).py", "w") as f:
    f.write(content)
