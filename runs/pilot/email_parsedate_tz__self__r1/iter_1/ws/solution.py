_monthnames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
               'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
               'september', 'october', 'november', 'december']
_daynames = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
_timezones = {'UT': 0, 'UTC': 0, 'GMT': 0, 'Z': 0,
              'AST': -400, 'ADT': -300, 'EST': -500, 'EDT': -400,
              'CST': -600, 'CDT': -500, 'MST': -700, 'MDT': -600,
              'PST': -800, 'PDT': -700}


def _p(data):
    if not data:
        return None
    data = data.split()
    if not data:
        return None
    if data[0].endswith(',') or data[0].lower() in _daynames:
        del data[0]
    else:
        i = data[0].rfind(',')
        if i >= 0:
            data[0] = data[0][i + 1:]
    if len(data) == 3:
        stuff = data[0].split('-')
        if len(stuff) == 3:
            data = stuff + data[1:]
    if len(data) == 4:
        s = data[3]
        i = s.find('+')
        if i == -1:
            i = s.find('-')
        if i > 0:
            data[3:] = [s[:i], s[i:]]
        else:
            data.append('')
    if len(data) < 5:
        return None
    data = data[:5]
    [dd, mm, yy, tm, tz] = data
    if not (dd and mm and yy):
        return None
    mm = mm.lower()
    if mm not in _monthnames:
        dd, mm = mm, dd.lower()
        if mm not in _monthnames:
            return None
    mm = _monthnames.index(mm) + 1
    if mm > 12:
        mm -= 12
    if dd[-1] == ',':
        dd = dd[:-1]
    i = yy.find(':')
    if i > 0:
        yy, tm = tm, yy
    if yy[-1] == ',':
        yy = yy[:-1]
        if not yy:
            return None
    if not yy[0].isdigit():
        yy, tz = tz, yy
    if tm[-1] == ',':
        tm = tm[:-1]
    tm = tm.split(':')
    if len(tm) == 2:
        [thh, tmm] = tm
        tss = '0'
    elif len(tm) == 3:
        [thh, tmm, tss] = tm
    elif len(tm) == 1 and '.' in tm[0]:
        tm = tm[0].split('.')
        if len(tm) == 2:
            [thh, tmm] = tm
            tss = 0
        elif len(tm) == 3:
            [thh, tmm, tss] = tm
        else:
            return None
    else:
        return None
    try:
        yy = int(yy)
        dd = int(dd)
        thh = int(thh)
        tmm = int(tmm)
        tss = int(tss)
    except ValueError:
        return None
    if yy < 100:
        if yy > 68:
            yy += 1900
        else:
            yy += 2000
    tzoffset = None
    tz = tz.upper()
    if tz in _timezones:
        tzoffset = _timezones[tz]
    else:
        try:
            tzoffset = int(tz)
        except ValueError:
            pass
        if tzoffset == 0 and tz.startswith('-'):
            tzoffset = None
    if tzoffset:
        if tzoffset < 0:
            tzsign = -1
            tzoffset = -tzoffset
        else:
            tzsign = 1
        tzoffset = tzsign * ((tzoffset // 100) * 3600 + (tzoffset % 100) * 60)
    return [yy, mm, dd, thh, tmm, tss, 0, 1, -1, tzoffset]


def solve(data):
    res = _p(data)
    if not res:
        return None
    if res[9] is None:
        res[9] = 0
    return tuple(res)
