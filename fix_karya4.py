import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target2 = """            new_karya = GaleriKarya(image_filename=filename, title=title, student_name=student_name)
            db.session.add(new_karya)
            db.session.commit()
        except Exception as e:
            db.session.rollback()

    return redirect(url_for('galeri_karya'))"""

replacement2 = """            new_karya = GaleriKarya(image_filename=filename, title=title, student_name=student_name)
            db.session.add(new_karya)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Gallery upload failed', exc_info=True)
            from flask import flash
            flash('Gagal mengunggah karya. Silakan coba lagi.', 'error')

    return redirect(url_for('galeri_karya'))"""

if target2 in content:
    content = content.replace(target2, replacement2)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced upload_karya bottom successfully")
else:
    print("Target bottom not found")
