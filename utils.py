import shutil
import zipfile
import httpx
from pathlib import Path
from rich.progress import Progress
from rich.console import Console
import datetime

console = Console()


def download_file(url: str, dest_path: Path):
    """
    使用进度条将文件从 URL 下载到目标路径。
    """
    try:
        with httpx.stream("GET", url, follow_redirects=True) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", 0))

            with open(dest_path, "wb") as f:
                with Progress() as progress:
                    task = progress.add_task(
                        f"[cyan]正在下载 {dest_path.name}...", total=total
                    )
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
        console.print(f"[green]成功下载: {dest_path}[/green]")
    except Exception as e:
        console.print(f"[red]下载失败 {url}: {e}[/red]")
        raise


def extract_zip(zip_path: Path, extract_to: Path):
    """
    将 Zip 文件解压到指定目录。
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        console.print(f"[green]成功解压到: {extract_to}[/green]")
    except Exception as e:
        console.print(f"[red]解压失败 {zip_path}: {e}[/red]")
        raise


def backup_dir(target_dir: Path):
    """
    如果目标目录存在，则通过重命名（添加时间戳）来备份该目录。
    """
    if target_dir.exists():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = target_dir.parent / f"{target_dir.name}_backup_{timestamp}"
        try:
            shutil.move(str(target_dir), str(backup_path))
            console.print(f"[yellow]已将现有配置备份至: {backup_path}[/yellow]")
        except PermissionError:
            console.print("[bold red]备份失败: 权限被拒绝。[/bold red]")
            console.print(
                "[yellow]请先退出 Rime 输入法程序（右键任务栏图标选择“退出”），然后再试。[/yellow]"
            )
            raise PermissionError(f"无法访问 {target_dir}，请确保没有程序正在占用它。")
        except Exception as e:
            console.print(f"[red]备份失败 {target_dir}: {e}[/red]")
            raise
    else:
        console.print(f"[dim]未在 {target_dir} 发现现有目录，跳过备份。[/dim]")
