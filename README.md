<p align="center"><img src="docs/iotnow-logo.png" alt="IoT Now" height="70"></p>

# Custom Branding for Home Assistant

**Make Home Assistant look like *your* product.** Put your own name, logo and colors on the **login page**, the **loading screen**, the **installed app (PWA)** icon and name, the **sidebar title** and the **browser tab title** — without editing any core file and without a reverse proxy.

> Perfect for installers, integrators, resellers and anyone who gives Home Assistant to a client, a family member or a company and wants it to carry their brand. (🇧🇷 Versão em português logo abaixo.)

| Loading screen | Login page |
| --- | --- |
| ![Loading screen](docs/splash.png) | ![Login page](docs/login.png) |

*(Example brand: IoT Now. The logo, name and colors are all yours to set.)*

## What it changes

| Where | What you get |
| --- | --- |
| **Loading screen** (the "Loading…" page after F5) | Your logo, a spinning ring in your accent color, your own text. The Home Assistant logo and the "Open Home Foundation" footer are hidden. |
| **Login page** | Your logo on top instead of the blue Home Assistant icon, your background and accent colors. |
| **Installed app / "Add to Home Screen" (PWA)** | Your app **name** and **icon** (Chrome, Edge, Android, iOS). |
| **Sidebar title** and **browser tab title** | "My Home" instead of "Home Assistant". |

Everything is optional: only the options you set are applied.

## Install

### With HACS (custom repository)
1. HACS → ⋮ → **Custom repositories** → add `https://github.com/DELACROZ/ha-custom-branding` as category **Integration**.
2. Download **Custom Branding**, then restart Home Assistant.

### Manual
Copy `custom_components/custom_branding` into your `/config/custom_components/` folder and restart.

## Configure

1. Put your images in `/config/www/branding/` (they are served at `/local/branding/...`):
   * `logo.png` — transparent PNG (wide logos work best), used on the loading screen and the login page. Made for dark backgrounds.
   * `icon-512.png` — square PNG (512×512), used as the app icon and favicon.
   * `icon-maskable.png` — optional, 512×512 with about 20 % padding, for Android adaptive icons.
2. Add to `configuration.yaml` and restart:

```yaml
custom_branding:
  name: "My Smart Home"
  short_name: "Smart Home"
  logo: /local/branding/logo.png
  icon: /local/branding/icon-512.png
  icon_maskable: /local/branding/icon-maskable.png
  background_color: "#0b1220"
  accent_color: "#38bdf8"
  text_color: "#eef7ff"
  loading_text: "Loading"
```

| Option | Default | Description |
| --- | --- | --- |
| `name` | *(unchanged)* | Name used in the tab title, sidebar, app name and metadata. |
| `short_name` | first 20 chars of `name` | Name under the app icon on the phone. |
| `logo` | – | Path/URL of the logo for the loading screen and login page. |
| `icon` | – | Path/URL of the square app icon and favicon. |
| `icon_maskable` | – | Optional maskable icon for Android. |
| `background_color` | `#04060a` | Background of the loading/login screens and the app's theme color. |
| `accent_color` | `#00d9ff` | Spinner, buttons, links and glow on the login page. |
| `text_color` | `#eef7ff` | Text color on the login page. |
| `loading_text` | `Loading` | Text under the spinner (empty string hides it). |
| `hide_ha_logo` | `true` | Hide the Home Assistant logo on the loading screen (needs `logo`). |
| `hide_open_home_foundation` | `true` | Hide the "A project from the Open Home Foundation" footer. |
| `sidebar_title` | `true` | Replace "Home Assistant" in the sidebar with `name`. |
| `tab_title` | `true` | Replace "Home Assistant" in the browser tab title with `name`. |

Colors accept `#rrggbb`, `rgb()/hsl()` or color names. Paths accept anything under `/local/` (or any public URL).

## Good to know

* **Cache:** after changing the settings, restart Home Assistant and reload the page with **Ctrl+F5** (on phones, clear the site data once). The generated files carry a version in their URL, so later changes are picked up automatically.
* **Already installed apps (PWA)** keep their old name/icon: uninstall and install again to get the new ones.
* **Light themes:** the login/loading screens are designed with a dark background. Pick a dark `background_color`.
* **Trademark note:** this only changes what *your* instance shows. Home Assistant and the Home Assistant logo are trademarks of the Open Home Foundation.

## How it works

Home Assistant renders the login page and the loading screen from fixed HTML files that no setting, theme or `extra_module_url` can reach. Custom Branding wraps the two web routes that serve them (`/` and `/auth/authorize`) and adds one `<link>`/`<script>` pair plus a few attribute swaps. Its own generated assets are served from `/custom_branding/` (public, because the login page needs them before anyone is signed in). If anything goes wrong, the original page is served untouched and a warning is logged.

It does **not** modify any Home Assistant file and keeps no state. To remove it: delete the `custom_branding:` block, remove the integration folder and restart.

## Troubleshooting

* *Nothing changed* → check **Settings → System → Logs** for `custom_branding`. Make sure the YAML key is at the top level and the image paths open in your browser (e.g. `https://your-ha/local/branding/logo.png`).
* *Logo looks too small/large* → use a transparent PNG cropped tight around the artwork.
* *Works on the home page but not the login* → hard-reload the login page; browsers cache it.

## Tests

`python tests/test_assets.py` (no Home Assistant needed) checks the HTML rewriting against real captured pages.

## Credits

Created by **Marcelo Junior ([@DELACROZ](https://github.com/DELACROZ))** · **IoT Now** — smart homes, offices and telemetry in Caldas Novas, Goiás, Brazil.
Born from a real client project and shared with the community. Issues and pull requests are welcome.

🌐 [marceloautomacoesgo.com.br](https://marceloautomacoesgo.com.br) · 📸 [@iot_now_automacoes](https://www.instagram.com/iot_now_automacoes)
Need a custom Home Assistant project, white-label setup or automation consulting? Get in touch through the website.

MIT licensed.

---

# 🇧🇷 Português

**Deixe o Home Assistant com a *sua* marca.** Coloque seu nome, logo e cores na **tela de login**, na **tela de carregamento**, no **ícone e nome do app instalado (PWA)**, no **título da barra lateral** e no **título da aba** — sem mexer em arquivos do sistema e sem proxy reverso.

**Instalação (HACS):** HACS → ⋮ → *Repositórios personalizados* → `https://github.com/DELACROZ/ha-custom-branding` → categoria *Integração* → baixar **Custom Branding** → reiniciar.

**Configuração:** coloque suas imagens em `/config/www/branding/` (`logo.png` transparente, `icon-512.png` quadrado) e adicione ao `configuration.yaml`:

```yaml
custom_branding:
  name: "Minha Casa Inteligente"
  short_name: "Minha Casa"
  logo: /local/branding/logo.png
  icon: /local/branding/icon-512.png
  background_color: "#0b1220"
  accent_color: "#38bdf8"
  loading_text: "Carregando"
```

Reinicie o Home Assistant e recarregue a página com **Ctrl+F5**. Para o app instalado mudar, desinstale e instale de novo. Todas as opções estão na tabela acima.

**Criado por Marcelo Junior ([@DELACROZ](https://github.com/DELACROZ))** · **IoT Now** — casas e escritórios inteligentes e telemetria em Caldas Novas, Goiás. Site: [marceloautomacoesgo.com.br](https://marceloautomacoesgo.com.br) · Instagram: [@iot_now_automacoes](https://www.instagram.com/iot_now_automacoes).
