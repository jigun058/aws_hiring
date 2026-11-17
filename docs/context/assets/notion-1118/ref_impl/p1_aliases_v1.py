import sys
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from aliases import A as A0, NEW
A = {k: list(v) for k, v in A0.items()}

# --- v1 changes (reasons in P1 rulebook) ---
A[24] = ["banking", "fintech", "credit risk", "underwriting", "insurance (?:products?|claims?|underwriting|sales|agents?)", "financial (?:analysis|services industry|modeling|products?|advis(?:or|ory)|planning)", "wealth management", "securities", "lending"]
A[17] = ["cybersecurity", "information security", "network security", "application security", "security engineer(?:s|ing)?", "security researchers?", "penetration testing", "vulnerabilit(?:y|ies)", "encryption", "firewalls?", "networking", "tcp/ip", "reverse engineering", "fuzzing"]
A[44] = ["java", "javascript", "typescript", "react(?:\\.js)?", "angular", "vue(?:\\.js)?", "node(?:\\.?js)", "html5?", "css3?", "spring boot", "spring", "next\\.js", "ruby on rails", "rails", "php", "rest(?:ful)? apis?", "graphql", "golang", "go language", "c#", "\\.net", "scala", "ruby", "spa frameworks?", "storybook"]
A[111] = ["software development", "software engineer(?:s|ing)?", "software developers?", "web development", "front[- ]?end (?:engineer|developer|development)s?", "back[- ]?end (?:engineer|developer|development)s?", "full[- ]?stack (?:engineer|developer|development)s?", "build (?:and maintain )?(?:scalable )?(?:applications|services|systems)", "distributed systems"]
A[113] = ["data collection", "web scraping", "scrapy", "crawl(?:ing|er)", "data ingestion", "surveys?"]
A[114] = ["data cleaning", "data preparation", "data wrangling", "feature engineering", "data cleansing"]
A[99] = ["quality assurance", "quality control", "quality inspection", "qa"]  # qa: context rule CTX-QA
A[103] = ["install(?:s|ing|ation of|ation and)", "repairs?", "repairing", "maintains? and repairs?", "maintain(?:s|ing)? (?:equipment|machinery|machines|vehicles)", "perform(?:s|ing)? maintenance", "maintenance (?:of|and repair|technicians?)", "hvac"]  # CTX-COMPANY
A[90] = ["facilit(?:y|ies) maintenance", "building maintenance", "property maintenance", "hvac"]
A[161] = ["budget(?:s|ing)?", "cost management", "forecasting"]  # exclude benefit phrases CTX-BENEFIT
A[175] = ["reporting (?:dashboards?|tools)", "write reports?", "analytical reports?", "present findings", "data-driven insights", "communicate insights"]
A[109] = ["research and development", "r&d (?:engineer|experience)", "research experience", "conduct research", "research engineer", "publications"]
A[72] = ["teaching", "tutoring", "instructors?", "teaching assistant"]
A[36] = ["excel", "spreadsheets?", "google sheets"]
A[43] = ["tableau", "power ?bi", "looker", "matplotlib", "seaborn", "d3\\.js", "plotly"]
A[144] = ["eager to learn", "quick learner", "curiosity", "curious", "learn quickly", "growth mindset", "teach yourself", "self-taught", "self-starter"]
A[15] = ["computer science fundamentals", "programming skills", "programming fundamentals", "programming chops", "algorithms", "data structures", "object[- ]oriented", "coding skills", "git"]
A[41] = ["sql", "postgres(?:ql)?", "mysql", "mariadb", "t-sql", "pl/sql", "sql server", "oracle database"]
A[16] = ["databases?", "data modeling", "mongodb", "nosql", "redis", "dynamodb", "elasticsearch", "snowflake", "bigquery", "database design"]
A[47] = ["linux", "unix", "docker", "kubernetes", "k8s", "helm", "devops", "terraform", "ci/cd", "jenkins", "ansible", "site reliability", "sre", "infrastructure as code", "bash", "shell scripting", "cdn"]
A[146] = ["heavy objects", "lift (?:up to )?\\d+ ?(?:lbs|pounds)", "heavy lifting"]
A[148] = ["overnight", "night shifts?", "rotating shifts?"]
A[91] = ["security officers?", "security guards?", "patrol"]
A[160] = ["project management", "project managers?", "agile", "scrum", "jira", "kanban"]
A[13] = ["marketing", "branding", "go-to-market", "gtm", "seo", "sem", "growth marketing", "digital marketing"]
A[174] = ["strategy", "strategic planning", "business strategy"]
A[67] = ["driver'?s license", "valid driver", "drive (?:company |maintenance )?(?:vehicles?|trucks?)"]
A[25] = ["product knowledge", "knowledge of [a-z]+ products"]
for k in (178, 179, 180, 181):
    pass
A[178] = ["machine learning", "deep learning", "llms?", "large language models?", "nlp", "natural language processing", "computer vision", "pytorch", "tensorflow", "scikit-learn", "generative ai", "neural networks?", "ml (?:engineers?|models?|experience|ops|background)", "mlops", "hugging ?face", "fine-tun(?:e|ing)", "retrieval-augmented", "ai (?:engineers?|models?|products?|agents?)", "ai-powered tools", "nerf"]
A[179] = ["ios", "android", "swift(?:ui)?", "react native", "flutter", "mobile (?:apps?|development|engineers?|developers?)", "xcode", "kotlin"]  # kotlin: CTX-KOTLIN
A[180] = ["data engineer(?:s|ing)?", "data pipelines?", "etl", "elt", "airflow", "dbt", "spark", "kafka", "databricks", "data warehous(?:e|ing)", "streaming pipelines?", "high-throughput data pipelines?"]
A[181] = ["test automation", "automated testing", "unit tests?", "unit testing", "integration tests?", "end-to-end tests?", "e2e tests?", "selenium", "cypress", "playwright", "qa engineers?", "software testing", "test cases", "tdd", "testing with"]

# Korean aliases ADDED in v1 (on top of careerlens.db synonyms)
KO_ADD = {
 178: "머신러닝|딥러닝|인공지능 모델|AI 모델 개발|LLM|거대언어모델|자연어 처리|컴퓨터 비전|텐서플로|파이토치|AI 에이전트 개발",
 179: "모바일 앱 개발|앱 개발|안드로이드|iOS|스위프트|코틀린|플러터|리액트 네이티브",
 180: "데이터 엔지니어|데이터 엔지니어링|데이터 파이프라인|ETL|데이터 웨어하우스|스파크|에어플로|카프카",
 181: "소프트웨어 테스트|테스트 자동화|단위 테스트|통합 테스트|QA 엔지니어|테스트 케이스|테스트 코드",
 47: "도커|쿠버네티스|CI/CD|데브옵스",
 41: "MariaDB|SQL Server",
 44: "타입스크립트|TypeScript|Angular|Next.js|GraphQL|C#|닷넷",
 15: "깃|Git|컴퓨터공학 기초",
 60: "전동조립|전동 드라이버|임팩트",
 67: "화물차|트럭|승합차|운송 경력",
 79: "병원 영업|의원 영업|영업 및 관리|영업 담당",
 25: "제품 정보 전달|자사제품|제품 설명",
 1: "장기요양|노인장기요양|요양보험",
 2: "장애인에 대한 이해|장애인 이해",
 22: "소방안전관리자|안전관리자 선임",
 128: "소방안전관리자",
 8: "조리사 면허|조리사 자격",
 85: "조리사 면허|조리사 자격",
}

# context rules: alias -> condition (applies to EN and KO)
CTX = {
 "CTX-SHORT": "한 글자·두 글자 기술명(R, C, Go, AI, ML, QA, PR, MD, PM, CS, TM, MC, PT, NC)은 단독 일치로 인정하지 않는다. 각 키워드의 문맥 패턴(다른 기술명과 나열, '언어/프로그래밍/를/로' 등 조사, 직무 명사 결합)을 만족할 때만 인정",
 "CTX-QA": "'QA'는 같은 문장에 software|code|test|자동화|앱|웹|버그 중 하나가 있으면 181, product|제품|불량|출하|수입검사|GMP가 있으면 99, 둘 다 없으면 unclassified(검토 목록)",
 "CTX-KOTLIN": "Kotlin은 android|mobile|앱 이 같은 문장/문단에 있으면 179, 그 외에는 44(서버 개발)",
 "CTX-BENEFIT": "benefits|we offer|perks|insurance(medical/dental/vision/life/disability)|401k|stipend|learning budget|equipment budget|복리후생|4대보험 가입 이 있는 문장은 역량 매핑에서 제외(복지 문장)",
 "CTX-COMPANY": "회사 소개 문장(About us, We are, our company/platform/customers, '~ builds/used by', 기업 소개)에 나온 기술·업무 표현은 매핑하지 않는다. 단, 'our stack is/we use' 문장은 P2에서 mention으로 기록만 한다",
 "CTX-NEGATION": "not required|not necessary|no ... required|won't|don't require|필수 아님|무관 이 붙은 표현은 역량 매핑은 하되 P2에서 요구 아님(mention)으로 넘긴다. 단 'won't spend ... writing reports'처럼 하지 않는 업무를 말하면 매핑하지 않는다",
 "CTX-SECURITY": "security 가 officer|guard|patrol|clearance|social security|national security 와 결합하면 17에 매핑하지 않는다(경비직이면 91, clearance는 비역량 자격)",
 "CTX-R": "R은 대문자 단독이고 Python|SQL|SAS|SPSS|statistic|RStudio 와 같은 문장에 있을 때만 42. E.R., HVAC/R, R&D, R&amp;D, Q&R 등은 제외",
 "CTX-GO": "go는 golang, 'Go'(대문자)+다른 프로그래밍 언어 나열, 'Go language/developer'일 때만 44. go-to-market, on the go, go live 는 제외(go-to-market은 13)",
 "CTX-LICENSE": "license|licensed|certification|certified|자격증|면허|기능사|기사 가 붙은 표현은 자격 요건으로 licenses에 기록한다. 역량은 courses.json rules(자격→키워드)에 있는 자격일 때만 implied로 연결하고, 그 외에는 연결하지 않는다(예: nursing license→자격만)",
 "CTX-MAJOR": "전공|학과|전공자|졸업자 가 바로 붙은 분야 표현(예: 기계설계 공학 전공자)은 역량으로 매핑하지 않고 학위·전공 요건으로 기록한다",
 "CTX-COURSERULE": "courses.json의 rules 63개 중 자격증 이름(3번째 값)이 있는 규칙만 공고·경험 문장에 적용한다. 자격증 이름이 없는 규칙(예: 청소|세척, CS|고객)은 교육과정명 전용이다",
 "CTX-HYGIENE": "'식품위생'·'위생교육 이수'는 7(지식)·자격 요건이고, '위생'이 단독 업무(위생 관리, 소독, 청결 유지)로 쓰일 때만 88",
 "CTX-JAEDAN": "'재단'은 의류·원단·패턴·봉제 문맥이면 134, 필름·판재·롤·슬리터·기계 문맥이면 102 가공",
}
