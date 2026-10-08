"""Parse downloaded AFL Tables pages (data/raw/afltables) into tidy CSVs.

Outputs (data/interim):
  afltables_matches.csv    one row per match: year, round, date, home, away, scores, attendance, venue
  afltables_teamgames.csv  one row per team per match with that team's stats (for and against)
"""
import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/afltables"
OUT = ROOT / "data/interim"
YEARS = range(2012, 2027)


def text(cell):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", cell))).strip()


def parse_matches(year):
    page = (RAW / f"seas_{year}.html").read_text(encoding="latin-1")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S)
    matches, rnd = [], None
    i = 0
    while i < len(rows):
        r = rows[i]
        head = re.search(r"<b>(Round \d+|(?:Wildcard|Qualifying|Elimination|Semi|Preliminary|Grand) Final)", r)
        if head:
            rnd = head.group(1)
        cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        # Crowd-less games (2020-21 COVID) have no "Att:" field.
        if len(cells) == 4 and "Venue:" in r and i + 1 < len(rows):
            nxt = re.findall(r"<td[^>]*>(.*?)</td>", rows[i + 1], re.S)
            info = text(cells[3])
            date = re.search(r"\d{2}-[A-Za-z]{3}-\d{4}", info).group(0)
            att = re.search(r"Att:\s*([\d,]+)", info)
            venue = info.split("Venue:")[1].strip()
            matches.append({
                "year": year, "round": rnd, "date": date,
                "home": text(cells[0]), "away": text(nxt[0]),
                "home_score": int(text(cells[2])), "away_score": int(text(nxt[2])),
                "attendance": int(att.group(1).replace(",", "")) if att else "",
                "venue": venue,
            })
            i += 2
            continue
        i += 1
    return matches


def parse_teamgames(year):
    page = (RAW / f"teamstats_{year}.html").read_text(encoding="latin-1")
    games = {}
    for table in re.findall(r'<table class="sortable".*?</table>', page, re.S):
        team = text(re.search(r"<th colspan=\d+>(.*?) Team Statistics", table).group(1))
        header = table[:table.index("<td")]
        cols = [text(h) for h in re.findall(r"<th[^>]*>(.*?)</th>", header)[1:]]
        for row in re.findall(r"<tr><td.*?(?=<tr>|</tbody>)", table, re.S):
            cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            if len(cells) != len(cols) or not re.match(r"^(R\d+|EF|QF|SF|PF|GF)$", cells[0]):
                continue
            key = (team, cells[0], cells[1])
            g = games.setdefault(key, {"year": year, "team": team, "round": cells[0], "opponent": cells[1]})
            for c, v in zip(cols[2:], cells[2:]):
                if "-" in v:
                    f, a = v.split("-")
                    g[f"{c}_for"], g[f"{c}_against"] = f, a
    return list(games.values())


def write(path, rows):
    fields = []
    for r in rows:
        fields += [k for k in r if k not in fields]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    matches = [m for y in YEARS for m in parse_matches(y)]
    teamgames = [g for y in YEARS for g in parse_teamgames(y)]
    write(OUT / "afltables_matches.csv", matches)
    write(OUT / "afltables_teamgames.csv", teamgames)
    print(len(matches), "matches,", len(teamgames), "team-games")
