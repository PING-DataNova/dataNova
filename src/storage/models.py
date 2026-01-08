"""
TODO: Modèles SQLAlchemy

Tables à créer:
1. documents
   - id, title, source_url, hs_code, publication_date, file_hash, content, created_at

2. analyses
   - id, document_id, keyword_score, nc_score, llm_score, total_score, criticality, created_at

3. alerts
   - id, analysis_id, alert_data (JSON), sent_at, recipients

4. execution_logs
   - id, agent_type, status, start_time, end_time, errors

5. company_profiles
   - id, name, nc_codes (JSON), keywords (JSON), config (JSON)
"""
