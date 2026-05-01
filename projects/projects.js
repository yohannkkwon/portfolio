import { fetchJSON, renderProjects } from '../global.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7.9.0/+esm';

// Fetch all project data
const projects = await fetchJSON('../lib/projects.json');
const projectsContainer = document.querySelector('.projects');

// Update heading with count
const projectsTitle = document.querySelector('.projects-title');
if (projectsTitle) {
  projectsTitle.textContent = `${projects.length} Projects`;
}

// D3 arc generator
let arcGenerator = d3.arc().innerRadius(0).outerRadius(50);
let colors = d3.scaleOrdinal(d3.schemeTableau10);

// ── State ──────────────────────────────────────────────────────────────────
// We track the selected *year label* (not index) so selection stays stable
// when the pie re-renders after a search query changes the slice count.
// This gives us the extra-credit combined filter for free.
let query = '';
let selectedYear = null;

// ── Pie chart renderer ─────────────────────────────────────────────────────
function renderPieChart(projectsGiven) {
  // Roll up projects by year
  let rolledData = d3.rollups(
    projectsGiven,
    (v) => v.length,
    (d) => d.year,
  );

  let data = rolledData.map(([year, count]) => ({
    value: count,
    label: year,
  }));

  // Re-find the selected index from the stable selectedYear value
  let selectedIndex = selectedYear
    ? data.findIndex((d) => String(d.label) === String(selectedYear))
    : -1;

  // Generate arc paths
  let sliceGenerator = d3.pie().value((d) => d.value);
  let arcData = sliceGenerator(data);
  let arcs = arcData.map((d) => arcGenerator(d));

  // Clear previous chart
  let svg = d3.select('#projects-pie-plot');
  svg.selectAll('path').remove();

  let legend = d3.select('.legend');
  legend.selectAll('li').remove();

  // Draw wedges
  arcs.forEach((arc, i) => {
    svg
      .append('path')
      .attr('d', arc)
      .attr('fill', colors(i))
      .attr('class', i === selectedIndex ? 'selected' : '')
      .on('click', () => {
        // Toggle: clicking the same year deselects; clicking another selects it
        selectedYear =
          selectedYear === String(data[i].label) ? null : String(data[i].label);
        update();
      });
  });

  // Draw legend items
  data.forEach((d, idx) => {
    legend
      .append('li')
      .attr('class', idx === selectedIndex ? 'legend-item selected' : 'legend-item')
      .attr('style', `--color:${colors(idx)}`)
      .html(`<span class="swatch"></span> ${d.label} <em>(${d.value})</em>`);
  });
}

// ── Central update function ────────────────────────────────────────────────
// Applies both filters (query + selectedYear) and re-renders everything.
// This is what makes the extra-credit combined filtering work: both the
// search handler and the pie click handler call update(), which always
// considers both pieces of state together.
function update() {
  // 1. Filter by search query across all project fields
  let queryFiltered = projects.filter((project) => {
    let values = Object.values(project).join('\n').toLowerCase();
    return values.includes(query.toLowerCase());
  });

  // 2. Re-render pie from query-filtered set (so slice sizes reflect search)
  renderPieChart(queryFiltered);

  // 3. Additionally filter by selected year on top of the query filter
  let display = queryFiltered;
  if (selectedYear) {
    display = display.filter((p) => String(p.year) === selectedYear);
  }

  // 4. Render project cards
  renderProjects(display, projectsContainer, 'h2');
}

// ── Initial render ─────────────────────────────────────────────────────────
update();

// ── Search bar ─────────────────────────────────────────────────────────────
let searchInput = document.querySelector('.searchBar');
searchInput.addEventListener('input', (event) => {
  query = event.target.value;
  update();
});
