import os
import shutil

# Root directory for fake sites
DEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", "fakesite"))

# Define site themes
SITES = {
    "aether": {
        "title": "Aether Resonance",
        "ru_title": "Эфирный Резонанс",
        "desc": "Сверхчастотная гармонизация нелинейных полей и эфирные резонансные модули.",
        "bg_color": "#0d0d11",
        "primary": "#7D56F4",
        "secondary": "#9C27B0",
        "card_bg": "#161622",
        "text": "#E0E0E0",
        "logo": "⬡ Aether",
        "terms": {
            "hero_h1": "Амплитудная синхронизация тонких полей",
            "hero_sub": "Обеспечиваем фазовую стабилизацию и гашение нелинейных флуктуаций с эффективностью до 99.8%. Наш дрейф находится под полным контролем.",
            "stat1": "Сверхпроводники",
            "stat2": "Резонанс",
            "stat3": "Стабилизация",
            "serv1_title": "Гармонизация поля",
            "serv1_desc": "Выравнивание фазовых углов эфирного излучения в диапазоне суб-миллиметровых волн для исключения диссипации.",
            "serv2_title": "Векторные эмиттеры",
            "serv2_desc": "Проектирование и калибровка направленных эмиттеров с изменяемой геометрией резонансного контура.",
            "serv3_title": "Спектральный анализ",
            "serv3_desc": "Мониторинг флуктуаций второго порядка с регистрацией микроструктурных искажений среды.",
            "about_p": "Эфирный Резонанс — независимая группа исследований, занимающаяся созданием когерентных систем взаимодействия в слабоструктурированных средах. Наша миссия — создание стабильных пространственных контуров для минимизации энтропийного сопротивления.",
            "contact_addr": "Сектор 7, Зона Эфира 14, Москва",
            "contact_email": "info@aether-resonance.net",
            "contact_phone": "+7 (800) 100-34-43"
        }
    },
    "nexus": {
        "title": "Quantum Nexus",
        "ru_title": "Квантовый Нексус",
        "desc": "Маршрутизация многомерных тензоров и суперпозиционная стабилизация.",
        "bg_color": "#060b13",
        "primary": "#00E5FF",
        "secondary": "#00B0FF",
        "card_bg": "#0f172a",
        "text": "#E2E8F0",
        "logo": "◈ Nexus",
        "terms": {
            "hero_h1": "Суперпозиционная координация тензоров",
            "hero_sub": "Масштабируемые квантовые мосты с компенсацией декогеренции в реальном времени. Внедрение фазовых цепочек без потери связности.",
            "stat1": "Тензоры",
            "stat2": "Мониторинг",
            "stat3": "Когерентность",
            "serv1_title": "Фазовый роутинг",
            "serv1_desc": "Канальная адресация суперпозиционных путей на базе многоуровневых вероятностных графов.",
            "serv2_title": "Коррекция декогеренции",
            "serv2_desc": "Динамическое выравнивание квантовых флуктуаций с обратной связью по фазовым сдвигам.",
            "serv3_title": "Сингулярные матрицы",
            "serv3_desc": "Генерация ортогональных сингулярных базисов высокой плотности для стабилизации потоков данных.",
            "about_p": "Quantum Nexus разрабатывает решения на стыке многомерной топологии и распределенных вероятностных систем. Мы строим логические мосты для интеграции сложных вычислительных матриц в нестабильных средах.",
            "contact_addr": "Комплекс Квант, Блок 9, Санкт-Петербург",
            "contact_email": "ops@quant-nexus.io",
            "contact_phone": "+7 (812) 777-99-88"
        }
    },
    "synapse": {
        "title": "Synaptic Dynamics",
        "ru_title": "Синаптическая Динамика",
        "desc": "Нейроморфная синергия, оптимизация мыслительных векторов и когнитивные буферы.",
        "bg_color": "#070c08",
        "primary": "#00F294",
        "secondary": "#00E5FF",
        "card_bg": "#121b14",
        "text": "#ECFDF5",
        "logo": "⬢ Synapse",
        "terms": {
            "hero_h1": "Оптимизация когнитивных синергий",
            "hero_sub": "Развертывание нейроморфных архитектур с обратным распространением когнитивного вектора. Полный контроль адаптивных весов.",
            "stat1": "Синапсы",
            "stat2": "Нейроны",
            "stat3": "Пластичность",
            "serv1_title": "Нейроморфная балансировка",
            "serv1_desc": "Автоматическая подстройка весовых коэффициентов синаптических соединений в условиях динамического шума.",
            "serv2_title": "Векторное сжатие",
            "serv2_desc": "Проектирование сверточных когнитивных буферов с сохранением структуры ассоциативных связей.",
            "serv3_title": "Адаптивный анализ",
            "serv3_desc": "Потоковый анализ синаптического дрейфа с возможностью мгновенной реконфигурации сети.",
            "about_p": "Синаптическая Динамика — проектное бюро, создающее алгоритмические структуры для обработки сложноорганизованных паттернов. Наша деятельность направлена на воспроизведение гибких связей в цифровых средах.",
            "contact_addr": "Технопарк Искра, Лаборатория 5Б, Новосибирск",
            "contact_email": "support@synaptic-dyn.ru",
            "contact_phone": "+7 (383) 999-88-77"
        }
    },
    "chronos": {
        "title": "Chronos Temporal",
        "ru_title": "Хроно-Вектор",
        "desc": "Хроно-модуляция, управление казуальными цепочками и стабилизация темпоральных фаз.",
        "bg_color": "#120c07",
        "primary": "#FF8A00",
        "secondary": "#FF3D00",
        "card_bg": "#1d140e",
        "text": "#FFF3E0",
        "logo": "⌛ Chronos",
        "terms": {
            "hero_h1": "Управление энтропией временных потоков",
            "hero_sub": "Фазовая балансировка казуальных цепей и локальное гашение темпорального шума. Инновационная ретроспективная стабилизация.",
            "stat1": "Контуры",
            "stat2": "Каузальность",
            "stat3": "Фаза",
            "serv1_title": "Каузальный анализ",
            "serv1_desc": "Расчет вероятностного влияния событий на стабильность пространственно-временной сетки.",
            "serv2_title": "Хроно-стабилизация",
            "serv2_desc": "Коррекция временного сдвига на границе раздела сред с различной плотностью хронального потока.",
            "serv3_title": "Векторные петли",
            "serv3_desc": "Проектирование замкнутых безэнтропийных контуров для локальной обработки каузальных цепей.",
            "about_p": "Chronos Temporal специализируется на проектировании систем с высокой темпоральной защищенностью. Мы предлагаем уникальные инструменты для мониторинга и коррекции фазовых сдвигов в микроструктурных каузальных графах.",
            "contact_addr": "Улица Часовая, Корпус 3, Екатеринбург",
            "contact_email": "time@chronos-temporal.su",
            "contact_phone": "+7 (343) 444-55-66"
        }
    },
    "stratum": {
        "title": "Stratum Synergy",
        "ru_title": "Стратум Синергия",
        "desc": "Многослойная фрактальная декомпозиция, семантический роутинг и распределение плотности.",
        "bg_color": "#ffffff",
        "primary": "#4F46E5",
        "secondary": "#06B6D4",
        "card_bg": "#f8fafc",
        "text": "#0f172a",
        "logo": "☲ Stratum",
        "terms": {
            "hero_h1": "Многоуровневый фрактальный синтез",
            "hero_sub": "Оптимизация плотности информационных потоков на базе многослойных координационных сетей. Полное фрактальное разделение.",
            "stat1": "Слои",
            "stat2": "Фракталы",
            "stat3": "Синтез",
            "serv1_title": "Семантическая селекция",
            "serv1_desc": "Маршрутизация данных на основе фрактальных индексов с переменной глубиной декомпозиции.",
            "serv2_title": "Плотность распределения",
            "serv2_desc": "Балансировка информационного наполнения по слоям для предотвращения перегрузки семантических узлов.",
            "serv3_title": "Фрактальные мосты",
            "serv3_desc": "Связывание изолированных страт в единую устойчивую информационную структуру высокой проводимости.",
            "about_p": "Стратум Синергия разрабатывает фрактальные архитектуры для обработки распределенных разнородных потоков. Наша цель — обеспечение бесшовной связи между независимыми семантическими слоями в больших системах.",
            "contact_addr": "Бизнес Центр Выставочный, Офис 402, Казань",
            "contact_email": "info@stratum-synergy.com",
            "contact_phone": "+7 (843) 222-33-44"
        }
    }
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ru_title} — {title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="header">
  <div class="container">
    <a href="index.html" class="logo">
      {logo}
    </a>
    <nav class="nav">
      <ul class="nav-list">
        <li><a href="index.html" class="nav-link {active_home}">Главная</a></li>
        <li><a href="services.html" class="nav-link {active_serv}">Технологии</a></li>
        <li><a href="about.html" class="nav-link {active_about}">О нас</a></li>
        <li><a href="contacts.html" class="nav-link {active_cont}">Контакты</a></li>
      </ul>
    </nav>
  </div>
</header>

{content}

<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="index.html" class="logo">{logo}</a>
        <p>{desc}</p>
      </div>
      <div class="footer-col">
        <h4>Навигация</h4>
        <ul>
          <li><a href="index.html">Главная</a></li>
          <li><a href="services.html">Технологии</a></li>
          <li><a href="about.html">О нас</a></li>
          <li><a href="contacts.html">Контакты</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Контакты</h4>
        <p>{contact_email}</p>
        <p>{contact_phone}</p>
        <p>{contact_addr}</p>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 {title}. Все права защищены. Разработка систем резонансной стабилизации.</span>
    </div>
  </div>
</footer>
</body>
</html>
"""

CSS_TEMPLATE = """/* General reset */
* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: {bg_color};
  color: {text_color};
  line-height: 1.6;
}}

.container {{
  width: 90%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}}

/* Header */
.header {{
  background-color: {header_bg};
  border-bottom: 1px solid {border_color};
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}}

.header .container {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 70px;
}}

.logo {{
  font-size: 1.5rem;
  font-weight: bold;
  color: {primary_color};
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}}

.nav-list {{
  display: flex;
  list-style: none;
  gap: 24px;
}}

.nav-link {{
  color: {text_muted};
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}}

.nav-link:hover, .nav-link.active {{
  color: {primary_color};
}}

/* Hero section */
.hero {{
  padding: 80px 0;
  border-bottom: 1px solid {border_color};
  background: radial-gradient(circle at 80% 20%, {gradient_spot} 0%, transparent 40%);
}}

.hero-content {{
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}}

.hero-tag {{
  display: inline-block;
  padding: 4px 12px;
  border: 1px solid {primary_color};
  color: {primary_color};
  font-size: 0.85rem;
  border-radius: 20px;
  margin-bottom: 16px;
  text-transform: uppercase;
  font-weight: 600;
}}

.hero h1 {{
  font-size: 3rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 20px;
  color: {title_color};
}}

.hero-sub {{
  font-size: 1.25rem;
  color: {text_muted};
  margin-bottom: 32px;
}}

/* Stats grid */
.stats {{
  padding: 40px 0;
  border-bottom: 1px solid {border_color};
}}

.stats-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 30px;
  text-align: center;
}}

.stat {{
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: {text_muted};
}}

.stat-num {{
  font-size: 2.5rem;
  font-weight: 800;
  color: {primary_color};
}}

/* Sections */
.section {{
  padding: 80px 0;
  border-bottom: 1px solid {border_color};
}}

.section-head {{
  text-align: center;
  max-width: 600px;
  margin: 0 auto 50px auto;
}}

.section-head h2 {{
  font-size: 2.25rem;
  color: {title_color};
  margin-bottom: 12px;
}}

.section-head p {{
  color: {text_muted};
}}

/* Cards grid */
.cards-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
}}

.card {{
  background-color: {card_bg};
  border: 1px solid {border_color};
  border-radius: 12px;
  padding: 30px;
  transition: transform 0.3s, border-color 0.3s;
}}

.card:hover {{
  transform: translateY(-5px);
  border-color: {primary_color};
}}

.card-icon {{
  font-size: 2rem;
  color: {primary_color};
  margin-bottom: 20px;
}}

.card h3 {{
  font-size: 1.5rem;
  color: {title_color};
  margin-bottom: 12px;
}}

.card p {{
  color: {text_muted};
  font-size: 0.95rem;
}}

/* Forms and interactions */
.btn-primary {{
  display: inline-block;
  background-color: {primary_color};
  color: {btn_text};
  padding: 12px 28px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: opacity 0.3s;
  border: none;
  cursor: pointer;
}}

.btn-primary:hover {{
  opacity: 0.9;
}}

.contact-form {{
  max-width: 600px;
  margin: 0 auto;
  background-color: {card_bg};
  border: 1px solid {border_color};
  padding: 40px;
  border-radius: 12px;
}}

.form-group {{
  margin-bottom: 20px;
}}

.form-group label {{
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: {title_color};
}}

.form-control {{
  width: 100%;
  padding: 12px;
  background-color: {bg_color};
  border: 1px solid {border_color};
  color: {text_color};
  border-radius: 6px;
  outline: none;
}}

.form-control:focus {{
  border-color: {primary_color};
}}

/* Tiers */
.tiers-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 30px;
  margin-top: 40px;
}}

.tier-card {{
  background-color: {card_bg};
  border: 1px solid {border_color};
  border-radius: 16px;
  padding: 40px 30px;
  text-align: center;
  position: relative;
}}

.tier-card.featured {{
  border-color: {primary_color};
}}

.tier-badge {{
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background-color: {primary_color};
  color: {btn_text};
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}}

.tier-price {{
  font-size: 2.5rem;
  font-weight: 800;
  margin: 20px 0;
  color: {title_color};
}}

.tier-features {{
  list-style: none;
  margin: 24px 0;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: {text_muted};
}}

/* Footer */
.footer {{
  background-color: {header_bg};
  border-top: 1px solid {border_color};
  padding: 60px 0 30px 0;
  margin-top: 80px;
}}

.footer-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 40px;
  margin-bottom: 40px;
}}

.footer-brand {{
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: {text_muted};
}}

.footer-col h4 {{
  font-size: 1.1rem;
  color: {title_color};
  margin-bottom: 20px;
}}

.footer-col ul {{
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}}

.footer-col ul a {{
  color: {text_muted};
  text-decoration: none;
  transition: color 0.3s;
}}

.footer-col ul a:hover {{
  color: {primary_color};
}}

.footer-col p {{
  color: {text_muted};
  margin-bottom: 12px;
}}

.footer-bottom {{
  border-top: 1px solid {border_color};
  padding-top: 30px;
  text-align: center;
  font-size: 0.85rem;
  color: {text_muted};
}}

@media (max-width: 768px) {{
  .hero h1 {{ font-size: 2.25rem; }}
  .header .container {{ flex-direction: column; height: auto; padding: 15px 0; gap: 15px; }}
  .nav-list {{ gap: 15px; }}
}}
"""

def generate_index(site):
    content = f"""
<section class="hero">
  <div class="container">
    <div class="hero-content">
      <p class="hero-tag">{site["ru_title"]}</p>
      <h1>{site["terms"]["hero_h1"]}</h1>
      <p class="hero-sub">{site["terms"]["hero_sub"]}</p>
      <div class="hero-btns">
        <a href="services.html" class="btn-primary">Наши Синергии</a>
      </div>
    </div>
  </div>
</section>

<section class="stats">
  <div class="container">
    <div class="stats-grid">
      <div class="stat"><span class="stat-num">99.8%</span><span>{site["terms"]["stat1"]}</span></div>
      <div class="stat"><span class="stat-num">1.2 ГГц</span><span>{site["terms"]["stat2"]}</span></div>
      <div class="stat"><span class="stat-num">~0 мс</span><span>{site["terms"]["stat3"]}</span></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <h2>Базовые Векторы Стабилизации</h2>
      <p>Комплексные алгоритмические контуры для компенсации нелинейного сопротивления сред</p>
    </div>
    <div class="cards-grid">
      <div class="card">
        <div class="card-icon">🌀</div>
        <h3>{site["terms"]["serv1_title"]}</h3>
        <p>{site["terms"]["serv1_desc"]}</p>
      </div>
      <div class="card">
        <div class="card-icon">⚡</div>
        <h3>{site["terms"]["serv2_title"]}</h3>
        <p>{site["terms"]["serv2_desc"]}</p>
      </div>
      <div class="card">
        <div class="card-icon">📈</div>
        <h3>{site["terms"]["serv3_title"]}</h3>
        <p>{site["terms"]["serv3_desc"]}</p>
      </div>
    </div>
  </div>
</section>
"""
    return HTML_TEMPLATE.format(
        title=site["title"],
        ru_title=site["ru_title"],
        desc=site["desc"],
        logo=site["logo"],
        contact_email=site["terms"]["contact_email"],
        contact_phone=site["terms"]["contact_phone"],
        contact_addr=site["terms"]["contact_addr"],
        active_home="active",
        active_serv="",
        active_about="",
        active_cont="",
        content=content
    )

def generate_about(site):
    content = f"""
<section class="section">
  <div class="container">
    <div class="section-head">
      <h2>О нашей концепции</h2>
      <p>История разработки фрактального баланса и стабилизирующих матриц</p>
    </div>
    <div style="max-width: 800px; margin: 0 auto; color: {site['text']};">
      <p style="margin-bottom: 20px; font-size: 1.1rem; text-indent: 20px;">
        {site["terms"]["about_p"]}
      </p>
      <p style="margin-bottom: 20px; font-size: 1.1rem; text-indent: 20px;">
        В рамках интеграционных тестов второго порядка была выявлена высокая чувствительность семантических фаз к внешнему фоновому излучению. Наш научно-исследовательский вектор полностью сфокусирован на синтезе экранирующих интерфейсов, исключающих перегрузку логических каналов.
      </p>
      <p style="margin-bottom: 20px; font-size: 1.1rem; text-indent: 20px;">
        Мы стремимся предоставлять стабильные базисы для развертывания когерентных систем. Наш опыт показывает, что многоуровневая структура связей позволяет справляться с дрейфом произвольной амплитуды.
      </p>
    </div>
  </div>
</section>
"""
    return HTML_TEMPLATE.format(
        title=site["title"],
        ru_title=site["ru_title"],
        desc=site["desc"],
        logo=site["logo"],
        contact_email=site["terms"]["contact_email"],
        contact_phone=site["terms"]["contact_phone"],
        contact_addr=site["terms"]["contact_addr"],
        active_home="",
        active_serv="",
        active_about="active",
        active_cont="",
        content=content
    )

def generate_services(site):
    content = f"""
<section class="section">
  <div class="container">
    <div class="section-head">
      <h2>Методологии Резонанса</h2>
      <p>Оцените доступные конфигурационные пакеты и профили адаптации</p>
    </div>
    <div class="tiers-grid">
      <div class="tier-card">
        <div class="tier-badge">Базовый</div>
        <h3>Alpha Vector</h3>
        <div class="tier-price">~1.2 Ф/с</div>
        <ul class="tier-features">
          <li>✔ Стабилизация первого уровня</li>
          <li>✔ Фазовый дрейф не более 5%</li>
          <li>✔ 3 ортогональных контура</li>
          <li>✔ Одноканальный сбор статистики</li>
        </ul>
      </div>
      <div class="tier-card featured">
        <div class="tier-badge">Рекомендуемый</div>
        <h3>Sigma Matrix</h3>
        <div class="tier-price">~8.4 Ф/с</div>
        <ul class="tier-features">
          <li>✔ Многофакторная балансировка</li>
          <li>✔ Компенсация шумов до -40 дБ</li>
          <li>✔ 12 динамических каналов</li>
          <li>✔ Обратная связь по сингулярности</li>
          <li>✔ Автоматическая реконфигурация</li>
        </ul>
      </div>
      <div class="tier-card">
        <div class="tier-badge">Премиум</div>
        <h3>Omega Stratum</h3>
        <div class="tier-price">~16.0 Ф/с</div>
        <ul class="tier-features">
          <li>✔ Полный фрактальный синтез</li>
          <li>✔ Нулевая диссипация поля</li>
          <li>✔ Неограниченная сетка тензоров</li>
          <li>✔ Режим когерентного экранирования</li>
          <li>✔ Поддержка каузальных петель</li>
        </ul>
      </div>
    </div>
  </div>
</section>
"""
    return HTML_TEMPLATE.format(
        title=site["title"],
        ru_title=site["ru_title"],
        desc=site["desc"],
        logo=site["logo"],
        contact_email=site["terms"]["contact_email"],
        contact_phone=site["terms"]["contact_phone"],
        contact_addr=site["terms"]["contact_addr"],
        active_home="",
        active_serv="active",
        active_about="",
        active_cont="",
        content=content
    )

def generate_contacts(site):
    content = f"""
<section class="section">
  <div class="container">
    <div class="section-head">
      <h2>Обратная связь</h2>
      <p>Оставьте запрос для инициализации калибровочного сеанса</p>
    </div>
    <form class="contact-form" onsubmit="event.preventDefault(); alert('Сеанс инициализирован. Ожидайте синхронизации контуров.');">
      <div class="form-group">
        <label>Идентификатор сессии (ФИО)</label>
        <input type="text" class="form-control" placeholder="Например, Вектор И.И." required>
      </div>
      <div class="form-group">
        <label>Канал связи (Email)</label>
        <input type="email" class="form-control" placeholder="email@address.com" required>
      </div>
      <div class="form-group">
        <label>Параметры сдвига (Сообщение)</label>
        <textarea class="form-control" rows="5" placeholder="Опишите наблюдаемые флуктуации..." required></textarea>
      </div>
      <button type="submit" class="btn-primary">Отправить тензор</button>
    </form>
  </div>
</section>
"""
    return HTML_TEMPLATE.format(
        title=site["title"],
        ru_title=site["ru_title"],
        desc=site["desc"],
        logo=site["logo"],
        contact_email=site["terms"]["contact_email"],
        contact_phone=site["terms"]["contact_phone"],
        contact_addr=site["terms"]["contact_addr"],
        active_home="",
        active_serv="",
        active_about="",
        active_cont="active",
        content=content
    )

def main():
    # Remove existing fakesite dir to clean up meridian/northcraft/techvision
    if os.path.exists(DEST_DIR):
        print(f"Cleaning existing fakesites at: {DEST_DIR}")
        shutil.rmtree(DEST_DIR)
    
    os.makedirs(DEST_DIR, exist_ok=True)
    print(f"Generating 5 fake sites at: {DEST_DIR}")

    for key, site in SITES.items():
        site_dir = os.path.join(DEST_DIR, key)
        os.makedirs(site_dir, exist_ok=True)

        # Style variables
        is_light = (site["bg_color"] == "#ffffff")
        text_color = site["text"]
        title_color = "#0f172a" if is_light else "#ffffff"
        text_muted = "#475569" if is_light else "#94a3b8"
        border_color = "#cbd5e1" if is_light else "#334155"
        header_bg = "rgba(248, 250, 252, 0.8)" if is_light else "rgba(15, 23, 42, 0.8)"
        gradient_spot = "rgba(79, 70, 229, 0.1)" if is_light else "rgba(125, 86, 244, 0.15)"
        btn_text = "#ffffff"

        css_content = CSS_TEMPLATE.format(
            bg_color=site["bg_color"],
            text_color=text_color,
            primary_color=site["primary"],
            secondary_color=site["secondary"],
            card_bg=site["card_bg"],
            title_color=title_color,
            text_muted=text_muted,
            border_color=border_color,
            header_bg=header_bg,
            gradient_spot=gradient_spot,
            btn_text=btn_text
        )

        with open(os.path.join(site_dir, "style.css"), "w", encoding="utf-8") as f:
            f.write(css_content)

        with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(generate_index(site))

        with open(os.path.join(site_dir, "about.html"), "w", encoding="utf-8") as f:
            f.write(generate_about(site))

        with open(os.path.join(site_dir, "services.html"), "w", encoding="utf-8") as f:
            f.write(generate_services(site))

        with open(os.path.join(site_dir, "contacts.html"), "w", encoding="utf-8") as f:
            f.write(generate_contacts(site))

        print(f"Generated fake site: {key} ({site['ru_title']})")

if __name__ == "__main__":
    main()
