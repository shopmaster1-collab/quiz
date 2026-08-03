/**
 * SECCIÓN: MASTER QUIZ WIDGET
 * FUNCIÓN: Renderiza el cuestionario, comunica con FastAPI y muestra resultados.
 */
(() => {
  "use strict";

  /* SECCIÓN: WIDGET CONFIG — Lee parámetros desde la etiqueta <script>. */
  const scriptTag = document.currentScript;
  const apiBase = (scriptTag?.dataset.apiBase || "").replace(/\/$/, "");
  const containerId = scriptTag?.dataset.containerId || "master-sensor-quiz";
  const container = document.getElementById(containerId);

  if (!container) {
    console.error(`[MASTER QUIZ · CONFIG] No existe el contenedor #${containerId}.`);
    return;
  }

  /* SECCIÓN: WIDGET STATE — Conserva sesión y pregunta activa en memoria. */
  const state = {
    sessionId: null,
    progressStep: 1,
    totalSteps: 5,
    currentQuestion: null,
    busy: false,
  };

  /* SECCIÓN: API HELPER — Unifica llamadas y manejo de errores HTTP. */
  async function apiRequest(path, options = {}) {
    const response = await fetch(`${apiBase}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || "No fue posible completar la solicitud.");
    }
    return payload;
  }

  /* SECCIÓN: HTML ESCAPE — Evita insertar texto peligroso en la interfaz. */
  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  /* SECCIÓN: SHELL TEMPLATE — Construye el marco visual compartido. */
  function shell(content) {
    const progress = Array.from({ length: state.totalSteps }, (_, index) => {
      const active = index + 1 <= state.progressStep ? "is-active" : "";
      return `<span class="master-progress__step ${active}"></span>`;
    }).join("");

    return `
      <section class="master-quiz-shell">
        <header class="master-quiz-header">
          <h1>Encuentra tu sensor</h1>
          <p>Responde algunas preguntas y conoce la solución más compatible.</p>
        </header>

        <div class="master-progress" aria-label="Avance del diagnóstico">
          ${progress}
        </div>

        ${content}
      </section>
    `;
  }

  /* SECCIÓN: STATUS RENDER — Informa carga sin dejar la página vacía. */
  function renderStatus(message) {
    container.innerHTML = shell(
      `<div class="master-status" role="status">${escapeHtml(message)}</div>`
    );
  }

  /* SECCIÓN: ERROR RENDER — Muestra un problema recuperable. */
  function renderError(error) {
    container.innerHTML = shell(`
      <div class="master-error" role="alert">
        <strong>No pudimos continuar.</strong><br>
        ${escapeHtml(error.message)}
      </div>
      <div class="master-actions">
        <button class="master-button" data-action="restart">Reiniciar diagnóstico</button>
      </div>
    `);

    container.querySelector('[data-action="restart"]')?.addEventListener("click", startQuiz);
  }

  /* SECCIÓN: QUESTION RENDER — Dibuja pregunta y opciones desde la base. */
  function renderQuestion(question) {
    state.currentQuestion = question;

    const options = question.options.map((option) => `
      <button
        type="button"
        class="master-option"
        data-answer="${escapeHtml(option.value)}"
      >
        <span class="master-option__icon" aria-hidden="true">${escapeHtml(option.icon || "•")}</span>
        <span>${escapeHtml(option.label)}</span>
      </button>
    `).join("");

    container.innerHTML = shell(`
      <article class="master-question-card">
        <h2>${escapeHtml(question.title)}</h2>
        <p>${escapeHtml(question.help_text || "")}</p>
        <div class="master-option-grid">
          ${options}
        </div>
      </article>
    `);

    container.querySelectorAll("[data-answer]").forEach((button) => {
      button.addEventListener("click", () => submitAnswer(button.dataset.answer));
    });
  }

  /* SECCIÓN: QUIZ START — Crea una nueva sesión pública. */
  async function startQuiz() {
    if (state.busy) return;
    state.busy = true;
    renderStatus("Preparando tu diagnóstico…");

    try {
      const data = await apiRequest("/api/v1/quiz/start", { method: "POST" });
      state.sessionId = data.session_id;
      state.progressStep = data.progress_step;
      state.totalSteps = data.total_steps;
      renderQuestion(data.question);
    } catch (error) {
      renderError(error);
    } finally {
      state.busy = false;
    }
  }

  /* SECCIÓN: ANSWER SUBMIT — Guarda respuesta y solicita siguiente pregunta. */
  async function submitAnswer(answer) {
    if (state.busy || !state.currentQuestion) return;
    state.busy = true;
    renderStatus("Guardando tu respuesta…");

    try {
      const data = await apiRequest("/api/v1/quiz/answer", {
        method: "POST",
        body: JSON.stringify({
          session_id: state.sessionId,
          question_code: state.currentQuestion.code,
          answer,
        }),
      });

      state.progressStep = data.progress_step;
      state.totalSteps = data.total_steps;

      if (data.completed) {
        await loadResult();
      } else {
        renderQuestion(data.question);
      }
    } catch (error) {
      renderError(error);
    } finally {
      state.busy = false;
    }
  }

  /* SECCIÓN: PRODUCT ACTIONS — Crea enlaces válidos únicamente cuando existen. */
  function productActions(product, primary = false) {
    const actions = [];

    if (product.shopify_url) {
      actions.push(
        `<a class="master-button" href="${escapeHtml(product.shopify_url)}" target="_top">
          ${primary ? "Comprar producto" : "Ver alternativa"}
        </a>`
      );
    }

    if (product.youtube_url) {
      actions.push(
        `<a class="master-button master-button--secondary" href="${escapeHtml(product.youtube_url)}" target="_blank" rel="noopener">
          Ver video
        </a>`
      );
    }

    if (product.manual_url) {
      actions.push(
        `<a class="master-button master-button--secondary" href="${escapeHtml(product.manual_url)}" target="_blank" rel="noopener">
          Ver manual
        </a>`
      );
    }

    return actions.join("");
  }

  /* SECCIÓN: PRODUCT CARD — Presenta recomendación o alternativa. */
  function productCard(product, primary = false) {
    const image = product.image_url
      ? `<img src="${escapeHtml(product.image_url)}" alt="${escapeHtml(product.name)}" loading="lazy">`
      : `<div class="master-status">Imagen pendiente de configurar</div>`;

    const reasons = product.reasons
      .map((reason) => `<li>${escapeHtml(reason)}</li>`)
      .join("");

    return `
      <article class="master-product-card">
        <div>${image}</div>
        <div>
          <div><strong>${primary ? "RECOMENDACIÓN PRINCIPAL" : "ALTERNATIVA"}</strong></div>
          <h${primary ? "2" : "3"}>${escapeHtml(product.name)}</h${primary ? "2" : "3"}>
          <p>${escapeHtml(product.short_description || "")}</p>
          <ul class="master-reasons">${reasons}</ul>
          <div class="master-actions">${productActions(product, primary)}</div>
        </div>
      </article>
    `;
  }

  /* SECCIÓN: RESULT LOAD — Solicita el motor de reglas y la redacción DeepSeek. */
  async function loadResult() {
    renderStatus("Analizando tus necesidades…");
    const result = await apiRequest(`/api/v1/quiz/${state.sessionId}/result`);

    const alternatives = result.alternatives
      .map((product) => productCard(product, false))
      .join("");

    container.innerHTML = shell(`
      <section class="master-result-summary">
        <h2>Tu diagnóstico</h2>
        <p>${escapeHtml(result.profile_summary)}</p>
      </section>

      ${productCard(result.primary_product, true)}

      ${alternatives ? `<h2>Otras opciones compatibles</h2>${alternatives}` : ""}

      <section class="master-email-box">
        <h2>Recibe este diagnóstico por correo</h2>
        <p>El registro es opcional y no bloquea tu resultado.</p>

        <form id="master-email-form">
          <label>
            Correo electrónico
            <input type="email" name="email" required autocomplete="email">
          </label>

          <label class="master-consent">
            <input type="checkbox" name="consent_email" required>
            Acepto que se use mi correo para enviarme este diagnóstico.
          </label>

          <label class="master-consent">
            <input type="checkbox" name="consent_marketing">
            También deseo recibir información comercial de MASTER.
          </label>

          <button class="master-button" type="submit">Guardar mi correo</button>
        </form>

        <p id="master-email-message" role="status"></p>
      </section>

      <div class="master-actions">
        <button class="master-button master-button--secondary" data-action="restart">
          Repetir diagnóstico
        </button>
      </div>
    `);

    container.querySelector('[data-action="restart"]')?.addEventListener("click", startQuiz);
    container.querySelector("#master-email-form")?.addEventListener("submit", submitEmail);
  }

  /* SECCIÓN: EMAIL SUBMIT — Guarda consentimientos separados. */
  async function submitEmail(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const message = container.querySelector("#master-email-message");
    const formData = new FormData(form);

    try {
      const result = await apiRequest("/api/v1/quiz/email", {
        method: "POST",
        body: JSON.stringify({
          session_id: state.sessionId,
          email: formData.get("email"),
          consent_email: formData.get("consent_email") === "on",
          consent_marketing: formData.get("consent_marketing") === "on",
        }),
      });

      message.textContent = result.message;
      form.querySelector("button").disabled = true;
    } catch (error) {
      message.textContent = error.message;
    }
  }

  /* SECCIÓN: WIDGET BOOT — Inicia cuando el script termina de cargar. */
  startQuiz();
})();
