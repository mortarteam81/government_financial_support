# 공공데이터 연계 IR 성과관리 시각화 시스템

> 대학혁신지원사업 IR 성과관리 시스템 구축 과제 일환으로 개발된  
> **CSV → 인터랙티브 HTML 대시보드** 범용 하네스(Harness)

---

## 개요

| 항목 | 내용 |
|---|---|
| 소관 부서 | 성신여자대학교 기획처 기획평가팀 |
| 데이터 출처 | 사학재정알리미 — 중앙정부 대학 예산지원 현황 (2015~2024년) |
| 적용 데이터 | 490개 대학 · 45개 부처 · 139,705건 |
| 기술 스택 | Python 3.x · pandas · PyYAML · Plotly.js |

---

## 파일 구조

```
.
├── run.py                        # 진입점 (여기만 실행)
├── config.yaml                   # 현재 프로젝트 설정
├── requirements.txt
│
├── harness/                      # 핵심 로직 모듈
│   ├── config_loader.py          # YAML → Config 객체 변환·검증
│   ├── explorer.py               # CSV 구조 탐색 리포트
│   ├── preprocessor.py           # config 기반 범용 집계 엔진
│   └── builder.py                # payload + 템플릿 → HTML 생성
│
├── templates/
│   └── dashboard.html            # 범용 대시보드 HTML 템플릿
│
├── configs/
│   └── 사학재정알리미_정부예산.yaml   # 프로젝트별 설정
│
├── output/
│   └── 중앙정부_대학예산지원_dashboard.html  # 생성된 대시보드
│
└── docs/
    ├── IR시각화시스템_구축계획안.docx
    └── IR시각화시스템_구축결과보고안.docx
```

---

## 빠른 시작

```bash
pip install pandas pyyaml

# CSV 구조 탐색
python run.py --explore-only

# 대시보드 생성
python run.py

# 다른 설정 파일 사용
python run.py -c configs/사학재정알리미_정부예산.yaml
```

---

## 대시보드 주요 기능

| 탭 | 기능 |
|---|---|
| 📈 시계열 추이 | 대학별 라인차트 · 합산 바차트 + 증감률 · 평균 추이 |
| 🏆 기간별 순위 | 수평 바차트 (상위 33% 🔴 / 중위 🟡 / 하위 🟢 색상 구분) |
| 🏢 그룹별 현황 | 부처별 · 사업유형별 추이 · 파이차트 · 히트맵 |
| 📊 데이터 테이블 | 대학 × 연도 크로스탭 · 헤더 클릭 정렬 |

### 필터 기능
- 연도 범위 슬라이더 (2015~2024)
- 학제 · 설립유형 · 소재지 칩 필터
- 대학명 텍스트 검색 + 멀티셀렉트
- 원클릭 프리셋 (서울사립대 / 서울여대6개 / 지방거점국립 / TOP10)

---

## 새 데이터셋 적용 방법

`config.yaml`의 컬럼 매핑만 수정하면 다른 CSV에 즉시 적용:

```yaml
columns:
  entity: "기관명"      # 분석 대상 개체 컬럼
  time:   "연도"        # 시계열 컬럼
  value:  "금액(천원)"  # 측정값 컬럼
```

---

## 관련 문서

- `docs/IR시각화시스템_구축계획안.docx` — 시스템 구축 계획(안) 공문
- `docs/IR시각화시스템_구축결과보고안.docx` — 시스템 구축 결과보고(안) 공문

---

## 데이터 준비

### 테스트 (즉시 실행 가능)
```bash
# 레포에 포함된 샘플 데이터로 동작 확인
python run.py -c configs/sample_test.yaml
```
→ `output/샘플_테스트_dashboard.html` 생성 확인

### 실제 데이터 사용
사학재정알리미에서 원본 CSV 다운로드 후 `data.csv`로 저장:

1. **사학재정알리미** (https://www.esf.go.kr) 접속
2. 상단 메뉴 → **통계 · 공시** → **대학별 중앙정부예산지원현황**
3. 연도 범위 설정 (2015~2024) → **Excel 다운로드** → `data.csv`로 저장
4. 아래 명령 실행:

```bash
python run.py -c config.yaml
```
→ `output/중앙정부_대학예산지원_dashboard.html` 생성

> **참고**: 원본 CSV 파일(`data.csv`)은 `.gitignore`에 의해 레포에서 제외됩니다.
