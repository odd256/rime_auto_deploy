import sys
import json
import subprocess
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rime_manager import get_manager
from config_integrator import ConfigIntegrator

console = Console()
SETTINGS_FILE = Path(__file__).parent / "settings.json"


def load_settings():
    """从本地文件加载设置"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_settings(settings):
    """保存设置到本地文件"""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        console.print(f"[red]保存设置失败: {e}[/red]")


def select_config_source(force_ask=False):
    """选择基础配置源"""
    settings = load_settings()
    if not force_ask and "config_source" in settings:
        return settings["config_source"]

    console.print("\n[bold cyan]请选择基础配置源:[/bold cyan]")
    console.print("[1] 雾凇拼音 (Rime-Ice) - 默认")
    console.print("[2] 白霜拼音 (Rime-Frost) - 词库更全")

    mapping = {
        "1": "rime-ice",
        "2": "rime-frost",
    }

    choice = Prompt.ask("输入序号", choices=["1", "2"], default="1")
    source = mapping.get(choice, "rime-ice")

    settings["config_source"] = source
    save_settings(settings)
    console.print(f"[green]配置源已设置为: {source}[/green]")
    return source


def select_schemas(force_ask=False):
    """
    选择输入方案逻辑。
    如果已经保存过方案且非强制询问，则直接返回保存的方案。
    """
    settings = load_settings()
    source = settings.get("config_source", "rime-ice")

    if not force_ask and "selected_schemas" in settings:
        return settings["selected_schemas"]

    console.print(
        "\n[bold cyan]请配置要启用的输入方案 (多选请用逗号分隔，直接回车默认为全拼):[/bold cyan]"
    )

    # 定义不同源的方案映射
    if source == "rime-frost":
        # 白霜拼音方案列表
        schemas_info = [
            ("1", "rime_frost", "白霜拼音 (全拼)"),
            ("2", "rime_frost_double_pinyin_flypy", "小鹤双拼"),
            ("3", "rime_frost_double_pinyin_mspy", "微软双拼"),
            ("4", "rime_frost_double_pinyin", "自然码双拼"),
            ("5", "rime_frost_double_pinyin_sogou", "搜狗双拼"),
        ]
        default_id = "rime_frost"
    else:
        # 雾凇拼音方案列表 (默认)
        schemas_info = [
            ("1", "rime_ice", "雾凇拼音 (全拼)"),
            ("2", "double_pinyin_flypy", "小鹤双拼"),
            ("3", "double_pinyin_mspro", "微软双拼"),
            ("4", "double_pinyin", "自然码双拼"),
            ("5", "double_pinyin_abc", "智能ABC双拼"),
        ]
        default_id = "rime_ice"

    for idx, schema_id, name in schemas_info:
        console.print(f"[{idx}] {name}")

    mapping = {idx: schema_id for idx, schema_id, name in schemas_info}

    input_str = Prompt.ask("输入序号", default="1")
    choices = [c.strip() for c in input_str.split(",")]

    selected = []
    for c in choices:
        if c in mapping:
            selected.append(mapping[c])

    if not selected:
        selected.append(default_id)

    # 保存到设置
    settings["selected_schemas"] = selected
    save_settings(settings)
    console.print(f"[green]方案设置已保存: {', '.join(selected)}[/green]")
    return selected


def run_step_01(manager):
    """Step 01: 安装 Rime 输入法"""
    console.print("\n[bold]Step 01: 安装 Rime 输入法[/bold]")
    try:
        manager.install_rime()
        console.print(
            "[yellow]提示: 请确保已将 Rime 设置为系统输入法（Windows 可能需要注销并重新登录）。[/yellow]"
        )
    except Exception as e:
        console.print(f"[red]安装发生错误: {e}[/red]")
        raise


def run_step_02(manager):
    """Step 02: 备份 Rime 默认配置"""
    console.print("\n[bold]Step 02: 备份 Rime 默认配置[/bold]")
    try:
        config_dir = manager.get_config_dir()
        from utils import backup_dir

        backup_dir(config_dir)
    except Exception as e:
        console.print(f"[red]备份发生错误: {e}[/red]")
        raise


def run_step_03(manager):
    """Step 03: 自动安装 Rime 配置 (拉取上游仓库)"""
    settings = load_settings()
    source_id = settings.get("config_source", "rime-ice")

    console.print(f"\n[bold]Step 03: 自动安装 {source_id} 配置 (拉取上游仓库)[/bold]")
    manager.stop_rime()
    config_dir = manager.get_config_dir()
    integrator = ConfigIntegrator(config_dir)
    selected = settings.get("selected_schemas")
    try:
        integrator.install_base_config(source_id=source_id, selected_schemas=selected)
    except Exception as e:
        console.print(f"[red]配置下载失败: {e}[/red]")
        raise


def run_step_04(manager):
    """Step 04: 同步自定义配置文件 (从本地 custom_config 目录)"""
    console.print(
        "\n[bold]Step 04: 同步自定义配置文件 (从本地 custom_config 目录)[/bold]"
    )

    # 自动获取已保存的方案
    selected = select_schemas()

    config_dir = manager.get_config_dir()
    integrator = ConfigIntegrator(config_dir)
    try:
        integrator.apply_custom_config(selected_schemas=selected)
    except Exception as e:
        console.print(f"[red]应用自定义设置失败: {e}[/red]")
        raise


def auto_mode(manager):
    console.print(
        Panel(
            "[bold green]进入自动模式 (Auto Mode)[/bold green]\n适用于第一次安装输入法"
        )
    )

    # 自动引导源选择和方案选择
    select_config_source()
    select_schemas()

    if Confirm.ask("开始执行 Step 01: 安装 Rime?", default=True):
        run_step_01(manager)

    if Confirm.ask("执行 Step 02~04 (备份、下载配置、同步自定义文件)?", default=True):
        run_step_02(manager)
        run_step_03(manager)
        run_step_04(manager)

    console.print("\n[bold green]自动模式流程完成！[/bold green]")
    manager.post_install_deploy()


def upgrade_mode(manager):
    while True:
        console.print(
            Panel(
                "[bold yellow]进入升级模式 (Upgrade Mode)[/bold yellow]\n用于对脚本或配置进行更新"
            )
        )
        console.print("[1] 升级 Rime Auto Deploy (脚本自身 - 仅 git 方式)")
        console.print("[2] 升级 Rime 配置 (上游雾凇拼音仓库)")
        console.print("[3] 同步最新本地自定义配置 (custom_config)")
        console.print("[4] 返回主菜单")

        choice = Prompt.ask("请选择升级项", choices=["1", "2", "3", "4"], default="4")

        if choice == "1":
            console.print("[cyan]正在尝试通过 git pull 更新脚本...[/cyan]")
            try:
                subprocess.run(["git", "pull"], check=True)
                console.print("[green]脚本已尝试更新，请重新启动脚本以应用。[/green]")
            except Exception as e:
                console.print(f"[red]更新失败: {e}[/red]")
        elif choice == "2":
            run_step_03(manager)
            manager.post_install_deploy()
        elif choice == "3":
            run_step_04(manager)
            manager.post_install_deploy()
        else:
            break


def main():
    try:
        manager = get_manager()

        # 启动时预选检查
        settings = load_settings()
        if "selected_schemas" not in settings or "config_source" not in settings:
            console.print(
                Panel(
                    "[yellow]欢迎！检测到您是第一次使用，请先设定您的基础配置源和输入方案。[/yellow]"
                )
            )
            select_config_source(force_ask=True)
            select_schemas(force_ask=True)

        while True:
            console.print("\n" + "=" * 20 + " Rime Deploy " + "=" * 20)
            console.print("欢迎使用 Rime 自动部署工具。\n")

            # 显示当前设置
            settings = load_settings()
            current_source = settings.get("config_source", "rime-ice")
            current_schemas = ", ".join(settings.get("selected_schemas", ["未设定"]))
            console.print(
                f"[dim]当前配置源: {current_source} | 已选方案: {current_schemas}[/dim]\n"
            )

            console.print("请选择工作模式:")
            console.print("[1] 自动模式 (Auto Mode): 适合第一次安装。")
            console.print("[2] 升级模式 (Upgrade Mode): 更新已有的 Rime 配置。")
            console.print(
                "[3] 同步配置 (Sync Config): 同步本地 custom_config 到 Rime。"
            )
            console.print("[4] 环境配置 (Environment Config): 修改配置源和输入方案。")
            console.print("[5] 退出")
            console.print("Tips: 输入索引编号(1/2/3/4/5)，Ctrl-C 退出。")

            choice = Prompt.ask("选择", choices=["1", "2", "3", "4", "5"], default="1")

            if choice == "1":
                auto_mode(manager)
            elif choice == "2":
                upgrade_mode(manager)
            elif choice == "3":
                run_step_04(manager)
                manager.post_install_deploy()
                Prompt.ask("\n[bold cyan]同步完成，按回车键返回主菜单[/bold cyan]")
            elif choice == "4":
                select_config_source(force_ask=True)
                select_schemas(force_ask=True)
                # 修改完后询问是否立即部署
                if Confirm.ask("方案已修改，是否立即同步到 Rime?", default=True):
                    run_step_04(manager)
                    manager.post_install_deploy()
                    Prompt.ask(
                        "\n[bold cyan]配置并同步完成，按回车键返回主菜单[/bold cyan]"
                    )
            elif choice == "5":
                console.print("感谢使用，再见！")
                sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n[yellow]用户已终止操作。[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]发生了致命错误: {e}[/bold red]")
        # 打印部分调用栈以便调试
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
