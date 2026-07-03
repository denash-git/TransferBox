package main

import (
	"fmt"
	"os"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/muesli/termenv"
)

// Vibrant color palette
var (
	colorPurple    = lipgloss.Color("#7D56F4")
	colorHotPink   = lipgloss.Color("#F02D7D")
	colorGreen     = lipgloss.Color("#00F294")
	colorRed       = lipgloss.Color("#FF4A4A")
	colorCyan      = lipgloss.Color("#00E5FF")
	colorGray      = lipgloss.Color("#777777")
	colorDarkGray  = lipgloss.Color("#222222")
	colorLightGray = lipgloss.Color("#DDDDDD")
	colorWhite     = lipgloss.Color("#FFFFFF")
)

// Premium UI Styles
var (
	// Header banner with gradient-like background using hot pink & purple
	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colorWhite).
			Background(colorPurple).
			Padding(1, 2).
			Width(76).
			Align(lipgloss.Center)

	subHeaderStyle = lipgloss.NewStyle().
			Foreground(colorHotPink).
			Bold(true).
			PaddingLeft(2)

	// Status panel styles
	panelTitleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colorCyan).
			PaddingLeft(2)

	labelStyle = lipgloss.NewStyle().
			Foreground(colorGray).
			Width(14).
			PaddingLeft(2)

	valueStyle = lipgloss.NewStyle().
			Foreground(colorLightGray).
			Bold(true)

	// Menu styling
	menuItemStyle = lipgloss.NewStyle().
			PaddingLeft(6).
			Foreground(colorLightGray)

	// Interactive active bar (like a real dashboard selection)
	selectedItemStyle = lipgloss.NewStyle().
				PaddingLeft(4).
				Foreground(colorWhite).
				Background(colorPurple).
				Bold(true).
				Width(66)

	// Border containers (making the app look much larger and spacious)
	mainBoxStyle = lipgloss.NewStyle().
			Border(lipgloss.DoubleBorder()).
			BorderForeground(colorPurple).
			Width(76).
			Padding(1, 2)

	statusBoxStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorHotPink).
			Width(76).
			Padding(1, 1)

	// User Status Pills
	pillActiveStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colorGreen).
			Padding(0, 1)

	pillInactiveStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colorRed).
			Padding(0, 1)

	footerStyle = lipgloss.NewStyle().
			Foreground(colorGray).
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
	userList      []userItem
	actionMenu    []string
	settingsMenu  []string
	logsMenu      []string
	selectedUser  userItem
	domain        string
	caddyStatus   string
	sbStatus      string
}

type userItem struct {
	name     string
	protocol string
	active   bool
}

func initialModel() model {
	return model{
		currentScreen: screenMain,
		cursor:        0,
		mainMenu:      []string{"Пользователи", "Настройки сервера", "Перезапустить службы", "Показать логи", "Выход"},
		usersMenu:     []string{"Список пользователей", "Новый пользователь", "Назад"},
		userList: []userItem{
			{name: "admin", protocol: "NaiveProxy", active: true},
			{name: "ivan_xhttp", protocol: "VLESS over XHTTP", active: true},
			{name: "test_ws", protocol: "VLESS over WebSocket", active: false},
		},
		actionMenu:   []string{"Показать QR и ссылку", "Включить / Отключить", "Удалить", "Назад"},
		settingsMenu: []string{"Домен: proxy.dtopl.online", "Email Let's Encrypt: admin@dtopl.online", "Фейк-сайт: techvision", "Назад"},
		logsMenu:     []string{"Caddy log (50 строк)", "sing-box log (50 строк)", "Назад"},
		domain:       "proxy.dtopl.online",
		caddyStatus:  "работает",
		sbStatus:     "работает",
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
		return 1
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
			// Toggle active status
			for i, u := range m.userList {
				if u.name == m.selectedUser.name {
					m.userList[i].active = !u.active
					m.selectedUser.active = m.userList[i].active
					break
				}
			}
		case 2:
			// Delete user
			for i, u := range m.userList {
				if u.name == m.selectedUser.name {
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

	// Top Banner
	s.WriteString(headerStyle.Render("TRANSFERBOX • PREMIUM GATEWAY DASHBOARD") + "\n\n")

	// Status Panel
	var statusContent strings.Builder
	statusContent.WriteString(panelTitleStyle.Render("● СИСТЕМНЫЙ СТАТУС") + "\n")
	statusContent.WriteString(fmt.Sprintf("%s %s\n", labelStyle.Render("Домен:"), valueStyle.Render(m.domain)))
	statusContent.WriteString(fmt.Sprintf("%s %s\n", labelStyle.Render("Caddy:"), valueStyle.Foreground(colorGreen).Render("● "+m.caddyStatus)))
	statusContent.WriteString(fmt.Sprintf("%s %s", labelStyle.Render("sing-box:"), valueStyle.Foreground(colorGreen).Render("● "+m.sbStatus)))

	s.WriteString(statusBoxStyle.Render(statusContent.String()) + "\n\n")

	// Main Interactive Window
	var windowContent strings.Builder
	switch m.currentScreen {
	case screenMain:
		windowContent.WriteString(subHeaderStyle.Render("ГЛАВНОЕ МЕНЮ") + "\n\n")
		windowContent.WriteString(m.renderMenu(m.mainMenu))

	case screenUsers:
		windowContent.WriteString(subHeaderStyle.Render("ПОЛЬЗОВАТЕЛИ") + "\n\n")
		windowContent.WriteString(m.renderMenu(m.usersMenu))

	case screenUserList:
		windowContent.WriteString(subHeaderStyle.Render("СПИСОК ПОЛЬЗОВАТЕЛЕЙ") + "\n\n")
		windowContent.WriteString(m.renderUserListMenu())

	case screenUserActions:
		windowContent.WriteString(subHeaderStyle.Render("ДЕЙСТВИЯ: "+m.selectedUser.name) + "\n\n")
		windowContent.WriteString(m.renderMenu(m.actionMenu))

	case screenShowQR:
		windowContent.WriteString(subHeaderStyle.Render("QR-КОД ПОДКЛЮЧЕНИЯ") + "\n\n")
		// Draw a stylized mock QR code
		qr := "  ▄▄▄▄▄▄▄   ▄▄  ▄ ▄▄▄▄▄▄▄\n" +
			"  █ ▄▄▄ █ ▀▀▀█▀██ █ ▄▄▄ █\n" +
			"  █ ███ █ █ ▀█ ▀▀ █ ███ █\n" +
			"  █▄▄▄▄▄█ █ █ █▀█ █▄▄▄▄▄█\n" +
			"  ▄▄  ▄▄▄ ▄▀▀ ▀▄▄ ▄▄▄ ▄ ▄\n" +
			"  ▄ █▄█▄▀█  ██▀█▀▄ █ ▄▀█▀\n" +
			"  ▀▄▄▀  ▀███▀▄▀ ▀  ▄ ▀█ ▄\n" +
			"  ▄▄▄▄▄▄▄  ▀▄ █▄█ ▀ ▀ █▀█\n" +
			"  █ ▄▄▄ █ █▀▀▀▀█▀██▀▄▄▀▀▀\n" +
			"  █ ███ █ ▀▄▀▀█ ▀▀█  ▀███\n" +
			"  █▄▄▄▄▄█ ██   ▀ █▀▀██ ▀ \n"
		windowContent.WriteString(lipgloss.NewStyle().Foreground(colorWhite).Render(qr) + "\n")
		windowContent.WriteString(lipgloss.NewStyle().Foreground(colorCyan).Render("  vless://d4187f5d-7a6b-4e12-886c-ec449c4f74d0@proxy.dtopl.online:443...\n\n"))
		windowContent.WriteString(selectedItemStyle.Render("  [ ENTER ] НАЗАД"))

	case screenSettings:
		windowContent.WriteString(subHeaderStyle.Render("НАСТРОЙКИ СЕРВЕРА") + "\n\n")
		windowContent.WriteString(m.renderMenu(m.settingsMenu))

	case screenApply:
		windowContent.WriteString(subHeaderStyle.Render("ПЕРЕЗАПУСК СЛУЖБ") + "\n\n")
		windowContent.WriteString(lipgloss.NewStyle().Foreground(colorGreen).Render("  ✓ Конфигурации успешно сгенерированы!\n  ✓ Службы перезапущены и активны!\n\n"))
		windowContent.WriteString(selectedItemStyle.Render("  [ ENTER ] НАЗАД"))

	case screenLogs:
		windowContent.WriteString(subHeaderStyle.Render("ЛОГИ СИСТЕМЫ") + "\n\n")
		windowContent.WriteString(m.renderMenu(m.logsMenu))
	}

	s.WriteString(mainBoxStyle.Render(windowContent.String()) + "\n\n")

	// Navigation instructions
	s.WriteString(footerStyle.Render("  ▲/▼: Навигация • Enter: Выбрать • Esc: Назад • q: Выход") + "\n")

	return s.String()
}

func (m model) renderMenu(items []string) string {
	var s strings.Builder
	for i, item := range items {
		// Padding lines to make the menu spacious and "большое"
		if i > 0 {
			s.WriteString("\n")
		}
		if m.cursor == i {
			s.WriteString(selectedItemStyle.Render(" ➔  "+item) + "\n")
		} else {
			s.WriteString(menuItemStyle.Render(item) + "\n")
		}
	}
	return s.String()
}

func (m model) renderUserListMenu() string {
	var s strings.Builder
	for i, u := range m.userList {
		if i > 0 {
			s.WriteString("\n")
		}

		statusStr := pillActiveStyle.Render("[ АКТИВЕН ]")
		if !u.active {
			statusStr = pillInactiveStyle.Render("[ ОТКЛЮЧЕН ]")
		}

		itemText := fmt.Sprintf("%-12s (%-20s)  %s", u.name, u.protocol, statusStr)

		if m.cursor == i {
			s.WriteString(selectedItemStyle.Render(" ➔  "+itemText) + "\n")
		} else {
			s.WriteString(menuItemStyle.Render(itemText) + "\n")
		}
	}

	// render "Back" item
	s.WriteString("\n")
	backIdx := len(m.userList)
	if m.cursor == backIdx {
		s.WriteString(selectedItemStyle.Render(" ➔  Назад") + "\n")
	} else {
		s.WriteString(menuItemStyle.Render("Назад") + "\n")
	}

	return s.String()
}

func main() {
	// Programmatically force TrueColor profile for rich coloring over SSH/terminals
	lipgloss.SetColorProfile(termenv.TrueColor)

	p := tea.NewProgram(initialModel())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error running program: %v", err)
		os.Exit(1)
	}
}
