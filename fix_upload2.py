import sys

file_path = "sekolah-luar-biasa-72 ( idcloudhost - Ninth Layer of Quality Control - Cyber Security - v.71 - Opus 4.6 Ex. Think. ).py"

with open(file_path, "r") as f:
    content = f.read()

target = """            student_id = request.form.get('student_id')
            if not db.session.get(Siswa, student_id):
                return "Student not found", 404
            port = StudentPortfolio(
                student_id=student_id,
                semester=request.form.get('semester'),
                filename=filename
            )
            db.session.add(port)
            db.session.commit()
        except Exception as e:
            db.session.rollback()

    return redirect(url_for('index'))"""

replacement = """            student_id = request.form.get('student_id')
            try:
                student_id_int = int(student_id)
            except (TypeError, ValueError):
                return "Invalid student ID", 400

            if not db.session.get(Siswa, student_id_int):
                return "Student not found", 404

            port = StudentPortfolio(
                student_id=str(student_id_int),
                semester=validate_str(request.form.get('semester'), 255) or 'Unknown',
                filename=filename
            )
            db.session.add(port)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Portfolio upload failed', exc_info=True)
            from flask import flash
            flash('Gagal mengunggah portfolio. Silakan coba lagi.', 'error')

    return redirect(url_for('index'))"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Target not found")
