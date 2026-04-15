/* ============================================
   Timeline — Lógica de la línea de tiempo
   + Links a guías
   ============================================ */

async function initTimeline() {
  let EVENTS, CITIES;
  try {
    const resp = await fetch("data/events.json");
    const data = await resp.json();
    EVENTS = data.events;
    EVENTS.sort((a, b) => a.year - b.year);
    CITIES = data.city_colors;
  } catch (e) {
    console.error("Error cargando events.json:", e);
    document.getElementById("timeline").innerHTML = "<p style='padding:40px;text-align:center;color:#8b8fa3'>Error cargando datos</p>";
    return;
  }

  let activeFilter = null;

  function formatYear(y) {
    return y < 0 ? Math.abs(y) + " a.C." : y + " d.C.";
  }

  function render(filter) {
    const container = document.getElementById("timeline");
    const events = filter ? EVENTS.filter(e => e.city === filter) : EVENTS;
    let html = "";
    let lastEra = "";
    events.forEach(ev => {
      if (ev.era !== lastEra) {
        html += `<div class="era-label">${ev.era}</div>`;
        lastEra = ev.era;
      }
      // Link al nombre si tiene guía
      let nameHtml = ev.name;
      if (ev.guide) {
        const guideSlug = ev.guide_slug || slugify(ev.name);
        const folder = ev.folder || ev.city;
        nameHtml = `<a href="index.html?city=${encodeURIComponent(folder)}&track=${encodeURIComponent(guideSlug)}&guide=1">${ev.name}</a>`;
      }
      html += `<div class="event" data-city="${ev.city}">
        <div class="event-card">
          <div class="event-year" style="color:${ev.color}">${formatYear(ev.year)}</div>
          <div class="event-name">${nameHtml}</div>
          <div class="event-desc">${ev.desc}</div>
          <div class="event-city" style="color:${ev.color}">${ev.city}</div>
        </div>
      </div>`;
    });
    container.innerHTML = html;
  }

  // Inject dynamic dot color CSS
  const styleEl = document.createElement("style");
  styleEl.textContent = Object.entries(CITIES).map(([city, color]) =>
    `.event[data-city="${city}"]::before { background: ${color}; }`
  ).join("\n");
  document.head.appendChild(styleEl);

  // Update stats
  const statsEl = document.getElementById("stats");
  if (statsEl) {
    const years = EVENTS.map(e => e.year);
    const minY = Math.min(...years);
    const maxY = Math.max(...years);
    const formatY = y => y < 0 ? Math.abs(y) + " a.C." : y + " d.C.";
    statsEl.innerHTML = `<strong>${EVENTS.length}</strong> lugares · <strong>${formatY(minY)} — ${formatY(maxY)}</strong> de historia · <strong>${Object.keys(CITIES).length}</strong> ciudades`;
  }

  // Filters
  const filtersDiv = document.getElementById("filters");
  const allBtn = document.createElement("button");
  allBtn.className = "filter-btn active";
  allBtn.textContent = "Todas";
  allBtn.addEventListener("click", () => {
    activeFilter = null;
    render(null);
    filtersDiv.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    allBtn.classList.add("active");
  });
  filtersDiv.appendChild(allBtn);

  Object.entries(CITIES).forEach(([city, color]) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.innerHTML = `<span style="color:${color}">●</span> ${city}`;
    btn.addEventListener("click", () => {
      activeFilter = city;
      render(city);
      filtersDiv.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
    filtersDiv.appendChild(btn);
  });

  render(null);
}

initTimeline();
