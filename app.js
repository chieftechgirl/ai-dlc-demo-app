// Simple config-driven demo app. No build step, no dependencies.
// Settings come from config.json; URL params override for quick demos:
//   ?industry=healthcare&company=Acme&primary=%23ff6600
(async function () {
  const [config, industries] = await Promise.all([
    fetch("config.json").then(r => r.json()),
    fetch("industries.json").then(r => r.json()),
  ]);

  const params = new URLSearchParams(location.search);
  const key = params.get("industry") || localStorage.getItem("industry") || config.industry;
  const company = params.get("company") || config.company.name;
  const brand = {
    primary: params.get("primary") || config.brand.primary,
    accent: params.get("accent") || config.brand.accent,
    dark: params.get("dark") || config.brand.dark,
  };

  // Apply branding
  const root = document.documentElement.style;
  root.setProperty("--primary", brand.primary);
  root.setProperty("--accent", brand.accent);
  root.setProperty("--dark", brand.dark);
  document.getElementById("company").textContent = company;
  document.title = company + " - AI-DLC Demo";
  const logo = document.getElementById("logo");
  if (config.company.logoUrl) { logo.src = config.company.logoUrl; logo.hidden = false; }
  const link = document.getElementById("siteLink");
  link.href = config.company.websiteUrl;
  link.textContent = config.company.websiteUrl;

  // Industry picker
  const select = document.getElementById("industry");
  Object.entries(industries).forEach(([k, v]) => {
    const o = new Option(v.label, k, false, k === key);
    select.add(o);
  });
  select.addEventListener("change", () => {
    localStorage.setItem("industry", select.value);
    render(select.value);
  });

  function render(k) {
    const ind = industries[k] || industries.retail;
    document.getElementById("industryLabel").textContent = ind.label;
    document.getElementById("tagline").textContent = config.company.tagline || ind.tagline;
    document.getElementById("recordsTitle").textContent = ind.records;
    document.getElementById("newItem").placeholder = "New " + ind.record.toLowerCase() + "...";
    document.getElementById("addBtn").textContent = "Add " + ind.record.toLowerCase();

    document.getElementById("kpis").innerHTML = ind.kpis
      .map((label, i) => `<div class="kpi"><div class="value">${[24, 3.2, 1.8][i] ?? 0}</div><div class="label">${label}</div></div>`)
      .join("");

    const storeKey = "items:" + k;
    let items = JSON.parse(localStorage.getItem(storeKey) || "null")
      || ind.samples.map(name => ({ name, status: ind.statuses[0] }));
    const save = () => localStorage.setItem(storeKey, JSON.stringify(items));

    const list = document.getElementById("list");
    function draw() {
      list.innerHTML = "";
      items.forEach((it, i) => {
        const li = document.createElement("li");
        const name = document.createElement("span");
        name.textContent = it.name;
        const sel = document.createElement("select");
        ind.statuses.forEach(s => sel.add(new Option(s, s, false, s === it.status)));
        sel.onchange = () => { items[i].status = sel.value; save(); };
        li.append(name, sel);
        list.append(li);
      });
    }
    document.getElementById("addForm").onsubmit = e => {
      e.preventDefault();
      const input = document.getElementById("newItem");
      items.push({ name: input.value, status: ind.statuses[0] });
      input.value = "";
      save(); draw();
    };
    draw();
  }

  render(key);
})();
