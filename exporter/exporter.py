"""
Cloud Cost Exporter — exposes fake/real cost metrics to Prometheus.

In a real setup this would call AWS Cost Explorer / GCP Billing API.
Here it simulates realistic cost data so you can build dashboards
without needing a cloud account.

Real AWS integration: uncomment the boto3 section at the bottom.
"""
import os, time, random, logging
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
app = Flask(__name__)

registry = CollectorRegistry()

# ── Cost metrics ─────────────────────────────────────────────────────
cost_daily = Gauge(
    "cloud_cost_daily_usd",
    "Daily cloud cost in USD",
    ["service", "resource_type", "environment"],
    registry=registry
)

cost_monthly = Gauge(
    "cloud_cost_monthly_usd",
    "Month-to-date cost in USD",
    ["service", "resource_type", "environment"],
    registry=registry
)

# ── Resource utilization ─────────────────────────────────────────────
resource_util = Gauge(
    "cloud_resource_utilization_percent",
    "Resource utilization percentage",
    ["resource", "instance_type", "environment"],
    registry=registry
)

# ── Resource inventory ────────────────────────────────────────────────
resource_count = Gauge(
    "cloud_resource_count",
    "Number of running cloud resources",
    ["resource_type", "environment"],
    registry=registry
)

# ── Budget tracking ───────────────────────────────────────────────────
budget_limit = Gauge(
    "cloud_budget_limit_usd",
    "Monthly budget limit in USD",
    ["environment"],
    registry=registry
)

budget_used = Gauge(
    "cloud_budget_used_percent",
    "Percentage of monthly budget used",
    ["environment"],
    registry=registry
)


def simulate_costs():
    """Generate realistic daily cost data with slight randomness."""
    # Simulate day-of-month (costs grow through month)
    dom = int(time.strftime("%d"))

    # ── Compute ───────────────────────────────────────────────────────
    ec2_daily_prod  = round(random.uniform(12.0, 16.0), 2)
    ec2_daily_dev   = round(random.uniform(3.0, 5.0), 2)
    k8s_daily       = round(random.uniform(8.0, 12.0), 2)

    cost_daily.labels("EC2",        "compute",   "prod").set(ec2_daily_prod)
    cost_daily.labels("EC2",        "compute",   "dev").set(ec2_daily_dev)
    cost_daily.labels("EKS",        "compute",   "prod").set(k8s_daily)
    cost_daily.labels("Lambda",     "compute",   "prod").set(round(random.uniform(0.1, 0.5), 3))

    cost_monthly.labels("EC2",      "compute",   "prod").set(round(ec2_daily_prod * dom, 2))
    cost_monthly.labels("EC2",      "compute",   "dev").set(round(ec2_daily_dev * dom, 2))
    cost_monthly.labels("EKS",      "compute",   "prod").set(round(k8s_daily * dom, 2))

    # ── Storage ───────────────────────────────────────────────────────
    s3_daily        = round(random.uniform(0.5, 1.5), 2)
    rds_daily       = round(random.uniform(4.0, 6.0), 2)
    ebs_daily       = round(random.uniform(1.0, 2.0), 2)

    cost_daily.labels("S3",         "storage",   "prod").set(s3_daily)
    cost_daily.labels("RDS",        "storage",   "prod").set(rds_daily)
    cost_daily.labels("EBS",        "storage",   "prod").set(ebs_daily)
    cost_daily.labels("S3",         "storage",   "dev").set(round(s3_daily * 0.2, 3))

    cost_monthly.labels("S3",       "storage",   "prod").set(round(s3_daily * dom, 2))
    cost_monthly.labels("RDS",      "storage",   "prod").set(round(rds_daily * dom, 2))
    cost_monthly.labels("EBS",      "storage",   "prod").set(round(ebs_daily * dom, 2))

    # ── Network ───────────────────────────────────────────────────────
    transfer_daily  = round(random.uniform(1.0, 3.0), 2)
    lb_daily        = round(random.uniform(0.5, 1.0), 2)
    nat_daily       = round(random.uniform(0.2, 0.8), 2)

    cost_daily.labels("DataTransfer","network",  "prod").set(transfer_daily)
    cost_daily.labels("ALB",         "network",  "prod").set(lb_daily)
    cost_daily.labels("NATGateway",  "network",  "prod").set(nat_daily)

    cost_monthly.labels("DataTransfer","network","prod").set(round(transfer_daily * dom, 2))
    cost_monthly.labels("ALB",        "network", "prod").set(round(lb_daily * dom, 2))
    cost_monthly.labels("NATGateway", "network", "prod").set(round(nat_daily * dom, 2))

    # ── Utilization ───────────────────────────────────────────────────
    resource_util.labels("cpu",    "t3.small",  "prod").set(random.uniform(15, 75))
    resource_util.labels("memory", "t3.small",  "prod").set(random.uniform(40, 85))
    resource_util.labels("cpu",    "t3.micro",  "dev").set(random.uniform(5, 40))
    resource_util.labels("memory", "t3.micro",  "dev").set(random.uniform(20, 60))
    resource_util.labels("storage","rds",       "prod").set(random.uniform(30, 70))

    # ── Inventory ─────────────────────────────────────────────────────
    resource_count.labels("ec2_instance",   "prod").set(2)
    resource_count.labels("ec2_instance",   "dev").set(1)
    resource_count.labels("rds_instance",   "prod").set(1)
    resource_count.labels("s3_bucket",      "prod").set(3)
    resource_count.labels("nat_gateway",    "prod").set(1)

    # ── Budget ────────────────────────────────────────────────────────
    prod_monthly_total = (
        ec2_daily_prod * dom + k8s_daily * dom +
        rds_daily * dom + s3_daily * dom +
        transfer_daily * dom + lb_daily * dom + nat_daily * dom
    )
    prod_budget = float(os.getenv("PROD_BUDGET_USD", "600"))
    dev_budget  = float(os.getenv("DEV_BUDGET_USD",  "100"))

    budget_limit.labels("prod").set(prod_budget)
    budget_limit.labels("dev").set(dev_budget)
    budget_used.labels("prod").set(round((prod_monthly_total / prod_budget) * 100, 1))
    budget_used.labels("dev").set(round(((ec2_daily_dev * dom) / dev_budget) * 100, 1))


@app.route("/metrics")
def metrics():
    simulate_costs()
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    log.info("Cost exporter started on :9101")
    app.run(host="0.0.0.0", port=9101)

# ── Real AWS integration (uncomment + pip install boto3) ──────────────
# import boto3, datetime
# def get_aws_costs():
#     client = boto3.client("ce", region_name="us-east-1")
#     today = datetime.date.today()
#     start = today.replace(day=1).isoformat()
#     end   = today.isoformat()
#     response = client.get_cost_and_usage(
#         TimePeriod={"Start": start, "End": end},
#         Granularity="DAILY",
#         Metrics=["UnblendedCost"],
#         GroupBy=[{"Type":"DIMENSION","Key":"SERVICE"}]
#     )
#     for result in response["ResultsByTime"]:
#         for group in result["Groups"]:
#             svc   = group["Keys"][0]
#             cost  = float(group["Metrics"]["UnblendedCost"]["Amount"])
#             cost_daily.labels(svc, "aws", "prod").set(cost)
