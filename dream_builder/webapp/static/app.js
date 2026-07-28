const dreamListEl = document.getElementById("dream-list");
const detailEl = document.getElementById("detail");
const newDreamForm = document.getElementById("new-dream-form");
const newDreamHints = document.getElementById("new-dream-hints");

let currentDreamId = null;
let buildPollTimer = null;

function esc(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

let errorBannerTimer = null;

function showError(message) {
  let banner = document.getElementById("error-banner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "error-banner";
    banner.className = "error-banner";
    document.body.appendChild(banner);
  }
  banner.textContent = message;
  banner.classList.add("visible");
  clearTimeout(errorBannerTimer);
  errorBannerTimer = setTimeout(() => banner.classList.remove("visible"), 8000);
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || data.detail || `Request failed (${res.status})`);
  }
  return data;
}

function renderHints(container, hints, dream) {
  if (!hints || hints.length === 0) {
    container.classList.add("hidden");
    container.innerHTML = "";
    return;
  }
  container.classList.remove("hidden");
  container.innerHTML =
    "<strong>Might be worth a look:</strong><ul>" +
    hints
      .map(
        (h, i) =>
          `<li>${esc(h)}${
            dream ? ` <button class="secondary capture-btn" data-hint-index="${i}">Save</button>` : ""
          }</li>`
      )
      .join("") +
    "</ul>";
  if (dream) {
    container.querySelectorAll(".capture-btn[data-hint-index]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const hint = hints[Number(btn.dataset.hintIndex)];
        captureItem(
          { label: hint.slice(0, 60), detail: hint, source_dream_id: dream.id, source_dream_title: dream.title },
          btn
        );
      });
    });
  }
}

async function loadDreamList() {
  const dreams = await api("/api/dreams");
  dreamListEl.innerHTML = dreams
    .map(
      (d) => `
      <li data-id="${esc(d.id)}" class="${d.id === currentDreamId ? "active" : ""}">
        <div>${esc(d.title)}</div>
        <div class="progress">${esc(d.status)} · ${d.steps_done}/${d.steps_total} steps</div>
      </li>`
    )
    .join("");
  dreamListEl.querySelectorAll("li").forEach((li) => {
    li.addEventListener("click", () => selectDream(li.dataset.id));
  });
}

newDreamForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = document.getElementById("new-title").value.trim();
  const description = document.getElementById("new-description").value.trim();
  if (!title || !description) return;
  const submitBtn = newDreamForm.querySelector("button");
  submitBtn.disabled = true;
  try {
    const dream = await api("/api/dreams", {
      method: "POST",
      body: JSON.stringify({ title, description }),
    });
    newDreamForm.reset();
    renderHints(newDreamHints, dream.resource_hints);
    await loadDreamList();
    selectDream(dream.id);
  } catch (err) {
    showError(err.message);
  } finally {
    submitBtn.disabled = false;
  }
});

async function selectDream(id) {
  currentDreamId = id;
  stopBuildPolling();
  const dream = await api(`/api/dreams/${id}`);
  renderDetail(dream);
  await loadDreamList();
}

function renderDetail(dream) {
  const plan = dream.plan || [];
  const resources = dream.resources || [];
  const reflections = dream.reflections || [];
  const hints = dream.resource_hints || [];
  const projection = dream.projection || null;
  const scaling = dream.scaling || null;

  detailEl.innerHTML = `
    <header>
      <h2 style="border:none;text-transform:none;letter-spacing:normal;font-size:1.4rem;color:inherit;">
        ${esc(dream.title)}<span class="status-badge">${esc(dream.status)}</span>
      </h2>
      <p>${esc(dream.description)}</p>
    </header>

    <div id="hints-section" class="hints ${hints.length ? "" : "hidden"}"></div>

    <section>
      <h2>Plan</h2>
      <ul class="plan-list">
        ${plan
          .map(
            (s, i) => `
          <li>
            <input type="checkbox" data-step="${i + 1}" ${s.done ? "checked" : ""} />
            <span>${esc(s.step)}${s.needs_internet ? '<span class="needs-internet">[needs internet]</span>' : ""}</span>
          </li>`
          )
          .join("") || "<li>No plan yet.</li>"}
      </ul>
      <button class="secondary" id="btn-plan">${plan.length ? "Regenerate plan" : "Generate plan"}</button>
    </section>

    <section>
      <h2>Resources</h2>
      <div id="resources-list">
        ${
          resources
            .map(
              (r, i) => `
          <div class="resource-card">
            <strong>${esc(r.resource)}</strong>
            <div class="why">${esc(r.why)}</div>
            <p>${esc(r.recommendation)}</p>
            <ul>${(r.options || [])
              .map((o) => `<li><a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.title)}</a></li>`)
              .join("")}</ul>
            <button class="secondary" data-resource-index="${i}">Save to action bucket</button>
          </div>`
            )
            .join("") || "<p>No resources gathered yet.</p>"
        }
      </div>
      <button class="secondary" id="btn-resources">Find resources</button>
      <span id="resources-spinner" class="hidden">Searching…</span>
    </section>

    <section>
      <h2>Projections</h2>
      <div id="projection-panel">
        ${
          projection
            ? `
          <p><strong>Time:</strong> ${esc(projection.time_estimate)}</p>
          <p><strong>Cost:</strong> ${esc(projection.cost_estimate)}</p>
          <p><strong>Lead measures</strong> <span class="why">(things you control, track weekly)</span></p>
          <ul>${(projection.lead_measures || []).map((m) => `<li>${esc(m)}</li>`).join("") || "<li>None given.</li>"}</ul>
          <p><strong>Lag measures</strong> <span class="why">(outcomes that confirm you're getting there)</span></p>
          <ul>${(projection.lag_measures || []).map((m) => `<li>${esc(m)}</li>`).join("") || "<li>None given.</li>"}</ul>
        `
            : "<p>No projection yet.</p>"
        }
      </div>
      <button class="secondary" id="btn-projection">${projection ? "Refresh projection" : "Get projection"}</button>
      <span id="projection-spinner" class="hidden">Estimating…</span>
    </section>

    <section>
      <h2>Funding &amp; Scaling</h2>
      <div id="scaling-panel">
        ${
          scaling
            ? `
          <p><strong>Funding strategy:</strong> ${esc(scaling.funding_strategy)}</p>
          <p><strong>Scaling strategy:</strong> ${esc(scaling.scaling_strategy)}</p>
          <p><strong>Funding milestones</strong></p>
          <ul>${(scaling.funding_milestones || []).map((m) => `<li>${esc(m)}</li>`).join("") || "<li>None given.</li>"}</ul>
          <p><strong>Scaling lead measures</strong> <span class="why">(things you control, track weekly)</span></p>
          <ul>${(scaling.scaling_lead_measures || []).map((m) => `<li>${esc(m)}</li>`).join("") || "<li>None given.</li>"}</ul>
          <p><strong>Scaling lag measures</strong> <span class="why">(outcomes that confirm real growth)</span></p>
          <ul>${(scaling.scaling_lag_measures || []).map((m) => `<li>${esc(m)}</li>`).join("") || "<li>None given.</li>"}</ul>
        `
            : "<p>No funding/scaling plan yet.</p>"
        }
      </div>
      <button class="secondary" id="btn-scaling">${scaling ? "Refresh funding &amp; scaling plan" : "Get funding &amp; scaling plan"}</button>
      <span id="scaling-spinner" class="hidden">Thinking…</span>
    </section>

    <section>
      <h2>Reflections</h2>
      <div id="reflections-list">
        ${
          reflections
            .slice()
            .reverse()
            .map((r) => `<div class="reflection"><time>${esc(r.date)}</time><div>${esc(r.text)}</div></div>`)
            .join("") || "<p>No reflections yet.</p>"
        }
      </div>
      <button class="secondary" id="btn-reflect">Get reflection</button>
    </section>

    <section>
      <h2>Build</h2>
      <p>Have Claude Code implement this dream as a real project. This calls a separate cloud service (Claude Code) — a deliberate, explicit exception to the local-first design.</p>
      <div class="build-controls">
        <input id="build-dir" type="text" placeholder="Target dir (optional)" />
        <select id="build-permission-mode">
          <option value="acceptEdits" selected>acceptEdits (default)</option>
          <option value="auto">auto</option>
          <option value="dontAsk">dontAsk</option>
          <option value="plan">plan</option>
          <option value="manual">manual</option>
          <option value="bypassPermissions">bypassPermissions</option>
        </select>
        <button id="btn-build">Build with Claude Code</button>
      </div>
      <div id="build-status"></div>
      <pre id="build-log" class="hidden"></pre>
    </section>
  `;

  renderHints(document.getElementById("hints-section"), hints, dream);

  detailEl.querySelectorAll('.plan-list input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener("change", () => toggleStep(dream.id, Number(cb.dataset.step), cb.checked));
  });
  detailEl.querySelectorAll("#resources-list [data-resource-index]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const r = resources[Number(btn.dataset.resourceIndex)];
      captureItem(
        {
          label: r.resource,
          detail: r.recommendation,
          url: (r.options && r.options[0] && r.options[0].url) || null,
          source_dream_id: dream.id,
          source_dream_title: dream.title,
        },
        btn
      );
    });
  });
  document.getElementById("btn-plan").addEventListener("click", () => generatePlan(dream.id));
  document.getElementById("btn-resources").addEventListener("click", () => findResources(dream.id));
  document.getElementById("btn-projection").addEventListener("click", () => getProjection(dream.id));
  document.getElementById("btn-scaling").addEventListener("click", () => getScaling(dream.id));
  document.getElementById("btn-reflect").addEventListener("click", () => getReflection(dream.id));
  document.getElementById("btn-build").addEventListener("click", () => startBuild(dream.id));
}

async function captureItem(item, btn) {
  try {
    await api("/api/bucket", { method: "POST", body: JSON.stringify(item) });
    if (btn) {
      btn.textContent = "Saved";
      btn.disabled = true;
    }
    await refreshBucketCount();
  } catch (err) {
    showError(err.message);
  }
}

async function refreshBucketCount() {
  const items = await api("/api/bucket");
  document.getElementById("bucket-count").textContent = items.length;
}

async function renderBucketView() {
  currentDreamId = null;
  stopBuildPolling();
  const items = await api("/api/bucket");
  detailEl.innerHTML = `
    <header>
      <h2 style="border:none;text-transform:none;letter-spacing:normal;font-size:1.4rem;color:inherit;">Action Bucket</h2>
      <p>Everything you've saved from resources and hints across your dreams. Select two or more and combine them into a new dream — handy for bundling several services (e.g. transportation + companionship) into one combined plan.</p>
    </header>
    <section>
      <ul class="bucket-list">
        ${
          items
            .map(
              (it) => `
          <li>
            <label>
              <input type="checkbox" class="bucket-select" value="${esc(it.id)}" />
              <strong>${esc(it.label)}</strong>${
                it.source_dream_title ? ` <span class="why">(from ${esc(it.source_dream_title)})</span>` : ""
              }
            </label>
            <p>${esc(it.detail)}</p>
            ${it.url ? `<a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.url)}</a>` : ""}
            <button class="secondary" data-remove-id="${esc(it.id)}">Remove</button>
          </li>`
            )
            .join("") || "<li>Nothing captured yet. Save a resource or hint from a dream to get started.</li>"
        }
      </ul>
    </section>
    <section>
      <h2>Combine into a new dream</h2>
      <input id="combine-title" type="text" placeholder="What's the combined concept called?" />
      <textarea id="combine-description" placeholder="Any extra context? (optional — the selected items are included automatically)"></textarea>
      <button id="btn-combine">Combine selected into a new dream</button>
    </section>
  `;

  detailEl.querySelectorAll("[data-remove-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/bucket/${btn.dataset.removeId}`, { method: "DELETE" });
      await refreshBucketCount();
      renderBucketView();
    });
  });

  document.getElementById("btn-combine").addEventListener("click", async () => {
    const selected = Array.from(detailEl.querySelectorAll(".bucket-select:checked")).map((cb) => cb.value);
    const title = document.getElementById("combine-title").value.trim();
    const description = document.getElementById("combine-description").value.trim();
    if (selected.length === 0) {
      showError("Select at least one item to combine.");
      return;
    }
    if (!title) {
      showError("Give the combined idea a title.");
      return;
    }
    try {
      const dream = await api("/api/bucket/combine", {
        method: "POST",
        body: JSON.stringify({ item_ids: selected, title, description }),
      });
      await loadDreamList();
      selectDream(dream.id);
    } catch (err) {
      showError(err.message);
    }
  });
}

document.getElementById("btn-view-bucket").addEventListener("click", renderBucketView);

async function toggleStep(id, step, done) {
  const dream = await api(`/api/dreams/${id}/steps/${step}`, {
    method: "PATCH",
    body: JSON.stringify({ done }),
  });
  renderDetail(dream);
  await loadDreamList();
}

async function generatePlan(id) {
  const dream = await api(`/api/dreams/${id}/plan`, { method: "POST" });
  renderDetail(dream);
  await loadDreamList();
}

async function findResources(id) {
  const spinner = document.getElementById("resources-spinner");
  const btn = document.getElementById("btn-resources");
  spinner.classList.remove("hidden");
  btn.disabled = true;
  try {
    await api(`/api/dreams/${id}/resources`, { method: "POST" });
    const dream = await api(`/api/dreams/${id}`);
    renderDetail(dream);
  } catch (err) {
    showError(err.message);
  } finally {
    spinner.classList.add("hidden");
    btn.disabled = false;
  }
}

async function getProjection(id) {
  const spinner = document.getElementById("projection-spinner");
  const btn = document.getElementById("btn-projection");
  spinner.classList.remove("hidden");
  btn.disabled = true;
  try {
    await api(`/api/dreams/${id}/projection`, { method: "POST" });
    const dream = await api(`/api/dreams/${id}`);
    renderDetail(dream);
  } catch (err) {
    showError(err.message);
  } finally {
    spinner.classList.add("hidden");
    btn.disabled = false;
  }
}

async function getScaling(id) {
  const spinner = document.getElementById("scaling-spinner");
  const btn = document.getElementById("btn-scaling");
  spinner.classList.remove("hidden");
  btn.disabled = true;
  try {
    await api(`/api/dreams/${id}/scaling`, { method: "POST" });
    const dream = await api(`/api/dreams/${id}`);
    renderDetail(dream);
  } catch (err) {
    showError(err.message);
  } finally {
    spinner.classList.add("hidden");
    btn.disabled = false;
  }
}

async function getReflection(id) {
  await api(`/api/dreams/${id}/reflect`, { method: "POST" });
  const dream = await api(`/api/dreams/${id}`);
  renderDetail(dream);
}

async function startBuild(id) {
  const dir = document.getElementById("build-dir").value.trim();
  const permission_mode = document.getElementById("build-permission-mode").value;
  const statusEl = document.getElementById("build-status");
  const logEl = document.getElementById("build-log");
  const btn = document.getElementById("btn-build");
  btn.disabled = true;
  try {
    const job = await api(`/api/dreams/${id}/build`, {
      method: "POST",
      body: JSON.stringify(dir ? { dir, permission_mode } : { permission_mode }),
    });
    statusEl.textContent = `Building in ${job.target_dir}…`;
    logEl.classList.remove("hidden");
    pollBuild(job.job_id, btn, statusEl, logEl);
  } catch (err) {
    showError(err.message);
    btn.disabled = false;
  }
}

function stopBuildPolling() {
  if (buildPollTimer) {
    clearInterval(buildPollTimer);
    buildPollTimer = null;
  }
}

function pollBuild(jobId, btn, statusEl, logEl) {
  stopBuildPolling();
  buildPollTimer = setInterval(async () => {
    try {
      const job = await api(`/api/builds/${jobId}`);
      logEl.textContent = job.log;
      logEl.scrollTop = logEl.scrollHeight;
      if (job.status !== "running") {
        stopBuildPolling();
        btn.disabled = false;
        statusEl.textContent =
          job.status === "done" ? `Done. Project is in ${job.target_dir}` : `Error: ${job.error}`;
      }
    } catch (err) {
      stopBuildPolling();
      btn.disabled = false;
      statusEl.textContent = `Error: ${err.message}`;
    }
  }, 2000);
}

loadDreamList();
refreshBucketCount();
