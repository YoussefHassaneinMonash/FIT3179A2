# Data Sources

All data was accessed on **7 October 2026**. Seasons covered: **2012–2026** (AFL men's competition).

## 1. Squiggle API: match results and ladders
- **Author:** Max Barry (Squiggle)
- **Home / docs:** https://api.squiggle.com.au
- **Used for:** match results, home/away teams, scores and the final home-and-away ladder each season.
- **Requests made** (repeated for each year 2012–2026):
  - Games: https://api.squiggle.com.au/?q=games;year=2026
  - Ladder: https://api.squiggle.com.au/?q=standings;year=2026
  - Teams: https://api.squiggle.com.au/?q=teams
- **Saved to:** `data/raw/squiggle/`

## 2. AFL Tables: crowds, venues and team statistics
- **Author:** Paul Jones (AFL Tables)
- **Home:** https://afltables.com/afl/afl_index.html
- **Season results pages** give scores by quarter, attendance and venue for every match:
  - https://afltables.com/afl/seas/2026.html (one page per year, `seas/2012.html` … `seas/2026.html`)
- **Team statistics pages** give per-game kicks, marks, handballs, tackles, inside 50s, clearances, contested possessions and more:
  - https://afltables.com/afl/stats/2026t.html (one page per year, `stats/2012t.html` … `stats/2026t.html`)
- **Saved to:** `data/raw/afltables/`. Parsed by `scripts/parse_afltables.py` into:
  - `data/interim/afltables_matches.csv`
  - `data/interim/afltables_teamgames.csv`

## 3. Australian Bureau of Statistics: state population
- **Author:** Australian Bureau of Statistics (ABS)
- **Dataset:** National, state and territory population, Estimated Resident Population, March quarter 2026
  - Release page: https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population
- **API request** (ABS Data API, dataflow `ERP_Q`):
  - https://data.api.abs.gov.au/rest/data/ABS,ERP_Q,1.0.0/1.3.TOT.1+2+3+4+5+6+7+8.Q?startPeriod=2026-Q1&endPeriod=2026-Q1
- **Licence:** CC BY 4.0
- **Saved to:** `data/raw/abs/erp_state_2026Q1.csv`

## 4. Wikipedia: venue coordinates
- **Author:** Wikipedia contributors
- **API request** (latitude/longitude of each ground's article):
  - https://en.wikipedia.org/w/api.php?action=query&prop=coordinates&colimit=max&titles=Melbourne%20Cricket%20Ground|Docklands%20Stadium|Adelaide%20Oval (the full list of 27 venues is in `data/interim/venues.csv`)
- **Licence:** CC BY-SA 4.0
- **Saved to:**
  - `data/raw/wikipedia/`
  - `data/interim/venues.csv` (with city and state added)

## 5. Australian state boundaries (map shapes)
- **Author:** Rowan Hogan (GitHub), derived from ABS boundary data
- **Repo:** https://github.com/rowanhogan/australian-states
- **File:** https://raw.githubusercontent.com/rowanhogan/australian-states/master/states.geojson
- **Saved to:** `data/raw/geo/aus_states.geojson`
- **To do:** we may replace this with the official ABS ASGS state boundaries before submission:
  - https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files

## Cross-checks
- Match counts per season are identical in Squiggle and AFL Tables.
- All 15 grand final scores (2012–2026) agree between the two sources.
- Team names match across sources.
