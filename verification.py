def judge_ess_dispatch(row, tolerance_rate=0.08, interval_h=0.25):
    capacity_mw = row["contract_capacity_mw"]
    target_mw = row["dispatch_target_mw"]
    actual_mw = row["actual_15min_avg_mw"]

    allowed_error_mw = capacity_mw * tolerance_rate
    raw_deviation_mw = actual_mw - target_mw

    feasible_discharge_mw, feasible_charge_mw = calc_feasible_output_mw(row, interval_h)

    if target_mw >= 0:
        feasible_target_mw = min(target_mw, feasible_discharge_mw)
        feasibility_gap_mw = max(target_mw - feasible_discharge_mw, 0)
    else:
        feasible_target_mw = max(target_mw, -feasible_charge_mw)
        feasibility_gap_mw = max(abs(target_mw) - feasible_charge_mw, 0)

    avoidable_deviation_mw = actual_mw - feasible_target_mw
    excess_deviation_mw = max(abs(raw_deviation_mw) - allowed_error_mw, 0)

    if abs(raw_deviation_mw) <= allowed_error_mw:
        compliance_flag = "이행"
    elif feasibility_gap_mw > allowed_error_mw:
        compliance_flag = "물리제약 확인필요"
    else:
        compliance_flag = "미이행 후보"

    return {
        "allowed_error_mw": allowed_error_mw,
        "raw_deviation_mw": raw_deviation_mw,
        "feasible_target_mw": feasible_target_mw,
        "feasibility_gap_mw": feasibility_gap_mw,
        "avoidable_deviation_mw": avoidable_deviation_mw,
        "excess_deviation_mw": excess_deviation_mw,
        "compliance_flag": compliance_flag,
    }