import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

old_cookie_assignment = """    response_obj = response.html(html_content)
    response_obj.cookies["csrf_token"] = csrf_token
    response_obj.cookies["csrf_token"]["httponly"] = True
    # Fix Defect 9: Secure flag and max-age
    response_obj.cookies["csrf_token"]["secure"] = True
    response_obj.cookies["csrf_token"]["samesite"] = "Strict"
    response_obj.cookies["csrf_token"]["max-age"] = 3600

    return response_obj"""

new_cookie_assignment = """    response_obj = response.html(html_content)
    response_obj.add_cookie(
        "csrf_token",
        csrf_token,
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=3600
    )

    return response_obj"""

content = content.replace(old_cookie_assignment, new_cookie_assignment)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
