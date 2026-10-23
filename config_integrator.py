import re
import shutil
import tempfile
from pathlib import Path
from rich.console import Console
from utils import download_file, extract_zip, backup_dir, backup_dir_copy

console = Console()

CONFIG_SOURCES = {
    "rime-ice": {
        "name": "雾凇拼音 (Rime-Ice)",
        "url": "https://github.com/iDvel/rime-ice/archive/refs/heads/main.zip",
    },
    "rime-frost": {
        "name": "白霜拼音 (Rime-Frost)",
        "url": "https://github.com/gaboolic/rime-frost/archive/refs/heads/master.zip",
    },
}


class ConfigIntegrator:
    def __init__(self, rime_config_dir: Path):
        self.rime_config_dir = rime_config_dir

    def install_base_config(self, source_id="rime-ice", selected_schemas=None):
        source = CONFIG_SOURCES.get(source_id, CONFIG_SOURCES["rime-ice"])
        console.print(
            f"[cyan]开始安装/更新 {source['name']} 基础文件到 {self.rime_config_dir}...[/cyan]"
        )

        # 1. 备份现有配置（复制而非移动，保留原始目录以便叠加更新）
        backup_dir_copy(self.rime_config_dir)

        # 确保目录存在
        self.rime_config_dir.mkdir(parents=True, exist_ok=True)

        # 2. 下载并解压
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / f"{source_id}.zip"

            console.print(f"[dim]正在通过 GitHub 下载 {source['name']} 配置...[/dim]")
            download_file(source["url"], zip_path)

            extract_path = temp_path / "extracted"
            extract_zip(zip_path, extract_path)

            source_dir = next(extract_path.iterdir())
            if not source_dir.is_dir():
                source_dir = extract_path

            console.print("[dim]正在将基础文件复制到配置目录...[/dim]")

            try:
                shutil.copytree(source_dir, self.rime_config_dir, dirs_exist_ok=True)
                console.print(
                    f"[green]{source['name']} 基础文件安装/更新完成。[/green]"
                )
            except Exception as e:
                console.print(f"[red]复制文件失败: {e}[/red]")
                raise

        # 3. 如果用户在 Step 03 选择了模式，生成一个基础配置
        if selected_schemas:
            default_custom = self.rime_config_dir / "default.custom.yaml"
            if default_custom.exists():
                console.print(
                    "[dim]已存在 default.custom.yaml，跳过生成以保留用户配置。[/dim]"
                )
            else:
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
        import sys

        project_root = Path(__file__).parent
        local_custom_dir = project_root / "custom_config"

        if not local_custom_dir.exists():
            local_custom_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[yellow]提示: 已创建 {local_custom_dir} 目录。[/yellow]")
            return

        console.print(
            f"\n[cyan]正在同步本地 {local_custom_dir.name} 执行配置部署...[/cyan]"
        )

        # 构建要注入的 YAML 字符串
        schemas_yaml = ""
        if selected_schemas:
            schemas_yaml = "  schema_list:\n" + "\n".join(
                [f"    - schema: {s}" for s in selected_schemas]
            )

        try:
            count = 0
            for item in local_custom_dir.iterdir():
                if item.is_file() and item.suffix in [".yaml", ".yml"]:
                    # 1. 平台过滤
                    if sys.platform == "win32" and "squirrel.custom" in item.name:
                        console.print(f"[dim]跳过 macOS 专用配置: {item.name}[/dim]")
                        continue
                    if sys.platform == "darwin" and "weasel.custom" in item.name:
                        console.print(f"[dim]跳过 Windows 专用配置: {item.name}[/dim]")
                        continue

                    # 2. 统一目标扩展名为 .yaml
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

                    # 3. 如果是 default.custom 且用户选了方案，尝试注入
                    if "default.custom" in item.name and selected_schemas:
                        if "schema_list:" not in content:
                            # 在 patch: 后面注入
                            if "patch:" in content:
                                content = content.replace(
                                    "patch:", f"patch:\n{schemas_yaml}"
                                )
                                console.print(
                                    f"[dim]已在 {item.name} 中自动注入当前勾选的方案[/dim]"
                                )
                            else:
                                content = f"patch:\n{schemas_yaml}\n" + content

                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    console.print(
                        f" [green]√[/green] 已同步到 Rime: [bold]{dest_name}[/bold]"
                    )
                    count += 1

            # 4. 确保每个选中的方案都有默认英文和 Emoji patch
            if selected_schemas:
                for schema_id in selected_schemas:
                    self._ensure_default_english(schema_id)
                    self._ensure_default_emoji(schema_id)

            console.print(
                f"\n[bold green]自定义配置同步完成！共处理 {count} 个文件。[/bold green]"
            )
            console.print(
                "[dim]提示: 请稍后在任务栏 Rime 图标上选择“部署/重新部署”以使配置生效。[/dim]\n"
            )
        except Exception as e:
            console.print(f"[red]同步自定义配置失败: {e}[/red]")
            raise

    def _ensure_default_english(self, schema_id):
        """
        为指定方案注入默认英文配置。
        """
        dest_path = self.rime_config_dir / f"{schema_id}.custom.yaml"
        patch_content = '  # 找到 switches 列表中的第一个元素（通常是 ascii_mode），将其重置状态设为 1\n  "switches/@0/reset": 1'

        content = ""
        if dest_path.exists():
            with open(dest_path, "r", encoding="utf-8") as f:
                content = f.read()

        if '"switches/@0/reset": 1' in content:
            return

        if not content.strip():
            content = f"patch:\n{patch_content}\n"
        elif "patch:" in content:
            # 在 patch: 后面注入，保持 yaml 层级
            content = content.replace("patch:", f"patch:\n{patch_content}")
        else:
            content = f"patch:\n{patch_content}\n" + content

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[dim]已在 {schema_id}.custom.yaml 中注入默认英文配置[/dim]")

    def _ensure_default_emoji(self, schema_id):
        """为指定方案注入默认开启 Emoji 的配置。"""
        schema_path = self.rime_config_dir / f"{schema_id}.schema.yaml"
        if not schema_path.exists():
            console.print(f"[yellow]未找到方案 {schema_id}，跳过 Emoji 配置。[/yellow]")
            return

        # 雾凇、白霜的开关顺序不同，从方案中定位 emoji，而不是固定索引。
        schema_content = schema_path.read_text(encoding="utf-8-sig")
        switches = re.search(
            r"^switches:[ \t]*(?:#.*)?\r?\n(.*?)(?=^\S|\Z)",
            schema_content,
            re.MULTILINE | re.DOTALL,
        )
        names = (
            re.findall(
                r"^\s*-\s+name:\s*[\"']?([\w]+)",
                switches.group(1),
                re.MULTILINE,
            )
            if switches else []
        )
        if "emoji" not in names:
            console.print(f"[yellow]方案 {schema_id} 没有 Emoji 开关，跳过。[/yellow]")
            return

        patch_key = f"switches/@{names.index('emoji')}/reset"
        dest_path = self.rime_config_dir / f"{schema_id}.custom.yaml"
        content = dest_path.read_text(encoding="utf-8") if dest_path.exists() else ""
        existing_patch = rf"(?m)^([ \t]*[\"']?{re.escape(patch_key)}[\"']?:[ \t]*)[^\n]*"
        if re.search(existing_patch, content):
            content = re.sub(existing_patch, r"\g<1>1", content)
        else:
            patch_content = f'  # 默认开启 Emoji 候选\n  "{patch_key}": 1'
            if not content.strip():
                content = f"patch:\n{patch_content}\n"
            elif "patch:" in content:
                content = content.replace("patch:", f"patch:\n{patch_content}", 1)
            else:
                content = f"patch:\n{patch_content}\n" + content

        dest_path.write_text(content, encoding="utf-8")
        console.print(f"[dim]已在 {schema_id}.custom.yaml 中注入默认 Emoji 配置[/dim]")
