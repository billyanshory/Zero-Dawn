import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# AGAIN it was reverted due to some checkout/patch overlap! Let's just fix it and teardown.

old_init = """class BrowserPool:
    def __init__(self, size):
        self.size = size
        self.queue = asyncio.Queue()
        self.playwright = None
        self.browsers = []

    async def initialize(self):"""

new_init = """class BrowserPool:
    def __init__(self, size):
        self.size = size
        self.queue = asyncio.Queue()
        self.playwright = None
        self.browsers = []
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def ensure_initialized(self):
        async with self._init_lock:
            if not self._initialized:
                await self._do_initialize()
                self._initialized = True

    async def _do_initialize(self):"""

content = content.replace(old_init, new_init)

old_teardown = """@app.after_server_stop
async def teardown_app(app, loop):
    await browser_pool.close_all()"""

new_teardown = """@app.after_server_stop
async def teardown_app(app, loop):
    if getattr(browser_pool, '_initialized', False):
        await browser_pool.close_all()"""

if old_teardown in content:
    content = content.replace(old_teardown, new_teardown)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
