/* ============================================
   Nav Links — Navegación centralizada
   --------------------------------------------
   Fuente única de verdad para los links de nav.
   Cada HTML solo necesita:
     <nav>
       <h1>Título</h1>
       <div class="links"></div>
     </nav>
   y cargar este script. No poner links a mano.
   
   Para agregar una página nueva:
     1. Agregar entrada en LINKS abajo.
     2. Crear el HTML con la estructura <nav> de arriba.
     3. Incluir <script src="js/nav-links.js"></script>.
     No hay que tocar los otros HTML.
   ============================================ */

(() => {
  "use strict";

  const LINKS = [
    { href: "index.html",    label: "🎧 Audio" },
    { href: "mapa.html",     label: "🗺️ Mapa" },
    { href: "timeline.html", label: "⏳ Timeline" },
    { href: "vitacora.html", label: "📝 Bitácora" },
  ];

  function getCurrentPage() {
    // Extraer solo el nombre del archivo, ignorando query params y hash
    const raw = window.location.pathname.split("/").pop() || "";
    const file = raw.split("?")[0].split("#")[0];
    return file.length > 0 ? file : "index.html";
  }

  function renderLinks(container, currentPage) {
    container.innerHTML = "";
    for (const item of LINKS) {
      const a = document.createElement("a");
      a.href = item.href;
      a.textContent = item.label;
      if (item.href === currentPage) {
        a.classList.add("active");
        a.setAttribute("aria-current", "page");
      }
      container.appendChild(a);
    }
  }

  function initNavLinks() {
    const nav = document.querySelector("nav");
    if (!nav) return;

    const linksContainer = nav.querySelector(".links");
    if (!linksContainer) return;

    renderLinks(linksContainer, getCurrentPage());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initNavLinks);
  } else {
    initNavLinks();
  }
})();
