# json형식

- 출처: https://app.notion.com/p/415746d99efb8027adebf6d9728bfa8b
- 경로: AI Bootcamp Innovation Challenger 2026 / 세부 로직 및 처리 방법(개발 외) / json형식
- Notion 최종 수정: 2026-11-16T14:48:14Z (가져온 날: 2026-11-17)
- 하위 페이지: [케글데이터 정돈](04-케글데이터-정돈.md)
- 첨부: `assets/experience_card_template.json`, `assets/job_posting_template.json`

### 1. 사용자 경험 카드 JSON (`experience_card_template.json`)

| 변수명 | 의미 |
| --- | --- |
| `card_id` | 경험 카드 고유번호 |
| `activity` | 활동명 |
| `activity_type` | 활동 유형 (프로젝트, 동아리, 아르바이트 등) |
| `period.start` | 활동 시작일 |
| `period.end` | 활동 종료일 |
| `objective` | 활동 목적 |
| `my_role` | 본인이 맡은 역할 |
| `actions` | 구체적으로 수행한 업무 |
| `tools_used` | 사용한 기술 및 프로그램 |
| `challenges` | 활동 중 겪은 문제와 어려움 |
| `outcomes` | 활동 결과 및 성과 |
| `skills` | 활동에서 확인된 역량 목록 |
| `skills.name` | 역량 이름 |
| `skills.category` | 역량 분류 |
| `skills.evidence` | 해당 역량을 보유했다는 근거 |
| `skills.evidence_source` | 역량 근거의 출처 |
| `source.type` | 경험 정보의 입력 방식 (파일, 인터뷰 등) |
| `source.file_name` | 업로드한 자료의 파일명 |
| `missing_information` | 추가 질문이나 확인이 필요한 정보 |

첨부 원문 (`assets/experience_card_template.json`):

```json
{
  "card_id": null,
  "activity": null,
  "activity_type": null,
  "period": {
    "start": null,
    "end": null
  },
  "objective": null,
  "my_role": null,
  "actions": [],
  "tools_used": [],
  "challenges": [],
  "outcomes": [],
  "skills": [
    {
      "name": null,
      "category": null,
      "evidence": null,
      "evidence_source": null
    }
  ],
  "source": {
    "type": null,
    "file_name": null
  },
  "missing_information": []
}
```

### 2. 채용공고 분석 JSON (`job_posting_template.json`)

| 변수명 | 의미 |
| --- | --- |
| `posting_id` | 채용공고 고유번호 |
| `company` | 기업명 |
| `title` | 채용공고 제목 |
| `industry` | 기업의 산업 분야 |
| `job_role` | 모집 직무 |
| `source.url` | 채용공고 원본 링크 |
| `source.posted_at` | 공고 등록일 |
| `source.deadline` | 지원 마감일 |
| `responsibilities` | 주요 담당 업무 |
| `required_skills` | 필수 기술 및 역량 목록 |
| `preferred_skills` | 우대 기술 및 역량 목록 |
| `name` | 추출된 기술의 표준 이름 |
| `original_expression` | 채용공고에 실제 기재된 기술 표현 |
| `evidence` | 기술·역량 추출의 원문 근거 |
| `other_requirements.career` | 요구 경력 조건 |
| `other_requirements.minimum_years` | 최소 요구 경력 연수 |
| `other_requirements.education` | 학력 조건 |
| `other_requirements.certifications` | 요구 자격증 |
| `other_requirements.other` | 기타 지원 자격 |
| `working_conditions.region` | 근무지역 |
| `working_conditions.employment_type` | 고용형태 (정규직, 계약직 등) |
| `working_conditions.salary` | 급여 조건 |
| `working_conditions.work_schedule` | 근무시간 및 일정 |
| `working_conditions.work_arrangement` | 근무방식 (재택, 출근, 하이브리드 등) |
| `working_conditions.benefits` | 복리후생 |
| `explicitly_not_required` | 필수가 아니라고 명시된 기술·조건 |
| `unmapped_requirements` | 표준 역량으로 분류되지 않은 조건 |
| `raw_text` | 채용공고 원문 |

첨부 원문 (`assets/job_posting_template.json`):

```json
{
  "posting_id": null,
  "company": null,
  "title": null,
  "industry": null,
  "job_role": null,
  "source": {
    "url": null,
    "posted_at": null,
    "deadline": null
  },
  "responsibilities": [],
  "required_skills": [
    {
      "name": null,
      "original_expression": null,
      "evidence": null
    }
  ],
  "preferred_skills": [
    {
      "name": null,
      "original_expression": null,
      "evidence": null
    }
  ],
  "other_requirements": {
    "career": null,
    "minimum_years": null,
    "education": null,
    "certifications": [],
    "other": []
  },
  "working_conditions": {
    "region": null,
    "employment_type": null,
    "salary": null,
    "work_schedule": null,
    "work_arrangement": null,
    "benefits": []
  },
  "explicitly_not_required": [],
  "unmapped_requirements": [],
  "raw_text": null
}
```
