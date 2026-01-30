import shutil
import tempfile
from pathlib import Path
from rich.console import Console
from utils import download_file, extract_zip, backup_dir

console = Console()

RIME_ICE_URL = "https://github.com/iDvel/rime-ice/archive/refs/heads/main.zip"


class ConfigIntegrator:
    def __init__(self, rime_config_dir: Path):
        self.rime_config_dir = rime_config_dir

    def install_rime_ice(self, selected_schemas=None):
        console.print(
            f"[cyan]开始安装/更新雾凇拼音 (Rime-Ice) 基础文件到 {self.rime_config_dir}...[/cyan]"
        )

        # 1. 备份现有配置
        backup_dir(self.rime_config_dir)

        # 确保目录存在
        self.rime_config_dir.mkdir(parents=True, exist_ok=True)

        # 2. 下载并解压
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "rime-ice.zip"

            console.print("[dim]正在通过 GitHub 下载雾凇拼音配置...[/dim]")
            download_file(RIME_ICE_URL, zip_path)

            extract_path = temp_path / "extracted"
            extract_zip(zip_path, extract_path)

            source_dir = next(extract_path.iterdir())
            if not source_dir.is_dir():
                source_dir = extract_path

            console.print("[dim]正在将基础文件复制到配置目录...[/dim]")

            try:
                shutil.copytree(source_dir, self.rime_config_dir, dirs_exist_ok=True)
                console.print("[green]雾凇拼音基础文件安装/更新完成。[/green]")
            except Exception as e:
                console.print(f"[red]复制文件失败: {e}[/red]")
                raise

        # 3. 如果用户在 Step 03 选择了模式，生成一个基础配置
        if selected_schemas:
            console.print(
                f"[cyan]正在根据选择初始化方案: {', '.join(selected_schemas)}[/cyan]"
            )
            self.write_base_config(selected_schemas)

    def write_base_config(self, selected_schemas):
        """
        在下载完仓库后，立即生成一个最基础的 default.custom.yaml。
        """
        dest_path = self.rime_config_dir / "default.custom.yaml"
        schemas_yaml = "\n".join([f"    - schema: {s}" for s in selected_schemas])

        content = f"""patch:
  "menu/page_size": 9
  schema_list:
{schemas_yaml}
"""
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[dim]已生成基础方案配置文件: {dest_path.name}[/dim]")

    def apply_custom_config(self, selected_schemas=None):
        """
        将项目根目录下 custom_config 文件夹内的所有配置文件同步到 Rime 目录。
        如果包含 default.custom.yaml，则自动注入 schema_list。
        """
        project_root = Path(__file__).parent
        local_custom_dir = project_root / "custom_config"

        if not local_custom_dir.exists():
            local_custom_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[yellow]提示: 已创建 {local_custom_dir} 目录。[/yellow]")
            return

        console.print(
            f"[cyan]正在同步本地 {local_custom_dir.name} 执行配置部署...[/cyan]"
        )

        # 构建要注入的 YAML 字符串
        schemas_yaml = ""
        if selected_schemas:
            schemas_yaml = "  schema_list:\n" + "\n".join(
                [f"    - schema: {s}" for s in selected_schemas]
            )

        try:
            for item in local_custom_dir.iterdir():
                if item.is_file() and item.suffix in [".yaml", ".yml"]:
                    # 统一目标扩展名为 .yaml
                    dest_name = (
                        "default.custom.yaml"
                        if item.stem == "default.custom"
                        else item.name
                    )
                    if dest_name.endswith(".yml"):
                        dest_name = dest_name[:-3] + "yaml"

                    dest_path = self.rime_config_dir / dest_name

                    content = ""
                    with open(item, "r", encoding="utf-8") as f:
                        content = f.read()

                    # 如果是 default.custom 且用户选了方案，尝试注入
                    if "default.custom" in item.name and selected_schemas:
                        if "schema_list:" not in content:
                            # 在 patch: 后面注入
                            if "patch:" in content:
                                content = content.replace(
                                    "patch:", f"patch:\n{schemas_yaml}"
                                )
                                console.print(
                                    f"[dim]已在 {item.name} 中注入方案选择[/dim]"
                                )
                            else:
                                content = f"patch:\n{schemas_yaml}\n" + content

                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    console.print(f"[dim]已部署: {dest_name}[/dim]")

            console.print("[bold green]自定义配置文件已成功部署到 Rime。[/bold green]")
        except Exception as e:
            console.print(f"[red]同步自定义配置失败: {e}[/red]")
            raise
