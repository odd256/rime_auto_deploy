import platform
import subprocess
import os
import shutil
from pathlib import Path
from rich.console import Console

console = Console()


class RimeManager:
    def install_rime(self):
        raise NotImplementedError

    def stop_rime(self):
        """尝试停止 Rime 服务/进程。"""
        pass

    def get_config_dir(self) -> Path:
        raise NotImplementedError

    def post_install_deploy(self):
        """如果可用，运行部署命令。"""
        pass


class WindowsRimeManager(RimeManager):
    def stop_rime(self):
        console.print("[cyan]正在尝试停止 Weasel 服务以解除文件占用...[/cyan]")
        # 终止 WeaselServer 和 WeaselDeployer
        processes = ["WeaselServer.exe", "WeaselDeployer.exe"]
        for proc in processes:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    def install_rime(self):
        console.print("[cyan]正在检查 Weasel (小狼毫)...[/cyan]")
        # 简单检查 WeaselDeployer.exe 是否存在于常见路径，或尝试使用 winget
        # 如果可用，使用 winget 更干净
        try:
            subprocess.run(
                ["winget", "install", "Rime.Weasel", "-e", "--source", "winget"],
                check=True,
            )
            console.print("[green]Weasel 已通过 Winget 成功安装。[/green]")
        except subprocess.CalledProcessError:
            console.print(
                "[yellow]Winget 安装失败或 Weasel 已安装。如果不存在，请确保手动安装 Weasel。[/yellow]"
            )

    def get_config_dir(self) -> Path:
        # 通常是 %APPDATA%\Rime
        return Path(os.environ["APPDATA"]) / "Rime"

    def post_install_deploy(self):
        console.print("[yellow]配置完成后，重新部署生效。[/yellow]")


class MacRimeManager(RimeManager):
    def install_rime(self):
        console.print("[cyan]正在检查 Squirrel (鼠须管)...[/cyan]")
        try:
            subprocess.run(["brew", "install", "--cask", "squirrel"], check=True)
            console.print("[green]Squirrel 已通过 Homebrew 成功安装。[/green]")
        except subprocess.CalledProcessError:
            console.print(
                "[yellow]Homebrew 安装失败。请确保手动安装 Squirrel。[/yellow]"
            )
        except FileNotFoundError:
            console.print(
                "[red]未找到 Homebrew。请安装 Homebrew 或手动安装 Squirrel。[/red]"
            )

    def get_config_dir(self) -> Path:
        return Path.home() / "Library" / "Rime"


class LinuxRimeManager(RimeManager):
    def __init__(self):
        self.variant = "fcitx5"  # 默认为 fcitx5

    def install_rime(self):
        console.print("[cyan]Linux Rime 安装[/cyan]")
        console.print("检测到 Linux。正在尝试安装 fcitx5-rime (推荐)...")

        # 简单的包管理器检测
        pkg_managers = {
            "apt": ["sudo", "apt", "install", "fcitx5-rime"],
            "pacman": ["sudo", "pacman", "-S", "fcitx5-rime"],
            "dnf": ["sudo", "dnf", "install", "fcitx5-rime"],
        }

        installed = False
        for mgr, cmd in pkg_managers.items():
            if shutil.which(mgr):
                try:
                    console.print(f"正在运行: {' '.join(cmd)}")
                    subprocess.run(cmd, check=True)
                    installed = True
                    break
                except subprocess.CalledProcessError:
                    console.print(f"[red]通过 {mgr} 安装失败。[/red]")

        if not installed:
            console.print(
                "[yellow]无法检测到支持的包管理器或安装失败。请手动安装 'fcitx5-rime'。[/yellow]"
            )

    def get_config_dir(self) -> Path:
        # Fcitx5 rime 路径
        return Path.home() / ".local" / "share" / "fcitx5" / "rime"


def get_manager() -> RimeManager:
    system = platform.system()
    if system == "Windows":
        return WindowsRimeManager()
    elif system == "Darwin":
        return MacRimeManager()
    elif system == "Linux":
        return LinuxRimeManager()
    else:
        raise OSError(f"不支持的操作系统: {system}")
