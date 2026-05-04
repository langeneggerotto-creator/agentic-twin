const API = "";  // same origin; set to "http://localhost:8000" for local dev

let token = localStorage.getItem("dm_token");
let currentUser = null;

/* ---- Utilities ---- */
function toast(msg, duration = 3000) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), duration);
}

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  const res = await fetch(API + path, { headers, ...opts });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function setToken(t) {
  token = t;
  localStorage.setItem("dm_token", t);
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem("dm_token");
  updateNav();
  toast("Logged out");
}

function updateNav() {
  const loginBtn = document.getElementById("nav-login");
  const logoutBtn = document.getElementById("nav-logout");
  const dashBtn = document.getElementById("nav-dashboard");
  const sellBtn = document.getElementById("nav-sell");
  if (!loginBtn) return;
  if (token && currentUser) {
    loginBtn.style.display = "none";
    if (logoutBtn) logoutBtn.style.display = "inline-flex";
    if (dashBtn) dashBtn.style.display = "inline-flex";
    if (sellBtn && (currentUser.role === "seller" || currentUser.role === "admin")) {
      sellBtn.style.display = "inline-flex";
    }
  } else {
    loginBtn.style.display = "inline-flex";
    if (logoutBtn) logoutBtn.style.display = "none";
    if (dashBtn) dashBtn.style.display = "none";
    if (sellBtn) sellBtn.style.display = "none";
  }
}

async function loadCurrentUser() {
  if (!token) return;
  try {
    currentUser = await api("/users/me");
    updateNav();
  } catch {
    token = null;
    localStorage.removeItem("dm_token");
  }
}

/* ---- Auth Modals ---- */
function openModal(id) {
  document.getElementById(id).classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    await loadCurrentUser();
    closeModal("modal-login");
    toast(`Welcome back, ${currentUser.username}!`);
    if (window.location.pathname === "/") loadProducts();
  } catch (err) {
    toast(`Login failed: ${err.message}`);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const payload = {
    email: document.getElementById("reg-email").value,
    username: document.getElementById("reg-username").value,
    password: document.getElementById("reg-password").value,
    role: document.getElementById("reg-role").value,
  };
  try {
    await api("/auth/register", { method: "POST", body: JSON.stringify(payload) });
    toast("Account created! Please log in.");
    closeModal("modal-register");
    openModal("modal-login");
  } catch (err) {
    toast(`Registration failed: ${err.message}`);
  }
}

/* ---- Products ---- */
const CATEGORY_ICONS = {
  template: "📄", ebook: "📚", tool: "🔧", course: "🎓", graphic: "🎨", plugin: "🔌", other: "📦",
};

function renderStars(rating) {
  const full = Math.round(rating);
  return "★".repeat(full) + "☆".repeat(5 - full);
}

function renderProductCard(p) {
  const icon = CATEGORY_ICONS[p.category] || "📦";
  const featured = p.is_featured ? `<span class="badge-featured">⚡ Featured</span>` : "";
  return `
    <div class="product-card" onclick="openProduct(${p.id})">
      <div class="product-thumb">${icon}</div>
      <div class="product-body">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span class="product-category">${p.category}</span>
          ${featured}
        </div>
        <div class="product-title">${p.title}</div>
        <div class="product-meta">
          <span class="product-price">$${p.price.toFixed(2)}</span>
          <span class="product-rating" title="${p.avg_rating.toFixed(1)} / 5">
            ${renderStars(p.avg_rating)} <small style="color:var(--muted)">(${p.review_count})</small>
          </span>
        </div>
      </div>
    </div>`;
}

let activeCategory = null;

async function loadProducts(category = null) {
  const grid = document.getElementById("product-grid");
  const search = document.getElementById("hero-search")?.value || "";
  if (!grid) return;
  grid.innerHTML = `<p style="color:var(--muted)">Loading...</p>`;

  const params = new URLSearchParams({ limit: "24" });
  if (category) params.set("category", category);
  if (search) params.set("search", search);

  try {
    const products = await api(`/products?${params}`);
    if (!products.length) {
      grid.innerHTML = `<p style="color:var(--muted);grid-column:1/-1">No products found.</p>`;
      return;
    }
    grid.innerHTML = products.map(renderProductCard).join("");
  } catch {
    grid.innerHTML = `<p style="color:var(--danger)">Failed to load products.</p>`;
  }
}

function filterCategory(cat) {
  activeCategory = activeCategory === cat ? null : cat;
  document.querySelectorAll(".cat-pill").forEach(p => {
    p.classList.toggle("active", p.dataset.cat === activeCategory);
  });
  loadProducts(activeCategory);
}

async function openProduct(id) {
  try {
    const p = await api(`/products/${id}`);
    const icon = CATEGORY_ICONS[p.category] || "📦";
    document.getElementById("modal-product-body").innerHTML = `
      <div style="font-size:4rem;text-align:center;margin-bottom:1rem">${icon}</div>
      <h2>${p.title}</h2>
      <p style="color:var(--muted);font-size:0.85rem;margin:0.5rem 0">${p.category.toUpperCase()} &bull; ${p.sales_count} sales &bull; ${renderStars(p.avg_rating)} (${p.review_count})</p>
      <p style="margin:1rem 0;color:var(--muted)">${p.description}</p>
      <p style="font-size:1.8rem;font-weight:800;color:var(--primary)">$${p.price.toFixed(2)}</p>
      <div class="modal-actions">
        <button class="btn btn-outline" onclick="closeModal('modal-product')">Close</button>
        <button class="btn btn-primary" onclick="buyProduct(${p.id}, ${p.price})">Buy Now</button>
      </div>`;
    openModal("modal-product");
  } catch (err) {
    toast(`Error: ${err.message}`);
  }
}

async function buyProduct(productId, price) {
  if (!token) {
    closeModal("modal-product");
    toast("Please log in to purchase");
    openModal("modal-login");
    return;
  }
  try {
    const order = await api("/orders", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, payment_method_id: "pm_mock_card" }),
    });
    closeModal("modal-product");
    toast(`Purchase successful! Order #${order.id}. Check your email for the download link.`);
  } catch (err) {
    toast(`Purchase failed: ${err.message}`);
  }
}

/* ---- Init ---- */
document.addEventListener("DOMContentLoaded", async () => {
  await loadCurrentUser();

  if (document.getElementById("product-grid")) {
    loadProducts();
  }

  document.getElementById("hero-search")?.addEventListener("keydown", e => {
    if (e.key === "Enter") loadProducts(activeCategory);
  });

  document.getElementById("btn-search")?.addEventListener("click", () => loadProducts(activeCategory));
  document.getElementById("nav-login")?.addEventListener("click", () => openModal("modal-login"));
  document.getElementById("nav-logout")?.addEventListener("click", logout);
  document.getElementById("nav-register")?.addEventListener("click", () => openModal("modal-register"));
  document.getElementById("form-login")?.addEventListener("submit", handleLogin);
  document.getElementById("form-register")?.addEventListener("submit", handleRegister);
});
