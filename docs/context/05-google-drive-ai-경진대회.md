# Google Drive: ai 경진대회

- 출처: https://drive.google.com/drive/folders/1dJKhAEPqvy8RqUFi8fkHnaGBJWe5vkkV (Notion 루트 페이지에서 링크)
- 가져온 날: 2026-11-17 (읽기만 함, Drive 수정 없음)
- 로컬 사본: `assets/drive/` (10MB 넘는 파일 4개는 받지 않음 — 아래 표의 "로컬" 열 참고)

## 폴더 구조와 파일 목록

```
ai 경진대회/
├── 서울시데이터/                        (트랙 B: 서울시 일자리포털 공고 기반)
│   ├── preprocessing_report.xlsx
│   ├── 직무별_역량_키워드.html
│   └── careerlens_db_outputs/
│       ├── README.md
│       ├── out/   (산출물 16개)
│       └── src/   (파이썬 코드 14개 + HTML 템플릿 1개)
├── 케글 데이터(개발자 관련)/            (트랙 A: 미국 Kaggle 공고)
│   ├── CareerLens_USA_선택형_검색대시보드.html
│   └── postings_usa_candidates_no_senior_6343.csv
└── 고용24 교육과정데이터/               (교육 추천: 국비 훈련과정)
    ├── work24_training_courses (원본데이터).csv
    ├── 교육과정 전처리 과정.docx
    ├── courses.json
    └── courses_viewer.html
```

### 서울시데이터

| 파일 | 크기 | 내용 | 로컬 |
| --- | --- | --- | --- |
| preprocessing_report.xlsx | 0.9MB | 품질 진단·검증·테스트·편향 비교 보고서 (시트 16개, 아래) | O |
| 직무별_역량_키워드.html | 0.5MB | 직무별 역량 키워드 조회 페이지 | O |
| careerlens_db_outputs/README.md | 3KB | DB 설명·실행법·추천 점수식 (아래 전문) | O |

`preprocessing_report.xlsx` 시트: 요약, 직무별키워드(요약), 직무별키워드(상세), 1_원본품질진단, 2_전처리전후, 3_직무표준화, 4_직무군분포, 5_키워드사전, 6_자격_법정근거, 7_자격요구유형, 8_우대조건, 9_테스트A-E, 10_추가검증입력, 11_편향검증, 12_품질체크, 13_한계와다음단계.
(`out/preprocessing_report.xlsx`와 바이트 단위로 동일한 파일이라 하나만 받음. 시트 내용은 열어 보지 않음.)

### 서울시데이터/careerlens_db_outputs/out

| 파일 | 행 수 / 크기 | 컬럼 | 로컬 |
| --- | --- | --- | --- |
| cleaned_job_postings.csv | 56MB (README: 40,479건) | — | X (용량) |
| careerlens.db | 96MB, SQLite 15개 테이블 | — | X (용량) |
| occupations.csv | 810 | occupation_id, occupation_name, original_occupation_names, occupation_code, all_codes, occupation_description, category, major_code, minor_code, job_family_id, job_family_name, posting_count, open_posting_count, market_size_log, has_legal_license, n_original_names | O |
| keywords.csv | 178 | keyword_id, keyword, category_code, keyword_category, synonyms, match_patterns, is_common_competency, n_occupations, n_occupations_core, idf, idf_norm, discriminative_weight | O |
| occupation_keywords.csv | 13,922 | occupation_id, keyword_id, keyword, importance, relevance_score, source_type, confidence, evidence_count, posting_share, basis | O |
| occupation_keyword_profile.csv | 11,509 | occupation_id, keyword_id, keyword, importance, combined_score, sources, evidence_count | O |
| licenses.csv | 532 | license_id, license_name, display_name, license_category, parent_license_id, posting_count, legal_basis_refs, is_qualification, sample_raw_text | O |
| occupation_licenses.csv | 2,086 | occupation_id, license_id, license_name, requirement_type, evidence_count, required_count, preferred_count, mention_count, n_postings, required_share, evidence_share, confidence, source_type, legal_id, legal_basis, legal_condition, verification_status, legal_source, legal_note, alternative_group | O |
| occupation_preferences.csv | 3,204 | preference_id, occupation_id, preference_name, preference_category, is_policy_target, evidence_count, sources, n_postings, posting_share, source_type, confidence, requirement_type, use_in_matching | O |
| experience_keyword_mapping.csv | 1,231 | mapping_id, rule_id, expression_pattern, example_expression, experience_activity, action, keyword_id, keyword, keyword_category, match_type, weight, source_type, note | O |
| keyword_relations.csv | 69 | keyword_id_a, keyword_a, keyword_id_b, keyword_b, relation_type, weight | O |
| database_schema.sql | 7KB | DB 스키마 | O |
| ERD.md | 3KB | mermaid ERD + 추천 흐름 | O |
| test_results.json | 85KB | 최상위 키: tests, probes, bias, checks | O |
| preprocessing_report.xlsx | 0.9MB | 상위 폴더 파일과 동일 | (중복) |

### 서울시데이터/careerlens_db_outputs/src (모두 로컬에 있음)

`run_all.py`, `common.py`, `s01_quality.py`, `s02a_occupations.py`, `s02b_clean.py`, `knowledge.py`(75KB, 키워드 사전·직무군 프로필·경험 규칙), `licenses_kb.py`, `s03_build.py`, `recommender.py`(추천 엔진), `recommend_cli.py`, `s04_evaluate.py`, `s05_database.py`, `s06_report.py`, `s07_keyword_page.py`, `keyword_page_template.html`

### 케글 데이터(개발자 관련)

| 파일 | 크기 | 내용 | 로컬 |
| --- | --- | --- | --- |
| postings_usa_candidates_no_senior_6343.csv | 12.7MB | 미국 Kaggle 공고 중 시니어 제외 후보 6,343건 (파일명 기준) | X (용량) |
| CareerLens_USA_선택형_검색대시보드.html | 18.4MB | 위 공고 검색 대시보드 | X (용량) |

### 고용24 교육과정데이터

| 파일 | 크기 | 내용 | 로컬 |
| --- | --- | --- | --- |
| work24_training_courses (원본데이터).csv | 4.3MB, 6,122행 | 고용24 API 원본 (30개 컬럼) | O |
| 교육과정 전처리 과정.docx | 0.2MB | 전처리 설명 문서 → [06-교육과정-전처리-과정.md](06-교육과정-전처리-과정.md)에 전문 전사 | O |
| courses.json | 3.3MB | 개발용 산출물 (kw 178 / crs 3,173 / occ 810 / occCrs 489 / ncs 211 / rules 63) | O |
| courses_viewer.html | 3.3MB | 검수용 뷰어 | O |

## 공통 역량 키워드 사전 (178개, 8개 분류)

`out/keywords.csv`에서 추출. Notion 투트랙 비교표의 "역량 사전 178개 키워드"와 같은 사전.

| 코드 | 분류 | 개수 | 키워드 |
| --- | --- | --- | --- |
| C1 | 전문지식 | 35 | 사회복지 지식 · 노인 돌봄 지식 · 장애인 지원 지식 · 아동 발달 지식 · 심리학 지식 · 간호·의료 지식 · 재활치료 지식 · 영양·식품위생 지식 · 조리 지식 · 회계·세무 지식 · 인사·노무 지식 · 무역 실무 지식 · 물류 지식 · 마케팅 지식 · 통계 지식 · 프로그래밍 지식 · 데이터베이스 지식 · 네트워크·보안 지식 · 건축·토목 지식 · 기계 지식 · 전기·전자 지식 · 화학·소재 지식 · 환경·안전 법규 지식 · 법률 지식 · 금융·보험 지식 · 제품·상품 지식 · 교육학·교수법 · 디자인 이론 · 의약품 지식 · 차량 정비 지식 · 농축산 지식 · 부동산 지식 · 공공행정 지식 · 문화·예술 지식 · 스포츠·운동 지식 |
| C2 | 기술 및 도구 활용 능력 | 33 | 문서작성(워드) · 스프레드시트(엑셀) · 프레젠테이션(PPT) · 회계 프로그램 · ERP 활용 · Python · SQL · R · 데이터 시각화 도구 · 웹·Java 개발 기술 · C·임베디드 기술 · 클라우드 · 서버·OS 운영 · CAD · 디자인 툴 · 영상 편집 툴 · SNS·마케팅 툴 · 쇼핑몰·오픈마켓 운영 툴 · POS 활용 · CNC·MCT 조작 · 용접 기술 · 지게차 운전 · 중장비 운전 · 측정·검사 장비 · PLC·자동제어 · 공구 활용 · 사회복지 전산시스템 · 의료 전산(EMR) · 조리 기구 활용 · 청소 장비 활용 · 외국어(영어) · 외국어(기타) · 차량 운전 |
| C3 | 업무 수행 능력 | 67 | 신체활동 지원 · 가사·생활 지원 · 돌봄 서비스 · 아동 보육·지도 · 교육·강의 · 상담 · 사례관리 · 프로그램 기획·운영 · 고객 응대 · 주문·결제 처리 · 판매 · 영업 · 상품 진열·매장 관리 · 재고 관리 · 물품 분류·포장 · 배송·배달 · 상하차·운반 · 조리 · 급식·배식 · 음료 제조 · 위생 관리 · 청소·미화 · 시설 관리·보수 · 경비·보안 · 사무 행정 · 데이터 입력 · 회계·경리 처리 · 인사·채용 업무 · 총무 업무 · 구매·자재 관리 · 생산 관리 · 품질 관리·검사 · 기계 조작 · 조립 · 가공 · 설치·정비 · 전기 작업 · 건설 시공 · 현장 관리 · 설계·도면 작성 · 서비스·화면 기획 · 연구개발 · 시험·분석 · 소프트웨어 개발 · 시스템 운영·IT 지원 · 데이터 수집 · 데이터 전처리 · 데이터 분석 · 콘텐츠 기획 · 콘텐츠 제작 · SNS 운영 · 홍보 · 광고 기획·운영 · 시장 조사 · 상품 기획 · 디자인 작업 · 행사 진행 · 통역·번역 · 문서 검토·법무 · 운전·운행 · 안전 관리 · 환자 간호 · 진료 보조 · 재활 치료 · 사육·재배 · 미용 시술 · 봉제·재단 |
| C4 | 소프트 스킬 | 10 | 책임감 · 꼼꼼함 · 공감 능력 · 시간 관리 · 팀워크 · 적응력 · 창의성 · 리더십 · 서비스 마인드 · 학습 능력 |
| C5 | 신체적 역량 | 5 | 체력 · 중량물 취급 · 손 기능·정교함 · 교대·야간 근무 적응 · 장시간 운전 |
| C6 | 의사소통 및 대인관계 | 8 | 의사소통 · 보호자·가족 소통 · 협상·설득 · 고객 관계 관리 · 민원 응대 · 전화 응대 · 발표 · 문서 커뮤니케이션 |
| C7 | 관리 및 운영 능력 | 10 | 매장 운영 관리 · 인력 관리 · 일정·프로젝트 관리 · 예산·비용 관리 · 문서·기록 관리 · 시설 운영 관리 · 배송 경로 관리 · 물품·자산 관리 · 공정·생산 운영 · 조직 운영 |
| C8 | 분석 및 문제해결 능력 | 10 | 문제해결 · 논리적 사고 · 성과 측정·분석 · 통계 분석 · 시각화 · 업무 개선 · 기획·전략 수립 · 데이터 해석·보고 · 정밀 판단·검수 · 위기 대응 |

## DB 구조 (out/ERD.md 요약)

전체 mermaid ERD는 `assets/drive/서울시데이터/careerlens_db_outputs/out/ERD.md` 참고.

- `occupations` 1—N `occupation_name_map`(원본 직종명 889개 → 표준 직무), `occupation_keywords`(출처별 역량), `occupation_keyword_profile`(출처 통합 역량), `occupation_licenses`(필수/우대 자격), `occupation_preferences`(우대조건), `job_postings`(대표 직무), `posting_occupations`(복수 직무 확장용)
- `keywords` 1—N `occupation_keywords`, `occupation_keyword_profile`, `keyword_relations`(전이 관계), `experience_keyword_mapping`(경험 표현), `posting_keywords`
- `licenses` 1—N `occupation_licenses`, `posting_licenses`; `licenses` 자기참조(상위 자격·급수)
- `job_postings` 1—N `posting_keywords`, `posting_licenses`, `posting_preferences`, `posting_occupations`
- 주요 값: `occupation_keywords.importance` = required/major/supplementary, `source_type` = job_posting/occupational_knowledge/inferred; `occupation_licenses.requirement_type` = 필수(법정)/필수(법정·조건부)/필수(채용관행)/일부 공고 필수/우대/일반 관련; `experience_keyword_mapping.match_type` = synonym/direct/derived/transferable; `occupations.posting_count`는 시장 규모(추천 점수에 미사용)

추천 흐름: 사용자 경험 → `experience_keyword_mapping`으로 역량 추출 → `occupation_keyword_profile`·`keyword_relations`로 직무 점수 → `occupation_licenses`로 자격 요건 확인 → `job_postings`에서 열린 공고 연결.

## careerlens_db_outputs/README.md 전문

# CareerLens 직무-역량 통합 DB (서울시 일자리포털 채용정보 기반)

### 실행

```bash
pip install pandas scikit-learn openpyxl kiwipiepy
# raw/seoul_jobs_raw.csv 에 원본 CSV(cp949)를 둔다 (원본은 덮어쓰지 않음)
python src/run_all.py                      # 전 단계 재생성(약 75초, API 호출 없음)
python src/recommend_cli.py "택배 물품을 분류하고 배송 업무를 수행했습니다."
```

### 파일

| 파일 | 내용 |
|---|---|
| out/cleaned_job_postings.csv | 정제 공고 40,479건(삭제 0건). posting_id·raw_row_number·row_hash로 원본 추적 |
| out/occupations.csv | 표준 직무 810개(원본 889개), 직무군 133개 |
| out/keywords.csv | 역량 키워드 178개(8개 분류, 동의어, IDF 변별력) |
| out/occupation_keywords.csv | 직무-키워드 다대다(출처별: job_posting / occupational_knowledge / inferred) |
| out/occupation_keyword_profile.csv | 출처를 합친 직무별 역량 프로필(추천에 사용) |
| out/licenses.csv | 자격면허 사전 532개(표기 통합, 상위 자격) |
| out/occupation_licenses.csv | 직무-자격(필수(법정)/필수(법정·조건부)/필수(채용관행)/일부 공고 필수/우대/일반 관련 + 법령 근거) |
| out/occupation_preferences.csv | 직무-우대조건(정책대상 우대는 매칭 제외) |
| out/experience_keyword_mapping.csv | 경험 표현 → 표준 역량(synonym/direct/derived/transferable) |
| out/keyword_relations.csv | 전이 가능 역량 관계 |
| out/careerlens.db | SQLite DB(15개 테이블, FK 위반 0) |
| out/database_schema.sql, out/ERD.md | DB 구조 |
| out/preprocessing_report.xlsx | 품질 진단·검증·테스트·편향 비교 보고서 |
| out/test_results.json | 테스트 A~E 및 추가 20개 입력 전체 결과 |

### 코드 구성

- `s01_quality.py` 인코딩·결측·중복·이상치 진단, posting_id 부여
- `s02a_occupations.py` 모집직종 표준화(괄호 변형·동일명 통합 + 수동 규칙)
- `s02b_clean.py` 직무내용 분해(업무/필수/우대/경력학력/근무조건/절차), 자격·우대 분리
- `knowledge.py` 키워드 사전·직무군 프로필·경험 규칙 / `licenses_kb.py` 자격 정규화·법령 근거
- `s03_build.py` 매핑 테이블 생성 / `recommender.py` 추천 엔진 / `s04_evaluate.py` 검증
- `s05_database.py` SQLite / `s06_report.py` 보고서

### 추천 점수

`100 × (0.30 키워드 일치 + 0.25 의미 유사 + 0.20 업무 행동 연관 + 0.15 성과·경험 수준 + 0.10 자격·우대)`
× 경력직 보정(관리직·경력 위주 공고 0.85~0.92) × 근거 신뢰도(공고 30건 미만 직무만 최대 −10%).
공고 수(시장 규모)는 점수에 넣지 않고 별도 표시. 직무군당 최대 2개 + MMR 다양성, 1위의 72% 미만은 추천하지 않음.
의미 유사도는 글자 n-gram TF-IDF(임베딩으로 교체 가능: `CareerMatcher._build_semantic`).
