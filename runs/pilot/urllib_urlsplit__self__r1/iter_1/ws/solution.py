import re
import ipaddress
import unicodedata

_STRIP = ''.join(chr(i) for i in range(0x21))
_SCHEME_CHARS = frozenset('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-.')


def _check_bracketed_host(h):
    if h.startswith('v'):
        if not re.match(r"\Av[a-fA-F0-9]+\..+\Z", h):
            raise ValueError("IPvFuture address is invalid")
    else:
        ip = ipaddress.ip_address(h)
        if isinstance(ip, ipaddress.IPv4Address):
            raise ValueError("An IPv4 address cannot be in brackets")


def _checknetloc(netloc):
    if not netloc or netloc.isascii():
        return
    n = netloc.replace('@', '').replace(':', '').replace('/', '').replace('?', '').replace('#', '')
    n2 = unicodedata.normalize('NFKC', n)
    if n == n2:
        return
    for c in '/?#@:':
        if c in n2:
            raise ValueError("netloc contains invalid characters under NFKC normalization")


def solve(url, scheme='', allow_fragments=True):
    url = url.lstrip(_STRIP)
    scheme = scheme.strip(_STRIP)
    for b in ('\t', '\r', '\n'):
        url = url.replace(b, '')
        scheme = scheme.replace(b, '')
    allow_fragments = bool(allow_fragments)
    netloc = query = fragment = ''
    i = url.find(':')
    if i > 0 and url[0].isascii() and url[0].isalpha():
        for c in url[:i]:
            if c not in _SCHEME_CHARS:
                break
        else:
            scheme, url = url[:i].lower(), url[i + 1:]
    if url[:2] == '//':
        delim = len(url)
        for c in '/?#':
            w = url.find(c, 2)
            if w >= 0:
                delim = min(delim, w)
        netloc, url = url[2:delim], url[delim:]
        if (('[' in netloc and ']' not in netloc) or
                (']' in netloc and '[' not in netloc)):
            raise ValueError("Invalid IPv6 URL")
        if '[' in netloc and ']' in netloc:
            _check_bracketed_host(netloc.partition('[')[2].partition(']')[0])
    if allow_fragments and '#' in url:
        url, fragment = url.split('#', 1)
    if '?' in url:
        url, query = url.split('?', 1)
    _checknetloc(netloc)
    return (scheme, netloc, url, query, fragment)
