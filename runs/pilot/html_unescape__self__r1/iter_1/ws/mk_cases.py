import json
C = [("a&amp;b", "a&b"), ("&amp", "&"), ("&ampx", "&x"), ("&notit;", "¬it;"), ("&notin;", "∉"),
     ("&#0;", "�"), ("&#x80;", "€"), ("&#128;", "€"), ("&#xD800;", "�"),
     ("&#x110000;", "�"), ("&#99999999999999;", "�"), ("&#;", "&#;"), ("&#x;", "&#x;"),
     ("&", "&"), ("& &", "& &"), ("&#1;", ""), ("&#65;", "A"), ("&#x41", "A"), ("&#X41;", "A"),
     ("&copy", "©"), ("&copy;x", "©x"), ("&nbsp;", " "), ("&lt;&gt;", "<>"),
     ("&bogus;", "&bogus;"), ("&fjlig;", "fj"), ("&NotEqualTilde;", "≂̸"),
     ("&eacute;", "é"), ("&eacutex", "éx"), ("&hellip;", "…"), ("&#xFFFE;", ""),
     ("&#x1FFFF;", ""), ("&#13;", "\r"), ("&#x7f;", ""), ("&#xfdd0;", ""), ("hello", "hello"),
     ("&AMP;", "&"), ("&quot", "\""), ("&aposx", "&aposx"), ("&#65abc", "Aabc"), ("x&#", "x&#"),
     ("&#" + "9" * 5000 + ";", {"raises": "ValueError"})]
json.dump([{"args": [a], "kwargs": {}, "expected": b} for a, b in C], open("self_cases.json", "w"))
