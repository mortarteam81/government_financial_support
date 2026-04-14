#!/usr/bin/env python3
"""
run.py — CSV Dashboard Harness 진입점
─────────────────────────────────────
사용법:
  python run.py                          # 기본 (config.yaml 사용)
  python run.py -c configs/사학재정.yaml  # 설정 파일 지정
  python run.py --explore-only           # 탐색 리포트만 출력 (HTML 미생성)
  python run.py --no-explore             # 탐색 생략 (빠른 재빌드)

[바이브코딩 팁]
  새 프로젝트 시작 시:
  1. python run.py --explore-only  로 컬럼 구조 확인
  2. config.yaml 의 columns 섹션 수정
  3. python run.py  로 대시보드 생성
"""

import argparse
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="CSV Dashboard Harness — config 기반 인터랙티브 대시보드 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="설정 파일 경로 (기본값: config.yaml)",
    )
    parser.add_argument(
        "--explore-only",
        action="store_true",
        help="데이터 탐색 리포트만 출력하고 종료",
    )
    parser.add_argument(
        "--no-explore",
        action="store_true",
        help="탐색 단계를 건너뛰고 바로 빌드 (재빌드 시 속도 향상)",
    )
    args = parser.parse_args()

    # ── 0. 의존성 확인 ──────────────────────────────────────────
    try:
        import pandas  # noqa
        import yaml    # noqa
    except ImportError as e:
        print(f"\n❌ 패키지 누락: {e}")
        print("   pip install pandas pyyaml  를 실행하세요.\n")
        sys.exit(1)

    # ── 1. config 로드 ──────────────────────────────────────────
    from harness.config_loader import load_config

    config_path = Path(args.config)
    print(f"\n{'═'*60}")
    print(f"  🚀 CSV Dashboard Harness")
    print(f"{'═'*60}")
    print(f"  설정 파일: {config_path}")

    try:
        cfg = load_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ {e}\n")
        sys.exit(1)

    print(f"  프로젝트 : {cfg.project_name}")
    print(f"  데이터   : {cfg.data_file}")
    print(f"  출력 디렉토리: {cfg.output.dir}\n")

    start = time.time()

    # ── 2. 탐색 ────────────────────────────────────────────────
    from harness.explorer import explore

    if not args.no_explore:
        try:
            df = explore(cfg, save_report=True)
        except FileNotFoundError as e:
            print(f"\n❌ {e}\n")
            sys.exit(1)
    else:
        import pandas as pd
        print("  ⏭️  탐색 단계 건너뜀 (--no-explore)")
        df = pd.read_csv(
            cfg.data_file,
            encoding=cfg.data_encoding,
            low_memory=cfg.data_low_memory,
        )

    if args.explore_only:
        print("  --explore-only 옵션: 탐색 완료 후 종료합니다.\n")
        sys.exit(0)

    # ── 3. 전처리 & 집계 ────────────────────────────────────────
    from harness.preprocessor import build_payload

    print("  🔄 집계 중...")
    try:
        payload = build_payload(df, cfg)
    except Exception as e:
        print(f"\n❌ 전처리 오류: {e}\n")
        raise

    # ── 4. 출력물 생성 ───────────────────────────────────────────
    from harness.builder import build_all

    print("  🏗️  출력물 생성 중...")
    try:
        build_all(payload, cfg)
    except Exception as e:
        print(f"\n❌ 빌드 오류: {e}\n")
        raise

    elapsed = time.time() - start
    print(f"\n{'═'*60}")
    print(f"  ✅ 완료! ({elapsed:.1f}초)")
    print(f"  출력 디렉토리: {Path(cfg.output.dir).resolve()}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
