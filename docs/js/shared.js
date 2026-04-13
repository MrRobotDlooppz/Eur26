/* ============================================
   Shared — Utilidades comunes
   ============================================ */

/**
 * Formatea segundos a mm:ss
 */
function fmtTime(s) {
  if (isNaN(s) || s < 0) return "0:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return m + ":" + String(sec).padStart(2, "0");
}

/**
 * Parsea query params de la URL
 */
function getQueryParams() {
  const params = {};
  new URLSearchParams(window.location.search).forEach((v, k) => { params[k] = v; });
  return params;
}

/**
 * Genera un slug a partir de un nombre (para matching de guías)
 * "Torre Guinigi" → "torre_guinigi"
 */
function slugify(name) {
  return name
    .toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}
