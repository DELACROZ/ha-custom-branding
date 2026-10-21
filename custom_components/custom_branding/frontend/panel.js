/* Custom Branding: the "Branding" panel (sidebar). Upload your images, pick colors, save. No restart needed. */
const TEXT = {
  en: {
    title: "Custom Branding",
    intro: "Your name, logo and colors on the login page, the loading screen and the installed app. Changes apply as soon as you save.",
    identity: "Identity", name: "Name", nameHelp: "Shown in the tab title, sidebar and as the app name.",
    shortName: "Short name", shortHelp: "Name under the app icon on the phone (about 12 letters).",
    loadingText: "Loading text", loadingHelp: "Text under the spinner. Leave empty to hide it.",
    welcomeText: "Login screen text", welcomeHelp: "Replaces \"Welcome Home!\" on the login page. Leave empty to keep the default.",
    footerLink: "Help link (bottom of login page)", footerHelp: "Replace it with a WhatsApp or Instagram button, or remove it.",
    footerDefault: "Default (link to Home Assistant docs)", footerHide: "Remove it", footerWhatsapp: "WhatsApp button", footerInstagram: "Instagram button",
    footerWhatsappValue: "WhatsApp number (with country code, e.g. 5564999999999)", footerInstagramValue: "Instagram username (e.g. iot_now_automacoes)",
    images: "Images", logo: "Logo", logoHelp: "Shown on the loading screen and the login page. PNG, JPEG, WebP or SVG.",
    blackBg: "My logo has a black background (make it transparent)",
    autoIcon: "Create the app icon from the logo", icon: "App icon (square)", maskable: "Maskable icon (Android)",
    chooseFile: "Choose file", noImage: "no image yet",
    colors: "Colors", background: "Background", accent: "Accent", text: "Text",
    options: "Options", hideHa: "Hide the Home Assistant logo on the loading screen",
    hideOhf: "Hide the \"Open Home Foundation\" footer", sidebarTitle: "Replace the sidebar title", tabTitle: "Replace the browser tab title",
    preview: "Preview (loading screen)", save: "Save", reset: "Reset to default",
    saved: "Saved. Reload the page with Ctrl+F5 to see it. Apps that are already installed must be uninstalled and installed again to get the new icon.",
    uploading: "Uploading…", failed: "Something went wrong: ", confirmReset: "Remove all branding and the uploaded images?",
    backupNote: "Tip: this only changes what your instance shows; it does not touch your configuration.",
  },
  pt: {
    title: "Custom Branding",
    intro: "Seu nome, logo e cores na tela de login, na tela de carregamento e no app instalado. As mudanças valem assim que você salva.",
    identity: "Identidade", name: "Nome", nameHelp: "Aparece no título da aba, na barra lateral e como nome do app.",
    shortName: "Nome curto", shortHelp: "Nome embaixo do ícone no celular (uns 12 caracteres).",
    loadingText: "Texto de carregamento", loadingHelp: "Texto embaixo da bolinha. Deixe vazio para esconder.",
    welcomeText: "Texto da tela de login", welcomeHelp: "Substitui \"Bem-vindo ao lar!\" na tela de login. Deixe vazio para manter o padrão.",
    footerLink: "Link de ajuda (rodapé da tela de login)", footerHelp: "Troca por um botão do WhatsApp ou Instagram, ou remove.",
    footerDefault: "Padrão (link para a documentação do Home Assistant)", footerHide: "Remover", footerWhatsapp: "Botão do WhatsApp", footerInstagram: "Botão do Instagram",
    footerWhatsappValue: "Número do WhatsApp (com DDI, ex: 5564999999999)", footerInstagramValue: "Usuário do Instagram (ex: iot_now_automacoes)",
    images: "Imagens", logo: "Logo", logoHelp: "Aparece na tela de carregamento e na de login. PNG, JPEG, WebP ou SVG.",
    blackBg: "Minha logo tem fundo preto (tornar transparente)",
    autoIcon: "Criar o ícone do app a partir da logo", icon: "Ícone do app (quadrado)", maskable: "Ícone maskable (Android)",
    chooseFile: "Escolher arquivo", noImage: "nenhuma imagem ainda",
    colors: "Cores", background: "Fundo", accent: "Destaque", text: "Texto",
    options: "Opções", hideHa: "Esconder o logo do Home Assistant na tela de carregamento",
    hideOhf: "Esconder o rodapé \"Open Home Foundation\"", sidebarTitle: "Trocar o título da barra lateral", tabTitle: "Trocar o título da aba do navegador",
    preview: "Prévia (tela de carregamento)", save: "Salvar", reset: "Voltar ao padrão",
    saved: "Salvo. Recarregue a página com Ctrl+F5 para ver. Apps já instalados precisam ser desinstalados e instalados de novo para pegar o ícone novo.",
    uploading: "Enviando…", failed: "Algo deu errado: ", confirmReset: "Remover toda a marca e as imagens enviadas?",
    backupNote: "Dica: isso só muda o que a sua instância mostra; não mexe na sua configuração.",
  },
};

const DEFAULT_COLORS = { background_color: "#04060a", accent_color: "#00d9ff", text_color: "#eef7ff" };

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("could not read the image"));
    img.src = url;
  });
}

/** Draw the logo on a canvas (max 900 px wide), optionally turning a black background transparent, trimmed. */
function processLogo(img, removeBlack) {
  const nw = img.naturalWidth || 600, nh = img.naturalHeight || 200;
  const sc = Math.min(1, 900 / nw);
  const w = Math.max(1, Math.round(nw * sc)), h = Math.max(1, Math.round(nh * sc));
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const ctx = c.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, w, h);
  const data = ctx.getImageData(0, 0, w, h);
  const px = data.data;
  if (removeBlack) {
    for (let i = 0; i < px.length; i += 4) {
      const m = Math.max(px[i], px[i + 1], px[i + 2]) / 255;
      const a = Math.min(1, Math.max(0, (m - 0.045) * 1.12));
      if (a > 0.004) { px[i] = Math.min(255, px[i] / a); px[i + 1] = Math.min(255, px[i + 1] / a); px[i + 2] = Math.min(255, px[i + 2] / a); }
      else { px[i] = px[i + 1] = px[i + 2] = 0; }
      px[i + 3] = Math.round(a * 255);
    }
    ctx.putImageData(data, 0, 0);
  }
  // trim transparent borders
  let x0 = w, y0 = h, x1 = 0, y1 = 0;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (px[(y * w + x) * 4 + 3] > 14) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  if (x1 <= x0 || y1 <= y0) return c;
  const pad = 14;
  const sx = Math.max(0, x0 - pad), sy = Math.max(0, y0 - pad);
  const sw = Math.min(w, x1 + pad) - sx, sh = Math.min(h, y1 + pad) - sy;
  const out = document.createElement("canvas");
  out.width = sw; out.height = sh;
  out.getContext("2d").drawImage(c, sx, sy, sw, sh, 0, 0, sw, sh);
  return out;
}

function makeIcon(logoCanvas, size, bg, fill) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const ctx = c.getContext("2d");
  ctx.fillStyle = bg; ctx.fillRect(0, 0, size, size);
  const max = size * fill;
  const sc = Math.min(max / logoCanvas.width, max / logoCanvas.height);
  const w = logoCanvas.width * sc, h = logoCanvas.height * sc;
  ctx.drawImage(logoCanvas, (size - w) / 2, (size - h) / 2, w, h);
  return c;
}

const toBlob = (canvas) => new Promise((res) => canvas.toBlob(res, "image/png"));

class CustomBrandingPanel extends HTMLElement {
  constructor() {
    super();
    this._s = {};
    this._defaults = {};
    this._ready = false;
    this._status = "";
    this._busy = false;
  }
  set hass(h) {
    this._hass = h;
    this._t = TEXT[(h.language || "en").toLowerCase().startsWith("pt") ? "pt" : "en"];
    if (!this._started) { this._started = true; this._load(); }
    const menu = this.querySelector("ha-menu-button");
    if (menu) { menu.hass = h; menu.narrow = this._narrow; }
  }
  set narrow(v) { this._narrow = v; const m = this.querySelector("ha-menu-button"); if (m) m.narrow = v; }
  set panel(_v) {}
  set route(_v) {}

  async _load() {
    try {
      const r = await this._hass.callWS({ type: "custom_branding/get" });
      this._s = { ...r.settings };
      this._defaults = r.defaults || {};
      this._ready = true;
      this._render();
    } catch (e) {
      this.innerHTML = `<p style="padding:24px">${e.message || e}</p>`;
    }
  }

  _val(k) { return this._s[k] !== undefined ? this._s[k] : (this._defaults[k] ?? ""); }
  _color(k) { const v = this._val(k); return /^#[0-9a-fA-F]{6}$/.test(v) ? v : DEFAULT_COLORS[k]; }

  _render() {
    const t = this._t, s = this._s;
    const imgRow = (key, label, help) => `
      <div class="row">
        <div class="lab"><b>${label}</b>${help ? `<small>${help}</small>` : ""}</div>
        <div class="img"><span class="thumb ${key}">${s[key] ? `<img src="${s[key]}" alt="">` : `<em>${t.noImage}</em>`}</span>
          <label class="btn small">${t.chooseFile}<input type="file" accept="image/*" data-up="${key}" hidden></label></div>
      </div>`;
    this.innerHTML = `
      <style>
        :host, custom-branding-panel { display:block; background:var(--primary-background-color); min-height:100%; color:var(--primary-text-color); }
        .bar { display:flex; align-items:center; gap:8px; height:56px; padding:0 16px; background:var(--app-header-background-color, var(--card-background-color)); border-bottom:1px solid var(--divider-color); }
        .bar h1 { font-size:20px; font-weight:500; margin:0; }
        .wrap { max-width:960px; margin:0 auto; padding:16px; display:grid; gap:16px; }
        .intro { color:var(--secondary-text-color); margin:4px 2px 0; }
        .card { background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:14px; padding:16px 18px; }
        .card h2 { font-size:16px; margin:0 0 12px; }
        .row { display:grid; grid-template-columns:minmax(140px,1fr) 2fr; gap:12px; align-items:center; padding:8px 0; border-top:1px solid var(--divider-color); }
        .row:first-of-type { border-top:0; }
        .lab small { display:block; color:var(--secondary-text-color); font-size:12px; margin-top:2px; }
        input[type=text], select { width:100%; box-sizing:border-box; padding:10px 12px; border-radius:8px; border:1px solid var(--divider-color); background:var(--primary-background-color); color:var(--primary-text-color); font:inherit; }
        input[type=color] { width:56px; height:36px; padding:0; border:1px solid var(--divider-color); border-radius:8px; background:none; }
        .colors { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
        .colors label { display:flex; flex-direction:column; gap:6px; font-size:13px; color:var(--secondary-text-color); }
        .img { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
        .thumb { display:grid; place-items:center; min-width:120px; height:64px; padding:6px; border-radius:10px; background:#04060a; border:1px solid var(--divider-color); }
        .thumb.icon, .thumb.icon_maskable { width:64px; min-width:64px; }
        .thumb img { max-width:200px; max-height:52px; object-fit:contain; } .thumb.icon img, .thumb.icon_maskable img { max-width:52px; }
        .thumb em { color:#8896a6; font-size:11px; }
        .btn { display:inline-flex; align-items:center; justify-content:center; padding:9px 16px; border-radius:20px; border:1px solid var(--primary-color); color:var(--primary-color); background:transparent; cursor:pointer; font:inherit; font-weight:500; }
        .btn.primary { background:var(--primary-color); color:var(--text-primary-color, #fff); }
        .btn.small { padding:6px 12px; font-size:13px; } .btn[disabled] { opacity:.5; pointer-events:none; }
        .chk { display:flex; align-items:center; gap:8px; padding:6px 0; }
        .preview { display:grid; place-items:center; height:220px; border-radius:12px; position:relative; overflow:hidden; }
        .preview .in { display:flex; flex-direction:column; align-items:center; gap:18px; }
        .preview img { max-width:60%; max-height:70px; } .ring { width:30px; height:30px; border-radius:50%; border:3px solid; animation:sp 1s linear infinite; }
        .preview small { font:600 10px Roboto,Arial; letter-spacing:.3em; text-transform:uppercase; }
        @keyframes sp { to { transform:rotate(360deg); } }
        .actions { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
        .status { color:var(--secondary-text-color); font-size:13px; flex:1; min-width:200px; }
        @media (max-width:640px) { .row { grid-template-columns:1fr; } .colors { grid-template-columns:1fr 1fr; } }
      </style>
      <div class="bar"><ha-menu-button></ha-menu-button><h1>${t.title}</h1></div>
      <div class="wrap">
        <p class="intro">${t.intro}</p>
        <section class="card"><h2>${t.identity}</h2>
          <div class="row"><div class="lab"><b>${t.name}</b><small>${t.nameHelp}</small></div><input type="text" data-k="name" value="${this._esc(s.name)}"></div>
          <div class="row"><div class="lab"><b>${t.shortName}</b><small>${t.shortHelp}</small></div><input type="text" data-k="short_name" value="${this._esc(s.short_name)}"></div>
          <div class="row"><div class="lab"><b>${t.loadingText}</b><small>${t.loadingHelp}</small></div><input type="text" data-k="loading_text" value="${this._esc(s.loading_text !== undefined ? s.loading_text : (this._defaults.loading_text || ""))}"></div>
          <div class="row"><div class="lab"><b>${t.welcomeText}</b><small>${t.welcomeHelp}</small></div><input type="text" data-k="welcome_text" value="${this._esc(s.welcome_text)}"></div>
          <div class="row"><div class="lab"><b>${t.footerLink}</b><small>${t.footerHelp}</small></div>
            <select data-k="footer_link">
              <option value="" ${!s.footer_link ? "selected" : ""}>${t.footerDefault}</option>
              <option value="hide" ${s.footer_link === "hide" ? "selected" : ""}>${t.footerHide}</option>
              <option value="whatsapp" ${s.footer_link === "whatsapp" ? "selected" : ""}>${t.footerWhatsapp}</option>
              <option value="instagram" ${s.footer_link === "instagram" ? "selected" : ""}>${t.footerInstagram}</option>
            </select>
          </div>
          ${s.footer_link === "whatsapp" || s.footer_link === "instagram" ? `
          <div class="row"><div class="lab"><b>${s.footer_link === "whatsapp" ? t.footerWhatsappValue : t.footerInstagramValue}</b></div>
            <input type="text" data-k="footer_link_value" value="${this._esc(s.footer_link_value)}"></div>` : ""}
        </section>
        <section class="card"><h2>${t.images}</h2>
          ${imgRow("logo", t.logo, t.logoHelp)}
          <label class="chk"><input type="checkbox" id="blackbg"> ${t.blackBg}</label>
          <label class="chk"><input type="checkbox" id="autoicon" checked> ${t.autoIcon}</label>
          ${imgRow("icon", t.icon)}
          ${imgRow("icon_maskable", t.maskable)}
        </section>
        <section class="card"><h2>${t.colors}</h2>
          <div class="colors">
            <label>${t.background}<input type="color" data-k="background_color" value="${this._color("background_color")}"></label>
            <label>${t.accent}<input type="color" data-k="accent_color" value="${this._color("accent_color")}"></label>
            <label>${t.text}<input type="color" data-k="text_color" value="${this._color("text_color")}"></label>
          </div>
        </section>
        <section class="card"><h2>${t.options}</h2>
          ${[["hide_ha_logo", t.hideHa], ["hide_open_home_foundation", t.hideOhf], ["sidebar_title", t.sidebarTitle], ["tab_title", t.tabTitle]].map(([k, l]) =>
            `<label class="chk"><input type="checkbox" data-b="${k}" ${this._bool(k) ? "checked" : ""}> ${l}</label>`).join("")}
        </section>
        <section class="card"><h2>${t.preview}</h2><div class="preview" id="pv"></div></section>
        <div class="actions"><button class="btn primary" id="save">${t.save}</button><button class="btn" id="reset">${t.reset}</button>
          <span class="status" id="status">${this._status}</span></div>
        <p class="intro">${t.backupNote}</p>
      </div>`;
    const menu = this.querySelector("ha-menu-button");
    if (menu) { menu.hass = this._hass; menu.narrow = this._narrow; }
    this._wire();
    this._preview();
  }

  _esc(v) { return String(v ?? "").replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;"); }
  _bool(k) { return this._s[k] !== undefined ? !!this._s[k] : this._defaults[k] !== false; }

  _wire() {
    this.querySelectorAll("[data-k]").forEach((el) => {
      const isSelect = el.tagName === "SELECT";
      el.addEventListener(isSelect ? "change" : "input", () => {
        this._s[el.dataset.k] = el.value;
        if (isSelect) this._render(); else this._preview();
      });
    });
    this.querySelectorAll("[data-b]").forEach((el) => el.addEventListener("change", () => { this._s[el.dataset.b] = el.checked; }));
    this.querySelectorAll("[data-up]").forEach((el) => el.addEventListener("change", () => el.files[0] && this._upload(el.dataset.up, el.files[0])));
    this.querySelector("#save").addEventListener("click", () => this._save());
    this.querySelector("#reset").addEventListener("click", () => this._reset());
  }

  _preview() {
    const pv = this.querySelector("#pv");
    if (!pv) return;
    const bg = this._color("background_color"), ac = this._color("accent_color");
    pv.style.background = `radial-gradient(60% 70% at 50% 45%, color-mix(in srgb, ${ac} 18%, transparent), transparent 72%), ${bg}`;
    const logo = this._s.logo ? `<img src="${this._s.logo}" alt="">` : "";
    const txt = this._s.loading_text !== undefined ? this._s.loading_text : (this._defaults.loading_text || "");
    pv.innerHTML = `<div class="in">${logo}<div class="ring" style="border-color:color-mix(in srgb, ${ac} 16%, transparent);border-top-color:${ac};border-right-color:${ac}"></div>${txt ? `<small style="color:${ac}">${this._esc(txt)}</small>` : ""}</div>`;
  }

  _setStatus(msg) { this._status = msg; const el = this.querySelector("#status"); if (el) el.textContent = msg; }

  async _post(kind, blob) {
    const resp = await this._hass.fetchWithAuth(`/api/custom_branding/upload/${kind}`, { method: "POST", body: blob, headers: { "Content-Type": blob.type || "image/png" } });
    if (!resp.ok) { let m = resp.statusText; try { m = (await resp.json()).message || m; } catch (e) { /* ignore */ } throw new Error(m); }
    return (await resp.json()).url;
  }

  async _upload(kind, file) {
    const t = this._t;
    try {
      this._setStatus(t.uploading);
      const img = await loadImage(file);
      if (kind === "logo") {
        const canvas = processLogo(img, this.querySelector("#blackbg").checked);
        this._s.logo = await this._post("logo", await toBlob(canvas));
        if (this.querySelector("#autoicon").checked) {
          const bg = this._color("background_color");
          this._s.icon = await this._post("icon", await toBlob(makeIcon(canvas, 512, bg, 0.78)));
          this._s.icon_maskable = await this._post("icon_maskable", await toBlob(makeIcon(canvas, 512, bg, 0.56)));
        }
      } else {
        const c = document.createElement("canvas");
        c.width = c.height = 512;
        c.getContext("2d").drawImage(img, 0, 0, 512, 512);
        this._s[kind] = await this._post(kind, await toBlob(c));
      }
      this._render();
      this._setStatus("");
    } catch (e) {
      this._setStatus(t.failed + (e.message || e));
    }
  }

  async _save() {
    const t = this._t;
    try {
      const settings = { ...this._s };
      const r = await this._hass.callWS({ type: "custom_branding/save", settings });
      this._s = { ...r.settings };
      this._setStatus(t.saved);
    } catch (e) {
      this._setStatus(t.failed + (e.message || e));
    }
  }

  async _reset() {
    const t = this._t;
    if (!confirm(t.confirmReset)) return;
    try {
      await this._hass.callWS({ type: "custom_branding/reset" });
      this._s = {};
      this._render();
      this._setStatus(t.saved);
    } catch (e) {
      this._setStatus(t.failed + (e.message || e));
    }
  }
}

if (!customElements.get("custom-branding-panel")) customElements.define("custom-branding-panel", CustomBrandingPanel);
