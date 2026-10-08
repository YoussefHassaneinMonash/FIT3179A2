// Embeds every chart. Each spec lives in its own human-readable file in js/specs/.
// The shared theme below keeps fonts and colours consistent across all charts.

const theme = {
  background: null,
  font: "Source Sans 3, sans-serif",
  view: { stroke: null },
  title: { font: "Barlow Condensed, sans-serif", fontSize: 18, fontWeight: 600, color: "#1c1b19", anchor: "start" },
  axis: {
    labelFont: "Source Sans 3, sans-serif", labelFontSize: 12, labelColor: "#55524b",
    titleFont: "Source Sans 3, sans-serif", titleFontSize: 12, titleFontWeight: 600, titleColor: "#55524b",
    domainColor: "#bdb8ab", tickColor: "#bdb8ab", gridColor: "#e6e2d8"
  },
  legend: {
    labelFont: "Source Sans 3, sans-serif", labelFontSize: 12, labelColor: "#55524b",
    titleFont: "Source Sans 3, sans-serif", titleFontSize: 12, titleFontWeight: 600, titleColor: "#55524b"
  },
  text: { font: "Source Sans 3, sans-serif", fontSize: 12, color: "#1c1b19" }
};

const charts = [
  ["#vis-ladder-heatmap", "js/specs/01_ladder_heatmap.vg.json"],
  ["#vis-bump", "js/specs/02_bump_chart.vg.json"],
  ["#vis-wins-bar", "js/specs/03_total_wins_bar.vg.json"],
  ["#vis-venue-map", "js/specs/04_venue_symbol_map.vg.json"],
  ["#vis-state-map", "js/specs/05_state_choropleth.vg.json"],
  ["#vis-flow-map", "js/specs/06_travel_flow_map.vg.json"],
  ["#vis-home-away", "js/specs/07_home_away_dumbbell.vg.json"],
  ["#vis-travel-scatter", "js/specs/08_travel_scatter.vg.json"],
  ["#vis-parallel", "js/specs/09_parallel_coordinates.vg.json"],
  ["#vis-radar", "js/specs/10_radar.vg.json"],
  ["#vis-h2h", "js/specs/11_head_to_head_matrix.vg.json"],
  ["#vis-ridgeline", "js/specs/12_margin_ridgeline.vg.json"],
  ["#vis-slope", "js/specs/13_ladder_slope.vg.json"],
  ["#vis-attendance", "js/specs/14_attendance_line.vg.json"]
];

for (const [el, spec] of charts) {
  if (!document.querySelector(el)) continue;
  vegaEmbed(el, spec, { actions: false, renderer: "svg", config: theme })
    .catch(err => console.error(`Chart ${spec} failed:`, err));
}
