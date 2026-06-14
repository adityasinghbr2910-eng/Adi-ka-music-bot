"""
blocked_playwords.py
────────────────────────────────────────────────────────────────────
Play query aane pe pehle is_query_blocked() call karo.
Injection attack + blocked words + blocked users detect karta hai.
Dynamic words/users MongoDB se aate hain (blockplay.py se).
────────────────────────────────────────────────────────────────────
"""

import re

# ── Dynamic blocked data MongoDB se (blockplay.py) ───────────────────────────
try:
    from KanhaMusic.plugins.play.blockplay import (
        get_blocked_words,
        get_blocked_users,
        is_user_play_blocked,
    )
except ImportError:
    async def get_blocked_words(): return []
    async def get_blocked_users(): return []
    async def is_user_play_blocked(uid): return False


# ══════════════════════════════════════════════════════════════════════════════
# 1. Shell / Command Injection Patterns
# ══════════════════════════════════════════════════════════════════════════════
INJECTION_PATTERNS = [
    r";",                       # semicolon — command chaining
    r"\$\{IFS\}",               # ${IFS} — space bypass
    r"\$\(",                    # $( — command substitution
    r"`",                       # backtick — command substitution
    r"\|\|",                    # || — OR chaining
    r"&&",                      # && — AND chaining
    r"\bcp\b",                  # cp command
    r"\bcurl\b",                # curl — exfiltration
    r"\bwget\b",                # wget — download
    r"\bcat\b\s+/",             # cat /... — file read
    r"/proc/",                  # /proc/ — system files
    r"/etc/passwd",             # sensitive file
    r"/etc/shadow",             # sensitive file
    r"webhook\.",               # webhook URLs
    r"webhook\.site",           # webhook.site specifically
    r"\btar\b",                 # tar — archive creation
    r"\bchmod\b",               # chmod
    r"\brm\b\s+-",              # rm -rf etc
    r"\benv\b",                 # env variables
    r"environ",                 # /proc/self/environ
    r"-X\s+POST",               # curl POST flag
    r"-F\s+file=@",             # curl file upload
    r"base64",                  # base64 encoding bypass
    r"\.\./",                   # path traversal ../
    r"%2e%2e",                  # URL encoded path traversal
    r"%252e",                   # double encoded
    r"<script",                 # XSS attempt
    r"javascript:",             # JS injection
    r"\bexec\b",                # exec command
    r"\beval\b",                # eval
    r"\bos\.system\b",          # python os.system
    r"\bsubprocess\b",          # python subprocess
    r"ngrok\.io",               # tunnel
    r"requestbin\.",            # data capture
    r"pipedream\.net",          # data capture
    r"burpcollaborator",        # burp
    r"canarytokens",            # canary
    r"serveo\.net",             # tunnel
    r"\bnc\b\s+-",              # netcat
    r"\bnetcat\b",              # netcat
    r"0x[0-9a-fA-F]{4,}",      # hex encoded values
    r"%00",                     # null byte
    r"\x00",                    # null byte literal
    r"gopher://",               # SSRF protocol
    r"file://",                 # SSRF protocol
    r"dict://",                 # SSRF protocol
    r"ftp://.*@",               # FTP with credentials
]

# ══════════════════════════════════════════════════════════════════════════════
# 2. Suspicious URL Patterns (non-music sites in query)
# ══════════════════════════════════════════════════════════════════════════════
BLOCKED_URL_PATTERNS = [
    r"webhook\.site",
    r"ngrok\.io",
    r"serveo\.net",
    r"burpcollaborator",
    r"requestbin",
    r"pipedream\.net",
    r"canarytokens",
]

# ══════════════════════════════════════════════════════════════════════════════
# 3. Compiled patterns for speed
# ══════════════════════════════════════════════════════════════════════════════
_compiled_injection = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
_compiled_url = [re.compile(p, re.IGNORECASE) for p in BLOCKED_URL_PATTERNS]


# ══════════════════════════════════════════════════════════════════════════════
# Main Check Function
# ══════════════════════════════════════════════════════════════════════════════

async def is_query_blocked(query: str) -> str | None:
    """
    Query check karo — agar blocked hai toh reason return karo, warna None.

    Usage:
        matched = await is_query_blocked(query)
        if matched:
            # block karo
    """
    if not query:
        return None

    q = query.strip()

    # ── 1. Shell Injection ─────────────────────────────────────────────────────
    for i, pattern in enumerate(_compiled_injection):
        if pattern.search(q):
            return f"[INJECTION] {INJECTION_PATTERNS[i]}"

    # ── 2. Blocked URLs ────────────────────────────────────────────────────────
    for i, pattern in enumerate(_compiled_url):
        if pattern.search(q):
            return f"[BLOCKED_URL] {BLOCKED_URL_PATTERNS[i]}"

    # ── 3. Dynamic Blocked Words (MongoDB se — owner ne add kiye) ─────────────
    q_lower = q.lower()
    dynamic_words = await get_blocked_words()
    for word in dynamic_words:
        if word.lower() in q_lower:
            return f"[BLOCKED_WORD] {word}"

    return None  # Sab theek — play hone do


async def is_user_blocked_from_play(user_id: int) -> bool:
    """Check karo kya owner ne yeh user play se block kiya hua hai."""
    return await is_user_play_blocked(user_id)