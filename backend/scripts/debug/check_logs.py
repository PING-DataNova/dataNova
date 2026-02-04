"""Afficher les logs d'exécution"""
from src.storage.database import get_session
from src.storage.models import ExecutionLog
from collections import Counter

session = get_session()
logs = session.query(ExecutionLog).order_by(ExecutionLog.created_at).all()

print('='*80)
print('TABLE EXECUTION_LOGS')
print('='*80)
print(f"{'AGENT':<12} | {'STATUS':<8} | {'TIME (ms)':<10} | {'DOC ID':<12} | ERROR")
print('-'*80)

for log in logs:
    doc_id = log.document_id[:8] if log.document_id else 'N/A'
    error = (log.error_message[:30] + '...') if log.error_message else ''
    print(f"{log.agent_name:<12} | {log.status:<8} | {log.execution_time_ms or 0:<10} | {doc_id:<12} | {error}")

print('-'*80)
print(f"TOTAL: {len(logs)} logs")
print()

# Stats par agent
agent_stats = Counter(log.agent_name for log in logs)
status_stats = Counter(log.status for log in logs)
print('Stats par agent:', dict(agent_stats))
print('Stats par status:', dict(status_stats))

session.close()
