import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

old_index = """@app.get("/")
async def index_page(request: Request):
    csrf_token = secrets.token_hex(32)

    response_obj = response.html("")
    response_obj.cookies["csrf_token"] = csrf_token
    response_obj.cookies["csrf_token"]["httponly"] = True
    response_obj.cookies["csrf_token"]["samesite"] = "Strict"

    async with get_db_session() as session:
        try:
            result = await session.execute(
                select(ScanLog).where(ScanLog.scan_status == ScanStatus.COMPLETED).order_by(desc(ScanLog.created_at)).limit(20)
            )
            history = result.scalars().all()
        except Exception as e:
            logger.error("Failed to fetch history for index", exc_info=True)
            history = []

    template = jinja_env.from_string(MAIN_PAGE_TEMPLATE)
    html_content = template.render(history=history, csrf_token=csrf_token, nonce=request.ctx.csp_nonce)
    response_obj.body = html_content.encode()
    return response_obj"""

new_index = """@app.get("/")
async def index_page(request: Request):
    csrf_token = secrets.token_hex(32)

    async with get_db_session() as session:
        try:
            result = await session.execute(
                select(ScanLog).where(ScanLog.scan_status == ScanStatus.COMPLETED).order_by(desc(ScanLog.created_at)).limit(20)
            )
            history = result.scalars().all()
        except Exception as e:
            logger.error("Failed to fetch history for index", exc_info=True)
            history = []

    template = jinja_env.from_string(MAIN_PAGE_TEMPLATE)
    html_content = template.render(history=history, csrf_token=csrf_token, nonce=request.ctx.csp_nonce)

    response_obj = response.html(html_content)
    response_obj.cookies["csrf_token"] = csrf_token
    response_obj.cookies["csrf_token"]["httponly"] = True
    # Fix Defect 9: Secure flag and max-age
    response_obj.cookies["csrf_token"]["secure"] = True
    response_obj.cookies["csrf_token"]["samesite"] = "Strict"
    response_obj.cookies["csrf_token"]["max-age"] = 3600

    return response_obj"""

content = content.replace(old_index, new_index)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
