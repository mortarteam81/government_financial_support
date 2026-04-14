"""
config_loader.py
────────────────
YAML 설정 파일을 로드하고 유효성을 검사한 뒤
하네스 전체에서 사용할 정규화된 Config 객체를 반환합니다.

[바이브코딩 팁]
  AI에게 "config.yaml의 ○○ 섹션을 추가/수정해줘" 라고 요청하면
  이 파일의 검증 로직도 함께 수정해야 합니다.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


# ── 데이터 클래스 정의 ─────────────────────────────────────────────────────
@dataclass
class ValueTransform:
    multiply: float = 1.0
    label: str = ""


@dataclass
class DimConfig:
    col: str
    label: str
    normalize: dict[str, str] = field(default_factory=dict)


@dataclass
class KpiConfig:
    label: str
    type: str           # entity_count | value_sum | top_entity | growth_rate
    unit: str = ""
    from_period: int | None = None
    to_period: int | None = None


@dataclass
class PresetConfig:
    label: str
    type: str           # entity_list | filter_match | top_n
    entities: list[str] = field(default_factory=list)
    match: dict[str, Any] = field(default_factory=dict)
    exclude_match: dict[str, list] = field(default_factory=dict)
    n: int = 10


@dataclass
class OutputConfig:
    dir: str = "./output"
    html_enabled: bool = True
    html_filename: str = "dashboard.html"


@dataclass
class Config:
    # project
    project_name: str = ""
    project_description: str = ""

    # data
    data_file: str = ""
    data_encoding: str = "utf-8-sig"
    data_low_memory: bool = False

    # columns
    entity_col: str = ""
    time_col: str = ""
    value_col: str = ""
    value_transform: ValueTransform = field(default_factory=ValueTransform)
    filter_dims: list[DimConfig] = field(default_factory=list)
    group_dims: list[DimConfig] = field(default_factory=list)

    # dashboard
    title: str = ""
    subtitle: str = ""
    theme: str = "dark"
    kpi: list[KpiConfig] = field(default_factory=list)
    badges: list[str] = field(default_factory=list)
    presets: list[PresetConfig] = field(default_factory=list)

    # output
    output: OutputConfig = field(default_factory=OutputConfig)


# ── 로더 ──────────────────────────────────────────────────────────────────
def load_config(yaml_path: str | Path) -> Config:
    """YAML 파일을 읽어 Config 객체로 반환합니다."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")

    with open(path, encoding="utf-8") as f:
        raw: dict = yaml.safe_load(f)

    cfg = Config()

    # ── project ──
    p = raw.get("project", {})
    cfg.project_name        = p.get("name", "project")
    cfg.project_description = p.get("description", "")

    # ── data ──
    d = raw.get("data", {})
    cfg.data_file       = d.get("file", "")
    cfg.data_encoding   = d.get("encoding", "utf-8-sig")
    cfg.data_low_memory = d.get("low_memory", False)

    # ── columns ──
    c = raw.get("columns", {})
    cfg.entity_col = _require(c, "entity", "columns.entity")
    cfg.time_col   = _require(c, "time",   "columns.time")
    cfg.value_col  = _require(c, "value",  "columns.value")

    vt = c.get("value_transform", {})
    cfg.value_transform = ValueTransform(
        multiply = float(vt.get("multiply", 1.0)),
        label    = vt.get("label", ""),
    )

    cfg.filter_dims = [
        DimConfig(col=d["col"], label=d.get("label", d["col"]),
                  normalize=d.get("normalize") or {})
        for d in c.get("filter_dims", [])
    ]
    cfg.group_dims = [
        DimConfig(col=d["col"], label=d.get("label", d["col"]),
                  normalize=d.get("normalize") or {})
        for d in c.get("group_dims", [])
    ]

    # ── dashboard ──
    db = raw.get("dashboard", {})
    cfg.title    = db.get("title", cfg.project_name)
    cfg.subtitle = db.get("subtitle", "")
    cfg.theme    = db.get("theme", "dark")
    cfg.badges   = db.get("badges", [])

    cfg.kpi = [
        KpiConfig(
            label       = k["label"],
            type        = k["type"],
            unit        = k.get("unit", ""),
            from_period = k.get("from_period"),
            to_period   = k.get("to_period"),
        )
        for k in db.get("kpi", [])
    ]

    cfg.presets = [
        PresetConfig(
            label         = pr["label"],
            type          = pr["type"],
            entities      = pr.get("entities", []),
            match         = pr.get("match", {}),
            exclude_match = pr.get("exclude_match", {}),
            n             = pr.get("n", 10),
        )
        for pr in db.get("presets", [])
    ]

    # ── output ──
    o = raw.get("output", {})
    html = o.get("html", {})
    cfg.output = OutputConfig(
        dir           = o.get("dir", "./output"),
        html_enabled  = html.get("enabled", True),
        html_filename = html.get("filename", "dashboard.html"),
    )

    return cfg


def _require(d: dict, key: str, path: str) -> Any:
    """필수 키가 없으면 명확한 에러 메시지를 출력합니다."""
    if key not in d:
        raise ValueError(
            f"[config 오류] '{path}' 가 설정 파일에 없습니다.\n"
            f"  → config.yaml의 columns 섹션을 확인하세요."
        )
    return d[key]
