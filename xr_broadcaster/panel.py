from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
import time
import threading

class ControlPanel:
    """终端底部中控面板，可使用 dict 更新数据"""

    def __init__(self, refresh_hz=8, title="中控面板"):
        self.console = Console()
        self.refresh_hz = refresh_hz
        self.title = title
        self.data = {}
        self._live = None

    # 构建面板
    def _make_panel(self):
        table = Table(expand=True)
        table.add_column("项目")
        table.add_column("值")  #, justify="right")

        for k, v in self.data.items():
            table.add_row(str(k), str(v))

        return Panel(table, title=self.title, border_style="cyan")

    # 更新接口 —— 推荐的版本
    def update(self, data: dict):
        """
        更新面板数据:
        panel.update({"CPU": "33%", "FPS": 99, "温度": "60°C"})
        """
        self.data.update(data)

        if self._live:
            self._live.update(self._make_panel())

    # 后台启动
    def start(self):
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    # 主循环
    def run(self):
        with Live(
            self._make_panel(),
            refresh_per_second=self.refresh_hz,
            console=self.console,
            screen=False,
        ) as live:
            self._live = live
            while True:
                time.sleep(0.1)


if __name__ == "__main__":
    import time
    import random

    panel = ControlPanel()
    panel.start()

    for i in range(9999):
        print(f"日志输出 {i}")

        panel.update({
            "CPU": f"{random.randint(1, 100)}%",
            "FPS": random.randint(20, 120),
            "温度": f"{random.randint(30, 90)}°C",
        })

        time.sleep(0.3)