// k6 run -e BASE=http://127.0.0.1:8000 benchmarks/k6-api.js
import http from 'k6/http';
import { check } from 'k6';
const BASE = __ENV.BASE || 'http://127.0.0.1:8000';
const names = ['GET /health', 'GET /classifications/summary', 'POST /pipeline/run'];
const thresholds = { http_req_failed: ['rate<0.01'] };
for (const n of names) {
  thresholds[`http_req_duration{name:${n}}`] = ['p(95)<60000'];
  thresholds[`http_reqs{name:${n}}`] = ['count>0'];
  thresholds[`http_req_failed{name:${n}}`] = ['rate<1'];
}
export const options = {
  summaryTrendStats: ['min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max', 'avg'],
  scenarios: {
    health:   { executor: 'constant-vus', vus: 50, duration: '20s', exec: 'health' },
    classify: { executor: 'constant-vus', vus: 50, duration: '20s', exec: 'classify', startTime: '25s' },
    pipeline: { executor: 'constant-vus', vus: 8,  duration: '20s', exec: 'pipeline', startTime: '50s' },
  },
  thresholds,
};
export function health() { check(http.get(`${BASE}/health`, { tags: { name: names[0] } }), { '200': (r) => r.status === 200 }); }
export function classify() { check(http.get(`${BASE}/classifications/summary`, { tags: { name: names[1] } }), { '200': (r) => r.status === 200 }); }
export function pipeline() {
  const body = JSON.stringify({ skip_visualizations: true, output_dir: `/tmp/bsa-bench/${__VU}` });
  check(http.post(`${BASE}/pipeline/run`, body, { headers: { 'Content-Type': 'application/json' }, tags: { name: names[2] } }), { '200': (r) => r.status === 200 });
}
