# AIOps Mini: Infrastructure Observability Demo

A local-first portfolio project combining application telemetry, Prometheus, Grafana, statistical anomaly detection, and incident triage.

## Architecture
- Demo app: `/health`, `/metrics`, `/aiops/status`
- Prometheus: scrapes app metrics every 5 seconds and evaluates alert rules
- Grafana: provisioned Prometheus datasource and service-health dashboard
- Python detector: rolling baseline flags latency spikes and high error/CPU signals; outputs structured incident JSON to app logs and `/aiops/status`

> This is a demo using synthetic telemetry and a lightweight statistical heuristic. It is not a trained ML model or a production AIOps platform.

## Requirements
Docker Engine, Docker Compose plugin, Git.

## Start
```bash
docker compose up --build -d
docker compose ps
```
- App health: http://localhost:8000/health
- Incident status: http://localhost:8000/aiops/status
- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (local demo only: `admin` / `changeme-local-only`)

## Simulate abnormal signals
```bash
SIMULATION_MODE=latency docker compose up -d --force-recreate app
<OR>
SIMULATION_MODE=database docker compose up -d --force-recreate app
<OR>
SIMULATION_MODE=cpu docker compose up -d --force-recreate app
<OR>
SIMULATION_MODE=errors docker compose up -d --force-recreate app
curl -s http://localhost:8000/aiops/status
docker compose logs --tail=50 app
```
For errors instead:
```bash
SIMULATION_MODE=errors docker compose up -d --force-recreate app
```
Return to normal:
```bash
docker compose up -d --force-recreate app
```
Wait for several 5-second samples. The simulation mode is read when the app starts.

Prometheus alert rules appear at http://localhost:9090/alerts. They define conditions but do not send external notifications; configure Alertmanager or Grafana contact points separately for email/Slack.

## Useful PromQL
```promql
demo_request_latency_seconds
demo_cpu_usage_percent
demo_http_error_ratio
aiops_anomaly_detected
rate(demo_http_requests_total[1m])
```

## Demo walkthrough
1. Show the healthy dashboard.
2. Switch to latency mode and observe latency/anomaly changes.
3. Show `/aiops/status` and explain the evidence and suggested checks.
4. Show Prometheus alert evaluation.
5. Explain how production would correlate metrics with logs/traces, deployment events, dependencies and SLOs.

## Production-hardening backlog
- Pin tested image versions instead of `latest;` add tests for detector and API.
- Replace synthetic CPU with real host metrics via Node Exporter or OpenTelemetry.
- Add logs/traces with correlation IDs, SLOs, error-budget alerts and deduplication.
- Add Alertmanager/Slack/ITSM integration and TLS/auth for remote access.
- Require human approval before remediation; never restart production systems from a single anomaly.

## Portfolio description
**AIOps Mini — Infrastructure Observability Lab:** Built a Docker Compose observability stack with Prometheus and Grafana, instrumented a sample service with health and performance metrics, implemented rolling-baseline anomaly detection in Python, and defined alert rules for latency and error-rate conditions. Generated structured incident evidence and remediation guidance to demonstrate an alert-to-triage workflow.

## Limitations
Signals are synthetic; CPU is not measured from the host. The detector is a heuristic and may produce false positives/negatives. Remediation guidance is advisory only.
