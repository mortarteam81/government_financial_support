"""
preprocessor.py
───────────────
config 설정을 기반으로 CSV 데이터를 집계하여
대시보드용 JSON 구조를 생성하는 범용 집계 엔진.

출력 JSON 구조 (정규화된 키 사용):
  entity_year   : 개체×연도별 값 합계
  entity_meta   : 개체별 메타 정보 (filter_dims)
  group_year    : 그룹차원×연도별 값 합계 (dict of list)
  entity_total  : 개체별 전체 기간 합산
  times         : 시계열 목록
  entities      : 개체 목록
  filter_values : 각 filter_dim의 고유값 목록

[바이브코딩 팁]
  새로운 집계 뷰가 필요하면 이 파일 하단의 "확장 포인트" 섹션에
  함수를 추가하고 build_payload()에서 호출하세요.
"""

from __future__ import annotations
from typing import Any
import pandas as pd
from .config_loader import Config, DimConfig


# ── 메인 진입점 ─────────────────────────────────────────────────────────────
def build_payload(df: pd.DataFrame, cfg: Config) -> dict[str, Any]:
    """
    집계를 수행하고 대시보드에 전달할 payload dict를 반환합니다.

    Parameters
    ----------
    df  : explorer.explore()가 반환한 원본 데이터프레임
    cfg : load_config()가 반환한 Config 객체
    """
    print("  🔄 데이터 전처리 시작...")

    # ── 1. 기본 정제 ──────────────────────────────────────────
    required_cols = [cfg.entity_col, cfg.time_col, cfg.value_col]
    df = df.dropna(subset=required_cols).copy()
    df[cfg.time_col]  = df[cfg.time_col].astype(int)
    df["_value"]      = pd.to_numeric(df[cfg.value_col], errors="coerce").fillna(0)
    df["_value"]     *= cfg.value_transform.multiply

    # ── 2. 그룹 차원 정규화 ───────────────────────────────────
    for dim in cfg.group_dims:
        if dim.col in df.columns and dim.normalize:
            df[dim.col] = df[dim.col].replace(dim.normalize)

    # ── 3. 핵심 집계 ──────────────────────────────────────────
    entity_year = _agg_entity_year(df, cfg)
    entity_meta = _agg_entity_meta(df, cfg)
    entity_total = _agg_entity_total(entity_year, cfg)
    group_year   = _agg_group_year(df, cfg)

    # ── 4. 고유값 목록 ────────────────────────────────────────
    times    = sorted(df[cfg.time_col].unique().tolist())
    entities = sorted(df[cfg.entity_col].unique().tolist())

    filter_values: dict[str, list] = {}
    for dim in cfg.filter_dims:
        if dim.col in df.columns:
            filter_values[dim.col] = sorted(df[dim.col].dropna().unique().tolist())

    # ── 5. 프리셋 데이터 빌드 ────────────────────────────────
    presets_data = _build_presets(cfg, entity_meta)

    # ── 6. payload 조립 ───────────────────────────────────────
    payload: dict[str, Any] = {
        # 데이터
        "entity_year":   entity_year,
        "entity_meta":   entity_meta,
        "entity_total":  entity_total,
        "group_year":    group_year,
        # 목록
        "times":         times,
        "entities":      entities,
        "filter_values": filter_values,
        # 프리셋
        "presets_data":  presets_data,
    }

    print(f"  ✅ 전처리 완료 | 개체: {len(entities)}개 | 기간: {min(times)}~{max(times)}")
    return payload


# ── 집계 함수들 ─────────────────────────────────────────────────────────────

def _agg_entity_year(df: pd.DataFrame, cfg: Config) -> list[dict]:
    """개체 × 연도 × 필터차원별 값 집계"""
    group_cols = [cfg.entity_col, cfg.time_col] + [
        d.col for d in cfg.filter_dims if d.col in df.columns
    ]
    agg = (
        df.groupby(group_cols)["_value"]
        .sum()
        .reset_index()
        .round(2)
    )
    # 정규화된 키로 rename
    agg = agg.rename(columns={
        cfg.entity_col: "entity",
        cfg.time_col:   "time",
        "_value":       "value",
    })
    # filter_dims 컬럼도 dim.col 이름 그대로 유지 (JS에서 사용)
    return agg.to_dict("records")


def _agg_entity_meta(df: pd.DataFrame, cfg: Config) -> list[dict]:
    """개체별 메타 정보 (설립·소재지·학제 등)"""
    agg_spec = {d.col: (d.col, "first") for d in cfg.filter_dims if d.col in df.columns}
    if not agg_spec:
        meta = df[[cfg.entity_col]].drop_duplicates()
        meta = meta.rename(columns={cfg.entity_col: "entity"})
        return meta.to_dict("records")

    meta = (
        df.groupby(cfg.entity_col)
        .agg(**agg_spec)
        .reset_index()
        .rename(columns={cfg.entity_col: "entity"})
    )
    return meta.to_dict("records")


def _agg_entity_total(entity_year: list[dict], cfg: Config) -> list[dict]:
    """개체별 전체 기간 합산 (내림차순 정렬)"""
    totals: dict[str, float] = {}
    for r in entity_year:
        totals[r["entity"]] = round(totals.get(r["entity"], 0.0) + r["value"], 2)
    return sorted(
        [{"entity": k, "value": v} for k, v in totals.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def _agg_group_year(df: pd.DataFrame, cfg: Config) -> dict[str, list[dict]]:
    """그룹 차원별 × 연도 집계 (부처별, 사업유형별 등)"""
    result: dict[str, list[dict]] = {}
    for dim in cfg.group_dims:
        if dim.col not in df.columns:
            continue
        agg = (
            df.groupby([dim.col, cfg.time_col])["_value"]
            .sum()
            .reset_index()
            .round(2)
            .rename(columns={dim.col: "group", cfg.time_col: "time", "_value": "value"})
        )
        result[dim.col] = agg.to_dict("records")
    return result


def _build_presets(cfg: Config, entity_meta: list[dict]) -> list[dict]:
    """config의 presets를 JavaScript에서 사용할 형태로 변환"""
    result = []
    for pr in cfg.presets:
        item: dict[str, Any] = {"label": pr.label, "type": pr.type}

        if pr.type == "entity_list":
            item["entities"] = pr.entities

        elif pr.type == "filter_match":
            # entity_meta에서 조건에 맞는 개체 목록 미리 계산
            matched = []
            for m in entity_meta:
                ok = all(m.get(col) == val for col, val in pr.match.items())
                if ok and pr.exclude_match:
                    for col, vals in pr.exclude_match.items():
                        if m.get(col) in vals:
                            ok = False
                            break
                if ok:
                    matched.append(m["entity"])
            item["entities"] = matched

        elif pr.type == "top_n":
            item["n"] = pr.n   # JS가 entity_total에서 상위 N개 선택

        result.append(item)
    return result


# ═══════════════════════════════════════════════════════════════════
#  확장 포인트
#  새로운 집계 뷰가 필요할 때 아래에 함수를 추가하고
#  build_payload() 의 payload dict에 키를 추가하세요.
#
#  예시:
#    def _agg_entity_growth(entity_year, cfg):
#        """개체별 전년대비 성장률"""
#        ...
#
#    # build_payload() 내부에 추가:
#    payload["entity_growth"] = _agg_entity_growth(entity_year, cfg)
# ═══════════════════════════════════════════════════════════════════
