import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

APP_TITLE = "GridProof ESS - 중앙계약시장 ESS 공공사업 이행검증 AI"
DATA_DIR = Path(__file__).parent / "data" / "processed"

st.set_page_config(page_title="GridProof ESS MVP", layout="wide")

@st.cache_data
def load_data():
    sites = pd.read_csv(DATA_DIR / "ess_sites.csv")
    logs = pd.read_csv(DATA_DIR / "hourly_verification_log.csv", parse_dates=["timestamp"])
    summary = pd.read_csv(DATA_DIR / "site_summary.csv")
    ess_capacity = pd.read_csv(DATA_DIR / "public_ess_capacity_latest.csv")
    curtail = pd.read_csv(DATA_DIR / "public_curtailment_2025q1.csv", parse_dates=["date"])
    solar_pattern = pd.read_csv(DATA_DIR / "public_jeonnam_solar_hourly_pattern_2025.csv")
    return sites, logs, summary, ess_capacity, curtail, solar_pattern

def risk_badge(level: str) -> str:
    if level == "높음":
        return "🔴 높음"
    if level == "중간":
        return "🟠 중간"
    return "🟢 낮음"

def make_report(site_row, site_logs):
    command_logs = site_logs[site_logs["command_kw"] > 0]
    report = f"""
# GridProof ESS 담당자 검토용 감사 리포트 초안

## 1. 대상 사업지
- 사업지: {site_row['site_name']}
- 지역: {site_row['municipality']}
- 계약용량: {site_row['contract_kw']:,} kW
- 설치확인용량: {site_row['installed_kw']:,} kW
- 데이터 구분: 합성 운영 로그 기반 MVP 검증

## 2. 요약 판단
- 위험점수: {site_row['risk_score']} / 100
- 위험등급: {site_row['risk_level']}
- 평균 지령 이행률: {site_row['mean_fulfillment_rate']*100:.1f}%
- 주요 단서: {site_row['main_reasons']}

## 3. 정량 단서
- 설치/계약 용량 차이율: {site_row['capacity_gap_rate']*100:.1f}%
- 통신 로그 결측률: {site_row['comm_missing_rate']*100:.1f}%
- SoC 부족 발생률: {site_row['soc_low_rate']*100:.1f}%
- PCS/BMS 알람 발생률: {site_row['alarm_rate']*100:.1f}%
- 품질플래그 확인률: {site_row['quality_flag_rate']*100:.1f}%

## 4. 권고 조치
{chr(10).join([f"- {a.strip()}" for a in str(site_row['recommended_actions']).split('/')])}

## 5. 주의 문구
본 리포트는 공개데이터 기반 환경 분석과 합성 로그 기반 End-to-End 이행검증 프로세스 구현 결과입니다.
실제 KPX 지령 로그, 실제 ESS BMS/PCS 로그, 실제 사업자 운영자료를 사용한 최종 검증 결과가 아닙니다.
AI는 고의성·부정수급 여부를 확정하지 않으며, 담당자 검토를 위한 점검 우선순위와 근거 단서만 제공합니다.
"""
    return report.strip()

sites, logs, summary, ess_capacity, curtail, solar_pattern = load_data()

st.title(APP_TITLE)
st.info(
    "본 MVP는 공개자료 기반 환경 분석과 합성 로그 기반 ESS 이행검증 프로세스를 구현한 시뮬레이션입니다. "
    "실제 KPX 지령 로그, ESS BMS/PCS 운영 로그, 사업자 실명 데이터는 사용하지 않았습니다."
)

with st.expander("📌 Evidence Matrix: 공개자료·합성로그·실제 도입 필요 데이터 구분", expanded=False):
    evidence = pd.DataFrame([
        {
            "검증 항목": "전남 ESS 중앙계약시장 규모",
            "근거": "전기신문·전남도 보도",
            "MVP 활용": "공개자료 기반 배경 설명",
            "실제 도입 시 필요": "KPX 계약정보, 사업별 계약조건, 운영 개시 현황",
        },
        {
            "검증 항목": "지령값 / Target MW",
            "근거": "신재생발전기 송전계통 연계기술기준 부록6",
            "MVP 활용": "합성 지령 로그 생성",
            "실제 도입 시 필요": "KPX 또는 VPP 지령 로그",
        },
        {
            "검증 항목": "실제 출력",
            "근거": "계량데이터·전력거래량 구조",
            "MVP 활용": "합성 실제출력 로그 생성",
            "실제 도입 시 필요": "계량기, PCS, PMS, VPP 운영 로그",
        },
        {
            "검증 항목": "SoC / PCS·BMS 알람",
            "근거": "ESS 운영·설비 로그 구조",
            "MVP 활용": "이행 저하 단서 태깅",
            "실제 도입 시 필요": "BMS SoC 로그, PCS/BMS 이벤트 로그",
        },
        {
            "검증 항목": "임밸런스 페널티·허용오차",
            "근거": "KPX 제주 시범사업 공지",
            "MVP 활용": "허용오차 초과·패널티 노출 가능 구간 표시",
            "실제 도입 시 필요": "최신 전력시장운영규칙, 계약별 정산 조건",
        },
        {
            "검증 항목": "기상·특보",
            "근거": "기상청 공개자료 활용 가능",
            "MVP 활용": "이행 저하 해석 단서",
            "실제 도입 시 필요": "사업지 좌표 기반 실시간 기상·특보 연계",
        },
    ])

    st.dataframe(evidence, use_container_width=True)

    st.caption(
        "주의: 본 MVP는 실제 ESS 이행검증 완료 시스템이 아니라, 공개자료와 기술기준을 바탕으로 "
        "합성 로그 기반 End-to-End 검증 절차를 구현한 프로토타입입니다."
    )
st.caption("HighSix · MVP 범위: 공개데이터 기반 환경 분석 + 합성 로그 기반 End-to-End 이행검증 프로세스 구현")

st.warning(
    "주의: 이 MVP는 실제 ESS 이행검증 완료 결과가 아닙니다. "
    "실제 KPX 지령 로그·ESS 운영 로그·SoC·PCS/BMS 알람은 합성데이터로 구현했습니다."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Overview", "2. Verification Dashboard", "3. Public Data Context", "4. Action Card", "5. Report Generator"
])

with tab1:
    st.subheader("Overview - 제어가 아니라 검증")
    jeonnam_capacity = ess_capacity[ess_capacity["지역"].astype(str).str.contains("전라남도|전남", regex=True)]
    jeonnam_ess_mw = float(jeonnam_capacity["ESS연계설비용량_MW"].sum()) if len(jeonnam_capacity) else 0.0
    jeonnam_curt = curtail[curtail["contains_jeonnam"] == True]
    target_sites = len(summary)
    need_check = int((summary["risk_score"] >= 25).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전남 ESS 연계 설비용량", f"{jeonnam_ess_mw:,.1f} MW", "공개데이터")
    c2.metric("2025 Q1 전남 포함 출력제어일", f"{jeonnam_curt['date'].nunique()}일", "공개데이터")
    c3.metric("검증 대상 ESS", f"{target_sites}개", "합성 사업지")
    c4.metric("점검 필요 사업지", f"{need_check}개", "위험점수 25점 이상")

    st.markdown("""
### MVP 핵심 메시지
- ESS를 직접 제어하지 않습니다.
- KPX 지령을 대체하지 않습니다.
- VPP/PMS와 경쟁하지 않습니다.
- 지령값과 실제 출력의 이행률, 로그 결측, SoC 부족, PCS/BMS 알람, 품질플래그를 사후 검증합니다.
- AI는 부정수급·고의성을 확정하지 않고 점검 우선순위와 담당자 검토용 근거만 제공합니다.
""")

    st.dataframe(summary[[
        "site_name", "municipality", "risk_score", "risk_level", "mean_fulfillment_rate",
        "comm_missing_rate", "soc_low_rate", "alarm_rate", "main_reasons"
    ]], use_container_width=True)

with tab2:
    st.subheader("Verification Dashboard - 지령값 vs 실제 출력")
    ordered = summary.sort_values("risk_score", ascending=False)
    selected_name = st.selectbox("사업지 선택", ordered["site_name"].tolist())
    site_row = ordered[ordered["site_name"] == selected_name].iloc[0]
    site_logs = logs[logs["site_name"] == selected_name].copy()
    cmd_logs = site_logs[site_logs["command_kw"] > 0].copy()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("위험점수", f"{site_row['risk_score']}", risk_badge(site_row["risk_level"]))
    k2.metric("평균 이행률", f"{site_row['mean_fulfillment_rate']*100:.1f}%")
    k3.metric("통신 결측률", f"{site_row['comm_missing_rate']*100:.1f}%")
    k4.metric("알람 발생률", f"{site_row['alarm_rate']*100:.1f}%")

    st.markdown("#### 시간대별 지령-출력 비교")
    chart_df = site_logs[["timestamp", "command_kw", "actual_kw"]].set_index("timestamp")
    st.line_chart(chart_df)

    st.markdown("#### 명령 발생 구간 상세 로그")
    st.dataframe(cmd_logs[[
        "timestamp", "command_kw", "actual_kw", "fulfillment_rate", "soc_pct", "comm_status",
        "pcs_alarm", "bms_alarm", "quality_flag", "weather_alert", "response_delay_min"
    ]].sort_values("timestamp", ascending=False), use_container_width=True, height=420)

with tab3:
    st.subheader("Public Data Context - 공개데이터는 환경 설명용")
    st.info("이 탭의 공개데이터는 ESS 검증 필요성과 지역 맥락을 설명하는 용도입니다. 실제 사업지 이행검증에는 합성 로그를 사용합니다.")

    st.markdown("#### 지역별 ESS 연계 설비용량")
    cap_chart = ess_capacity[["지역", "ESS연계설비용량_MW"]].sort_values("ESS연계설비용량_MW", ascending=False).set_index("지역")
    st.bar_chart(cap_chart)

    st.markdown("#### 2025년 1분기 출력제어 발생일")
    curtail_daily = curtail.groupby(["date", "curtailment_type"], as_index=False)["control_hours"].sum()
    st.dataframe(curtail_daily.sort_values("date"), use_container_width=True)

    st.markdown("#### 2025년 전남 태양광 전력거래량 시간대별 평균 패턴")
    solar_chart = solar_pattern.set_index("hour")
    st.line_chart(solar_chart)

with tab4:
    st.subheader("Action Card - 담당자 확인용")
    selected_card = st.selectbox("Action Card 사업지", ordered["site_name"].tolist(), key="card_select")
    row = ordered[ordered["site_name"] == selected_card].iloc[0]

    st.markdown(f"""
## {row['site_name']}
### 위험도: {row['risk_score']} / 100 · {risk_badge(row['risk_level'])}

**주요 단서**  
{row['main_reasons']}

**권고 조치**  
{chr(10).join([f"- {a.strip()}" for a in str(row['recommended_actions']).split('/')])}

**주의**  
이 카드는 담당자 검토용 단서입니다. 고의성·부정수급·법적 책임 여부를 확정하지 않습니다.
""")

with tab5:
    st.subheader("Report Generator - 감사 리포트 초안")
    selected_report = st.selectbox("리포트 생성 사업지", ordered["site_name"].tolist(), key="report_select")
    row = ordered[ordered["site_name"] == selected_report].iloc[0]
    site_logs = logs[logs["site_name"] == selected_report]
    report = make_report(row, site_logs)
    st.markdown(report)
    st.download_button(
        "리포트 Markdown 다운로드",
        report,
        file_name=f"GridProof_Report_{row['site_id']}.md",
        mime="text/markdown"
    )
