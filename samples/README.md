# Muestras de las APIs de Open-Meteo

Respuestas reales guardadas tal cual por `python/scripts/fetch_samples.py`. Sirven de referencia del formato y de datos de prueba sin red.

- Fecha de referencia D (America/Bogota): 2026-10-18
- Descarga (UTC): 2026-10-19T03:40:18Z
- Datos: Open-Meteo.com (CC BY 4.0), a partir de ERA5 (Copernicus Climate Change Service) y CAMS global (Copernicus Atmosphere Monitoring Service).

| Archivo | Contenido | Rango | URL |
|---|---|---|---|
| `era5_year.json` | ERA5: temperatura, humedad y viento de un año | 2025-10-18 → 2026-10-17 | https://archive-api.open-meteo.com/v1/archive?latitude=6.2447&longitude=-75.5748&elevation=1495&hourly=temperature_2m%2Crelative_humidity_2m%2Cwind_speed_10m&models=era5&wind_speed_unit=ms&timezone=GMT&start_date=2025-10-18&end_date=2026-10-17 |
| `era5_recent_month.json` | ERA5: últimos 30 días (incluye los nulos finales de los días no publicados) | 2026-09-18 → 2026-10-17 | https://archive-api.open-meteo.com/v1/archive?latitude=6.2447&longitude=-75.5748&elevation=1495&hourly=temperature_2m%2Crelative_humidity_2m%2Cwind_speed_10m&models=era5&wind_speed_unit=ms&timezone=GMT&start_date=2026-09-18&end_date=2026-10-17 |
| `cams_pm25_year.json` | CAMS global: PM2.5 de un año | 2025-10-18 → 2026-10-17 | https://air-quality-api.open-meteo.com/v1/air-quality?latitude=6.2447&longitude=-75.5748&hourly=pm2_5&domains=cams_global&timezone=GMT&start_date=2025-10-18&end_date=2026-10-17 |
| `cams_pm25_last_week.json` | CAMS global: PM2.5 de los últimos 7 días | 2026-10-11 → 2026-10-17 | https://air-quality-api.open-meteo.com/v1/air-quality?latitude=6.2447&longitude=-75.5748&hourly=pm2_5&domains=cams_global&timezone=GMT&start_date=2026-10-11&end_date=2026-10-17 |

Los parámetros completos de cada petición están en `manifest.json`.
