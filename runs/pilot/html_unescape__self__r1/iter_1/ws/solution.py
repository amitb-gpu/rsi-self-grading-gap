import re

_INV = {0x00: '�', 0x0d: '\r', 0x80: '€', 0x81: '\x81', 0x82: '‚', 0x83: 'ƒ',
        0x84: '„', 0x85: '…', 0x86: '†', 0x87: '‡', 0x88: 'ˆ', 0x89: '‰',
        0x8a: 'Š', 0x8b: '‹', 0x8c: 'Œ', 0x8d: '\x8d', 0x8e: 'Ž', 0x8f: '\x8f',
        0x90: '\x90', 0x91: '‘', 0x92: '’', 0x93: '“', 0x94: '”', 0x95: '•',
        0x96: '–', 0x97: '—', 0x98: '˜', 0x99: '™', 0x9a: 'š', 0x9b: '›',
        0x9c: 'œ', 0x9d: '\x9d', 0x9e: 'ž', 0x9f: 'Ÿ'}
_BAD = (set(range(0x1, 0x9)) | set(range(0xe, 0x20)) | set(range(0x7f, 0xa0))
        | set(range(0xfdd0, 0xfdf0)) | {0xb})
for _p in range(17):
    _BAD.add(_p * 0x10000 + 0xfffe)
    _BAD.add(_p * 0x10000 + 0xffff)

# Latin-1 entities (valid with and without ';')
_L1 = ("nbsp iexcl cent pound curren yen brvbar sect uml copy ordf laquo not shy reg macr deg plusmn "
       "sup2 sup3 acute micro para middot cedil sup1 ordm raquo frac14 frac12 frac34 iquest Agrave Aacute "
       "Acirc Atilde Auml Aring AElig Ccedil Egrave Eacute Ecirc Euml Igrave Iacute Icirc Iuml ETH Ntilde "
       "Ograve Oacute Ocirc Otilde Ouml times Oslash Ugrave Uacute Ucirc Uuml Yacute THORN szlig agrave "
       "aacute acirc atilde auml aring aelig ccedil egrave eacute ecirc euml igrave iacute icirc iuml eth "
       "ntilde ograve oacute ocirc otilde ouml divide oslash ugrave uacute ucirc uuml yacute thorn yuml").split()
_E = {}
for _i, _n in enumerate(_L1):
    _E[_n] = chr(0xa0 + _i)
    _E[_n + ';'] = chr(0xa0 + _i)
for _n, _c in (('amp', '&'), ('lt', '<'), ('gt', '>'), ('quot', '"'), ('AMP', '&'), ('LT', '<'),
               ('GT', '>'), ('QUOT', '"'), ('COPY', '\xa9'), ('REG', '\xae')):
    _E[_n] = _c
    _E[_n + ';'] = _c

# Semicolon-only entities (subset of the HTML5 table, from memory)
_SEMI = {
 'apos': "'", 'OElig': 'Œ', 'oelig': 'œ', 'Scaron': 'Š', 'scaron': 'š', 'Yuml': 'Ÿ',
 'fnof': 'ƒ', 'circ': 'ˆ', 'tilde': '˜',
 'Alpha': 'Α', 'Beta': 'Β', 'Gamma': 'Γ', 'Delta': 'Δ', 'Epsilon': 'Ε', 'Zeta': 'Ζ',
 'Eta': 'Η', 'Theta': 'Θ', 'Iota': 'Ι', 'Kappa': 'Κ', 'Lambda': 'Λ', 'Mu': 'Μ',
 'Nu': 'Ν', 'Xi': 'Ξ', 'Omicron': 'Ο', 'Pi': 'Π', 'Rho': 'Ρ', 'Sigma': 'Σ',
 'Tau': 'Τ', 'Upsilon': 'Υ', 'Phi': 'Φ', 'Chi': 'Χ', 'Psi': 'Ψ', 'Omega': 'Ω',
 'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'epsilon': 'ε', 'zeta': 'ζ',
 'eta': 'η', 'theta': 'θ', 'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ',
 'nu': 'ν', 'xi': 'ξ', 'omicron': 'ο', 'pi': 'π', 'rho': 'ρ', 'sigmaf': 'ς',
 'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ', 'phi': 'φ', 'chi': 'χ', 'psi': 'ψ',
 'omega': 'ω', 'thetasym': 'ϑ', 'upsih': 'ϒ', 'piv': 'ϖ',
 'ensp': ' ', 'emsp': ' ', 'thinsp': ' ', 'zwnj': '‌', 'zwj': '‍', 'lrm': '‎',
 'rlm': '‏', 'ndash': '–', 'mdash': '—', 'lsquo': '‘', 'rsquo': '’', 'sbquo': '‚',
 'ldquo': '“', 'rdquo': '”', 'bdquo': '„', 'dagger': '†', 'Dagger': '‡',
 'bull': '•', 'hellip': '…', 'permil': '‰', 'prime': '′', 'Prime': '″',
 'lsaquo': '‹', 'rsaquo': '›', 'oline': '‾', 'frasl': '⁄', 'euro': '€',
 'image': 'ℑ', 'weierp': '℘', 'real': 'ℜ', 'trade': '™', 'alefsym': 'ℵ',
 'larr': '←', 'uarr': '↑', 'rarr': '→', 'darr': '↓', 'harr': '↔', 'crarr': '↵',
 'lArr': '⇐', 'uArr': '⇑', 'rArr': '⇒', 'dArr': '⇓', 'hArr': '⇔',
 'forall': '∀', 'part': '∂', 'exist': '∃', 'empty': '∅', 'nabla': '∇',
 'isin': '∈', 'notin': '∉', 'ni': '∋', 'prod': '∏', 'sum': '∑', 'minus': '−',
 'lowast': '∗', 'radic': '√', 'prop': '∝', 'infin': '∞', 'ang': '∠', 'and': '∧',
 'or': '∨', 'cap': '∩', 'cup': '∪', 'int': '∫', 'there4': '∴', 'sim': '∼',
 'cong': '≅', 'asymp': '≈', 'ne': '≠', 'equiv': '≡', 'le': '≤', 'ge': '≥',
 'sub': '⊂', 'sup': '⊃', 'nsub': '⊄', 'sube': '⊆', 'supe': '⊇', 'oplus': '⊕',
 'otimes': '⊗', 'perp': '⊥', 'sdot': '⋅', 'lceil': '⌈', 'rceil': '⌉',
 'lfloor': '⌊', 'rfloor': '⌋', 'lang': '⟨', 'rang': '⟩', 'loz': '◊',
 'spades': '♠', 'clubs': '♣', 'hearts': '♥', 'diams': '♦',
 'Tab': '\t', 'NewLine': '\n', 'excl': '!', 'num': '#', 'dollar': '$', 'percnt': '%', 'lpar': '(',
 'rpar': ')', 'ast': '*', 'plus': '+', 'comma': ',', 'period': '.', 'sol': '/', 'colon': ':', 'semi': ';',
 'equals': '=', 'quest': '?', 'commat': '@', 'lsqb': '[', 'lbrack': '[', 'bsol': '\\', 'rsqb': ']',
 'rbrack': ']', 'Hat': '^', 'lowbar': '_', 'grave': '`', 'lcub': '{', 'lbrace': '{', 'verbar': '|',
 'vert': '|', 'rcub': '}', 'rbrace': '}', 'check': '✓', 'star': '☆', 'starf': '★',
 'phone': '☎', 'female': '♀', 'male': '♂', 'cross': '✗', 'checkmark': '✓',
 'half': '\xbd', 'Dot': '\xa8', 'die': '\xa8', 'strns': '\xaf', 'pm': '\xb1', 'centerdot': '\xb7',
 'div': '\xf7', 'angst': '\xc5', 'fjlig': 'fj', 'ThickSpace': '  ', 'bne': '=⃥',
 'nvlt': '<⃒', 'nvgt': '>⃒', 'nbump': '≎̸', 'NotEqualTilde': '≂̸',
 'NotGreaterFullEqual': '≧̸', 'nles': '⩽̸', 'nges': '⩾̸',
 'nvap': '≍⃒', 'napid': '≋̸', 'acE': '∾̳', 'NotLessLess': '≪̸',
 'NotGreaterGreater': '≫̸', 'vnsub': '⊂⃒', 'vnsup': '⊃⃒',
 'nsubE': '⫅̸', 'nsupE': '⫆̸', 'lesg': '⋚︀', 'gesl': '⋛︀',
 'caps': '∩︀', 'cups': '∪︀', 'nang': '∠⃒', 'nGg': '⋙̸',
 'nLl': '⋘̸', 'nGt': '≫⃒', 'nLt': '≪⃒', 'ngE': '≧̸',
 'nlE': '≦̸', 'ngeqq': '≧̸', 'nleqq': '≦̸',
 'hbar': 'ℏ', 'ell': 'ℓ', 'Re': 'ℜ', 'Im': 'ℑ', 'aleph': 'ℵ',
 'natural': '♮', 'flat': '♭', 'sharp': '♯', 'copysr': '℗', 'incare': '℅',
 'Copf': 'ℂ', 'Nopf': 'ℕ', 'Qopf': 'ℚ', 'Ropf': 'ℝ', 'Zopf': 'ℤ',
 'Aopf': '\U0001d538', 'Afr': '\U0001d504', 'Ascr': '\U0001d49c', 'afr': '\U0001d51e', 'ascr': '\U0001d4b6',
 'aopf': '\U0001d552', 'bopf': '\U0001d553', 'fopf': '\U0001d557', 'Bopf': '\U0001d539',
 'nlt': '≮', 'ngt': '≯', 'nle': '≰', 'nge': '≱', 'nequiv': '≢', 'nsim': '≁',
 'ncong': '≇', 'nap': '≉', 'napprox': '≉', 'nless': '≮', 'ngtr': '≯',
 'NotLess': '≮', 'NotGreater': '≯', 'notni': '∌', 'notinva': '∉', 'NotElement': '∉',
 'nisd': '⋺', 'notnivb': '⋾', 'notnivc': '⋽', 'notinvb': '⋷', 'notinvc': '⋶',
 'nexist': '∄', 'nexists': '∄', 'NotExists': '∄', 'nmid': '∤', 'npar': '∦',
 'nparallel': '∦', 'nsup': '⊅', 'nsube': '⊈', 'nsupe': '⊉', 'nrarr': '↛',
 'nlarr': '↚', 'nharr': '↮', 'nlArr': '⇍', 'nrArr': '⇏', 'nhArr': '⇎',
 'Amacr': 'Ā', 'amacr': 'ā', 'Abreve': 'Ă', 'abreve': 'ă',
 'Aogon': 'Ą', 'aogon': 'ą', 'Cacute': 'Ć', 'cacute': 'ć', 'Ccaron': 'Č',
 'ccaron': 'č', 'Dcaron': 'Ď', 'dcaron': 'ď', 'Dstrok': 'Đ', 'dstrok': 'đ',
 'Emacr': 'Ē', 'emacr': 'ē', 'Eogon': 'Ę', 'eogon': 'ę', 'Ecaron': 'Ě',
 'ecaron': 'ě', 'Gbreve': 'Ğ', 'gbreve': 'ğ', 'Idot': 'İ', 'imath': 'ı',
 'inodot': 'ı', 'Lstrok': 'Ł', 'lstrok': 'ł', 'Nacute': 'Ń', 'nacute': 'ń',
 'Ncaron': 'Ň', 'ncaron': 'ň', 'Odblac': 'Ő', 'odblac': 'ő', 'Rcaron': 'Ř',
 'rcaron': 'ř', 'Sacute': 'Ś', 'sacute': 'ś', 'Scedil': 'Ş', 'scedil': 'ş',
 'Tcaron': 'Ť', 'tcaron': 'ť', 'Uring': 'Ů', 'uring': 'ů', 'Udblac': 'Ű',
 'udblac': 'ű', 'Zacute': 'Ź', 'zacute': 'ź', 'Zdot': 'Ż', 'zdot': 'ż',
 'Zcaron': 'Ž', 'zcaron': 'ž', 'caron': 'ˇ', 'breve': '˘', 'dot': '˙',
 'ring': '˚', 'ogon': '˛', 'dblac': '˝', 'Gcirc': 'Ĝ', 'gcirc': 'ĝ',
 'Hcirc': 'Ĥ', 'hcirc': 'ĥ', 'Jcirc': 'Ĵ', 'jcirc': 'ĵ', 'Scirc': 'Ŝ',
 'scirc': 'ŝ', 'Ubreve': 'Ŭ', 'ubreve': 'ŭ', 'IJlig': 'Ĳ', 'ijlig': 'ĳ',
 'Cdot': 'Ċ', 'cdot': 'ċ', 'Edot': 'Ė', 'edot': 'ė', 'Gdot': 'Ġ', 'gdot': 'ġ',
 'Imacr': 'Ī', 'imacr': 'ī', 'Iogon': 'Į', 'iogon': 'į', 'Omacr': 'Ō',
 'omacr': 'ō', 'Umacr': 'Ū', 'umacr': 'ū', 'Uogon': 'Ų', 'uogon': 'ų',
 'Wcirc': 'Ŵ', 'wcirc': 'ŵ', 'Ycirc': 'Ŷ', 'ycirc': 'ŷ', 'Itilde': 'Ĩ',
 'itilde': 'ĩ', 'Utilde': 'Ũ', 'utilde': 'ũ', 'Lacute': 'Ĺ', 'lacute': 'ĺ',
 'Racute': 'Ŕ', 'racute': 'ŕ', 'Lcaron': 'Ľ', 'lcaron': 'ľ', 'Lmidot': 'Ŀ',
 'lmidot': 'ŀ', 'ENG': 'Ŋ', 'eng': 'ŋ', 'Tstrok': 'Ŧ', 'tstrok': 'ŧ',
 'Hstrok': 'Ħ', 'hstrok': 'ħ', 'kgreen': 'ĸ', 'napos': 'ŉ',
 'Cedilla': '\xb8', 'DiacriticalAcute': '\xb4', 'PlusMinus': '\xb1',
 'larrhk': '↩', 'rarrhk': '↪', 'map': '↦', 'mapsto': '↦', 'rightarrow': '→',
 'leftarrow': '←', 'uparrow': '↑', 'downarrow': '↓', 'leftrightarrow': '↔',
 'Rightarrow': '⇒', 'Leftarrow': '⇐', 'Leftrightarrow': '⇔', 'RightArrow': '→',
 'LeftArrow': '←', 'UpArrow': '↑', 'DownArrow': '↓', 'iff': '⇔', 'implies': '⇒',
 'ForAll': '∀', 'Exists': '∃', 'emptyset': '∅', 'varnothing': '∅', 'Element': '∈',
 'in': '∈', 'isinv': '∈', 'Sum': '∑', 'Product': '∏', 'Sqrt': '√',
 'Integral': '∫', 'therefore': '∴', 'because': '∵', 'becaus': '∵',
 'Therefore': '∴', 'Because': '∵', 'approx': '≈', 'ap': '≈', 'thickapprox': '≈',
 'NotEqual': '≠', 'leq': '≤', 'geq': '≥', 'subset': '⊂', 'supset': '⊃',
 'subseteq': '⊆', 'supseteq': '⊇', 'bot': '⊥', 'bottom': '⊥', 'top': '⊤',
 'vee': '∨', 'wedge': '∧', 'setminus': '∖', 'smallsetminus': '∖', 'compfn': '∘',
 'bullet': '•', 'mldr': '…', 'nldr': '‥', 'hyphen': '‐', 'dash': '‐',
 'horbar': '―', 'Vert': '‖', 'Verbar': '‖', 'lsquor': '‚', 'rsquor': '’',
 'ldquor': '„', 'rdquor': '”', 'OpenCurlyQuote': '‘', 'CloseCurlyQuote': '’',
 'OpenCurlyDoubleQuote': '“', 'CloseCurlyDoubleQuote': '”', 'ddagger': '‡',
 'tprime': '‴', 'bprime': '‵', 'backprime': '‵', 'qprime': '⁗', 'caret': '⁁',
 'hybull': '⁃', 'MediumSpace': ' ', 'NoBreak': '⁠', 'ApplyFunction': '⁡', 'af': '⁡',
 'InvisibleTimes': '⁢', 'it': '⁢', 'InvisibleComma': '⁣', 'ic': '⁣',
 'emsp13': ' ', 'emsp14': ' ', 'numsp': ' ', 'puncsp': ' ', 'hairsp': ' ',
 'VeryThinSpace': ' ', 'ThinSpace': ' ', 'ZeroWidthSpace': '​', 'NegativeThinSpace': '​',
 'NonBreakingSpace': '\xa0', 'TRADE': '™', 'tdot': '⃛', 'DotDot': '⃜',
 'sung': '♪', 'ohm': 'Ω', 'mho': '℧',
 'epsi': 'ε', 'epsiv': 'ϵ', 'varepsilon': 'ϵ', 'straightepsilon': 'ϵ', 'thetav': 'ϑ',
 'vartheta': 'ϑ', 'phiv': 'ϕ', 'varphi': 'ϕ', 'straightphi': 'ϕ', 'varpi': 'ϖ',
 'varrho': 'ϱ', 'rhov': 'ϱ', 'varsigma': 'ς', 'sigmav': 'ς', 'kappav': 'ϰ',
 'varkappa': 'ϰ', 'Gammad': 'Ϝ', 'gammad': 'ϝ', 'digamma': 'ϝ', 'Upsi': 'ϒ',
 'upsi': 'υ', 'ohgr': 'ω', 'OHgr': 'Ω', 'bepsi': '϶', 'backepsilon': '϶',
 'IOcy': 'Ё', 'iocy': 'ё', 'Acy': 'А', 'acy': 'а', 'Bcy': 'Б',
 'bcy': 'б', 'Vcy': 'В', 'vcy': 'в', 'Gcy': 'Г', 'gcy': 'г', 'Dcy': 'Д',
 'dcy': 'д', 'IEcy': 'Е', 'iecy': 'е', 'ZHcy': 'Ж', 'zhcy': 'ж', 'Zcy': 'З',
 'zcy': 'з', 'Icy': 'И', 'icy': 'и', 'Jcy': 'Й', 'jcy': 'й', 'Kcy': 'К',
 'kcy': 'к', 'Lcy': 'Л', 'lcy': 'л', 'Mcy': 'М', 'mcy': 'м', 'Ncy': 'Н',
 'ncy': 'н', 'Ocy': 'О', 'ocy': 'о', 'Pcy': 'П', 'pcy': 'п', 'Rcy': 'Р',
 'rcy': 'р', 'Scy': 'С', 'scy': 'с', 'Tcy': 'Т', 'tcy': 'т', 'Ucy': 'У',
 'ucy': 'у', 'Fcy': 'Ф', 'fcy': 'ф', 'KHcy': 'Х', 'khcy': 'х', 'TScy': 'Ц',
 'tscy': 'ц', 'CHcy': 'Ч', 'chcy': 'ч', 'SHcy': 'Ш', 'shcy': 'ш',
 'SHCHcy': 'Щ', 'shchcy': 'щ', 'HARDcy': 'Ъ', 'hardcy': 'ъ', 'Ycy': 'Ы',
 'ycy': 'ы', 'SOFTcy': 'Ь', 'softcy': 'ь', 'Ecy': 'Э', 'ecy': 'э',
 'YUcy': 'Ю', 'yucy': 'ю', 'YAcy': 'Я', 'yacy': 'я',
 'fflig': 'ﬀ', 'filig': 'ﬁ', 'fllig': 'ﬂ', 'ffilig': 'ﬃ', 'ffllig': 'ﬄ',
 'blk14': '░', 'blk12': '▒', 'blk34': '▓', 'block': '█', 'squ': '□',
 'square': '□', 'squf': '▪', 'blacksquare': '▪', 'utri': '▵', 'dtri': '▿',
 'ltri': '◃', 'rtri': '▹', 'utrif': '▴', 'dtrif': '▾', 'ltrif': '◂',
 'rtrif': '▸', 'cir': '○', 'lozenge': '◊', 'lozf': '⧫', 'bigcirc': '◯',
 'frac13': '⅓', 'frac23': '⅔', 'frac15': '⅕', 'frac25': '⅖', 'frac35': '⅗',
 'frac45': '⅘', 'frac16': '⅙', 'frac56': '⅚', 'frac18': '⅛', 'frac38': '⅜',
 'frac58': '⅝', 'frac78': '⅞',
 'boxh': '─', 'boxv': '│', 'boxdr': '┌', 'boxdl': '┐', 'boxur': '└',
 'boxul': '┘', 'boxvr': '├', 'boxvl': '┤', 'boxhd': '┬', 'boxhu': '┴',
 'boxvh': '┼', 'boxH': '═', 'boxV': '║', 'uhblk': '▀', 'lhblk': '▄',
 'lbbrk': '❲', 'rbbrk': '❳', 'langle': '⟨', 'rangle': '⟩', 'Lang': '⟪',
 'Rang': '⟫', 'lobrk': '⟦', 'robrk': '⟧', 'LeftAngleBracket': '⟨',
 'RightAngleBracket': '⟩', 'xlarr': '⟵', 'xrarr': '⟶', 'xharr': '⟷',
 'longrightarrow': '⟶', 'longleftarrow': '⟵', 'Longrightarrow': '⟹',
 'Longleftarrow': '⟸', 'xlArr': '⟸', 'xrArr': '⟹', 'xhArr': '⟺',
 'heartsuit': '♥', 'spadesuit': '♠', 'clubsuit': '♣', 'diamondsuit': '♦',
 'sext': '✶', 'malt': '✠', 'maltese': '✠',
 'lE': '≦', 'gE': '≧', 'leqq': '≦', 'geqq': '≧', 'les': '⩽', 'ges': '⩾',
 'leqslant': '⩽', 'geqslant': '⩾', 'lne': '⪇', 'gne': '⪈', 'lnE': '≨',
 'gnE': '≩', 'lneqq': '≨', 'gneqq': '≩', 'll': '≪', 'gg': '≫', 'Lt': '≪',
 'Gt': '≫', 'lap': '⪅', 'gap': '⪆', 'lsim': '≲', 'gsim': '≳', 'lg': '≶',
 'gl': '≷', 'pr': '≺', 'sc': '≻', 'prec': '≺', 'succ': '≻', 'npr': '⊀',
 'nsc': '⊁', 'osol': '⊘', 'odot': '⊙', 'ominus': '⊖',
 'CirclePlus': '⊕', 'CircleTimes': '⊗', 'CircleDot': '⊙', 'CircleMinus': '⊖',
 'vdash': '⊢', 'dashv': '⊣', 'models': '⊧', 'vDash': '⊨', 'Vdash': '⊩',
 'nvdash': '⊬', 'nvDash': '⊭', 'diam': '⋄', 'diamond': '⋄', 'Diamond': '⋄',
 'sstarf': '⋆', 'Star': '⋆', 'bowtie': '⋈', 'xcap': '⋂', 'xcup': '⋃',
 'bigcap': '⋂', 'bigcup': '⋃', 'xvee': '⋁', 'xwedge': '⋀', 'bigvee': '⋁',
 'bigwedge': '⋀', 'vellip': '⋮', 'ctdot': '⋯', 'utdot': '⋰', 'dtdot': '⋱',
 'Tilde': '∼', 'thksim': '∼', 'bsim': '∽', 'backsim': '∽', 'wreath': '≀',
 'wr': '≀', 'esim': '≂', 'eqsim': '≂', 'sime': '≃', 'simeq': '≃',
 'TildeEqual': '≃', 'TildeFullEqual': '≅', 'TildeTilde': '≈', 'ape': '≊',
 'approxeq': '≊', 'bump': '≎', 'bumpe': '≏', 'doteq': '≐', 'esdot': '≐',
 'eDot': '≑', 'ecolon': '≕', 'colone': '≔', 'coloneq': '≔', 'Colon': '∷',
 'Proportion': '∷', 'Colone': '⩴', 'ratio': '∶', 'minusd': '∸', 'dotminus': '∸',
 'lrarr': '⇆', 'rlarr': '⇄', 'lrhar': '⇋', 'rlhar': '⇌', 'udarr': '⇅',
 'duarr': '⇵', 'varr': '↕', 'updownarrow': '↕', 'nwarr': '↖', 'nearr': '↗',
 'searr': '↘', 'swarr': '↙', 'lAarr': '⇚', 'rAarr': '⇛', 'Larr': '↞',
 'Rarr': '↠', 'larrtl': '↢', 'rarrtl': '↣', 'lharu': '↼', 'lhard': '↽',
 'rharu': '⇀', 'rhard': '⇁', 'vArr': '⇕', 'Updownarrow': '⇕', 'zigrarr': '⇝',
 'lsh': '↰', 'rsh': '↱', 'Lsh': '↰', 'Rsh': '↱', 'olarr': '↺', 'orarr': '↻',
 'cularr': '↶', 'curarr': '↷', 'ldsh': '↲', 'rdsh': '↳',
}
for _k, _v in _SEMI.items():
    _E.setdefault(_k + ';', _v)

_RE = re.compile(r'&(#[0-9]+;?|#[xX][0-9a-fA-F]+;?|[^\t\n\f <&#;]{1,32};?)')


def _rep(m):
    s = m.group(1)
    if s[0] == '#':
        num = int(s[2:].rstrip(';'), 16) if s[1] in 'xX' else int(s[1:].rstrip(';'))
        if num in _INV:
            return _INV[num]
        if 0xD800 <= num <= 0xDFFF or num > 0x10FFFF:
            return '�'
        if num in _BAD:
            return ''
        return chr(num)
    if s in _E:
        return _E[s]
    for x in range(len(s) - 1, 1, -1):
        if s[:x] in _E:
            return _E[s[:x]] + s[x:]
    return '&' + s


def solve(s: str) -> str:
    if '&' not in s:
        return s
    return _RE.sub(_rep, s)
