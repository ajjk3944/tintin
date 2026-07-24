import heapq

MAX_MEMORY = 80.0
MAX_TEMP = 100.0
CRITICAL_RISK = 75

_job_queue = []
_job_counter = 0

def _score_node(node_row, risk_row):
    risk_score = risk_row['risk_score'] / 100.0
    memory_ratio = 1 - (node_row['memory_used'] / MAX_MEMORY)
    thermal_headroom = 1 - (node_row['temperature'] / MAX_TEMP)

    score = (1 - risk_score) * 0.5 + memory_ratio * 0.3 + thermal_headroom * 0.2
    return round(score, 4)

def add_job(job_name, priority=1):
    global _job_counter
    heapq.heappush(_job_queue, (-priority, _job_counter, job_name))
    _job_counter += 1

def assign_job(metrics_df, risk_df):
    if not _job_queue:
        return None, None, "No jobs in queue"

    scores = []
    for _, node_row in metrics_df.iterrows():
        risk_row = risk_df[risk_df['node_id'] == node_row['node_id']].iloc[0]
        if risk_row['risk_score'] >= CRITICAL_RISK:
            continue
        s = _score_node(node_row, risk_row)
        scores.append((s, int(node_row['node_id'])))

    if not scores:
        return None, None, "All nodes critical — job held"

    scores.sort(reverse=True)
    best_node = scores[0][1]
    best_score = scores[0][0]

    _, _, job_name = heapq.heappop(_job_queue)
    reason = f"Score={best_score} | Best available node"
    return job_name, best_node, reason

def check_migration(metrics_df, risk_df):
    migrations = []
    # Find candidate healthy nodes for migration target
    healthy_nodes = []
    for _, node_row in metrics_df.iterrows():
        risk_row = risk_df[risk_df['node_id'] == node_row['node_id']].iloc[0]
        if risk_row['risk_score'] < CRITICAL_RISK:
            s = _score_node(node_row, risk_row)
            healthy_nodes.append((s, int(node_row['node_id'])))
    
    healthy_nodes.sort(reverse=True)
    target_node = healthy_nodes[0][1] if healthy_nodes else None

    for _, row in risk_df.iterrows():
        if row['risk_score'] >= CRITICAL_RISK:
            target_str = f"Node {target_node}" if target_node else "Pending Healthy Node"
            migrations.append({
                'node_id': int(row['node_id']),
                'risk_score': row['risk_score'],
                'target_node': target_node,
                'action': f"AUTO-MIGRATED Workload → {target_str} (Risk Score: {row['risk_score']})"
            })
    return migrations

def queue_length():
    return len(_job_queue)
