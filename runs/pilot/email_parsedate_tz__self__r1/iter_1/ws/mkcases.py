import json
from solution import solve

ins = ["Mon, 20 Nov 1995 19:12:08 -0500", "20 Nov 95 19:12 EST", "Tue, 5 Jan 2021 10:11:12 GMT",
       "1 Feb 2020", "31 Dec 1999 23:59:60 +0530", "Thu, 01 Jan 1970 00:00:00 -0000",
       "Nov 20 1995 19:12:08 PST", "20 nov 1995 19.12.08 pdt", "0 Foo 2000 10:00:00 UTC",
       "32 JAN 3 24:60:61 Z", "15 March 100 10:00 +0100", "5 Jan 10000 25:00:00 EDT",
       "Sun, 6 Nov 1994 08:49:37 GMT", "06-Nov-94 08:49:37 GMT", "junk", "",
       "10 Oct 2000 10:00:00 -0330", "10 Oct 2000 10:00:00.5 UTC", "10 Oct 2000 10:00:00+0200",
       "Mon 10 Oct 2000 10:00:00 A", "10,Oct,2000 10:00:00", "10 Oct 2000 10:00:00 (comment)",
       "10 Oct 1900 12:00 bogus", "10 Oct 0 12:00:00 +1", "Wed, 10 Oct 2000 12:00:00 -0000",
       "10 Oct 2000 10:00:00 -", "Oct 10 2000 10:00", "10 Oct 2000 10:00:00 +99999",
       "10 Oct 2000 1:2:3 cst", "10 Oct 2000 12:00 MDT", "10 Oct 68 12:00 UT",
       "10 Oct 69 12:00 UT", "10 Oct 2000 10:00:00 pdt"]
c = []
for s in ins:
    try:
        r = solve(s)
        r = list(r) if r else r
    except Exception as e:
        r = {"raises": type(e).__name__}
    print(s, r)
    c.append({"args": [s], "kwargs": {}, "expected": r})
json.dump(c, open("self_cases.json", "w"))
