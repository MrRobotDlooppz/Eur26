/* ============================================
   Nav Links — Configuracion centralizada
   ============================================ */

(() => {
  "use strict";

  const LINKS = [
    { href: "index.html", label: "🎧 Audio" },
    { href: "mapa.html", label: "🗺️ Mapa" },
    { href: "timeline.html", label: "⏳ Timeline" },
    { href: "vitacora.html", label: "📝 Bitácora" },
  ];

  function getCurrentPage() {
    const file = window.location.pathname.split("/").pop();
    return file && file.length > 0 ? file : "index.html";
  }

  function renderLinks(container, currentPage) {
    container.innerHTML = "";
    for (const item of LINKS) {
      const a = document.createElement("a");
      a.href = item.href;
      a.textContent = item.label;
      if (item.href === currentPage) {
        a.classList.add("active");
      }
      container.appendChild(a);
    }
  }

  function initNavLinks() {
    const nav = document.querySelector("nav");
    if (!nav) return;

    const currentPage = getCurrentPage();
    const linksContainer = nav.querySelector(".links") || nav;

    renderLinks(linksContainer, currentPage);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initNavLinks);
  } else {
    initNavLinks();
  }
})();
