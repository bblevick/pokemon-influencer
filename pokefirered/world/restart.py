"""Managed host restart dispositions. HTTP transports are never resumed."""
def recover_durable_work(store):
    intent=store.pending_save()
    if intent:
        return {'status':'waiting_save','intent':intent['id'],'operations':[]}
    operations=[]
    for row in store.db.execute("SELECT id FROM puppeteer_jobs WHERE status='active'").fetchall():
        operations.append({'kind':'recap','jobID':row['id'],'result':store.recover_job(row['id'],'host_restart')})
    strategy_jobs=store.db.execute("SELECT id FROM strategy_jobs WHERE status='active'").fetchall() if hasattr(store,'revoke_strategy') else []
    for row in strategy_jobs:
        store.revoke_strategy(row['id'],'host_restart_waiting_future_authorization')
        operations.append({'kind':'strategy','jobID':row['id'],'status':'revoked','logicalDisposition':'waiting_future_authorization','transportResumed':False})
    return {'status':'recovered','operations':operations}
