"""
builder.py
──────────
전처리된 payload + config를 받아 출력물을 생성하는 빌더 모듈.
현재 지원: HTML 대시보드
향후 확장: Excel, PPTX, Markdown 리포트

[바이브코딩 팁]
  새 출력 포맷(예: PPTX)을 추가하려면:
  1. build_pptx(payload, cfg, output_path) 함수를 작성
  2. build_all()에서 cfg.output.pptx_enabled 조건으로 호출
"""

from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Any

from .config_loader import Config


# ── 메인 진입점 ─────────────────────────────────────────────────────────────
def build_all(payload: dict[str, Any], cfg: Config) -> None:
    """활성화된 모든 출력물을 생성합니다."""
    out_dir = Path(cfg.output.dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if cfg.output.html_enabled:
        filename = f"{cfg.project_name}_{cfg.output.html_filename}"
        out_path = out_dir / filename
        build_html(payload, cfg, out_path)
        print(f"  📄 HTML 대시보드: {out_path}")

    # ── 향후 확장 슬롯 ──
    # if cfg.output.excel_enabled:
    #     build_excel(payload, cfg, out_dir / f"{cfg.project_name}_data.xlsx")
    #
    # if cfg.output.pptx_enabled:
    #     build_pptx(payload, cfg, out_dir / f"{cfg.project_name}_report.pptx")


# ── HTML 빌더 ───────────────────────────────────────────────────────────────
def build_html(payload: dict[str, Any], cfg: Config, out_path: Path) -> None:
    """
    templates/dashboard.html 을 읽어
    데이터(JSON)와 config(JSON)를 인라인으로 삽입한 뒤 저장합니다.
    """
    # 템플릿 경로: builder.py 기준 ../templates/dashboard.html
    template_path = Path(__file__).parent.parent / "templates" / "dashboard.html"
    if not template_path.exists():
        raise FileNotFoundError(
            f"[빌더 오류] 템플릿을 찾을 수 없습니다: {template_path}\n"
            "  → templates/dashboard.html 이 있는지 확인하세요."
        )

    template = template_path.read_text(encoding="utf-8")

    # config를 JavaScript가 읽을 수 있는 형태로 직렬화
    ui_config = _build_ui_config(cfg)

    data_json   = json.dumps(payload,   ensure_ascii=False)
    config_json = json.dumps(ui_config, ensure_ascii=False)

    html = (
        template
        .replace("__DATA_PLACEHOLDER__",   data_json)
        .replace("__CONFIG_PLACEHOLDER__", config_json)
    )

    out_path.write_text(html, encoding="utf-8")


def _build_ui_config(cfg: Config) -> dict[str, Any]:
    """Config 객체에서 JavaScript UI에 필요한 설정만 추출합니다."""
    return {
        "title":        cfg.title,
        "subtitle":     cfg.subtitle,
        "theme":        cfg.theme,
        "value_label":  cfg.value_transform.label,
        "entity_label": cfg.entity_col,
        "time_label":   cfg.time_col,
        "badges":       cfg.badges,
        "filter_dims": [
            {"col": d.col, "label": d.label}
            for d in cfg.filter_dims
        ],
        "group_dims": [
            {"col": d.col, "label": d.label}
            for d in cfg.group_dims
        ],
        "kpi": [
            {
                "label":       k.label,
                "type":        k.type,
                "unit":        k.unit,
                "from_period": k.from_period,
                "to_period":   k.to_period,
            }
            for k in cfg.kpi
        ],
    }
