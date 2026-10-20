import json, math, os, random, threading, time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

APP = os.getenv("APP_NAME", "demo-checkout")
REQUESTS = Counter("demo_http_requests_total", "Simulated requests", ["status"])
LATENCY = Gauge("demo_request_latency_seconds", "Latest simulated request latency")
ERROR_RATIO = Gauge("demo_http_error_ratio", "Latest simulated HTTP error ratio")
CPU = Gauge("demo_cpu_usage_percent", "Simulated CPU usage percentage")
ANOMALY = Gauge("aiops_anomaly_detected", "Rolling detector anomaly flag")
window = deque(maxlen=20)
lock = threading.Lock()
incident = {"status": "NORMAL", "reason": "Waiting for samples"}

def telemetry():
    global incident
    tick = 0
    while True:
        tick += 1
        mode = os.getenv("SIMULATION_MODE", "normal").lower()
        if mode == "latency" and tick % 10 >= 5:
            latency, cpu, err = random.uniform(1.2, 2), random.uniform(75, 95), random.uniform(.03, .12)
        elif mode == "errors" and tick % 10 >= 5:
            latency, cpu, err = random.uniform(.3, .8), random.uniform(25, 60), random.uniform(.2, .4)
        else:
            latency, cpu, err = random.uniform(.06, .22), random.uniform(15, 55), random.uniform(0, .02)
        LATENCY.set(latency); CPU.set(cpu); ERROR_RATIO.set(err)
        REQUESTS.labels(status="5xx" if err > .05 else "2xx").inc(random.randint(4, 15))
        window.append(latency)
        detected, reason = False, "Signals within expected range"
        if len(window) >= 8:
            prev = list(window)[:-1]
            avg = sum(prev) / len(prev)
            sd = math.sqrt(sum((x-avg)**2 for x in prev) / len(prev))
            if latency > max(avg + 3*sd, avg*2.5, .7):
                detected, reason = True, f"Latency spike: {latency:.2f}s vs baseline {avg:.2f}s"
            elif err > .15:
                detected, reason = True, f"Elevated HTTP error ratio: {err:.1%}"
            elif cpu > 85:
                detected, reason = True, f"High CPU signal: {cpu:.1f}%"
        ANOMALY.set(int(detected))
        with lock:
            incident = ({"status":"OPEN", "service":APP, "severity":"HIGH" if err>.15 or cpu>85 else "MEDIUM",
                         "reason":reason, "latency_seconds":round(latency,3), "cpu_percent":round(cpu,1),
                         "error_ratio":round(err,4), "timestamp":int(time.time()),
                         "suggested_action":"Check recent deployments, dependency latency, CPU saturation and application logs; validate before remediation."}
                        if detected else {"status":"NORMAL", "service":APP, "reason":reason, "timestamp":int(time.time())})
        if detected: print(json.dumps(incident), flush=True)
        time.sleep(5)

class Handler(BaseHTTPRequestHandler):
    def send_json(self, code, obj):
        b=json.dumps(obj, indent=2).encode()
        self.send_response(code); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/metrics":
            b=generate_latest(); self.send_response(200); self.send_header("Content-Type",CONTENT_TYPE_LATEST); self.end_headers(); self.wfile.write(b)
        elif self.path == "/health": self.send_json(200, {"status":"ok","service":APP})
        elif self.path == "/aiops/status":
            with lock: data=dict(incident)
            self.send_json(200,data)
        elif self.path == "/": self.send_json(200, {"service":APP,"endpoints":["/health","/metrics","/aiops/status"]})
        else: self.send_json(404, {"error":"not found"})
    def log_message(self, fmt, *args): print(fmt % args, flush=True)

if __name__ == "__main__":
    threading.Thread(target=telemetry,daemon=True).start()
    print(f"Starting {APP} telemetry demo on :8000",flush=True)
    ThreadingHTTPServer(("0.0.0.0",8000),Handler).serve_forever()
