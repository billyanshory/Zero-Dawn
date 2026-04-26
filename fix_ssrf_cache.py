import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

# Update abort_private_routes signature
old_abort = """async def abort_private_routes(route, request):
    # Try parsing host from url to check private IPs again (post-redirect)
    parsed = urllib.parse.urlparse(request.url)
    hostname = parsed.hostname
    if hostname:
        try:
            # We don't await resolve_and_check_ssrf here directly inside the route handler
            # due to synchronous playwright routing. Just check if it looks like an IP directly.
            ip = ipaddress.ip_address(hostname)
            if is_private_ip(str(ip)):
                await route.abort()
                return
        except ValueError:
            pass # It's a hostname, we rely on the initial resolve
    await route.continue_()"""

new_abort = """async def abort_private_routes(route, request, original_hostname):
    # Try parsing host from url to check private IPs again (post-redirect)
    parsed = urllib.parse.urlparse(request.url)
    hostname = parsed.hostname
    if hostname:
        if hostname != original_hostname:
            await route.abort()
            return

        try:
            # We don't await resolve_and_check_ssrf here directly inside the route handler
            # due to synchronous playwright routing. Just check if it looks like an IP directly.
            ip = ipaddress.ip_address(hostname)
            if is_private_ip(str(ip)):
                await route.abort()
                return
        except ValueError:
            pass # It's a hostname, we rely on the initial resolve
    await route.continue_()"""

content = content.replace(old_abort, new_abort)

# Update scrape_inner to pass original_hostname
old_route_setup = 'await context.route("**/*", abort_private_routes)'
new_route_setup = """original_hostname = urllib.parse.urlparse(url).hostname
                    await context.route("**/*", lambda route, request: abort_private_routes(route, request, original_hostname))"""

content = content.replace(old_route_setup, new_route_setup)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
