import re

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "r") as f:
    content = f.read()

old_is_private = """def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        if (ip.is_private or ip.is_loopback or ip.is_link_local or
            ip.is_multicast or ip.is_reserved or
            ip in ipaddress.ip_network('169.254.169.254/32') or
            ip in ipaddress.ip_network('fd00:ec2::254/128')):
            return True
        return False
    except ValueError:
        return True"""

new_is_private = """_AWS_METADATA_NETS = [ipaddress.ip_network('169.254.169.254/32'), ipaddress.ip_network('fd00:ec2::254/128')]

def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        if (ip.is_private or ip.is_loopback or ip.is_link_local or
            ip.is_multicast or ip.is_reserved or
            any(ip in net for net in _AWS_METADATA_NETS)):
            return True
        return False
    except ValueError:
        return True"""

content = content.replace(old_is_private, new_is_private)

with open("gam-bit-hunter-1 ( idcloudhost - debugging & enhance ).py", "w") as f:
    f.write(content)
