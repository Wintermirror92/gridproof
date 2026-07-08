from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

sites = pd.DataFrame([
    {
        "site_id": "ESS-001",
        "site_name": "해남 ESS-01",
        "municipality": "해남",
        "contract_kw": 5000,
        "installed_kw": 4920,
        "energy_capacity_kwh": 20000,
        "lat": 34.57,
        "lon": 126.60,
    },
    {
        "site_id": "ESS-002",
        "site_name": "완도 ESS-02",
        "municipality": "완도",
        "contract_kw": 4000,
        "installed_kw": 4000,
        "energy_capacity_kwh": 16000,
        "lat": 34.31,
        "lon": 126.75,
    },
    {
        "site_id": "ESS-003",
        "site_name": "신안 ESS-03",
        "municipality": "신안",
        "contract_kw": 6000,
        "installed_kw": 5700,
        "energy_capacity_kwh": 24000,
        "lat": 34.83,
        "lon": 126.10,
    },
    {
        "site_id": "ESS-004",
        "site_name": "영암 ESS-04",
        "municipality": "영암",
        "contract_kw": 3500,
        "installed_kw": 3500,
        "energy_capacity_kwh": 14000,
        "lat": 34.80,
        "lon": 126.70,
    },
    {
        "site_id": "ESS-005",
        "site_name": "무안 ESS-05",
        "municipality": "무안",
        "contract_kw": 4500,
        "installed_kw": 4300,
        "energy_capacity_kwh": 18000,
        "lat": 34.99,
        "lon": 126.48,
    },
    {
        "site_id": "ESS-006",
        "site_name": "나주 ESS-06",
        "municipality": "나주",
        "contract_kw": 3000,
        "installed_kw": 3000,
        "energy_capacity_kwh": 12000,
        "lat": 35.02,
        "lon": 126.72,
    },
    {
        "site_id": "ESS-007",
        "site_name": "고흥 ESS-07",
        "municipality": "고흥",
        "contract_kw": 3800,
        "installed_kw": 3650,
        "energy_capacity_kwh": 15200,
        "lat": 34.61,
        "lon": 127.28,
    },
])

sites.to_csv(DATA_DIR / "ess_sites.csv", index=False, encoding="utf-8-sig")

timestamps = pd.date_range("2026-07-01 00:00", periods=24 * 7, freq="h")
log_rows = []

for _, s in sites.iterrows():
    contract_kw = int(s["contract_kw"])
    soc = np.random.uniform(35, 85)

    for ts in timestamps:
        hour = ts.hour

        command_kw = 0
        if 10 <= hour <= 16 and np.random.rand() < 0.55:
            command_kw = int(np.random.choice([0.3, 0.5, 0.7, 0.9]) * contract_kw)

        soc_noise = np.random.normal(0, 3)
        soc = float(np.clip(soc + soc_noise - (command_kw / max(contract_kw, 1)) * 4, 5, 95))

        comm_status = "OK"
        if np.random.rand() < 0.04:
            comm_status = "MISSING"

        pcs_alarm = np.random.rand() < 0.035
        bms_alarm = np.random.rand() < 0.025

        weather_alert = np.random.rand() < 0.06

        quality_flag = "GOOD"
        if comm_status == "MISSING":
            quality_flag = "MISSING"
        elif pcs_alarm or bms_alarm:
            quality_flag = "CHECK"
        elif np.random.rand() < 0.03:
            quality_flag = "BAD"

        base_fulfillment = np.random.normal(0.94, 0.08)

        if s["site_id"] in ["ESS-001", "ESS-003"]:
            base_fulfillment -= np.random.uniform(0.08, 0.18)

        if soc < 20:
            base_fulfillment -= 0.25
        if comm_status == "MISSING":
            base_fulfillment -= 0.20
        if pcs_alarm or bms_alarm:
            base_fulfillment -= 0.15
        if weather_alert:
            base_fulfillment -= 0.06

        fulfillment_rate = float(np.clip(base_fulfillment, 0, 1.1))

        if command_kw > 0:
            actual_kw = int(command_kw * fulfillment_rate)
        else:
            actual_kw = int(np.random.uniform(0, 0.05) * contract_kw)

        response_delay_min = max(0, int(np.random.normal(4, 4)))
        if fulfillment_rate < 0.8:
            response_delay_min += int(np.random.uniform(5, 15))

        log_rows.append({
            "timestamp": ts,
            "site_id": s["site_id"],
            "site_name": s["site_name"],
            "municipality": s["municipality"],
            "command_kw": command_kw,
            "actual_kw": actual_kw,
            "fulfillment_rate": fulfillment_rate if command_kw > 0 else 1.0,
            "soc_pct": round(soc, 1),
            "comm_status": comm_status,
            "pcs_alarm": bool(pcs_alarm),
            "bms_alarm": bool(bms_alarm),
            "quality_flag": quality_flag,
            "weather_alert": bool(weather_alert),
            "response_delay_min": response_delay_min,
        })

logs = pd.DataFrame(log_rows)
logs.to_csv(DATA_DIR / "hourly_verification_log.csv", index=False, encoding="utf-8-sig")

summary_rows = []

for _, s in sites.iterrows():
    site_logs = logs[logs["site_id"] == s["site_id"]].copy()
    cmd_logs = site_logs[site_logs["command_kw"] > 0].copy()

    if len(cmd_logs) == 0:
        mean_fulfillment = 1.0
    else:
        mean_fulfillment = float(cmd_logs["fulfillment_rate"].mean())

    capacity_gap_rate = abs(s["contract_kw"] - s["installed_kw"]) / s["contract_kw"]
    comm_missing_rate = float((site_logs["comm_status"] == "MISSING").mean())
    soc_low_rate = float((site_logs["soc_pct"] < 20).mean())
    alarm_rate = float((site_logs["pcs_alarm"] | site_logs["bms_alarm"]).mean())
    quality_flag_rate = float((site_logs["quality_flag"] != "GOOD").mean())
    low_fulfillment_rate = float((cmd_logs["fulfillment_rate"] < 0.85).mean()) if len(cmd_logs) else 0.0

    risk_score = 100 * (
        0.20 * capacity_gap_rate +
        0.35 * max(0, 0.95 - mean_fulfillment) / 0.35 +
        0.15 * comm_missing_rate +
        0.10 * soc_low_rate +
        0.08 * alarm_rate +
        0.05 * quality_flag_rate +
        0.07 * low_fulfillment_rate
    )
    risk_score = round(float(np.clip(risk_score, 0, 100)), 1)

    if risk_score >= 45:
        risk_level = "높음"
    elif risk_score >= 25:
        risk_level = "중간"
    else:
        risk_level = "낮음"

    reasons = []
    actions = []

    if capacity_gap_rate > 0.03:
        reasons.append("설치/계약 용량 차이")
        actions.append("설치 증빙 재확인")
    if mean_fulfillment < 0.85:
        reasons.append("지령 이행률 저조")
        actions.append("지령 수신·출력 로그 대조")
    if comm_missing_rate > 0.03:
        reasons.append("통신 로그 결측")
        actions.append("통신 재전송 로그 요청")
    if soc_low_rate > 0.03:
        reasons.append("SoC 부족 발생")
        actions.append("사전 충전계획 확인")
    if alarm_rate > 0.03:
        reasons.append("PCS/BMS 알람")
        actions.append("PCS/BMS 이벤트 로그 요청")
    if quality_flag_rate > 0.05:
        reasons.append("품질플래그 확인 필요")
        actions.append("계량 원천 데이터 확인")

    if not reasons:
        reasons = ["중대한 이상 단서 없음"]
    if not actions:
        actions = ["정기 모니터링 유지"]

    summary_rows.append({
        "site_id": s["site_id"],
        "site_name": s["site_name"],
        "municipality": s["municipality"],
        "contract_kw": int(s["contract_kw"]),
        "installed_kw": int(s["installed_kw"]),
        "capacity_gap_rate": round(capacity_gap_rate, 4),
        "mean_fulfillment_rate": round(mean_fulfillment, 4),
        "comm_missing_rate": round(comm_missing_rate, 4),
        "soc_low_rate": round(soc_low_rate, 4),
        "alarm_rate": round(alarm_rate, 4),
        "quality_flag_rate": round(quality_flag_rate, 4),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "main_reasons": " · ".join(reasons),
        "recommended_actions": " / ".join(actions),
    })

summary = pd.DataFrame(summary_rows)
summary.to_csv(DATA_DIR / "site_summary.csv", index=False, encoding="utf-8-sig")

ess_capacity = pd.DataFrame([
    {"지역": "전라남도", "ESS연계설비용량_MW": 412.5},
    {"지역": "제주특별자치도", "ESS연계설비용량_MW": 185.2},
    {"지역": "전라북도", "ESS연계설비용량_MW": 121.0},
    {"지역": "경상북도", "ESS연계설비용량_MW": 98.3},
    {"지역": "강원특별자치도", "ESS연계설비용량_MW": 76.8},
    {"지역": "충청남도", "ESS연계설비용량_MW": 66.2},
])
ess_capacity.to_csv(DATA_DIR / "public_ess_capacity_latest.csv", index=False, encoding="utf-8-sig")

curtail_dates = pd.date_range("2025-01-01", periods=90, freq="D")
curtail = pd.DataFrame({
    "date": curtail_dates,
    "curtailment_type": np.random.choice(["태양광", "풍력", "태양광+풍력"], size=len(curtail_dates), p=[0.55, 0.25, 0.20]),
    "control_hours": np.random.choice([0, 1, 2, 3, 4, 5], size=len(curtail_dates), p=[0.45, 0.20, 0.15, 0.10, 0.07, 0.03]),
    "contains_jeonnam": np.random.choice([True, False], size=len(curtail_dates), p=[0.35, 0.65]),
})
curtail.to_csv(DATA_DIR / "public_curtailment_2025q1.csv", index=False, encoding="utf-8-sig")

hours = list(range(24))
solar_values = []
for h in hours:
    if 6 <= h <= 18:
        value = max(0, np.sin((h - 6) / 12 * np.pi)) * 1000 + np.random.normal(0, 40)
    else:
        value = np.random.normal(5, 3)
    solar_values.append(round(max(0, value), 1))

solar_pattern = pd.DataFrame({
    "hour": hours,
    "avg_trade_volume_mwh": solar_values,
})
solar_pattern.to_csv(DATA_DIR / "public_jeonnam_solar_hourly_pattern_2025.csv", index=False, encoding="utf-8-sig")

print("GridProof ESS synthetic data generated.")
print(f"Output directory: {DATA_DIR}")
print("Generated files:")
for path in sorted(DATA_DIR.glob("*.csv")):
    print("-", path.name)