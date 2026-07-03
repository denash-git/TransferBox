package main

import (
	"fmt"
	"os"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Define styles using Lip Gloss
var (
	purple = lipgloss.Color("#7D56F4")
	green  = lipgloss.Color("#04B575")
	red    = lipgloss.Color("#FF5555")
	cyan   = lipgloss.Color("#00D7FF")
	gray   = lipgloss.Color("#888888")
	white  = lipgloss.Color("#FFFFFF")

	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(white).
			Background(purple).
			Padding(1, 4).
			Width(62).
			Align(lipgloss.Center)

	statusLabelStyle = lipgloss.NewStyle().Foreground(gray).Width(12)
	statusValStyle   = lipgloss.NewStyle().Bold(true)
	infoStyle        = lipgloss.NewStyle().Foreground(cyan)

	menuItemStyle = lipgloss.NewStyle().
			PaddingLeft(4).
			Foreground(lipgloss.Color("#CCCCCC"))

	selectedItemStyle = lipgloss.NewStyle().
				PaddingLeft(2).
				Foreground(purple).
				Bold(true)

	borderStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(purple).
			Width(62).
			Padding(0, 1)

	footerStyle = lipgloss.NewStyle().
			Foreground(gray).
			Italic(true).
			PaddingLeft(2)
)

type screen int

const (
	screenMain screen = iota
	screenUsers
	screenUserList
	screenUserActions
	screenShowQR
	screenSettings
	screenApply
	screenLogs
)

type model struct {
	currentScreen screen
	cursor        int
	mainMenu      []string
	usersMenu     []string
	userList      []string
	actionMenu    []string
	settingsMenu  []string
	logsMenu      []string
	selectedUser  string
	qrContent     string
	domain        string
	caddyStatus   string
	sbStatus      string
}

func initialModel() model {
	return model{
		currentScreen: screenMain,
		cursor:        0,
		mainMenu:      []string{"Пользователи", "Настройки сервера", "Перезапустить службы", "Показать логи", "Выход"},
		usersMenu:     []string{"Список пользователей", "Новый пользователь", "Назад"},
		userList:      []string{"admin (NaiveProxy) — активен", "ivan_xhttp (VLESS over XHTTP) — активен", "test_ws (VLESS over WebSocket) — отключен"},
		actionMenu:    []string{"Показать QR и ссылку", "Включить / Отключить", "Удалить", "Назад"},
		settingsMenu:  []string{"Домен: proxy.dtopl.online", "Email Let's Encrypt: admin@dtopl.online", "Фейк-сайт: techvision", "Назад"},
		logsMenu:      []string{"Caddy log (50 строк)", "sing-box log (50 строк)", "Назад"},
		domain:        "proxy.dtopl.online",
		caddyStatus:   "работает",
		sbStatus:      "работает",
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			if m.currentScreen == screenMain {
				return m, tea.Quit
			}
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			maxItems := m.getMenuLength() - 1
			if m.cursor < maxItems {
				m.cursor++
			}
		case "enter", " ":
			return m.handleSelect()
		case "esc", "backspace":
			m.goBack()
		}
	}
	return m, nil
}

func (m *model) getMenuLength() int {
	switch m.currentScreen {
	case screenMain:
		return len(m.mainMenu)
	case screenUsers:
		return len(m.usersMenu)
	case screenUserList:
		return len(m.userList) + 1 // +1 for "Back"
	case screenUserActions:
		return len(m.actionMenu)
	case screenSettings:
		return len(m.settingsMenu)
	case screenLogs:
		return len(m.logsMenu)
	case screenShowQR, screenApply:
		return 1 // Just press enter to go back
	}
	return 0
}

func (m *model) goBack() {
	m.cursor = 0
	switch m.currentScreen {
	case screenUsers, screenSettings, screenApply, screenLogs:
		m.currentScreen = screenMain
	case screenUserList, screenShowQR:
		m.currentScreen = screenUsers
	case screenUserActions:
		m.currentScreen = screenUserList
	}
}

func (m model) handleSelect() (tea.Model, tea.Cmd) {
	switch m.currentScreen {
	case screenMain:
		switch m.cursor {
		case 0:
			m.currentScreen = screenUsers
		case 1:
			m.currentScreen = screenSettings
		case 2:
			m.currentScreen = screenApply
		case 3:
			m.currentScreen = screenLogs
		case 4:
			return m, tea.Quit
		}
		m.cursor = 0

	case screenUsers:
		switch m.cursor {
		case 0:
			m.currentScreen = screenUserList
		case 1:
			// Prototype new user placeholder
			m.currentScreen = screenMain
		case 2:
			m.currentScreen = screenMain
		}
		m.cursor = 0

	case screenUserList:
		if m.cursor == len(m.userList) {
			m.currentScreen = screenUsers
		} else {
			m.selectedUser = m.userList[m.cursor]
			m.currentScreen = screenUserActions
		}
		m.cursor = 0

	case screenUserActions:
		switch m.cursor {
		case 0:
			m.currentScreen = screenShowQR
		case 1:
			// Toggle user status mock
			idx := strings.Index(m.selectedUser, " — ")
			if idx != -1 {
				namePart := m.selectedUser[:idx]
				if strings.Contains(m.selectedUser, "активен") {
					m.selectedUser = namePart + " — отключен"
				} else {
					m.selectedUser = namePart + " — активен"
				}
				// update list
				for i, u := range m.userList {
					if strings.HasPrefix(u, namePart) {
						m.userList[i] = m.selectedUser
					}
				}
			}
		case 2:
			// Delete mock
			for i, u := range m.userList {
				if u == m.selectedUser {
					m.userList = append(m.userList[:i], m.userList[i+1:]...)
					break
				}
			}
			m.currentScreen = screenUserList
		case 3:
			m.currentScreen = screenUserList
		}
		m.cursor = 0

	case screenSettings:
		if m.cursor == len(m.settingsMenu)-1 {
			m.currentScreen = screenMain
		}
		m.cursor = 0

	case screenLogs:
		if m.cursor == len(m.logsMenu)-1 {
			m.currentScreen = screenMain
		}
		m.cursor = 0

	case screenShowQR, screenApply:
		m.goBack()
	}

	return m, nil
}

func (m model) View() string {
	var s strings.Builder

	// Header Title
	s.WriteString(titleStyle.Render("TransferBox — Modern Go TUI") + "\n\n")

	// Status Info Block
	statusBlock := fmt.Sprintf(
		"  %s %s\n  %s %s\n  %s %s",
		statusLabelStyle.Render("Домен:"), infoStyle.Render(m.domain),
		statusLabelStyle.Render("Caddy:"), statusValStyle.Foreground(green).Render("● "+m.caddyStatus),
		statusLabelStyle.Render("sing-box:"), statusValStyle.Foreground(green).Render("● "+m.sbStatus),
	)
	s.WriteString(statusBlock + "\n\n")

	// Main content area based on current screen
	var content strings.Builder
	switch m.currentScreen {
	case screenMain:
		content.WriteString(lipgloss.NewStyle().Bold(true).Foreground(white).Render("Главное Меню") + "\n\n")
		content.WriteString(m.renderMenu(m.mainMenu))

	case screenUsers:
		content.WriteString(lipgloss.NewStyle().Bold(true).Foreground(white).Render("Раздел: Пользователи") + "\n\n")
		content.WriteString(m.renderMenu(m.usersMenu))

	case screenUserList:
		content.WriteString(lipgloss.NewStyle().Bold(true).Foreground(white).Render("Список Пользователей") + "\n\n")
		list := append([]string{}, m.userList...)
		list = append(list, "Назад")
		content.WriteString(m.renderMenu(list))

	case screenUserActions:
		content.WriteString(lipgloss.NewStyle().Bold(true).Foreground(white).Render("Действие над: "+m.selectedUser) + "\n\n")
		content.WriteString(m.renderMenu(m.actionMenu))

	case screenShowQR:
		content.WriteString(lipgloss.NewStyle().Bold(true).Foreground(white).Render("QR-код подключения") + "\n\n")
		// Draw a mock QR code in terminal using block characters
		qr := "  █▀▀▀▀▀█ ▄▄█▀▀█▄ █▀▀▀▀▀█\n" +
			"  █ ███ █ ▄ ▀█ ▄▄ █ ███ █\n" +
			"  █ ▀▀▀ █  ▀  ▀██ █ ▀▀▀ █\n" +
			"  ▀▀▀▀▀▀▀ ▀▄█ ▀ █ ▀▀▀▀▀▀▀\n" +
			"  ▄▀▀▀▄▄▀ ▀  █▀▄▀▄▀▄▄▄ ▀▀\n" +
			"  █▀██▀ ▀▀▀█▄▀▄ █▀ █▄  ▄█\n" +
			"  ▀ ▀▀  ▀▀ ▀▄▄ ▄▀▄▀▀  ▀▀█\n" +
			"  █▀▀▀▀▀█ ▄▄▄▄ ▀  █▀ ▀ ██\n" +
			"  █ ███ █ █ █ █ █ █ ▀ █▀ \n" +
			"  █ ▀▀▀ █ █▀▀▀▀ ▀ ▀▀▀██  \n" +
			"  ▀▀▀▀▀▀▀ ▀▀▀  ▀▀▀▀▀  ▀  \n"
		content.WriteString(lipgloss.NewStyle().Foreground(white).Render(qr) + "\n")
		content.WriteString(lipgloss.NewStyle().Foreground(cyan).Render("  vless://d4187f5d-7a... (сокращено)\n\n"))
		content.WriteString(selectedItemStyle.Render("> Нажмите Enter для возврата"))

	case screenSettings:
		content.WriteString(lipgloss.NewStyle().Bold(true).Foreground(white).Render("Настройки Сервера") + "\n\n")
		content.WriteString(m.renderMenu(m.settingsMenu))

	case screenApply:
		content.WriteString(lipgloss.NewStyle().Bold(true).Foreground(white).Render("Перезапуск Служб") + "\n\n")
		content.WriteString(lipgloss.NewStyle().Foreground(green).Render("  ✓ Конфигурации сгенерированы!\n  ✓ Службы перезапущены успешно!\n\n"))
		content.WriteString(selectedItemStyle.Render("> Нажмите Enter для возврата"))

	case screenLogs:
		content.WriteString(lipgloss.NewStyle().Bold(true).Foreground(white).Render("Просмотр Логов") + "\n\n")
		content.WriteString(m.renderMenu(m.logsMenu))
	}

	// Render inside borders
	s.WriteString(borderStyle.Render(content.String()) + "\n\n")

	// Footer instructions
	s.WriteString(footerStyle.Render("↑/↓: Навигация • Enter: Выбрать • Esc: Назад • q: Выход") + "\n")

	return s.String()
}

func (m model) renderMenu(items []string) string {
	var s strings.Builder
	for i, item := range items {
		if m.cursor == i {
			s.WriteString(selectedItemStyle.Render("➔ "+item) + "\n")
		} else {
			s.WriteString(menuItemStyle.Render(item) + "\n")
		}
	}
	return s.String()
}

func main() {
	p := tea.NewProgram(initialModel())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error running program: %v", err)
		os.Exit(1)
	}
}
