function csrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : "";
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast align-items-center text-bg-${type} border-0`;
  el.setAttribute("role", "alert");
  el.innerHTML =
    '<div class="d-flex"><div class="toast-body"></div>' +
    '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Schließen"></button></div>';
  el.querySelector(".toast-body").textContent = message;
  container.appendChild(el);
  el.addEventListener("hidden.bs.toast", () => el.remove());
  new bootstrap.Toast(el, { delay: 5000 }).show();
}

async function fetchJSON(url, { json, ...options } = {}) {
  const headers = {
    Accept: "application/json",
    "X-CSRFToken": csrfToken(),
    ...(options.headers || {}),
  };
  if (json !== undefined) {
    options.body = JSON.stringify(json);
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(url, { credentials: "same-origin", ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Etwas ist schiefgelaufen.");
  }
  return data;
}

function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function updateProgress() {
  const bar = document.getElementById("today-progress");
  if (!bar) return;
  const boxes = [...document.querySelectorAll('.habit-check[data-today="true"]')];
  const done = boxes.filter((box) => box.checked).length;
  const percent = boxes.length ? Math.round((done / boxes.length) * 100) : 0;
  bar.style.width = `${percent}%`;
  bar.parentElement.setAttribute("aria-valuenow", percent);
  document.getElementById("today-count").textContent = `${done} von ${boxes.length}`;
}

function initHabitChecks() {
  document.addEventListener("change", async (event) => {
    const box = event.target.closest(".habit-check");
    if (!box) return;

    box.disabled = true;
    try {
      const data = await fetchJSON(box.dataset.url, {
        method: "POST",
        json: { date: box.dataset.date, completed: box.checked },
      });

      if (box.dataset.reload) {
        location.reload();
        return;
      }

      const row = box.closest("[data-habit-row]");
      if (row) row.classList.toggle("habit-done", data.completed);

      const id = box.dataset.habitId;
      document.querySelectorAll(`[data-streak-for="${id}"]`).forEach((el) => {
        el.textContent = data.streak;
      });
      if (data.week_count !== null) {
        document.querySelectorAll(`[data-week-for="${id}"]`).forEach((el) => {
          el.textContent = data.week_count;
        });
      }
      updateProgress();
    } catch (error) {
      box.checked = !box.checked;
      showToast(error.message, "danger");
    } finally {
      box.disabled = false;
    }
  });
}

function initLiveSearch() {
  const form = document.getElementById("filter-form");
  const results = document.getElementById("results");
  if (!form || !results) return;

  let controller = null;

  async function search() {
    const params = new URLSearchParams();
    new FormData(form).forEach((value, key) => {
      if (value !== "") params.append(key, value);
    });

    if (controller) controller.abort();
    controller = new AbortController();
    results.classList.add("opacity-50");

    try {
      const data = await fetchJSON(`${form.dataset.searchUrl}?${params}`, { signal: controller.signal });
      results.innerHTML = data.html;
      const query = params.toString();
      history.replaceState(null, "", query ? `${location.pathname}?${query}` : location.pathname);
      results.classList.remove("opacity-50");
    } catch (error) {
      if (error.name === "AbortError") return;
      results.classList.remove("opacity-50");
      showToast(error.message, "danger");
    }
  }

  form.addEventListener("input", debounce(search, 300));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    search();
  });
}

function initConfirmModal() {
  const modalEl = document.getElementById("confirmModal");
  if (!modalEl) return;

  const modal = new bootstrap.Modal(modalEl);
  const form = document.getElementById("confirmModalForm");
  const text = document.getElementById("confirmModalText");

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-confirm-action]");
    if (!trigger) return;
    event.preventDefault();
    form.action = trigger.dataset.confirmAction;
    text.textContent = trigger.dataset.confirmText || "Das kann nicht rückgängig gemacht werden.";
    modal.show();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("#toast-container .toast").forEach((el) => {
    new bootstrap.Toast(el, { delay: 5000 }).show();
  });
  initConfirmModal();
  initHabitChecks();
  initLiveSearch();
});
