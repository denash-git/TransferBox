from __future__ import annotations
from rich.console import Console

from core.services.diagnostics_service import DiagnosticsService
from tui.components.menu import ArrowMenu, MenuItem
from tui.components.dialogs import pause_prompt
from tui.components.layout import get_block_padding, BLOCK_WIDTH, DOUBLE_LINE, SINGLE_LINE

console = Console(highlight=False)


class DiagnosticsScreen:
    def __init__(self, diagnostics_service: DiagnosticsService):
        self.diagnostics_service = diagnostics_service

    def show(self):
        while True:
            metrics = self.diagnostics_service.get_system_metrics()
            items = [
                MenuItem(id="metrics", label=f"Ресурсы: CPU {metrics['cpu_percent']}% | RAM {metrics['ram_percent']}%"),
                MenuItem(id="speedtest", label="Тест скорости сети (Ookla Speedtest)"),
                MenuItem(id="iperf3", label="Тест пропускной способности (iperf3, порт 5201)"),
                MenuItem(id="logs_caddy", label="Журнал логов Caddy (journalctl)"),
                MenuItem(id="logs_singbox", label="Журнал логов Sing-Box"),
                MenuItem(id="logs_mieru", label="Журнал логов Mieru"),
                MenuItem(id="back", label="Назад в главное меню"),
            ]

            menu = ArrowMenu(
                title="Диагностика и Мониторинг",
                subtitle=f"Аптайм: {metrics['uptime_str']} | Диск: {metrics['disk_used_gb']}/{metrics['disk_total_gb']} GB",
                items=items,
            )
            choice = menu.show()

            if choice in ("back", None):
                break
            elif choice == "metrics":
                self._show_metrics_details(metrics)
            elif choice == "speedtest":
                self._run_speedtest_flow()
            elif choice == "iperf3":
                self._run_iperf3_flow()
            elif choice == "logs_caddy":
                self._show_logs("caddy")
            elif choice == "logs_singbox":
                self._show_logs("sing-box")
            elif choice == "logs_mieru":
                self._show_logs("mita")

    def _show_metrics_details(self, metrics: dict):
        pad = get_block_padding(BLOCK_WIDTH)
        console.print(f"\n{pad}[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]")
        console.print(f"{pad}[bold white]{'Системные показатели сервера'.center(BLOCK_WIDTH)}[/bold white]")
        console.print(f"{pad}[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]")
        console.print(f"{pad}  Процессор (CPU):    [bold yellow]{metrics['cpu_percent']}%[/bold yellow]")
        console.print(f"{pad}  Оперативная память: [bold green]{metrics['ram_used_mb']}[/bold green] / {metrics['ram_total_mb']} MB ({metrics['ram_percent']}%)")
        console.print(f"{pad}  Дисковое хранилище: [bold cyan]{metrics['disk_used_gb']}[/bold cyan] / {metrics['disk_total_gb']} GB ({metrics['disk_percent']}%)")
        console.print(f"{pad}  Время работы:       [bold white]{metrics['uptime_str']}[/bold white]")
        console.print(f"{pad}[dim]{SINGLE_LINE}[/dim]\n")
        pause_prompt()

    def _run_speedtest_flow(self):
        pad = get_block_padding(BLOCK_WIDTH)
        console.print(f"\n{pad}[bold yellow]Выполняется тест скорости Ookla Speedtest... Пожалуйста, подождите (до 30 сек)[/bold yellow]")
        ok, res = self.diagnostics_service.run_speedtest()
        if not ok:
            console.print(f"\n{pad}[bold red]{res.get('error', 'Сбой запуска теста скорости.')}[/bold red]")
            pause_prompt()
            return

        console.print(f"\n{pad}[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]")
        console.print(f"{pad}[bold white]{'Результаты Speedtest'.center(BLOCK_WIDTH)}[/bold white]")
        console.print(f"{pad}[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]")
        console.print(f"{pad}  Сервер / Провайдер: [bold white]{res['server_name']} ({res['provider']})[/bold white]")
        console.print(f"{pad}  Задержка (Ping):    [bold yellow]{res['latency_ms']} ms[/bold yellow] (jitter: {res['jitter_ms']} ms)")
        console.print(f"{pad}  Входящая скорость:  [bold green]{res['download_mbps']} Mbps[/bold green]")
        console.print(f"{pad}  Исходящая скорость: [bold green]{res['upload_mbps']} Mbps[/bold green]")
        console.print(f"{pad}  Потеря пакетов:     [bold cyan]{res['packet_loss_percent']}%[/bold cyan]")
        console.print(f"{pad}[dim]{SINGLE_LINE}[/dim]\n")
        pause_prompt()

    def _run_iperf3_flow(self):
        pad = get_block_padding(BLOCK_WIDTH)
        console.print(f"\n{pad}[bold yellow]Запуск сервера iperf3 (таймаут 180 сек, порт 5201 открыт в UFW)...[/bold yellow]")
        ok, msg = self.diagnostics_service.run_ephemeral_iperf3(timeout_sec=180)
        console.print(f"\n{pad}[bold green]✓ {msg}[/bold green]\n")
        pause_prompt()

    def _show_logs(self, service: str):
        pad = get_block_padding(BLOCK_WIDTH)
        logs = self.diagnostics_service.get_service_logs(service, lines_count=30)
        console.print(f"\n{pad}[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]")
        console.print(f"{pad}[bold white]{f'Журнал службы {service}'.center(BLOCK_WIDTH)}[/bold white]")
        console.print(f"{pad}[bold sky_blue]{DOUBLE_LINE}[/bold sky_blue]\n")
        for line in logs.splitlines():
            console.print(f"  {line[:110]}")
        console.print(f"\n{pad}[dim]{SINGLE_LINE}[/dim]\n")
        pause_prompt()
