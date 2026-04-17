import re

fname = "sekolah-luar-biasa-83 ( idcloudhost - pengembalian kembali - dashboard guru).py"
with open(fname, 'r') as f:
    content = f.read()

def fix_guards(text):
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip the decorator definition itself, and the inner wrapper which has "if session.get('peran') not in roles:"
        if "session.get('peran') not in" in line and "def require_auth" not in line and "not in roles:" not in line:
            # We also might have line continuation... let's just grab the bracket contents
            match = re.search(r"not in \[(.*?)\]", line)
            if not match:
                # Could be split across lines?
                # Let's check next line
                combined = line + lines[i+1]
                match = re.search(r"not in \[(.*?)\]", combined)
                if not match:
                    print("Still failing on:", line)
                    i += 1
                    continue

            roles_str = match.group(1)

            if "ROLE_ORANG_TUA" in roles_str and "ROLE_GURU" in roles_str and "ROLE_KEPALA_SEKOLAH" in roles_str:
                decorator = "@require_auth(roles=ALL_ROLES)"
            elif "ROLE_GURU" in roles_str and "ROLE_KEPALA_SEKOLAH" in roles_str and "ROLE_ORANG_TUA" not in roles_str:
                decorator = "@require_auth(roles=STAFF_ROLES)"
            elif "ROLE_ORANG_TUA" in roles_str and "ROLE_KEPALA_SEKOLAH" in roles_str and "ROLE_GURU" not in roles_str:
                decorator = "@require_auth(roles={ROLE_ORANG_TUA, ROLE_KEPALA_SEKOLAH})"
            else:
                decorator = f"@require_auth(roles={{{roles_str}}})"

            j = i
            while j >= 0 and not lines[j].strip().startswith("def "):
                j -= 1

            if j >= 0:
                lines.insert(j, " " * (len(lines[j]) - len(lines[j].lstrip())) + decorator)
                i += 1
                j += 1

                base_indent = len(lines[i]) - len(lines[i].lstrip())
                del lines[i]

                while i < len(lines) and (len(lines[i]) - len(lines[i].lstrip()) > base_indent or lines[i].strip() == ""):
                    # Also need to handle cases where there's an 'else' block or similar? No, these guards just return.
                    # Wait, if there's an empty line inside the guard, it will delete it.
                    # This is fine. But if there's a comment?
                    if len(lines[i].strip()) > 0 and len(lines[i]) - len(lines[i].lstrip()) <= base_indent:
                        break
                    del lines[i]

                continue
        i += 1
    return "\n".join(lines)

new_content = fix_guards(content)
with open(fname, 'w') as f:
    f.write(new_content)
