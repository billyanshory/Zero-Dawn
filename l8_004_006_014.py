import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

# 1. Add OperationalError to imports
content = content.replace("from sqlalchemy.exc import IntegrityError", "from sqlalchemy.exc import IntegrityError, OperationalError")

# We want to replace `except Exception as e:` inside database mutation blocks with:
# except IntegrityError:
#     db.session.rollback()
#     ... return 409 ...
# except OperationalError:
#     db.session.rollback()
#     ... return 503 ...
# except Exception as e:
#     ... original handling ...
#
# But the original generic excepts have different return types (jsonify vs flash).
# We need to detect if the route uses jsonify or flash.
# Wait, the instruction says:
# replace the single broad `except Exception:` with a layered pattern: first an `except IntegrityError:` clause that calls `db.session.rollback()` and returns a four-hundred-nine conflict response with a user-friendly Indonesian message describing the specific constraint violated (for example, "Data duplikat terdeteksi. Silakan periksa kembali." for a unique violation), then an `except OperationalError:` clause that calls `db.session.rollback()` and returns a five-hundred-three response with "Koneksi database terganggu. Silakan coba lagi.", then the existing broad `except Exception:` clause preserved.

def fix_excepts(text):
    lines = text.split('\n')
    i = 0
    in_db_transaction = False

    while i < len(lines):
        line = lines[i]

        # We need to track if we're in a function
        # And if we saw a db.session.commit()
        # The easiest is to just look for `except Exception`
        # and check if the block before it has db.session.commit()
        # But maybe it's easier to just find `except Exception` blocks and analyze them.

        if line.strip().startswith("except Exception"):
            # Let's see if there's a rollback inside it, which means it was a DB mutation
            has_rollback = False
            is_json = False
            for j in range(i+1, min(i+10, len(lines))):
                if "db.session.rollback()" in lines[j]:
                    has_rollback = True
                if "jsonify(" in lines[j]:
                    is_json = True
                if lines[j].strip().startswith("except ") or lines[j].strip() == "":
                    # next block
                    pass

            if has_rollback:
                # Let's insert the layered exceptions right before this except Exception block
                indent = line[:len(line) - len(line.lstrip())]

                integrity_str = "Data duplikat terdeteksi. Silakan periksa kembali."
                operational_str = "Koneksi database terganggu. Silakan coba lagi."

                if is_json:
                    integrity_block = f"""{indent}except IntegrityError:
{indent}    db.session.rollback()
{indent}    return jsonify({{'error': '{integrity_str}'}}), 409
{indent}except OperationalError:
{indent}    db.session.rollback()
{indent}    return jsonify({{'error': '{operational_str}'}}), 503"""
                else:
                    # Flash + redirect fallback
                    # Wait, if we return redirect, we need to know where.
                    # Usually we can just `return redirect(request.referrer or url_for('index'))`
                    # or better: we just flash, and then let it fall through? No, we must return.
                    # Actually, if we just look at what the original except block returns, we can copy its return.
                    return_line = None
                    for j in range(i+1, min(i+15, len(lines))):
                        if lines[j].strip().startswith("return "):
                            return_line = lines[j].strip()
                            break
                    if not return_line:
                        return_line = "return redirect(request.referrer or url_for('index'))"

                    integrity_block = f"""{indent}except IntegrityError:
{indent}    db.session.rollback()
{indent}    flash("{integrity_str}", "error")
{indent}    {return_line}
{indent}except OperationalError:
{indent}    db.session.rollback()
{indent}    flash("{operational_str}", "error")
{indent}    {return_line}"""

                lines.insert(i, integrity_block)
                i += 1 # because we inserted a big block (as a single string, so 1 element in lines list)

        i += 1

    return "\n".join(lines)

content = fix_excepts(content)

with open(fname, 'w') as f:
    f.write(content)
