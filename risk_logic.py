def calc_risk_score(summary):
    compliance_risk = summary["excess_interval_rate"]          # 허용오차 초과 구간 비율
    avoidable_risk = summary["avoidable_deviation_rate"]       # 회피 가능 편차 비율
    repeat_risk = summary["repeat_failure_rate"]               # 반복 미이행 비율
    comm_risk = summary["comm_missing_rate"]                   # 통신 결측률
    alarm_risk = summary["alarm_rate"]                         # PCS/BMS 알람률
    evidence_risk = summary["evidence_mismatch_score"] / 100   # 증빙 불일치
    soc_risk = summary["soc_constraint_rate"]                  # SoC 제약 발생률

    score = 100 * (
        0.25 * compliance_risk +
        0.20 * avoidable_risk +
        0.15 * repeat_risk +
        0.12 * comm_risk +
        0.10 * alarm_risk +
        0.10 * evidence_risk +
        0.08 * soc_risk
    )

    return round(min(score, 100), 1)