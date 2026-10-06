# 💰 Cloud Cost Tracking — Grafana Dashboard

Track compute, storage, and network spend with a Prometheus + Grafana stack. Simulates realistic AWS costs locally — plug in real AWS Cost Explorer API when ready.

## Architecture
```
Cost Exporter (:9101/metrics)
      ↓
Prometheus (scrapes every 60s)
      ↓
Grafana (pre-built dashboard)
```

## Quick Start
```bash
docker compose up -d --build
```
Open Grafana: http://localhost:3000 (admin / admin123)

The **Cloud Cost Dashboard** auto-loads with:
- Daily spend by service
- Month-to-date breakdown
- Budget gauge (prod + dev)
- Compute vs storage vs network pie chart
- Resource utilization vs cost correlation

## Dashboard panels

| Panel | What it shows |
|-------|---------------|
| Total Daily Spend | Sum of all prod costs today |
| Month-to-Date | Rolling MTD total |
| Budget Used % | Gauge — goes red at 90% |
| Daily Dev Spend | Dev environment daily cost |
| Cost by Service | Time series per AWS service |
| Cost by Type | Pie: compute / storage / network |
| Network Costs | Data transfer + ALB + NAT breakdown |
| Utilization vs Cost | Are you paying for idle resources? |

## Key Prometheus queries

```promql
# Total daily spend
sum(cloud_cost_daily_usd{environment="prod"})

# Most expensive service today
topk(3, cloud_cost_daily_usd{environment="prod"})

# Budget burn rate — will you exceed budget?
sum(cloud_cost_monthly_usd{environment="prod"}) / on() cloud_budget_limit_usd{environment="prod"} * 100

# Cost per service type
sum by (resource_type) (cloud_cost_daily_usd{environment="prod"})

# Underutilized compute (paying for idle)
cloud_resource_utilization_percent{resource="cpu"} < 20
```

## Connect real AWS data

1. Install boto3: `pip install boto3`
2. Configure AWS credentials: `aws configure`
3. Uncomment the `get_aws_costs()` function in `exporter/exporter.py`
4. Set env vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

## What to observe after running for a week
- Which service costs the most?
- Is dev environment spending proportionally too much?
- Is CPU utilization < 20% while paying for larger instances? (right-size opportunity)
- Is NAT Gateway cost high? (maybe S3 Gateway endpoint would be free)
- Is data transfer cost growing? (CDN might help)
