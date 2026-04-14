"""
explorer.py
───────────
CSV를 처음 만났을 때 구조를 파악하는 탐색 모듈.
실행하면 콘솔에 리포트를 출력하고 선택적으로 텍스트 파일로 저장합니다.

[바이브코딩 팁]
  새 CSV를 받으면 먼저 이 모듈을 실행해서 컬럼명과 고유값을 확인한 뒤
  config.yaml의 columns 섹션을 채우세요.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
from .config_loader import Config


def explore(cfg: Config, save_report: bool = True) -> pd.DataFrame:
    """
    CSV를 로드하고 구조 리포트를 출력합니다.

    Returns
    -------
    pd.DataFrame : 원본 데이터프레임 (후속 파이프라인에서 재사용)
    """
    print("\n" + "═" * 60)
    print("  📋 데이터 탐색 리포트")
    print("═" * 60)

    # ── 1. 로드 ───────────────────────────────────────────────
    data_path = Path(cfg.data_file)
    if not data_path.exists():
        raise FileNotFoundError(
            f"[데이터 오류] 파일을 찾을 수 없습니다: {data_path}\n"
            f"  → config.yaml의 data.file 경로를 확인하세요."
        )

    df = pd.read_csv(
        data_path,
        encoding=cfg.data_encoding,
        low_memory=cfg.data_low_memory,
    )
    print(f"\n✅ 파일 로드 성공: {data_path.name}")
    print(f"   행 수: {len(df):,}  |  열 수: {len(df.columns)}")

    # ── 2. 컬럼 목록 ──────────────────────────────────────────
    print("\n【전체 컬럼】")
    for i, col in enumerate(df.columns, 1):
        dtype = str(df[col].dtype)
        n_unique = df[col].nunique()
        null_cnt = df[col].isna().sum()
        print(f"  {i:2d}. {col:<30} dtype={dtype:<10} unique={n_unique:,}  null={null_cnt:,}")

    # ── 3. 핵심 컬럼 검증 ──────────────────────────────────────
    print("\n【config 매핑 컬럼 검증】")
    key_cols = {
        "entity": cfg.entity_col,
        "time":   cfg.time_col,
        "value":  cfg.value_col,
    }
    all_ok = True
    for role, col in key_cols.items():
        ok = col in df.columns
        mark = "✅" if ok else "❌"
        print(f"  {mark} columns.{role} = '{col}'", "" if ok else "← 컬럼 없음!")
        if not ok:
            all_ok = False

    if not all_ok:
        print("\n  ⚠️  config.yaml의 columns 섹션을 수정한 뒤 다시 실행하세요.")

    # ── 4. 주요 컬럼 고유값 ────────────────────────────────────
    print(f"\n【{cfg.entity_col} 고유값 수】")
    print(f"  총 {df[cfg.entity_col].nunique():,}개")

    print(f"\n【{cfg.time_col} 범위】")
    times = sorted(df[cfg.time_col].dropna().unique().tolist())
    print(f"  {times}")

    for dim in cfg.filter_dims + cfg.group_dims:
        if dim.col in df.columns:
            vals = df[dim.col].dropna().unique().tolist()
            display = vals[:10]
            suffix = f" ... ({len(vals)}개)" if len(vals) > 10 else f" ({len(vals)}개)"
            print(f"\n【{dim.label} ({dim.col}) 고유값】")
            print(f"  {display}{suffix}")

    # ── 5. 값 컬럼 기초 통계 ──────────────────────────────────
    if cfg.value_col in df.columns:
        val_series = pd.to_numeric(df[cfg.value_col], errors="coerce")
        mul = cfg.value_transform.multiply
        lbl = cfg.value_transform.label or "(원본 단위)"
        print(f"\n【{cfg.value_col} 기초 통계】 (변환 후: ×{mul} = {lbl})")
        print(f"  합계 : {val_series.sum() * mul:,.1f} {lbl}")
        print(f"  평균 : {val_series.mean() * mul:,.1f} {lbl}")
        print(f"  최대 : {val_series.max() * mul:,.1f} {lbl}")
        print(f"  null : {val_series.isna().sum():,}개")

    print("\n" + "═" * 60 + "\n")

    # ── 6. 리포트 저장 (선택) ──────────────────────────────────
    if save_report:
        import sys, io
        # 이미 출력했으므로 파일 저장은 별도 수행
        report_path = Path(cfg.output.dir) / f"{cfg.project_name}_explore_report.txt"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        # 간단 요약만 저장
        lines = [
            f"프로젝트: {cfg.project_name}",
            f"파일: {cfg.data_file}",
            f"행 수: {len(df):,}",
            f"entity ({cfg.entity_col}) 고유값: {df[cfg.entity_col].nunique():,}",
            f"time ({cfg.time_col}) 범위: {times}",
            f"컬럼 목록: {df.columns.tolist()}",
        ]
        report_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  💾 탐색 리포트 저장: {report_path}")

    return df
