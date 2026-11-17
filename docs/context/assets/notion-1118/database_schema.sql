PRAGMA foreign_keys = ON;

CREATE TABLE occupations (
    occupation_id TEXT PRIMARY KEY,
    occupation_name TEXT NOT NULL,
    original_occupation_names TEXT,
    occupation_code TEXT NOT NULL,
    all_codes TEXT,
    occupation_description TEXT,
    category TEXT,
    major_code TEXT,
    minor_code TEXT,
    job_family_id TEXT,
    job_family_name TEXT,
    posting_count INTEGER,
    open_posting_count INTEGER,
    market_size_log REAL,
    has_legal_license INTEGER,
    n_original_names INTEGER
);

CREATE TABLE occupation_name_map (
    original_label TEXT PRIMARY KEY,
    original_code TEXT NOT NULL,
    original_name TEXT,
    base_name TEXT,
    merge_rule TEXT,
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    posting_count INTEGER
);

CREATE TABLE keywords (
    keyword_id TEXT PRIMARY KEY,
    keyword TEXT NOT NULL UNIQUE,
    category_code TEXT,
    keyword_category TEXT NOT NULL,
    synonyms TEXT,
    match_patterns TEXT,
    is_common_competency INTEGER,
    n_occupations INTEGER,
    n_occupations_core INTEGER,
    idf REAL,
    idf_norm REAL,
    discriminative_weight REAL
);

CREATE TABLE occupation_keywords (
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    keyword_id TEXT NOT NULL REFERENCES keywords(keyword_id),
    keyword TEXT,
    importance TEXT CHECK (importance IN ('required','major','supplementary')),
    relevance_score REAL,
    source_type TEXT CHECK (source_type IN ('job_posting','occupational_knowledge','inferred')),
    confidence REAL,
    evidence_count INTEGER,
    posting_share REAL,
    basis TEXT,
    PRIMARY KEY (occupation_id, keyword_id, source_type)
);

CREATE TABLE occupation_keyword_profile (
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    keyword_id TEXT NOT NULL REFERENCES keywords(keyword_id),
    keyword TEXT,
    importance TEXT,
    combined_score REAL,
    sources TEXT,
    evidence_count INTEGER,
    PRIMARY KEY (occupation_id, keyword_id)
);

CREATE TABLE keyword_relations (
    keyword_id_a TEXT NOT NULL REFERENCES keywords(keyword_id),
    keyword_a TEXT,
    keyword_id_b TEXT NOT NULL REFERENCES keywords(keyword_id),
    keyword_b TEXT,
    relation_type TEXT,
    weight REAL,
    PRIMARY KEY (keyword_id_a, keyword_id_b)
);

CREATE TABLE licenses (
    license_id TEXT PRIMARY KEY,
    license_name TEXT NOT NULL UNIQUE,
    display_name TEXT,
    license_category TEXT,
    parent_license_id TEXT REFERENCES licenses(license_id),
    posting_count INTEGER,
    legal_basis_refs TEXT,
    is_qualification INTEGER,
    sample_raw_text TEXT
);

CREATE TABLE occupation_licenses (
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    license_id TEXT NOT NULL REFERENCES licenses(license_id),
    license_name TEXT,
    requirement_type TEXT NOT NULL,
    evidence_count INTEGER,
    required_count INTEGER,
    preferred_count INTEGER,
    mention_count INTEGER,
    n_postings INTEGER,
    required_share REAL,
    evidence_share REAL,
    confidence REAL,
    source_type TEXT,
    legal_id TEXT,
    legal_basis TEXT,
    legal_condition TEXT,
    verification_status TEXT,
    legal_source TEXT,
    legal_note TEXT,
    alternative_group TEXT,
    PRIMARY KEY (occupation_id, license_id)
);

CREATE TABLE occupation_preferences (
    preference_id TEXT PRIMARY KEY,
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    preference_name TEXT NOT NULL,
    preference_category TEXT,
    is_policy_target INTEGER,
    evidence_count INTEGER,
    sources TEXT,
    n_postings INTEGER,
    posting_share REAL,
    source_type TEXT,
    confidence REAL,
    requirement_type TEXT,
    use_in_matching INTEGER
);

CREATE TABLE job_postings (
    posting_id TEXT PRIMARY KEY,
    raw_row_number INTEGER NOT NULL UNIQUE,
    row_hash TEXT,
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    original_occupation_label TEXT,
    original_occupation_code TEXT,
    company TEXT,
    title TEXT,
    job_description_raw TEXT,
    duty_text TEXT,
    required_text TEXT,
    preferred_text TEXT,
    career_edu_text TEXT,
    duty_actions TEXT,
    duty_tools TEXT,
    duty_competencies TEXT,
    duty_targets TEXT,
    license_field_raw TEXT,
    required_quals TEXT,
    preference_field_raw TEXT,
    computer_skills TEXT,
    region TEXT,
    sido TEXT,
    sigungu TEXT,
    career TEXT,
    min_education TEXT,
    major TEXT,
    industry TEXT,
    employment_type_raw TEXT,
    employment_type TEXT,
    is_part_time INTEGER,
    recruit_count INTEGER,
    wage_raw TEXT,
    wage_type TEXT,
    wage_min INTEGER,
    wage_max INTEGER,
    work_hours TEXT,
    reg_date TEXT,
    deadline TEXT,
    until_hired INTEGER,
    is_open_as_of_run INTEGER,
    is_exact_duplicate INTEGER,
    duplicate_of TEXT,
    is_near_duplicate INTEGER
);

CREATE TABLE posting_occupations (
    posting_id TEXT NOT NULL REFERENCES job_postings(posting_id),
    occupation_id TEXT NOT NULL REFERENCES occupations(occupation_id),
    is_primary INTEGER NOT NULL,
    PRIMARY KEY (posting_id, occupation_id)
);

CREATE TABLE posting_keywords (
    posting_id TEXT NOT NULL REFERENCES job_postings(posting_id),
    keyword_id TEXT NOT NULL REFERENCES keywords(keyword_id),
    found_in TEXT,
    PRIMARY KEY (posting_id, keyword_id)
);

CREATE TABLE posting_licenses (
    posting_id TEXT NOT NULL REFERENCES job_postings(posting_id),
    license_id TEXT REFERENCES licenses(license_id),
    license_name TEXT,
    source TEXT,
    requirement_level TEXT,
    raw_text TEXT
);

CREATE TABLE posting_preferences (
    posting_id TEXT NOT NULL REFERENCES job_postings(posting_id),
    preference_name TEXT,
    preference_category TEXT,
    is_policy_target INTEGER,
    source TEXT,
    raw_text TEXT
);

CREATE TABLE experience_keyword_mapping (
    mapping_id TEXT PRIMARY KEY,
    rule_id TEXT,
    expression_pattern TEXT,
    example_expression TEXT,
    experience_activity TEXT,
    action TEXT,
    keyword_id TEXT NOT NULL REFERENCES keywords(keyword_id),
    keyword TEXT,
    keyword_category TEXT,
    match_type TEXT,
    weight REAL,
    source_type TEXT,
    note TEXT
);

CREATE INDEX ix_jp_occ ON job_postings(occupation_id);
CREATE INDEX ix_jp_open ON job_postings(is_open_as_of_run, deadline);
CREATE INDEX ix_ok_kw ON occupation_keywords(keyword_id);
CREATE INDEX ix_okp_kw ON occupation_keyword_profile(keyword_id);
CREATE INDEX ix_ol_lic ON occupation_licenses(license_id);
CREATE INDEX ix_op_occ ON occupation_preferences(occupation_id);
CREATE INDEX ix_pk_kw ON posting_keywords(keyword_id);
CREATE INDEX ix_pl_post ON posting_licenses(posting_id);
CREATE INDEX ix_pp_post ON posting_preferences(posting_id);
CREATE INDEX ix_em_kw ON experience_keyword_mapping(keyword_id);

CREATE VIEW v_occupation_summary AS
SELECT o.occupation_id, o.occupation_name, o.job_family_name, o.posting_count, o.open_posting_count,
       (SELECT COUNT(*) FROM occupation_keyword_profile p WHERE p.occupation_id = o.occupation_id) AS n_keywords,
       (SELECT GROUP_CONCAT(license_name, ', ') FROM occupation_licenses l WHERE l.occupation_id = o.occupation_id AND l.requirement_type LIKE '필수(법정%') AS legal_licenses
FROM occupations o;
