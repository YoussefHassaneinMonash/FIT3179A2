"""Build the small, chart-ready datasets in data/ from data/raw and data/interim.

Run after scripts/parse_afltables.py:  python3 scripts/build_datasets.py
"""
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
INTERIM = ROOT / "data/interim"
OUT = ROOT / "data"
YEARS = range(2012, 2027)

# Club metadata. home_venue is the club's main home ground (AFL Tables venue name),
# used as the starting point for travel distances.
TEAMS = pd.DataFrame([
    ("Adelaide", "ADE", "SA", "Adelaide Oval", "#002B5C"),
    ("Brisbane Lions", "BRI", "QLD", "Gabba", "#A30046"),
    ("Carlton", "CAR", "VIC", "M.C.G.", "#0E1E2D"),
    ("Collingwood", "COL", "VIC", "M.C.G.", "#000000"),
    ("Essendon", "ESS", "VIC", "Docklands", "#CC2031"),
    ("Fremantle", "FRE", "WA", "Perth Stadium", "#2A1A54"),
    ("Geelong", "GEE", "VIC", "Kardinia Park", "#1C3C63"),
    ("Gold Coast", "GCS", "QLD", "Carrara", "#D93E39"),
    ("Greater Western Sydney", "GWS", "NSW", "Sydney Showground", "#F15C22"),
    ("Hawthorn", "HAW", "VIC", "M.C.G.", "#4D2004"),
    ("Melbourne", "MEL", "VIC", "M.C.G.", "#0F1131"),
    ("North Melbourne", "NOR", "VIC", "Docklands", "#013B9F"),
    ("Port Adelaide", "POR", "SA", "Adelaide Oval", "#008AAB"),
    ("Richmond", "RIC", "VIC", "M.C.G.", "#E5B800"),
    ("St Kilda", "STK", "VIC", "Docklands", "#ED0F05"),
    ("Sydney", "SYD", "NSW", "S.C.G.", "#ED171F"),
    ("West Coast", "WCE", "WA", "Perth Stadium", "#062EE2"),
    ("Western Bulldogs", "WBD", "VIC", "Docklands", "#014896"),
], columns=["team", "abbr", "state", "home_venue", "colour"])

STATE_NAMES = {"NSW": "New South Wales", "VIC": "Victoria", "QLD": "Queensland",
               "SA": "South Australia", "WA": "Western Australia", "TAS": "Tasmania",
               "NT": "Northern Territory", "ACT": "Australian Capital Territory"}
ABS_REGION = {1: "NSW", 2: "VIC", 3: "QLD", 4: "SA", 5: "WA", 6: "TAS", 7: "NT", 8: "ACT"}


def km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def load_games():
    rows = []
    for y in YEARS:
        rows += json.loads((RAW / f"squiggle/games_{y}.json").read_text())["games"]
    g = pd.DataFrame(rows)
    g["final"] = g["is_final"] > 0
    g["margin"] = (g["hscore"] - g["ascore"]).abs()
    return g


def load_ladder(games):
    rows = []
    for y in YEARS:
        for s in json.loads((RAW / f"squiggle/standings_{y}.json").read_text())["standings"]:
            rows.append({"year": y, "team": s["name"], "rank": s["rank"], "wins": s["wins"],
                         "losses": s["losses"], "draws": s["draws"], "played": s["played"],
                         "percentage": round(s["percentage"], 1)})
    lad = pd.DataFrame(rows)
    gf = games[games["is_grand_final"] == 1][["year", "winner"]]
    lad["premier"] = lad.apply(lambda r: r["team"] == gf.set_index("year")["winner"].get(r["year"]), axis=1)
    finals = games[games["final"]]
    in_finals = set(zip(finals["year"], finals["hteam"])) | set(zip(finals["year"], finals["ateam"]))
    lad["made_finals"] = [(y, t) in in_finals for y, t in zip(lad["year"], lad["team"])]
    return lad.merge(TEAMS[["team", "abbr"]], on="team")


def team_results(games):
    """One row per team per game (both sides), from that team's point of view."""
    home = games.assign(team=games["hteam"], opp=games["ateam"], score=games["hscore"],
                        opp_score=games["ascore"], side="home")
    away = games.assign(team=games["ateam"], opp=games["hteam"], score=games["ascore"],
                        opp_score=games["hscore"], side="away")
    tr = pd.concat([home, away])[["year", "round", "final", "venue", "team", "opp", "score", "opp_score", "side"]]
    tr["win"] = (tr["score"] > tr["opp_score"]).astype(float)
    tr.loc[tr["score"] == tr["opp_score"], "win"] = 0.5  # a draw counts as half a win
    return tr


def main():
    games = load_games()
    matches = pd.read_csv(INTERIM / "afltables_matches.csv")
    venues = pd.read_csv(INTERIM / "venues.csv")
    teamgames = pd.read_csv(INTERIM / "afltables_teamgames.csv")
    pop = pd.read_csv(RAW / "abs/erp_state_2026Q1.csv")
    pop = pd.DataFrame({"state": pop["REGION"].map(ABS_REGION), "population": pop["OBS_VALUE"]})

    # teams.csv: club metadata used by every chart (colours, abbreviations)
    TEAMS.to_csv(OUT / "teams.csv", index=False)

    # ladder.csv: final home-and-away ladder each season (heatmap, bump, slope, bar)
    ladder = load_ladder(games)
    ladder.to_csv(OUT / "ladder.csv", index=False)

    tr = team_results(games)

    # head_to_head.csv: win % of each club against each opponent, all games 2012-2026
    h2h = tr.groupby(["team", "opp"]).agg(games=("win", "size"), wins=("win", "sum")).reset_index()
    h2h["win_pct"] = (100 * h2h["wins"] / h2h["games"]).round(1)
    # Order both axes by each club's overall win rate so the matrix reads best-to-worst.
    overall = tr.groupby("team")["win"].mean().sort_values(ascending=False)
    order = {t: i for i, t in enumerate(overall.index, start=1)}
    h2h["team_order"] = h2h["team"].map(order)
    h2h["opp_order"] = h2h["opp"].map(order)
    h2h.to_csv(OUT / "head_to_head.csv", index=False)

    # home_away.csv: home vs away win %, home-and-away season games only (dumbbell)
    ha = tr[~tr["final"]].groupby(["team", "side"]).agg(games=("win", "size"), wins=("win", "sum")).reset_index()
    ha["win_pct"] = (100 * ha["wins"] / ha["games"]).round(1)
    ha.to_csv(OUT / "home_away.csv", index=False)

    # margins.csv: winning margin of every game (ridgeline)
    games[["year", "margin"]].to_csv(OUT / "margins.csv", index=False)

    # travel_season.csv and travel_routes.csv: km travelled to each ground (scatter, flow map)
    vcoord = venues.set_index("venue")
    home = TEAMS.set_index("team")["home_venue"]
    am = matches.copy()
    am = pd.concat([am.assign(team=am["home"], side="home"), am.assign(team=am["away"], side="away")])
    am["km"] = [round(km(*vcoord.loc[home[t], ["lat", "lon"]], *vcoord.loc[v, ["lat", "lon"]]))
                for t, v in zip(am["team"], am["venue"])]
    am["round_trip_km"] = 2 * am["km"]
    routes = am.groupby(["year", "team", "venue"]).agg(games=("km", "size"), km=("km", "first")).reset_index()
    routes = routes.merge(venues[["venue", "lat", "lon", "state"]], on="venue")
    hv = TEAMS[["team", "home_venue"]].merge(venues[["venue", "lat", "lon"]], left_on="home_venue", right_on="venue")
    routes = routes.merge(hv[["team", "lat", "lon"]].rename(columns={"lat": "home_lat", "lon": "home_lon"}), on="team")
    routes.to_csv(OUT / "travel_routes.csv", index=False)

    away = tr[(tr["side"] == "away") & ~tr["final"]].groupby(["year", "team"])["win"].mean().mul(100).round(1)
    ts = am.groupby(["year", "team"])["round_trip_km"].sum().rename("km_travelled").reset_index()
    ts = ts.merge(away.rename("away_win_pct").reset_index(), on=["year", "team"]).merge(TEAMS[["team", "state"]], on="team")
    ts["interstate_club"] = ts["state"] != "VIC"
    ts.to_csv(OUT / "travel_season.csv", index=False)

    # venue_season.csv: crowds per ground per season (proportional symbol map)
    vs = matches.groupby(["year", "venue"]).agg(games=("attendance", "size"), total_crowd=("attendance", "sum"),
                                                avg_crowd=("attendance", "mean")).reset_index()
    vs["avg_crowd"] = vs["avg_crowd"].round(0)  # mean ignores crowd-less games (NaN)
    vs = vs.merge(venues, on="venue")
    vs.to_csv(OUT / "venue_season.csv", index=False)

    # attendance_season.csv: league crowds per season (line chart)
    att = matches.groupby("year").agg(games=("attendance", "size"), total_crowd=("attendance", "sum"),
                                      avg_crowd=("attendance", "mean"),
                                      no_crowd_games=("attendance", lambda s: int(s.isna().sum()))).reset_index()
    att["avg_crowd"] = att["avg_crowd"].round(0)
    att.to_csv(OUT / "attendance_season.csv", index=False)

    # state_footy.csv: 2026 crowds per resident and club success by state (choropleth)
    m26 = matches[matches["year"] == 2026].merge(venues[["venue", "state"]], on="venue")
    st = m26.groupby("state").agg(games_2026=("attendance", "size"), crowd_2026=("attendance", "sum")).reset_index()
    st = pop.merge(st, on="state", how="left").fillna({"games_2026": 0, "crowd_2026": 0})
    st["crowd_per_100_residents"] = (100 * st["crowd_2026"] / st["population"]).round(1)
    club_state = TEAMS.set_index("team")["state"]
    st["clubs"] = st["state"].map(TEAMS["state"].value_counts()).fillna(0).astype(int)
    prem = ladder[ladder["premier"]]["team"].map(club_state).value_counts()
    st["premierships_2012_2026"] = st["state"].map(prem).fillna(0).astype(int)
    st["state_name"] = st["state"].map(STATE_NAMES)
    # Approximate label positions (inside each state; ACT is labelled offshore as it is tiny).
    label_pos = {"WA": (-25.5, 121.5), "NT": (-19.5, 133.5), "SA": (-29.5, 135.3), "QLD": (-22.5, 144.5),
                 "NSW": (-32.3, 146.5), "VIC": (-36.9, 144.0), "TAS": (-42.1, 146.6), "ACT": (-36.0, 152.6)}
    st["label_lat"] = st["state"].map(lambda k: label_pos[k][0])
    st["label_lon"] = st["state"].map(lambda k: label_pos[k][1])
    st.to_csv(OUT / "state_footy.csv", index=False)

    # team_profiles.csv: average per game of key stats per club per season (parallel coords, radar)
    stats = {"IF_for": "inside_50s", "CL_for": "clearances", "CP_for": "contested_possessions",
             "TK_for": "tackles", "MK_for": "marks", "KI_for": "kicks", "HB_for": "handballs",
             "MI_for": "marks_inside_50", "RB_for": "rebound_50s", "GL_for": "goals"}
    tp = teamgames.groupby(["year", "team"])[list(stats)].mean().round(1).rename(columns=stats).reset_index()
    tp = tp.merge(ladder[["year", "team", "rank", "premier"]], on=["year", "team"])
    tp.to_csv(OUT / "team_profiles.csv", index=False)

    for f in sorted(OUT.glob("*.csv")):
        # Write booleans as 1/0 so Vega-Lite parses them reliably.
        df = pd.read_csv(f)
        df[df.select_dtypes("bool").columns] = df.select_dtypes("bool").astype(int)
        df.to_csv(f, index=False)
        print(f"{f.name:28s} {f.stat().st_size / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
