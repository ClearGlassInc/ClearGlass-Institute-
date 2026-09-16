/* ============================================================================
   CLEARGLASS // CONTROL SURFACE v3.0 — interaction engine
   Vanilla JS, zero dependencies. Keyboard-first, ARIA-correct, motion-safe.

   Architecture
     · Telemetry      — pluggable source → maps raw API status to 4 states,
                        rolls systems up to one global state, notifies the UI.
     · CommandPalette — ⌘K / Ctrl-K modal; combobox + listbox keyboard model.
     · SystemsDrawer  — right-side modal; renders systems + contextual controls.
     · MobileRail     — bottom navigation that mirrors the global state.
     · Bar            — sticky header: status readout, clock, scrollspy.

   States: NOMINAL · SYNCING · DEGRADED · FAILURE
   Public: window.ClearGlassControlSurface.configure({ source, pollMs })
           lets a real GitHub source be injected (see GitHubSource notes).
   ========================================================================== */
(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $  = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));

  /* ====================================================== STATUS MODEL */
  const STATE = { NOMINAL: "NOMINAL", SYNCING: "SYNCING", DEGRADED: "DEGRADED", FAILURE: "FAILURE" };
  // Worst-wins ordering for the global roll-up.
  const SEVERITY = { NOMINAL: 0, SYNCING: 1, DEGRADED: 2, FAILURE: 3 };
  const worst = (states) =>
    states.reduce((acc, s) => (SEVERITY[s] > SEVERITY[acc] ? s : acc), STATE.NOMINAL);

  // Map a GitHub Actions run (status + conclusion) to an operational state.
  // Mirrors the REST shape: status ∈ queued|in_progress|completed,
  // conclusion ∈ success|failure|cancelled|timed_out|neutral|skipped|null.
  const mapActions = (status, conclusion) => {
    if (status !== "completed") return STATE.SYNCING;
    switch (conclusion) {
      case "success":   return STATE.NOMINAL;
      case "failure":
      case "timed_out": return STATE.FAILURE;
      default:          return STATE.DEGRADED; // cancelled / neutral / skipped
    }
  };
  // Map a GitHub deployment status state to an operational state.
  const mapDeployment = (state) => {
    switch (state) {
      case "success":  return STATE.NOMINAL;
      case "queued":
      case "pending":
      case "in_progress": return STATE.SYNCING;
      case "failure":
      case "error":    return STATE.FAILURE;
      default:         return STATE.DEGRADED; // inactive / unknown
    }
  };

  /* ====================================================== TELEMETRY SOURCE
     Default is a self-contained simulator so the page works as a static
     GitHub Pages deploy (the Actions API needs auth). To go live, inject a
     real source via configure({ source }); a source is any object with an
     async poll() → [{ id, name, kind, state, detail, meta, href }]. */
  const REPO_ACTIONS = "https://github.com/clearglassinc/opal-koboi/actions";

  const SimulatedSource = (() => {
    // Seed each system from a realistic raw payload, exercising the mappers.
    const systems = [
      { id: "ci",     name: "CI · Build & Test",    kind: "actions",
        raw: { status: "completed", conclusion: "success" }, detail: "ci.yml · main", meta: "#1042" },
      { id: "repair", name: "Workflow Repair Agent", kind: "actions",
        raw: { status: "completed", conclusion: "success" }, detail: "weekly audit · clean", meta: "scheduled" },
      { id: "publish",name: "npm Publish",            kind: "actions",
        raw: { status: "completed", conclusion: "success" }, detail: "v0.1.0 published", meta: "release" },
      { id: "pages",  name: "Pages Deploy",           kind: "deployment",
        raw: { state: "in_progress" }, detail: "github-pages · building", meta: "env: production" },
      { id: "api",    name: "API Gateway",            kind: "deployment",
        raw: { state: "success" }, detail: "p99 312ms · 5 regions", meta: "env: edge" },
    ];
    const project = (s) => ({
      id: s.id, name: s.name, kind: s.kind, detail: s.detail, meta: s.meta, href: REPO_ACTIONS,
      state: s.kind === "actions"
        ? mapActions(s.raw.status, s.raw.conclusion)
        : mapDeployment(s.raw.state),
    });
    let ticks = 0;
    return {
      // Allow contextual controls to mutate the simulated truth (e.g. Re-run).
      set(id, patch) {
        const s = systems.find((x) => x.id === id);
        if (s) Object.assign(s, patch);
      },
      async poll() {
        ticks++;
        // A believable narrative so the surface visibly reacts:
        //  · the Pages build settles "deploying → live" on the 2nd poll;
        //  · the API gateway then runs a self-healing incident on a loop
        //    (watch → failover → recovered), exercising DEGRADED and SYNCING
        //    and the contextual controls that only appear in those states.
        if (ticks === 2) {
          SimulatedSource.set("pages", { raw: { state: "success" }, detail: "github-pages · live", meta: "env: production" });
        }
        if (ticks > 3) {
          const phase = ticks % 9;
          if (phase === 4) SimulatedSource.set("api", { raw: { state: "inactive" },    detail: "eu-west p99 elevated · watch",  meta: "env: edge" });
          else if (phase === 6) SimulatedSource.set("api", { raw: { state: "in_progress" }, detail: "eu-west failover · rerouting", meta: "env: edge" });
          else if (phase === 8) SimulatedSource.set("api", { raw: { state: "success" },  detail: "p99 312ms · 5 regions",        meta: "env: edge" });
        }
        return systems.map(project);
      },
    };
    /* --- To wire a real source, replace the above with:
       const GitHubSource = (token, owner, repo) => ({
         async poll() {
           const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/actions/runs?per_page=5`,
             { headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" } });
           const { workflow_runs } = await r.json();
           return workflow_runs.map(run => ({
             id: String(run.id), name: run.name, kind: "actions",
             state: mapActions(run.status, run.conclusion),
             detail: `${run.head_branch} · ${run.event}`, meta: `#${run.run_number}`, href: run.html_url,
           }));
         }
       });
       ClearGlassControlSurface.configure({ source: GitHubSource(TOKEN, "clearglassinc", "opal-koboi") }); */
  })();

  const Telemetry = {
    source: SimulatedSource,
    pollMs: 5200,
    systems: [],
    global: STATE.NOMINAL,
    _subs: new Set(),
    _timer: null,
    subscribe(fn) { this._subs.add(fn); return () => this._subs.delete(fn); },
    _emit() { this._subs.forEach((fn) => fn(this.systems, this.global)); },
    async refresh() {
      try {
        this.systems = await this.source.poll();
        this.global = worst(this.systems.map((s) => s.state));
        this._emit();
      } catch (err) {
        // A telemetry outage is itself a degraded signal, never a crash.
        this.global = STATE.DEGRADED;
        this._emit();
      }
    },
    start() {
      this.refresh();
      if (this._timer) clearInterval(this._timer);
      this._timer = setInterval(() => this.refresh(), this.pollMs);
    },
  };

  /* ====================================================== A11Y HELPERS */
  const FOCUSABLE =
    'a[href],button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex="-1"])';

  // Returns a teardown fn. Traps Tab/Shift-Tab within `container`.
  function trapFocus(container) {
    const onKey = (e) => {
      if (e.key !== "Tab") return;
      const f = $$(FOCUSABLE, container).filter((el) => el.offsetParent !== null || el === document.activeElement);
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    container.addEventListener("keydown", onKey);
    return () => container.removeEventListener("keydown", onKey);
  }

  const lockScroll = (on) => {
    document.documentElement.classList.toggle("cs-modal-open", on);
    document.body.classList.toggle("cs-modal-open", on);
  };

  const ICONS = {
    arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    doc:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 2h8l4 4v16H6z"/><path d="M14 2v4h4"/></svg>',
    grid:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
    pulse: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 12h4l3 8 4-16 3 8h4"/></svg>',
    bolt:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg>',
    sync:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a9 9 0 1 1-3-6.7M21 4v5h-5"/></svg>',
    eye:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    stop:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>',
    motion:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>',
    link:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg>',
  };

  /* ====================================================== COMMAND PALETTE */
  const Palette = {
    el: null, input: null, list: null, empty: null,
    commands: [], filtered: [], active: 0, lastFocus: null,
    init() {
      this.el = $("[data-cs-palette]"); if (!this.el) return;
      this.input = $("[data-cs-palette-input]", this.el);
      this.list  = $("[data-cs-palette-list]", this.el);
      this.empty = $("[data-cs-palette-empty]", this.el);
      this.commands = this.buildCommands();

      this.input.addEventListener("input", () => this.filter(this.input.value));
      this.input.addEventListener("keydown", (e) => this.onKey(e));
      this.el.addEventListener("pointerdown", (e) => { if (e.target === this.el) this.close(); });
      this._untrap = null;

      // Global hotkey: ⌘K / Ctrl-K, plus "/" when nothing is focused.
      document.addEventListener("keydown", (e) => {
        const k = e.key.toLowerCase();
        if ((e.metaKey || e.ctrlKey) && k === "k") { e.preventDefault(); this.toggle(); }
        else if (k === "/" && !/^(input|textarea)$/i.test(document.activeElement.tagName) && this.el.hidden) {
          e.preventDefault(); this.open();
        }
      });
    },
    buildCommands() {
      const go = (sel) => () => {
        const t = $(sel); if (!t) return;
        t.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
        t.setAttribute("tabindex", "-1"); t.focus({ preventScroll: true });
      };
      const open = (href) => () => window.open(href, href.startsWith("http") ? "_blank" : "_self");
      return [
        { group: "Navigate", icon: ICONS.bolt,  title: "Capabilities", hint: "Operational capabilities", keys: ["capabilities","features"], run: go("#capabilities") },
        { group: "Navigate", icon: ICONS.pulse, title: "Telemetry",    hint: "Live metric band",          keys: ["telemetry","metrics"],     run: go("#telemetry") },
        { group: "Navigate", icon: ICONS.grid,  title: "Systems",      hint: "Event stream & posture",    keys: ["systems","events","log"],  run: go("#systems") },
        { group: "Navigate", icon: ICONS.grid,  title: "Components",   hint: "Interface system",          keys: ["components","ui","library"], run: go("#components") },
        { group: "Open",     icon: ICONS.doc,   title: "Specification",hint: "spec.html",                 keys: ["spec","specification"],    run: open("spec.html") },
        { group: "Open",     icon: ICONS.link,  title: "Repository",   hint: "github.com",                keys: ["repo","github","source"],  run: open("https://github.com/clearglassinc/opal-koboi") },
        { group: "Systems",  icon: ICONS.grid,  title: "Open Systems Drawer", hint: "Live status & controls", keys: ["drawer","status","systems"], run: () => Drawer.open() },
        { group: "Systems",  icon: ICONS.sync,  title: "Refresh Telemetry",   hint: "Re-poll all sources",    keys: ["refresh","reload","poll"],   run: () => Telemetry.refresh() },
        { group: "Surface",  icon: ICONS.motion,title: "Toggle Reduced Motion", hint: "Disable spring motion", keys: ["motion","animation","accessibility"], run: () => toggleMotion() },
      ];
    },
    open() {
      if (!this.el.hidden) return;
      this.lastFocus = document.activeElement;
      this.el.hidden = false; lockScroll(true);
      this.input.value = ""; this.filter("");
      this._untrap = trapFocus(this.el);
      requestAnimationFrame(() => this.input.focus());
    },
    close() {
      if (this.el.hidden) return;
      this.el.hidden = true; lockScroll(false);
      if (this._untrap) { this._untrap(); this._untrap = null; }
      if (this.lastFocus && this.lastFocus.focus) this.lastFocus.focus();
    },
    toggle() { this.el.hidden ? this.open() : this.close(); },
    filter(q) {
      const query = q.trim().toLowerCase();
      this.filtered = !query ? this.commands.slice() : this.commands.filter((c) =>
        (c.title + " " + c.hint + " " + c.keys.join(" ")).toLowerCase().includes(query));
      this.active = 0;
      this.render();
    },
    render() {
      this.list.innerHTML = "";
      this.empty.hidden = this.filtered.length > 0;
      let lastGroup = null;
      this.filtered.forEach((c, i) => {
        if (c.group !== lastGroup) {
          const g = document.createElement("li");
          g.className = "cs-palette__group"; g.setAttribute("role", "presentation");
          g.textContent = c.group; this.list.appendChild(g); lastGroup = c.group;
        }
        const li = document.createElement("li");
        li.className = "cs-opt"; li.id = `cs-opt-${i}`;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", String(i === this.active));
        li.innerHTML =
          `<span class="cs-opt__icon" aria-hidden="true">${c.icon}</span>` +
          `<span class="cs-opt__body"><span class="cs-opt__title">${c.title}</span>` +
          `<span class="cs-opt__hint">${c.hint}</span></span>` +
          `<span class="cs-opt__key cs-kbd">↵</span>`;
        li.addEventListener("pointermove", () => this.setActive(i));
        li.addEventListener("click", () => this.exec(i));
        this.list.appendChild(li);
      });
      this.syncActiveDescendant();
    },
    setActive(i) {
      this.active = i;
      $$(".cs-opt", this.list).forEach((el, n) => el.setAttribute("aria-selected", String(n === i)));
      this.syncActiveDescendant();
    },
    syncActiveDescendant() {
      const opt = this.list.querySelector(`.cs-opt[aria-selected="true"]`);
      this.input.setAttribute("aria-activedescendant", opt ? opt.id : "");
      this.input.setAttribute("aria-expanded", String(this.filtered.length > 0));
      if (opt) opt.scrollIntoView({ block: "nearest" });
    },
    onKey(e) {
      if (e.key === "Escape") { e.preventDefault(); this.close(); return; }
      if (!this.filtered.length) return;
      if (e.key === "ArrowDown") { e.preventDefault(); this.setActive((this.active + 1) % this.filtered.length); }
      else if (e.key === "ArrowUp") { e.preventDefault(); this.setActive((this.active - 1 + this.filtered.length) % this.filtered.length); }
      else if (e.key === "Home") { e.preventDefault(); this.setActive(0); }
      else if (e.key === "End") { e.preventDefault(); this.setActive(this.filtered.length - 1); }
      else if (e.key === "Enter") { e.preventDefault(); this.exec(this.active); }
    },
    exec(i) {
      const c = this.filtered[i]; if (!c) return;
      this.close();
      // Run after close so focus return + scroll target don't fight.
      requestAnimationFrame(() => c.run());
    },
  };

  /* ====================================================== SYSTEMS DRAWER */
  // Contextual controls per state — only relevant actions are surfaced.
  const CONTROLS = {
    NOMINAL:  [],
    SYNCING:  [
      { label: "Follow", icon: "eye",  primary: true,  act: (s) => window.open(s.href, "_blank") },
      { label: "Cancel", icon: "stop", act: (s) => { SimulatedSource.set(s.id, { raw: { state: "inactive" }, detail: "run cancelled by operator" }); Telemetry.refresh(); } },
    ],
    DEGRADED: [
      { label: "View logs", icon: "doc", primary: true, act: (s) => window.open(s.href, "_blank") },
      { label: "Re-sync",   icon: "sync", act: (s) => { SimulatedSource.set(s.id, { raw: { state: "in_progress" }, detail: "operator re-sync requested" }); Telemetry.refresh(); } },
    ],
    FAILURE:  [
      { label: "Re-run",    icon: "sync", primary: true, act: (s) => { SimulatedSource.set(s.id, { raw: { state: "in_progress" }, detail: "re-run dispatched" }); Telemetry.refresh(); } },
      { label: "View logs", icon: "doc",  act: (s) => window.open(s.href, "_blank") },
    ],
  };

  const Drawer = {
    el: null, body: null, meta: null, lastFocus: null, _untrap: null,
    init() {
      this.el = $("[data-cs-drawer]"); this.scrim = $("[data-cs-scrim]");
      if (!this.el) return;
      this.body = $("[data-cs-drawer-body]", this.el);
      this.meta = $("[data-cs-drawer-meta]", this.el);
      $$("[data-cs-drawer-close]", this.el).forEach((b) => b.addEventListener("click", () => this.close()));
      this.scrim.addEventListener("click", () => this.close());
      document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !this.el.hidden) this.close(); });
      Telemetry.subscribe(() => { if (!this.el.hidden) this.render(); });
    },
    open() {
      if (!this.el.hidden) return;
      this.lastFocus = document.activeElement;
      this.scrim.hidden = false; this.el.hidden = false; lockScroll(true);
      this.render();
      // next frame so the transform transition runs from off-canvas
      requestAnimationFrame(() => {
        this.el.classList.add("is-open");
        const first = $(FOCUSABLE, this.el); if (first) first.focus();
      });
      this._untrap = trapFocus(this.el);
    },
    close() {
      if (this.el.hidden) return;
      this.el.classList.remove("is-open");
      const finish = () => { this.el.hidden = true; this.scrim.hidden = true; lockScroll(false);
        if (this._untrap) { this._untrap(); this._untrap = null; }
        if (this.lastFocus && this.lastFocus.focus) this.lastFocus.focus(); };
      if (reduceMotion) finish();
      else { const t = setTimeout(finish, 340); this.el.addEventListener("transitionend", () => { clearTimeout(t); finish(); }, { once: true }); }
    },
    render() {
      const sys = Telemetry.systems;
      this.meta.innerHTML =
        `<span>${sys.length} systems</span>` +
        `<span>global · <b style="color:var(--cs-accent)">${Telemetry.global}</b></span>`;
      this.body.innerHTML = "";
      sys.forEach((s) => {
        const ctrls = CONTROLS[s.state] || [];
        const row = document.createElement("div");
        row.className = "cs-sys"; row.setAttribute("data-state", s.state);
        row.innerHTML =
          `<div class="cs-sys__top">` +
            `<span class="cs-dot ${s.state === "NOMINAL" ? "" : "cs-dot--pulse"}"></span>` +
            `<span class="cs-sys__name">${s.name}</span>` +
            `<span class="cs-pill cs-sys__pill">${s.state}</span>` +
          `</div>` +
          `<div class="cs-sys__detail">${s.detail} · <b>${s.meta}</b></div>` +
          `<div class="cs-sys__actions"></div>`;
        const actWrap = $(".cs-sys__actions", row);
        ctrls.forEach((c) => {
          const b = document.createElement("button");
          b.type = "button";
          b.className = "cs-act" + (c.primary ? " cs-act--primary" : "");
          b.innerHTML = `${ICONS[c.icon] || ""}<span>${c.label}</span>`;
          b.addEventListener("click", () => c.act(s));
          actWrap.appendChild(b);
        });
        this.body.appendChild(row);
      });
    },
  };

  /* ====================================================== BAR + RAIL */
  const Bar = {
    el: null, status: null, label: null, dot: null, clock: null,
    init() {
      this.el = $("[data-cs-bar]"); if (!this.el) return;
      this.status = $("[data-cs-status]", this.el);
      this.label  = $("[data-cs-status-label]", this.el);
      this.dot    = $(".cs-dot", this.status);
      this.clock  = $("[data-cs-clock]", this.el);
      $$("[data-cs-open-palette]").forEach((b) => b.addEventListener("click", () => Palette.open()));
      $$("[data-cs-open-drawer]").forEach((b) => b.addEventListener("click", () => Drawer.open()));

      // Sticky elevation when scrolled.
      const onScroll = () => this.el.classList.toggle("is-stuck", window.scrollY > 8);
      onScroll(); window.addEventListener("scroll", onScroll, { passive: true });

      // Clock (UTC) — independent of console.js footer clock.
      const pad = (n) => String(n).padStart(2, "0");
      const tick = () => { if (!this.clock) return; const d = new Date();
        this.clock.textContent = `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`; };
      tick(); setInterval(tick, 1000);

      this.initScrollSpy();
      Telemetry.subscribe((systems, global) => this.reflect(global));
    },
    reflect(global) {
      if (this.status) this.status.setAttribute("data-state", global);
      if (this.label)  this.label.textContent = global;
      if (this.dot) this.dot.classList.toggle("cs-dot--pulse", global !== STATE.NOMINAL);
    },
    initScrollSpy() {
      const links = $$("[data-cs-nav] a[href^='#']");
      const ids = links.map((a) => a.getAttribute("href").slice(1)).filter(Boolean);
      const sections = ids.map((id) => document.getElementById(id)).filter(Boolean);
      if (!sections.length || !("IntersectionObserver" in window)) return;
      const setCurrent = (id) => links.forEach((a) =>
        a.setAttribute("aria-current", String(a.getAttribute("href") === `#${id}`)));
      const io = new IntersectionObserver((entries) => {
        entries.forEach((en) => { if (en.isIntersecting) setCurrent(en.target.id); });
      }, { rootMargin: "-45% 0px -50% 0px", threshold: 0 });
      sections.forEach((s) => io.observe(s));
    },
  };

  const Rail = {
    init() {
      this.el = $("[data-cs-rail]"); if (!this.el) return;
      this.statusBtn = $("[data-cs-rail-status]", this.el);
      $$("[data-cs-open-palette]", this.el).forEach((b) => b.addEventListener("click", () => Palette.open()));
      $$("[data-cs-open-drawer]", this.el).forEach((b) => b.addEventListener("click", () => Drawer.open()));
      Telemetry.subscribe((systems, global) => {
        if (this.statusBtn) {
          this.statusBtn.setAttribute("data-state", global);
          const lbl = $("[data-cs-rail-status-label]", this.statusBtn);
          if (lbl) lbl.textContent = global;
        }
      });
    },
  };

  /* ====================================================== MOTION TOGGLE */
  function toggleMotion() {
    const root = document.documentElement;
    const off = root.classList.toggle("cs-no-motion");
    try { localStorage.setItem("cs-no-motion", off ? "1" : "0"); } catch (e) {}
  }
  (() => { try { if (localStorage.getItem("cs-no-motion") === "1") document.documentElement.classList.add("cs-no-motion"); } catch (e) {} })();

  /* ====================================================== PUBLIC API + BOOT */
  window.ClearGlassControlSurface = {
    STATE, mapActions, mapDeployment,
    configure({ source, pollMs } = {}) {
      if (source) Telemetry.source = source;
      if (pollMs) Telemetry.pollMs = pollMs;
      Telemetry.start();
    },
    refresh: () => Telemetry.refresh(),
    openPalette: () => Palette.open(),
    openDrawer: () => Drawer.open(),
  };

  const boot = () => { Bar.init(); Rail.init(); Palette.init(); Drawer.init(); Telemetry.start(); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
