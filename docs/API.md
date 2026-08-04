# API Reference

Base URL: `http://localhost:8000`

## `GET /health`

Health check for load balancers and Docker.

**Response**
```json
{"status": "ok", "service": "battery-allocation"}
```

## `GET /classifications/summary`

Summary of battery classification counts from default dataset paths.

## `GET /requests/summary`

Summary of vehicle request counts by priority.

## `POST /pipeline/run`

Run full pipeline (classification, allocation, metrics, optional charts).

**Body**
```json
{
  "battery_csv": "data/Problem_1_Battery_Fleet_200_Packs.csv",
  "vehicle_csv": "data/Problem_1_Vehicle_Demand_50_Requests.csv",
  "output_dir": "outputs",
  "skip_visualizations": false,
  "twist": {
    "name": "onsite_twist",
    "min_soh_percent": 75,
    "max_temperature_c": 40
  }
}
```

All fields are optional; defaults resolve from config and project paths.

**Response**
```json
{
  "success": true,
  "proposed_metrics": { ... },
  "baseline_metrics": { ... },
  "output_paths": ["outputs/battery_classifications.csv", ...],
  "violations": []
}
```

## Start server

```bash
battery-allocation serve --host 0.0.0.0 --port 8000
```

## OpenAPI

Interactive docs: `http://localhost:8000/docs`
