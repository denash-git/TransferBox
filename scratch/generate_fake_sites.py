import os
import shutil

# Destination path for the fakesite templates
DEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", "fakesite"))

# Define the HTML and CSS for each site individually to ensure maximum variety

# =============================================================================
# 1. AETHER RESONANCE (Cyberpunk Retro-Terminal Diagnostic Console)
# =============================================================================
AETHER_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background-color: #050805;
  color: #33ff33;
  font-family: "Courier New", Courier, monospace;
  font-size: 0.95rem;
  line-height: 1.5;
  padding: 20px;
}
.console-box {
  border: 2px solid #33ff33;
  box-shadow: 0 0 15px rgba(51,255,51,0.2);
  max-width: 1000px;
  margin: 0 auto;
  background-color: #020402;
  border-radius: 4px;
  overflow: hidden;
}
.console-header {
  background-color: #33ff33;
  color: #020402;
  padding: 8px 15px;
  font-weight: bold;
  display: flex;
  justify-content: space-between;
}
.nav-bar {
  display: flex;
  background-color: #112211;
  border-bottom: 2px solid #33ff33;
}
.nav-link {
  color: #33ff33;
  text-decoration: none;
  padding: 10px 20px;
  border-right: 1px solid #33ff33;
  font-weight: bold;
}
.nav-link:hover, .nav-link.active {
  background-color: #33ff33;
  color: #020402;
}
.content-area { padding: 30px; }
.hero-title { font-size: 2.2rem; margin-bottom: 15px; border-bottom: 1px dashed #33ff33; padding-bottom: 10px; }
.blink { animation: blink-animation 1s steps(2, start) infinite; }
@keyframes blink-animation { to { visibility: hidden; } }
.section-title { font-size: 1.5rem; margin: 25px 0 15px 0; text-transform: uppercase; color: #88ff88; }
.grid-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }
.grid-card { border: 1px solid #33ff33; padding: 20px; background-color: #050a05; }
.grid-card h3 { font-size: 1.2rem; margin-bottom: 10px; color: #88ff88; }
.terminal-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
.terminal-table th, .terminal-table td { border: 1px solid #33ff33; padding: 10px; text-align: left; }
.terminal-table th { background-color: #112211; }
.form-input {
  width: 100%;
  background: #020402;
  border: 1px solid #33ff33;
  color: #33ff33;
  padding: 10px;
  font-family: monospace;
  margin-top: 5px;
}
.btn-submit {
  background-color: #33ff33;
  color: #020402;
  border: none;
  padding: 10px 20px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 15px;
  font-family: monospace;
}
.btn-submit:hover { background-color: #88ff88; }
.footer { border-top: 2px solid #33ff33; padding: 15px; text-align: center; font-size: 0.8rem; background-color: #090e09; }
"""

AETHER_LAYOUT = """
<div class="console-box">
  <div class="console-header">
    <span>SYSTEM MONITOR v8.241</span>
    <span>STATUS: OPERATIONAL</span>
  </div>
  <div class="nav-bar">
    <a href="index.html" class="nav-link {active_home}">[ HOME ]</a>
    <a href="services.html" class="nav-link {active_serv}">[ DIAGNOSTICS ]</a>
    <a href="about.html" class="nav-link {active_about}">[ ABOUT LOG ]</a>
    <a href="contacts.html" class="nav-link {active_cont}">[ CALIBRATE ]</a>
  </div>
  <div class="content-area">
    {content}
  </div>
  <div class="footer">
    AETHER_RESONANCE_NET_OPERATIONS © 2026 // NO_PERSONAL_DATA_FOUND // SECURITY: ENABLED
  </div>
</div>
"""

# =============================================================================
# 2. QUANTUM NEXUS (Ultra-Modern Premium Dark Corporate Landing Page)
# =============================================================================
NEXUS_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background-color: #030712;
  color: #9ca3af;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  line-height: 1.6;
}
header {
  background-color: rgba(3, 7, 18, 0.85);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid #1f2937;
}
.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
.logo {
  font-size: 1.5rem;
  font-weight: 800;
  color: #f3f4f6;
  text-decoration: none;
  background: linear-gradient(to right, #00ffcc, #00b0ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.nav-menu { display: flex; list-style: none; gap: 30px; }
.nav-menu a { color: #9ca3af; text-decoration: none; font-weight: 500; transition: color 0.3s; }
.nav-menu a:hover, .nav-menu a.active { color: #00ffcc; }
.hero {
  padding: 100px 20px;
  text-align: center;
  background: radial-gradient(circle at center, rgba(0,255,204,0.08) 0%, transparent 70%);
}
.hero h1 {
  font-size: 3.5rem;
  font-weight: 900;
  color: #f9fafb;
  line-height: 1.1;
  margin-bottom: 25px;
}
.hero p { font-size: 1.25rem; max-width: 700px; margin: 0 auto 35px auto; color: #9ca3af; }
.btn-premium {
  display: inline-block;
  background: linear-gradient(to right, #00ffcc, #00b0ff);
  color: #030712;
  padding: 14px 35px;
  border-radius: 30px;
  text-decoration: none;
  font-weight: 700;
  transition: transform 0.3s, box-shadow 0.3s;
}
.btn-premium:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0,255,204,0.25);
}
.section { padding: 80px 20px; max-width: 1200px; margin: 0 auto; }
.section h2 { font-size: 2.2rem; color: #f9fafb; margin-bottom: 40px; text-align: center; }
.cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 30px; }
.nexus-card {
  background-color: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 35px;
  transition: border-color 0.3s, transform 0.3s;
}
.nexus-card:hover { border-color: #00ffcc; transform: translateY(-5px); }
.nexus-card h3 { font-size: 1.4rem; color: #f3f4f6; margin-bottom: 15px; }
.contact-container {
  max-width: 600px;
  margin: 0 auto;
  background-color: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 20px;
  padding: 40px;
}
.form-input {
  width: 100%;
  padding: 12px 18px;
  background-color: #030712;
  border: 1px solid #1e293b;
  color: #f3f4f6;
  border-radius: 8px;
  margin-top: 8px;
  outline: none;
}
.form-input:focus { border-color: #00ffcc; }
.footer { background-color: #020617; border-top: 1px solid #1f2937; padding: 40px 20px; text-align: center; }
"""

NEXUS_LAYOUT = """
<header>
  <div class="nav-container">
    <a href="index.html" class="logo">QUANTUM_NEXUS</a>
    <ul class="nav-menu">
      <li><a href="index.html" class="{active_home}">Главная</a></li>
      <li><a href="services.html" class="{active_serv}">Спектры</a></li>
      <li><a href="about.html" class="{active_about}">Концепт</a></li>
      <li><a href="contacts.html" class="{active_cont}">Связь</a></li>
    </ul>
  </div>
</header>
{content}
<footer class="footer">
  <p>© 2026 Quantum Nexus Operations. Все данные зашифрованы алгоритмом фазовой модуляции.</p>
</footer>
"""

# =============================================================================
# 3. SYNAPTIC DYNAMICS (Trendy Neo-Brutalist Minimalist Design)
# =============================================================================
SYNAPSE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background-color: #fbfbf6;
  color: #1a1a1a;
  font-family: "Helvetica Neue", Arial, sans-serif;
  padding: 20px;
}
.brutal-container {
  max-width: 1100px;
  margin: 0 auto;
  border: 4px solid #1a1a1a;
  background: #ffffff;
  box-shadow: 10px 10px 0px #1a1a1a;
}
.header {
  border-bottom: 4px solid #1a1a1a;
  padding: 30px;
  background-color: #ffde4d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.logo { font-size: 2.2rem; font-weight: 900; letter-spacing: -2px; text-transform: uppercase; color: #1a1a1a; text-decoration: none; }
.nav-links { display: flex; gap: 15px; }
.nav-btn {
  background-color: #ffffff;
  border: 2px solid #1a1a1a;
  padding: 8px 16px;
  font-weight: 800;
  text-decoration: none;
  color: #1a1a1a;
  box-shadow: 3px 3px 0px #1a1a1a;
}
.nav-btn:hover, .nav-btn.active {
  background-color: #ff4069;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 5px 5px 0px #1a1a1a;
}
.hero {
  padding: 60px 40px;
  background-color: #ff764d;
  border-bottom: 4px solid #1a1a1a;
}
.hero h1 { font-size: 3.5rem; font-weight: 900; line-height: 1; letter-spacing: -1px; margin-bottom: 20px; text-transform: uppercase; }
.hero p { font-size: 1.2rem; font-weight: 500; max-width: 600px; }
.section { padding: 50px 40px; }
.section-title { font-size: 2.5rem; font-weight: 900; text-transform: uppercase; margin-bottom: 30px; }
.brutal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; }
.brutal-card {
  border: 4px solid #1a1a1a;
  padding: 30px;
  background-color: #a6e3e9;
  box-shadow: 8px 8px 0px #1a1a1a;
}
.brutal-card.alt { background-color: #cbd5e1; }
.brutal-card h3 { font-size: 1.5rem; font-weight: 800; text-transform: uppercase; margin-bottom: 15px; }
.form-field {
  width: 100%;
  padding: 12px;
  border: 3px solid #1a1a1a;
  font-weight: bold;
  margin-top: 8px;
  outline: none;
  font-size: 1rem;
}
.btn-brutal {
  display: inline-block;
  background-color: #ffde4d;
  border: 3px solid #1a1a1a;
  padding: 15px 30px;
  font-weight: 900;
  text-transform: uppercase;
  cursor: pointer;
  box-shadow: 5px 5px 0px #1a1a1a;
  margin-top: 20px;
}
.btn-brutal:hover {
  transform: translate(-3px, -3px);
  box-shadow: 8px 8px 0px #1a1a1a;
}
.footer { border-top: 4px solid #1a1a1a; padding: 25px; text-align: center; font-weight: 800; background-color: #a6e3e9; }
"""

SYNAPSE_LAYOUT = """
<div class="brutal-container">
  <div class="header">
    <a href="index.html" class="logo">SYNAPSE_DYN</a>
    <div class="nav-links">
      <a href="index.html" class="nav-btn {active_home}">Главная</a>
      <a href="services.html" class="nav-btn {active_serv}">Синергия</a>
      <a href="about.html" class="nav-btn {active_about}">Профиль</a>
      <a href="contacts.html" class="nav-btn {active_cont}">Связь</a>
    </div>
  </div>
  {content}
  <div class="footer">
    SYNAPTIC_DYNAMICS_LABS // 2026 // АВТОГЕНЕРАЦИЯ ВЕКТОРОВ
  </div>
</div>
"""

# =============================================================================
# 4. CHRONOS TEMPORAL (Elegantly Structured Classical Academic Portal)
# =============================================================================
CHRONOS_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background-color: #fdfaf2;
  color: #3b3a36;
  font-family: Georgia, "Times New Roman", Times, serif;
  line-height: 1.7;
}
.wrapper {
  max-width: 1200px;
  margin: 0 auto;
  background-color: #ffffff;
  border-left: 1px solid #e7e2d7;
  border-right: 1px solid #e7e2d7;
  min-height: 100vh;
}
header {
  border-bottom: 3px double #b38644;
  padding: 40px;
  text-align: center;
}
.portal-title {
  font-size: 2.5rem;
  color: #800020;
  font-weight: normal;
  letter-spacing: 1px;
}
.portal-sub { font-size: 0.9rem; font-style: italic; color: #b38644; margin-top: 5px; }
nav {
  border-bottom: 1px solid #e7e2d7;
  display: flex;
  justify-content: center;
  background-color: #faf8f5;
}
nav a {
  padding: 15px 30px;
  text-decoration: none;
  color: #555450;
  font-size: 0.95rem;
  border-right: 1px solid #e7e2d7;
  transition: background-color 0.3s;
}
nav a:hover, nav a.active { background-color: #f5f0e6; color: #800020; }
.main-layout { display: flex; }
.main-content { flex: 3; padding: 40px; }
.sidebar { flex: 1; padding: 40px 30px; border-left: 1px solid #e7e2d7; background-color: #fbfbf9; }
.article-title { font-size: 1.8rem; color: #800020; font-weight: normal; margin-bottom: 15px; }
.meta-info { font-size: 0.85rem; color: #b38644; font-style: italic; margin-bottom: 20px; }
.sidebar-section h4 { font-size: 1.1rem; color: #800020; font-weight: normal; margin-bottom: 15px; border-bottom: 1px solid #b38644; padding-bottom: 5px; }
.sidebar-list { list-style: none; }
.sidebar-list li { margin-bottom: 12px; font-size: 0.9rem; }
.sidebar-list a { color: #555450; text-decoration: none; }
.sidebar-list a:hover { color: #800020; }
.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #b38644;
  font-family: inherit;
  margin-top: 5px;
}
.btn-classic {
  background-color: #800020;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
  margin-top: 15px;
  font-family: inherit;
}
.btn-classic:hover { background-color: #b38644; }
.footer { border-top: 3px double #b38644; padding: 30px; text-align: center; font-size: 0.85rem; color: #777672; }
"""

CHRONOS_LAYOUT = """
<div class="wrapper">
  <header>
    <h1 class="portal-title">CHRONOS TEMPORAL SYSTEMS</h1>
    <p class="portal-sub">Институт темпоральных исследований и казуальной стабильности</p>
  </header>
  <nav>
    <a href="index.html" class="{active_home}">Главный архив</a>
    <a href="services.html" class="{active_serv}">Каузальные контуры</a>
    <a href="about.html" class="{active_about}">О проекте</a>
    <a href="contacts.html" class="{active_cont}">Синхронизация</a>
  </nav>
  <div class="main-layout">
    <div class="main-content">
      {content}
    </div>
    <div class="sidebar">
      <div class="sidebar-section">
        <h4>Недавние публикации</h4>
        <ul class="sidebar-list">
          <li><a href="#">О дрейфе событий второго порядка (2025)</a></li>
          <li><a href="#">Энтропийный баланс хрональных полей</a></li>
          <li><a href="#">Теория петель бездиффузионного переноса</a></li>
        </ul>
      </div>
    </div>
  </div>
  <footer class="footer">
    © 2026 Chronos Temporal Inc. // Архивы и базы данных защищены временной печатью.
  </footer>
</div>
"""

# =============================================================================
# 5. STRATUM SYNERGY (Clean light Enterprise Operations Dashboard)
# =============================================================================
STRATUM_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background-color: #f1f5f9;
  color: #1e293b;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}
.dashboard-wrapper { display: flex; min-height: 100vh; }
.sidebar-nav {
  width: 260px;
  background-color: #0f172a;
  color: #f1f5f9;
  padding: 30px 20px;
  display: flex;
  flex-direction: column;
}
.sidebar-brand { font-size: 1.4rem; font-weight: 800; margin-bottom: 40px; color: #3b82f6; }
.sidebar-menu { list-style: none; }
.sidebar-menu a {
  display: block;
  color: #94a3b8;
  text-decoration: none;
  padding: 12px 15px;
  border-radius: 6px;
  margin-bottom: 8px;
  font-weight: 500;
  transition: all 0.3s;
}
.sidebar-menu a:hover, .sidebar-menu a.active { background-color: #1e293b; color: #3b82f6; }
.main-body { flex: 1; display: flex; flex-direction: column; }
.top-header {
  background-color: #ffffff;
  padding: 20px 40px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dashboard-title { font-size: 1.6rem; font-weight: 700; }
.dashboard-content { padding: 40px; }
.kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }
.kpi-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 25px; }
.kpi-label { font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; }
.kpi-value { font-size: 2rem; font-weight: 700; color: #0f172a; margin-top: 5px; }
.kpi-growth { font-size: 0.8rem; color: #10b981; font-weight: 600; margin-top: 5px; }
.data-panel { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 30px; }
.data-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 20px; color: #0f172a; }
.strata-table { width: 100%; border-collapse: collapse; text-align: left; }
.strata-table th, .strata-table td { padding: 15px; border-bottom: 1px solid #e2e8f0; }
.strata-table th { background-color: #f8fafc; font-weight: 600; color: #475569; }
.badge-active { background-color: #d1fae5; color: #065f46; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #cbd5e1;
  background-color: #ffffff;
  color: #0f172a;
  border-radius: 6px;
  margin-top: 8px;
  outline: none;
}
.btn-dashboard {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 15px;
}
.btn-dashboard:hover { background-color: #2563eb; }
.footer { border-top: 1px solid #e2e8f0; background-color: #ffffff; padding: 25px; text-align: center; font-size: 0.85rem; color: #64748b; margin-top: auto; }
"""

STRATUM_LAYOUT = """
<div class="dashboard-wrapper">
  <div class="sidebar-nav">
    <div class="sidebar-brand">STRATUM OPERATIONAL</div>
    <ul class="sidebar-menu">
      <li><a href="index.html" class="{active_home}">Инфо-панель</a></li>
      <li><a href="services.html" class="{active_serv}">Декомпозиция</a></li>
      <li><a href="about.html" class="{active_about}">Базовый стек</a></li>
      <li><a href="contacts.html" class="{active_cont}">Связь с узлом</a></li>
    </ul>
  </div>
  <div class="main-body">
    <div class="top-header">
      <div class="dashboard-title">Админ-панель Stratum Synergy v4.2</div>
      <div style="font-size: 0.85rem; font-weight: 600; color: #10b981;">● Соединение защищено</div>
    </div>
    <div class="dashboard-content">
      {content}
    </div>
    <footer class="footer">
      © 2026 Stratum Synergy Operations. Все процессы завершены штатно.
    </footer>
  </div>
</div>
"""

# =============================================================================
# GENERATOR LOGIC
# =============================================================================

def generate_aether_pages():
    pages = {}
    
    # 1. Index
    content = """
    <h1 class="hero-title">СИНХРОНИЗАЦИЯ СУБЧАСТОТНЫХ ЭФИРНЫХ ЭМИТТЕРОВ <span class="blink">_</span></h1>
    <p>Амплитудная балансировка тонких нелинейных полей. Фиксация дрейфа в секторе 7.</p>
    
    <div class="grid-container">
      <div class="grid-card">
        <h3>Эфирный дрейф</h3>
        <p>Стабилизация колебаний второго порядка с коэффициентом гашения 99.8%. Исключение диссипации среды.</p>
      </div>
      <div class="grid-card">
        <h3>Резонансный барьер</h3>
        <p>Автоматическая регулировка фазовых углов для исключения тепловых флуктуаций проводников.</p>
      </div>
      <div class="grid-card">
        <h3>Векторные петли</h3>
        <p>Калибровка направленного излучения с геометрической подстройкой фазового спектра.</p>
      </div>
    </div>
    """
    pages["index.html"] = AETHER_LAYOUT.format(active_home="active", active_serv="", active_about="", active_cont="", content=content)

    # 2. Services
    content = """
    <h1 class="hero-title">ДИАГНОСТИКА РЕЗОНАНСНОЙ СЕТКИ</h1>
    <p>Мониторинг коэффициентов нелинейного сопротивления в режиме реального времени.</p>
    
    <table class="terminal-table">
      <thead>
        <tr>
          <th>Модуль</th>
          <th>Частота</th>
          <th>Фаза</th>
          <th>Статус</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Aether-Alpha</td>
          <td>1.2 ГГц</td>
          <td>0.00°</td>
          <td style="color:#33ff33">ОПЕРАЦИОННО</td>
        </tr>
        <tr>
          <td>Aether-Sigma</td>
          <td>8.4 ГГц</td>
          <td>+0.12°</td>
          <td style="color:#33ff33">СТАБИЛЬНО</td>
        </tr>
        <tr>
          <td>Aether-Omega</td>
          <td>16.0 ГГц</td>
          <td>-0.05°</td>
          <td style="color:#33ff33">АКТИВНО</td>
        </tr>
      </tbody>
    </table>
    """
    pages["services.html"] = AETHER_LAYOUT.format(active_home="", active_serv="active", active_about="", active_cont="", content=content)

    # 3. About
    content = """
    <h1 class="hero-title">ОТЧЕТ ИССЛЕДОВАТЕЛЬСКОЙ ГРУППЫ</h1>
    <p>Эфирный Резонанс — независимое объединение исследователей, изучающих процессы в слабоструктурированных средах.</p>
    <p style="margin-top: 15px;">Наша цель — создание стабильных пространственных контуров без потери энергии. Мы концентрируемся на выравнивании полей и подавлении нежелательного фонового шума.</p>
    """
    pages["about.html"] = AETHER_LAYOUT.format(active_home="", active_serv="", active_about="active", active_cont="", content=content)

    # 4. Contacts
    content = """
    <h1 class="hero-title">КАЛИБРОВКА ЧАСТОТНЫХ ПАРАМЕТРОВ</h1>
    <p>Отправьте калибровочный тензор для синхронизации вашего терминала с центральным узлом.</p>
    
    <form style="margin-top: 20px;" onsubmit="event.preventDefault(); alert('Тензор отправлен.');">
      <div>
        <label>ID Терминала</label>
        <input type="text" class="form-input" placeholder="TERM-824" required>
      </div>
      <div style="margin-top: 15px;">
        <label>Канал связи (Email)</label>
        <input type="email" class="form-input" placeholder="address@domain.io" required>
      </div>
      <div style="margin-top: 15px;">
        <label>Параметры сдвига</label>
        <textarea class="form-input" rows="4" placeholder="Опишите частотные отклонения..." required></textarea>
      </div>
      <button type="submit" class="btn-submit">Отправить калибровочный вектор</button>
    </form>
    """
    pages["contacts.html"] = AETHER_LAYOUT.format(active_home="", active_serv="", active_about="", active_cont="active", content=content)

    return pages

def generate_nexus_pages():
    pages = {}
    
    # 1. Index
    content = """
    <section class="hero">
      <h1>Координация многомерных тензорных полей</h1>
      <p>Проектируем высокоточные квантовые мосты с компенсацией декогеренции. Повышаем связность распределенных вычислительных сетей.</p>
      <a href="services.html" class="btn-premium">Исследовать Матрицы</a>
    </section>
    """
    pages["index.html"] = NEXUS_LAYOUT.format(active_home="active", active_serv="", active_about="", active_cont="", content=content)

    # 2. Services
    content = """
    <section class="section">
      <h2>Спектральный анализ квантовых структур</h2>
      <div class="cards-grid">
        <div class="nexus-card">
          <h3>Фазовый роутинг</h3>
          <p>Канальное перераспределение вероятностных траекторий на базе ортогональных графов высокой проводимости.</p>
        </div>
        <div class="nexus-card">
          <h3>Подавление шума</h3>
          <p>Локальная нейтрализация квантовой декогеренции за счет динамических фазовых компенсаторов.</p>
        </div>
        <div class="nexus-card">
          <h3>Сингулярные матрицы</h3>
          <p>Стабилизация потоков данных с использованием плотных фрактальных базисов третьего порядка.</p>
        </div>
      </div>
    </section>
    """
    pages["services.html"] = NEXUS_LAYOUT.format(active_home="", active_serv="active", active_about="", active_cont="", content=content)

    # 3. About
    content = """
    <section class="section">
      <h2>Концепция когерентных систем</h2>
      <p style="max-width: 800px; margin: 0 auto; text-align: center; font-size: 1.1rem; line-height: 1.8;">
        Мы разрабатываем математические и программные модели для анализа многомерных пространств. Наша цель — создание бесшовных мостов для интеграции сложных логических структур в динамические нестабильные среды. Мы исследуем фундаментальные принципы стабилизации и оптимизации тензорной плотности.
      </p>
    </section>
    """
    pages["about.html"] = NEXUS_LAYOUT.format(active_home="", active_serv="", active_about="active", active_cont="", content=content)

    # 4. Contacts
    content = """
    <section class="section">
      <h2>Инициализировать соединение с Нексусом</h2>
      <div class="contact-container">
        <form onsubmit="event.preventDefault(); alert('Соединение установлено.');">
          <div>
            <label style="color:#f3f4f6; font-weight:600;">Идентификатор узла (ФИО)</label>
            <input type="text" class="form-input" placeholder="Узел №918" required>
          </div>
          <div style="margin-top: 20px;">
            <label style="color:#f3f4f6; font-weight:600;">Вектор связи (Email)</label>
            <input type="email" class="form-input" placeholder="email@nexus.io" required>
          </div>
          <div style="margin-top: 20px;">
            <label style="color:#f3f4f6; font-weight:600;">Параметры сдвига</label>
            <textarea class="form-input" rows="4" placeholder="Введите конфигурацию сдвига..." required></textarea>
          </div>
          <button type="submit" class="btn-premium" style="margin-top: 20px; width: 100%; border: none;">Установить канал связи</button>
        </form>
      </div>
    </section>
    """
    pages["contacts.html"] = NEXUS_LAYOUT.format(active_home="", active_serv="", active_about="", active_cont="active", content=content)

    return pages

def generate_synapse_pages():
    pages = {}
    
    # 1. Index
    content = """
    <div class="hero">
      <h1>Оптимизация когнитивных синергий</h1>
      <p>Развертывание нейроморфных сетевых архитектур с распределенным коэффициентом синаптического веса.</p>
    </div>
    <div class="section">
      <h2 class="section-title">Синаптические контуры</h2>
      <div class="brutal-grid">
        <div class="brutal-card">
          <h3>Балансировка весов</h3>
          <p>Автоматическая подстройка и калибровка соединений в условиях сильного внешнего шума.</p>
        </div>
        <div class="brutal-card alt">
          <h3>Векторное сжатие</h3>
          <p>Сверточные когнитивные буферы для сохранения ассоциативных цепочек высокой плотности.</p>
        </div>
      </div>
    </div>
    """
    pages["index.html"] = SYNAPSE_LAYOUT.format(active_home="active", active_serv="", active_about="", active_cont="", content=content)

    # 2. Services
    content = """
    <div class="section">
      <h2 class="section-title">Интеграционные Синергии</h2>
      <div class="brutal-grid">
        <div class="brutal-card">
          <h3>Нейробаланс</h3>
          <p>Регулировка пластичности сети для оптимальной обработки разнородных сигналов.</p>
        </div>
        <div class="brutal-card">
          <h3>Анализ дрейфа</h3>
          <p>Регистрация отклонений синаптического спектра в реальном времени с адаптивной компенсацией.</p>
        </div>
        <div class="brutal-card alt">
          <h3>Ассоциации</h3>
          <p>Построение устойчивых фрактальных цепочек связей между изолированными сегментами.</p>
        </div>
      </div>
    </div>
    """
    pages["services.html"] = SYNAPSE_LAYOUT.format(active_home="", active_serv="active", active_about="", active_cont="", content=content)

    # 3. About
    content = """
    <div class="section">
      <h2 class="section-title">Концепция бюро</h2>
      <p style="font-size: 1.2rem; font-weight: 600; line-height: 1.6; max-width: 800px; margin-bottom: 20px;">
        Мы строим гибкие алгоритмические структуры для обработки сложноорганизованных паттернов. Наша деятельность направлена на создание устойчивых связей в цифровых средах.
      </p>
      <p style="font-size: 1.1rem; line-height: 1.6; max-width: 800px;">
        В рамках проекта исследуются механизмы самоорганизации сетей и оптимизации когнитивной плотности. Мы создаем программные слои, защищенные от внешних помех.
      </p>
    </div>
    """
    pages["about.html"] = SYNAPSE_LAYOUT.format(active_home="", active_serv="", active_about="active", active_cont="", content=content)

    # 4. Contacts
    content = """
    <div class="section">
      <h2 class="section-title">Адаптивный запрос</h2>
      <div style="max-width: 600px; border: 4px solid #1a1a1a; padding: 40px; box-shadow: 6px 6px 0px #1a1a1a; background-color: #ffde4d;">
        <form onsubmit="event.preventDefault(); alert('Данные приняты.');">
          <div>
            <label style="font-weight:900;">Идентификатор узла</label>
            <input type="text" class="form-field" placeholder="NODE-ID" required>
          </div>
          <div style="margin-top: 15px;">
            <label style="font-weight:900;">Электронный вектор (Email)</label>
            <input type="email" class="form-field" placeholder="vector@domain.io" required>
          </div>
          <div style="margin-top: 15px;">
            <label style="font-weight:900;">Спецификация сдвига</label>
            <textarea class="form-field" rows="4" placeholder="Опишите параметры..." required></textarea>
          </div>
          <button type="submit" class="btn-brutal">Отправить синаптический импульс</button>
        </form>
      </div>
    </div>
    """
    pages["contacts.html"] = SYNAPSE_LAYOUT.format(active_home="", active_serv="", active_about="", active_cont="active", content=content)

    return pages

def generate_chronos_pages():
    pages = {}
    
    # 1. Index
    content = """
    <h2 class="article-title">Стабилизация каузальных цепей в условиях темпорального шума</h2>
    <div class="meta-info">Опубликовано: 12.04.2026 // Раздел: Теоретическая хронодинамика</div>
    <p>
      Настоящий архив содержит результаты исследований по снижению энтропийного сопротивления временных потоков на границах раздела фаз. Описаны базовые алгоритмы предотвращения каузальных петель и методы локального гашения флуктуаций среды.
    </p>
    <p style="margin-top: 15px;">
      В ходе экспериментов была подтверждена гипотеза о фазовой балансировке замкнутых контуров бездиффузионного переноса. Читайте подробные материалы в разделе «Каузальные контуры».
    </p>
    """
    pages["index.html"] = CHRONOS_LAYOUT.format(active_home="active", active_serv="", active_about="", active_cont="", content=content)

    # 2. Services
    content = """
    <h2 class="article-title">Методологии хроно-балансировки</h2>
    <div class="meta-info">Классификация каузальных контуров по уровню защиты от декогеренции</div>
    
    <div style="margin-top: 25px;">
      <h3 style="color:#800020; font-weight:normal;">Контур Alpha Vector</h3>
      <p style="margin-bottom: 15px;">Локальное гашение темпоральных сдвигов первого порядка. Фазовый шум в пределах нормы (до 5%). Подходит для стабилизации простых причинно-следственных связей.</p>
      
      <h3 style="color:#800020; font-weight:normal;">Контур Sigma Matrix</h3>
      <p style="margin-bottom: 15px;">Многофакторная калибровка с обратной связью по сингулярности. Эффективное подавление шумов до -40 дБ на средних частотах.</p>
      
      <h3 style="color:#800020; font-weight:normal;">Контур Omega Stratum</h3>
      <p style="margin-bottom: 15px;">Полный темпоральный синтез с нулевой диссипацией хронального поля. Поддержка стабильности сложных каузальных петель.</p>
    </div>
    """
    pages["services.html"] = CHRONOS_LAYOUT.format(active_home="", active_serv="active", active_about="", active_cont="", content=content)

    # 3. About
    content = """
    <h2 class="article-title">О целях нашего института</h2>
    <div class="meta-info">Историческая справка и миссия</div>
    <p>
      Институт темпоральных исследований специализируется на изучении каузальной стабильности пространственно-временных сеток. Мы разрабатываем аналитические инструменты для фиксации фазовых сдвигов и предотвращения локальных сингулярностей.
    </p>
    <p style="margin-top: 15px;">
      Наша группа объединяет математиков, физиков и инженеров по стабильности сред. Совместными усилиями мы создаем стабильные контуры связи.
    </p>
    """
    pages["about.html"] = CHRONOS_LAYOUT.format(active_home="", active_serv="", active_about="active", active_cont="", content=content)

    # 4. Contacts
    content = """
    <h2 class="article-title">Синхронизация каузальных параметров</h2>
    <div class="meta-info">Форма обратной связи для верификации узлов</div>
    
    <form style="margin-top: 20px;" onsubmit="event.preventDefault(); alert('Запрос на синхронизацию отправлен.');">
      <div>
        <label>Код исследователя</label>
        <input type="text" class="form-input" placeholder="ID-7741" required>
      </div>
      <div style="margin-top: 15px;">
        <label>Канал связи (Email)</label>
        <input type="email" class="form-input" placeholder="office@chronos.su" required>
      </div>
      <div style="margin-top: 15px;">
        <label>Описание флуктуации</label>
        <textarea class="form-input" rows="5" placeholder="Опишите временной сдвиг..." required></textarea>
      </div>
      <button type="submit" class="btn-classic">Запустить синхронизацию</button>
    </form>
    """
    pages["contacts.html"] = CHRONOS_LAYOUT.format(active_home="", active_serv="", active_about="", active_cont="active", content=content)

    return pages

def generate_stratum_pages():
    pages = {}
    
    # 1. Index
    content = """
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">Плотность слоев</div>
        <div class="kpi-value">98.24%</div>
        <div class="kpi-growth">▲ Стабильно</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Индекс энтропии</div>
        <div class="kpi-value">0.034</div>
        <div class="kpi-growth" style="color:#ef4444;">▼ Снижение</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Активные страты</div>
        <div class="kpi-value">12 / 12</div>
        <div class="kpi-growth">▲ Синхронизировано</div>
      </div>
    </div>
    
    <div class="data-panel">
      <div class="data-title">Состояние распределенных векторов</div>
      <table class="strata-table">
        <thead>
          <tr>
            <th>Страта</th>
            <th>Пропускная способность</th>
            <th>Индекс сдвига</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Stratum-Alpha</td>
            <td>1.2 Гб/с</td>
            <td>0.00%</td>
            <td><span class="badge-active">ACTIVE</span></td>
          </tr>
          <tr>
            <td>Stratum-Beta</td>
            <td>8.4 Гб/с</td>
            <td>0.02%</td>
            <td><span class="badge-active">ACTIVE</span></td>
          </tr>
          <tr>
            <td>Stratum-Gamma</td>
            <td>16.0 Гб/с</td>
            <td>0.00%</td>
            <td><span class="badge-active">ACTIVE</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    """
    pages["index.html"] = STRATUM_LAYOUT.format(active_home="active", active_serv="", active_about="", active_cont="", content=content)

    # 2. Services
    content = """
    <div class="data-panel">
      <div class="data-title">Спецификация фрактальных уровней</div>
      <p style="margin-bottom: 20px; color:#64748b;">Ниже приведена схема декомпозиции информационных слоев для балансировки семантической плотности.</p>
      
      <div style="border-left: 3px solid #3b82f6; padding-left: 15px; margin-bottom: 20px;">
        <h4 style="color:#0f172a;">Семантическая селекция</h4>
        <p style="font-size:0.9rem; color:#64748b;">Маршрутизация данных по фрактальным индексам с целью предотвращения перегрузки семантических шлюзов.</p>
      </div>
      
      <div style="border-left: 3px solid #3b82f6; padding-left: 15px; margin-bottom: 20px;">
        <h4 style="color:#0f172a;">Фрактальные мосты</h4>
        <p style="font-size:0.9rem; color:#64748b;">Интеграция изолированных слоев в единую устойчивую распределенную структуру высокой проводимости.</p>
      </div>
    </div>
    """
    pages["services.html"] = STRATUM_LAYOUT.format(active_home="", active_serv="active", active_about="", active_cont="", content=content)

    # 3. About
    content = """
    <div class="data-panel">
      <div class="data-title">О многоуровневых системах Stratum</div>
      <p style="line-height:1.8; margin-bottom: 15px;">
        Stratum Synergy занимается проектированием многослойных фрактальных архитектур для обработки разнородных информационных потоков. Наша основная цель — создание защищенных шлюзов и балансировка семантической нагрузки по слоям.
      </p>
      <p style="line-height:1.8;">
        Мы предоставляем стабильные решения для крупных систем распределенных данных, обеспечивая бесшовное взаимодействие между всеми слоями сети.
      </p>
    </div>
    """
    pages["about.html"] = STRATUM_LAYOUT.format(active_home="", active_serv="", active_about="active", active_cont="", content=content)

    # 4. Contacts
    content = """
    <div class="data-panel" style="max-width:600px; margin:0 auto;">
      <div class="data-title">Запрос калибровочных данных у стратум-менеджера</div>
      <form onsubmit="event.preventDefault(); alert('Параметры стратификации обновлены.');">
        <div>
          <label style="font-size:0.85rem; font-weight:600; color:#475569;">Имя узла</label>
          <input type="text" class="form-input" placeholder="Узел №718" required>
        </div>
        <div style="margin-top: 15px;">
          <label style="font-size:0.85rem; font-weight:600; color:#475569;">Email узла</label>
          <input type="email" class="form-input" placeholder="node@stratum-synergy.com" required>
        </div>
        <div style="margin-top: 15px;">
          <label style="font-size:0.85rem; font-weight:600; color:#475569;">Спецификация плотности</label>
          <textarea class="form-input" rows="4" placeholder="Опишите семантические параметры..." required></textarea>
        </div>
        <button type="submit" class="btn-dashboard">Отправить параметры</button>
      </form>
    </div>
    """
    pages["contacts.html"] = STRATUM_LAYOUT.format(active_home="", active_serv="", active_about="", active_cont="active", content=content)

    return pages

# =============================================================================
# MAIN DIRECTORY GENERATOR
# =============================================================================

def main():
    if os.path.exists(DEST_DIR):
        print(f"Cleaning existing fakesites at: {DEST_DIR}")
        shutil.rmtree(DEST_DIR)
    
    os.makedirs(DEST_DIR, exist_ok=True)
    print(f"Generating 5 distinct websites at: {DEST_DIR}")

    # 1. Aether
    aether_dir = os.path.join(DEST_DIR, "aether")
    os.makedirs(aether_dir, exist_ok=True)
    with open(os.path.join(aether_dir, "style.css"), "w", encoding="utf-8") as f:
        f.write(AETHER_CSS)
    aether_pages = generate_aether_pages()
    for name, html in aether_pages.items():
        with open(os.path.join(aether_dir, name), "w", encoding="utf-8") as f:
            f.write(html)
    print("Generated Aether Resonance (Cyberpunk Console)")

    # 2. Nexus
    nexus_dir = os.path.join(DEST_DIR, "nexus")
    os.makedirs(nexus_dir, exist_ok=True)
    with open(os.path.join(nexus_dir, "style.css"), "w", encoding="utf-8") as f:
        f.write(NEXUS_CSS)
    nexus_pages = generate_nexus_pages()
    for name, html in nexus_pages.items():
        with open(os.path.join(nexus_dir, name), "w", encoding="utf-8") as f:
            f.write(html)
    print("Generated Quantum Nexus (Premium Dark Corporate)")

    # 3. Synapse
    synapse_dir = os.path.join(DEST_DIR, "synapse")
    os.makedirs(synapse_dir, exist_ok=True)
    with open(os.path.join(synapse_dir, "style.css"), "w", encoding="utf-8") as f:
        f.write(SYNAPSE_CSS)
    synapse_pages = generate_synapse_pages()
    for name, html in synapse_pages.items():
        with open(os.path.join(synapse_dir, name), "w", encoding="utf-8") as f:
            f.write(html)
    print("Generated Synaptic Dynamics (Brutalist Modern Art Agency)")

    # 4. Chronos
    chronos_dir = os.path.join(DEST_DIR, "chronos")
    os.makedirs(chronos_dir, exist_ok=True)
    with open(os.path.join(chronos_dir, "style.css"), "w", encoding="utf-8") as f:
        f.write(CHRONOS_CSS)
    chronos_pages = generate_chronos_pages()
    for name, html in chronos_pages.items():
        with open(os.path.join(chronos_dir, name), "w", encoding="utf-8") as f:
            f.write(html)
    print("Generated Chronos Temporal (Academic Archive)")

    # 5. Stratum
    stratum_dir = os.path.join(DEST_DIR, "stratum")
    os.makedirs(stratum_dir, exist_ok=True)
    with open(os.path.join(stratum_dir, "style.css"), "w", encoding="utf-8") as f:
        f.write(STRATUM_CSS)
    stratum_pages = generate_stratum_pages()
    for name, html in stratum_pages.items():
        with open(os.path.join(stratum_dir, name), "w", encoding="utf-8") as f:
            f.write(html)
    print("Generated Stratum Synergy (Corporate SaaS Dashboard)")

if __name__ == "__main__":
    main()
