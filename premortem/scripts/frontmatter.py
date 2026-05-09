"""Parse/render YAML frontmatter с сохранением порядка ключей."""
# /// script
# dependencies = ["pyyaml>=6.0"]
# ///
from __future__ import annotations
import yaml


class FrontmatterError(ValueError):
    pass


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Возвращает (frontmatter_dict, body_text). Бросает FrontmatterError если формат сломан."""
    if not text.startswith("---\n"):
        raise FrontmatterError("не найден frontmatter в начале файла (ожидался ---)")

    end = text.find("\n---\n", 4)
    if end == -1:
        raise FrontmatterError("frontmatter не закрыт (ожидался --- после YAML-блока)")

    yaml_block = text[4:end]
    body = text[end + 5:]

    try:
        data = yaml.safe_load(yaml_block) or {}
    except yaml.YAMLError as e:
        raise FrontmatterError(f"невалидный YAML: {e}") from e

    if not isinstance(data, dict):
        raise FrontmatterError(f"frontmatter должен быть dict, не {type(data).__name__}")

    return data, body


def render_frontmatter(fm: dict, body: str) -> str:
    """Рендерит ---YAML---\\nbody. Сохраняет порядок ключей dict."""
    yaml_text = yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False,
    )
    return f"---\n{yaml_text}---\n{body}"
