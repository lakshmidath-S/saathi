from enum import Enum


class TrustLevel(Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    BLOCK = "block"


TOOL_POLICY = {
    "browser.navigate": TrustLevel.ALLOW,
    "browser.find": TrustLevel.ALLOW,
    "browser.scroll": TrustLevel.ALLOW,
    "browser.extract": TrustLevel.ALLOW,

    "browser.search": TrustLevel.BLOCK,

    "filesystem.read": TrustLevel.ALLOW,
    "filesystem.write": TrustLevel.CONFIRM,

    "shell.run": TrustLevel.CONFIRM,
}


def check_permission(tool_name: str) -> TrustLevel:
    return TOOL_POLICY.get(tool_name, TrustLevel.BLOCK)
