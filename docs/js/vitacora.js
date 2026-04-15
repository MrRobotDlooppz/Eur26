/* ============================================
   Bitácora — Lógica principal
   Auth (Firebase) + CRUD (Firestore)
   ============================================ */

(() => {
  "use strict";

  // Ciudades disponibles (hardcodeadas para evitar fetch extra)
  const CIUDADES = ["Benalmádena", "Firenze", "Granada", "Lucca", "Madrid", "Málaga", "Pisa", "Roma", "Toledo"];

  // ── Referencias DOM ──
  const $loginSection  = document.getElementById("login-section");
  const $loginForm     = document.getElementById("login-form");
  const $loginEmail    = document.getElementById("login-email");
  const $loginPassword = document.getElementById("login-password");
  const $loginError    = document.getElementById("login-error");
  const $userBar       = document.getElementById("user-bar");
  const $userName      = document.getElementById("user-display-name");
  const $btnLogout     = document.getElementById("btn-logout");
  const $btnNewEntry   = document.getElementById("btn-new-entry");
  const $editorSection = document.getElementById("editor-section");
  const $editorTitle   = document.getElementById("editor-title");
  const $entryTitulo   = document.getElementById("entry-titulo");
  const $entryCiudad   = document.getElementById("entry-ciudad");
  const $entryLugar    = document.getElementById("entry-lugar");
  const $entryContenido = document.getElementById("entry-contenido");
  const $btnCancel     = document.getElementById("btn-cancel-entry");
  const $btnSave       = document.getElementById("btn-save-entry");
  const $filterCity    = document.getElementById("filter-city");
  const $entriesList   = document.getElementById("entries-list");
  const $btnToggleIndex = document.getElementById("btn-toggle-index");
  const $entryIndex    = document.getElementById("entry-index");

  let currentUser = null;
  let editingId = null; // null = nueva entrada, string = editando existente
  let cachedEntries = []; // last snapshot for re-render on auth change
  let unsubEntries = null; // onSnapshot unsubscribe function

  // ── Imágenes ──
  const MAX_IMAGES = 5;
  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB original
  const COMPRESS_MAX_WIDTH = 800;
  const COMPRESS_QUALITY = 0.6;
  let pendingImages = []; // [{id: 0, data: "data:image/jpeg;base64,..."}]

  const $btnInsertImage = document.getElementById("btn-insert-image");
  const $imageInput     = document.getElementById("image-input");
  const $imagePreviews  = document.getElementById("image-previews");
  const $imgCountHint   = document.getElementById("img-count-hint");

  // ── Poblar selects de ciudades ──
  function populateCitySelects() {
    CIUDADES.forEach(c => {
      const opt1 = new Option(c, c);
      const opt2 = new Option(c, c);
      $entryCiudad.appendChild(opt1);
      $filterCity.appendChild(opt2);
    });
  }

  // ── Auth: estado ──
  auth.onAuthStateChanged(user => {
    currentUser = user;
    if (user) {
      const name = getDisplayName(user);
      $loginSection.style.display = "none";
      $userBar.style.display = "flex";
      $userName.textContent = name;
      $btnNewEntry.style.display = "block";
      showEntriesSection(true);
      if (!unsubEntries) listenEntries();
    } else {
      $loginSection.style.display = "block";
      $userBar.style.display = "none";
      $btnNewEntry.style.display = "none";
      closeEditor();
      showEntriesSection(false);
      // Stop listener and clear cache
      if (unsubEntries) { unsubEntries(); unsubEntries = null; }
      cachedEntries = [];
      $entriesList.innerHTML = "";
      $entryIndex.innerHTML = "";
      if ($entryIndex.classList.contains("visible")) {
        $entryIndex.classList.remove("visible");
        $btnToggleIndex.textContent = "📑 Índice";
      }
    }
  });

  function showEntriesSection(show) {
    const d = show ? "" : "none";
    document.querySelector(".entries-header").style.display = show ? "flex" : "none";
    $entryIndex.style.display = show && $entryIndex.classList.contains("visible") ? "block" : "none";
    $entriesList.style.display = show ? "block" : "none";
  }

  // ── Auth: login ──
  $loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    $loginError.textContent = "";
    const email = $loginEmail.value.trim();
    const pass = $loginPassword.value;
    try {
      await auth.signInWithEmailAndPassword(email, pass);
    } catch (err) {
      const msgs = {
        "auth/user-not-found": "Usuario no encontrado",
        "auth/wrong-password": "Contraseña incorrecta",
        "auth/invalid-email": "Email inválido",
        "auth/too-many-requests": "Demasiados intentos. Esperá un momento.",
        "auth/invalid-credential": "Credenciales inválidas",
      };
      $loginError.textContent = msgs[err.code] || "Error al iniciar sesión";
    }
  });

  // ── Auth: logout ──
  $btnLogout.addEventListener("click", () => auth.signOut());

  // ── Imágenes: compresión ──
  function compressImage(file) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        URL.revokeObjectURL(url);
        let w = img.width, h = img.height;
        if (w > COMPRESS_MAX_WIDTH) {
          h = Math.round(h * COMPRESS_MAX_WIDTH / w);
          w = COMPRESS_MAX_WIDTH;
        }
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, w, h);
        resolve(canvas.toDataURL("image/jpeg", COMPRESS_QUALITY));
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("No se pudo leer la imagen"));
      };
      img.src = url;
    });
  }

  // ── Imágenes: insertar ──
  function updateImgCountHint() {
    $imgCountHint.textContent = pendingImages.length > 0
      ? `${pendingImages.length}/${MAX_IMAGES}`
      : "";
  }

  function renderImagePreviews() {
    $imagePreviews.innerHTML = pendingImages.map((img, i) =>
      `<div class="img-preview-item" data-idx="${i}">
        <img src="${img.data}" alt="Preview ${i}">
        <button class="img-preview-remove" data-idx="${i}" title="Quitar imagen">✕</button>
        <span class="img-preview-tag">[img:${img.id}]</span>
      </div>`
    ).join("");

    $imagePreviews.querySelectorAll(".img-preview-remove").forEach(btn => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.dataset.idx, 10);
        removeImage(idx);
      });
    });

    updateImgCountHint();
  }

  function removeImage(idx) {
    const removed = pendingImages[idx];
    if (!removed) return;
    // Remove marker from textarea
    const marker = `[img:${removed.id}]`;
    $entryContenido.value = $entryContenido.value.split(marker).join("");
    pendingImages.splice(idx, 1);
    renderImagePreviews();
  }

  function getNextImageId() {
    if (pendingImages.length === 0) return 0;
    return Math.max(...pendingImages.map(i => i.id)) + 1;
  }

  $btnInsertImage.addEventListener("click", () => {
    if (pendingImages.length >= MAX_IMAGES) {
      alert(`Máximo ${MAX_IMAGES} imágenes por entrada`);
      return;
    }
    $imageInput.value = "";
    $imageInput.click();
  });

  $imageInput.addEventListener("change", async () => {
    const file = $imageInput.files[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      alert("Solo se permiten archivos de imagen");
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      alert("La imagen es demasiado grande (máx 5MB)");
      return;
    }
    if (pendingImages.length >= MAX_IMAGES) {
      alert(`Máximo ${MAX_IMAGES} imágenes por entrada`);
      return;
    }

    $btnInsertImage.disabled = true;
    $btnInsertImage.textContent = "⏳ Procesando…";
    try {
      const dataUrl = await compressImage(file);
      const id = getNextImageId();
      pendingImages.push({ id, data: dataUrl });

      // Insert marker at cursor position in textarea
      const pos = $entryContenido.selectionStart || $entryContenido.value.length;
      const text = $entryContenido.value;
      const marker = `[img:${id}]`;
      $entryContenido.value = text.slice(0, pos) + marker + text.slice(pos);
      $entryContenido.focus();
      $entryContenido.selectionStart = $entryContenido.selectionEnd = pos + marker.length;

      renderImagePreviews();
    } catch (err) {
      console.error("Error al procesar imagen:", err);
      alert("Error al procesar la imagen");
    } finally {
      $btnInsertImage.disabled = false;
      $btnInsertImage.textContent = "📷 Imagen";
    }
  });

  // ── Editor: abrir/cerrar ──
  function openEditor(entry = null) {
    editingId = entry ? entry.id : null;
    $editorTitle.textContent = entry ? "Editar entrada" : "Nueva entrada";
    $entryTitulo.value = entry ? entry.titulo : "";
    $entryCiudad.value = entry ? (entry.ciudad || "") : "";
    $entryLugar.value = entry ? (entry.lugar || "") : "";
    $entryContenido.value = entry ? entry.contenido : "";
    // Load existing images if editing
    pendingImages = entry && entry.imagenes ? entry.imagenes.map(img => ({ ...img })) : [];
    renderImagePreviews();
    $editorSection.classList.add("visible");
    $entryTitulo.focus();
  }

  function closeEditor() {
    editingId = null;
    $editorSection.classList.remove("visible");
    $entryTitulo.value = "";
    $entryCiudad.value = "";
    $entryLugar.value = "";
    $entryContenido.value = "";
    pendingImages = [];
    renderImagePreviews();
  }

  $btnNewEntry.addEventListener("click", () => openEditor());
  $btnCancel.addEventListener("click", closeEditor);

  // ── Editor: guardar ──
  $btnSave.addEventListener("click", async () => {
    const titulo = $entryTitulo.value.trim();
    const contenido = $entryContenido.value.trim();
    if (!titulo || !contenido) {
      alert("Título y contenido son obligatorios");
      return;
    }

    const name = getDisplayName(currentUser);
    const data = {
      titulo,
      contenido,
      ciudad: $entryCiudad.value || null,
      lugar: $entryLugar.value.trim() || null,
      imagenes: pendingImages.length > 0 ? pendingImages : null,
      editadoEn: firebase.firestore.FieldValue.serverTimestamp(),
      editadoPor: name,
    };

    $btnSave.disabled = true;
    $btnSave.textContent = "Guardando…";

    try {
      if (editingId) {
        await db.collection("vitacora").doc(editingId).update(data);
      } else {
        data.autor = name;
        data.autorUid = currentUser.uid;
        data.creadoEn = firebase.firestore.FieldValue.serverTimestamp();
        await db.collection("vitacora").add(data);
      }
      closeEditor();
    } catch (err) {
      console.error("Error al guardar:", err);
      alert("Error al guardar la entrada. Revisá la consola.");
    } finally {
      $btnSave.disabled = false;
      $btnSave.textContent = "Guardar";
    }
  });

  // ── Entradas: listener en tiempo real ──
  function listenEntries() {
    unsubEntries = db.collection("vitacora")
      .orderBy("creadoEn", "desc")
      .onSnapshot(snapshot => {
        renderEntries(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      }, err => {
        console.error("Error cargando entradas:", err);
        $entriesList.innerHTML = `<div class="empty-state">Error al cargar entradas. ¿Configuraste Firebase?</div>`;
      });
  }

  // ── Entradas: renderizar ──
  function renderEntries(entries) {
    cachedEntries = entries;
    const filterCity = $filterCity.value;
    const filtered = filterCity
      ? entries.filter(e => e.ciudad === filterCity)
      : entries;

    if (filtered.length === 0) {
      $entriesList.innerHTML = `<div class="empty-state">No hay entradas${filterCity ? " para " + filterCity : ""}.</div>`;
      return;
    }

    $entriesList.innerHTML = filtered.map(e => {
      const fecha = e.creadoEn ? formatTimestamp(e.creadoEn) : "";
      const editado = e.editadoEn && e.editadoPor && e.editadoPor !== e.autor
        ? `<span class="entry-edited">editado por ${escapeHtml(e.editadoPor)}</span>`
        : "";
      const badge = e.ciudad
        ? `<span class="entry-badge">${escapeHtml(e.ciudad)}${e.lugar ? " · " + escapeHtml(e.lugar) : ""}</span>`
        : "";
      const canEdit = currentUser && (currentUser.uid === e.autorUid);
      const actions = canEdit
        ? `<div class="entry-actions">
             <button class="btn-edit" data-id="${e.id}">✏️ Editar</button>
             <button class="btn-delete" data-id="${e.id}">🗑️ Eliminar</button>
           </div>`
        : "";

      return `
        <div class="entry-card" data-entry-id="${e.id}">
          <div class="entry-meta">
            <span class="entry-author">${escapeHtml(e.autor || "Anónimo")}</span>
            <span class="entry-date">${fecha}</span>
            ${badge}
            ${editado}
          </div>
          <div class="entry-title">${escapeHtml(e.titulo)}</div>
          <div class="entry-content">${renderContentWithImages(e.contenido, e.imagenes)}</div>
          ${actions}
        </div>`;
    }).join("");

    // Event delegation para edit/delete
    $entriesList.querySelectorAll(".btn-edit").forEach(btn => {
      btn.addEventListener("click", () => {
        const entry = entries.find(e => e.id === btn.dataset.id);
        if (entry) openEditor(entry);
      });
    });

    $entriesList.querySelectorAll(".btn-delete").forEach(btn => {
      btn.addEventListener("click", async () => {
        if (!confirm("¿Eliminar esta entrada?")) return;
        try {
          await db.collection("vitacora").doc(btn.dataset.id).delete();
        } catch (err) {
          console.error("Error al eliminar:", err);
          alert("Error al eliminar.");
        }
      });
    });
  }

  // ── Filtro por ciudad ──
  $filterCity.addEventListener("change", () => {
    // Re-render with cached data (no extra Firestore read)
    if (cachedEntries.length > 0) renderEntries(cachedEntries);
  });

  // ── Índice de entradas ──
  $btnToggleIndex.addEventListener("click", () => {
    const visible = $entryIndex.classList.toggle("visible");
    $btnToggleIndex.textContent = visible ? "📑 Ocultar" : "📑 Índice";
    if (visible && cachedEntries.length > 0) renderIndex(cachedEntries);
  });

  function renderIndex(entries) {
    // Group by city (null → "Sin ciudad")
    const groups = {};
    entries.forEach(e => {
      const city = e.ciudad || "Sin ciudad";
      if (!groups[city]) groups[city] = [];
      groups[city].push(e);
    });

    const cities = Object.keys(groups).sort((a, b) => {
      if (a === "Sin ciudad") return 1;
      if (b === "Sin ciudad") return -1;
      return a.localeCompare(b);
    });

    $entryIndex.innerHTML = cities.map(city => {
      const items = groups[city].map(e => {
        const fecha = e.creadoEn ? formatTimestamp(e.creadoEn).split(" ")[0] : "";
        return `<li class="index-item" data-id="${e.id}">
          <span class="index-title">${escapeHtml(e.titulo)}</span>
          <span class="index-meta">${escapeHtml(e.autor || "")} · ${fecha}</span>
        </li>`;
      }).join("");
      return `<div class="index-group">
        <h4 class="index-city">${escapeHtml(city)}</h4>
        <ul class="index-list">${items}</ul>
      </div>`;
    }).join("");

    // Click to scroll to entry card
    $entryIndex.querySelectorAll(".index-item").forEach(li => {
      li.addEventListener("click", () => {
        const id = li.dataset.id;
        const entryCard = $entriesList.querySelector(`.entry-card[data-entry-id="${id}"]`);
        if (entryCard) {
          entryCard.scrollIntoView({ behavior: "smooth", block: "center" });
          entryCard.classList.add("highlight");
          setTimeout(() => entryCard.classList.remove("highlight"), 1500);
        }
      });
    });
  }

  // ── Helpers ──

  /** Render entry content replacing [img:N] markers with actual images */
  function renderContentWithImages(contenido, imagenes) {
    let html = escapeHtml(contenido);
    if (imagenes && imagenes.length > 0) {
      const imgMap = {};
      imagenes.forEach(img => { imgMap[img.id] = img.data; });
      html = html.replace(/\[img:(\d+)\]/g, (match, idStr) => {
        const src = imgMap[parseInt(idStr, 10)];
        if (src) {
          return `<img class="entry-image" src="${src}" alt="Imagen adjunta" loading="lazy">`;
        }
        return match;
      });
    }
    return html;
  }

  /** Lightbox — click on entry images to view fullscreen */
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("entry-image")) {
      const overlay = document.createElement("div");
      overlay.className = "lightbox-overlay";
      overlay.innerHTML = `<img src="${e.target.src}" alt="Imagen ampliada">`;
      overlay.addEventListener("click", () => overlay.remove());
      document.body.appendChild(overlay);
    }
  });

  function formatTimestamp(ts) {
    if (!ts || !ts.toDate) return "";
    const d = ts.toDate();
    const day = String(d.getDate()).padStart(2, "0");
    const mon = String(d.getMonth() + 1).padStart(2, "0");
    const year = d.getFullYear();
    const h = String(d.getHours()).padStart(2, "0");
    const m = String(d.getMinutes()).padStart(2, "0");
    return `${day}/${mon}/${year} ${h}:${m}`;
  }

  function escapeHtml(str) {
    const el = document.createElement("span");
    el.textContent = str;
    return el.innerHTML;
  }

  // ── Init ──
  populateCitySelects();
  // listenEntries() se llama desde onAuthStateChanged al autenticarse

})();
