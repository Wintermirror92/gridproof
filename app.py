import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="GridProof ESS MVP", layout="wide")

APP_TITLE = "GridProof ESS - 중앙계약시장 ESS 공공사업 이행검증 AI"

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "processed"
ASSET_DIR = BASE_DIR / "assets"


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


def clean_label(value) -> str:
    return (
        str(value)
        .replace("PCS/BMS", "PCS·BMS")
        .replace("BMS/PCS", "BMS·PCS")
    )


def split_actions(value):
    text = clean_label(value)

    if " | " in text:
        parts = text.split(" | ")
    elif " / " in text:
        parts = text.split(" / ")
    else:
        parts = [text]

    return [p.strip() for p in parts if p.strip()]


def pct(value) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "-"


def num(value, digits=1) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):.{digits}f}"
    except Exception:
        return "-"


ROLE_OPTIONS = [
    "한국에너지공단·지자체 사후관리 담당자",
    "전력거래소 데이터 연계 담당자",
    "전기위원회·전력감독원(가칭) 검토자",
    "ESS 사업자·VPP/PMS 소명 담당자",
]


def get_role_view(role: str, row):
    risk_score = row.get("risk_score", "-")
    risk_level = row.get("risk_level", "-")

    base_notice = (
        "AI는 고의성·부정수급·법적 책임을 확정하지 않습니다. "
        "이 카드는 담당자 검토를 위한 단서와 다음 조치만 제시합니다."
    )

    if role == "한국에너지공단·지자체 사후관리 담당자":
        return {
            "title": "보조·실증사업 사후관리 카드",
            "focus": "설치·운영 증빙과 사업지별 사후관리 필요 여부를 우선 확인합니다.",
            "metrics": [
                ("위험점수", f"{risk_score} / 100"),
                ("위험등급", risk_badge(risk_level)),
                ("설치/계약 용량 차이율", pct(row.get("capacity_gap_rate", 0))),
                ("품질플래그 확인률", pct(row.get("quality_flag_rate", 0))),
            ],
            "evidence": [
                "계약용량과 설치확인용량의 차이 여부",
                "사업자정보·설치위치·운영개시일 증빙 일치 여부",
                "품질플래그 및 계량 원천 데이터 확인 필요 여부",
            ],
            "actions": [
                "설치 증빙 재확인",
                "운영개시일·설치확인용량 자료 대조",
                "계량 원천 데이터 제출 요청",
                "사후관리 점검 대상 여부 검토",
            ],
            "next_step": "확인 필요 사업지는 Evidence Package로 묶어 사후관리 점검 대상으로 분류합니다.",
            "notice": base_notice,
        }

    if role == "전력거래소 데이터 연계 담당자":
        return {
            "title": "지령 이행 데이터 연계 카드",
            "focus": "지령값 대비 실제출력, 응답지연, 통신결측 등 이행 로그를 우선 확인합니다.",
            "metrics": [
                ("위험점수", f"{risk_score} / 100"),
                ("평균 이행률", pct(row.get("mean_fulfillment_rate", 0))),
                ("통신 결측률", pct(row.get("comm_missing_rate", 0))),
                ("PCS·BMS 알람률", pct(row.get("alarm_rate", 0))),
            ],
            "evidence": [
                "Target MW 대비 Actual Output 이행률",
                "명령 발생 구간의 응답지연",
                "통신 결측 및 PCS·BMS 알람 발생 여부",
            ],
            "actions": [
                "지령 수신·출력 로그 대조",
                "통신 재전송 로그 요청",
                "PCS·BMS 이벤트 로그 확인",
                "응답지연 반복 구간 확인",
            ],
            "next_step": "KPX는 대체 대상이 아니라 지령·출력 기준 데이터 연계 대상입니다.",
            "notice": base_notice,
        }

    if role == "전기위원회·전력감독원(가칭) 검토자":
        score_value = float(row.get("risk_score", 0))
        return {
            "title": "상위 감독·정책 검토 카드",
            "focus": "개별 처분보다 반복 위험 유형과 제도개선 필요성을 우선 확인합니다.",
            "metrics": [
                ("위험점수", f"{risk_score} / 100"),
                ("위험등급", risk_badge(risk_level)),
                ("반복위험 후보", "확인 필요" if score_value >= 25 else "낮음"),
                ("감독 리포트 필요", "예" if score_value >= 25 else "아니오"),
            ],
            "evidence": [
                "반복 미이행 또는 반복 결측 가능성",
                "지역·사업지별 위험 유형 분포",
                "정책 리포트로 집계 가능한 사후관리 단서",
            ],
            "actions": [
                "반복위험 사업지 목록에 포함 여부 검토",
                "지역별·사업유형별 위험 패턴 집계",
                "제도개선 검토용 요약 리포트 생성",
                "실제 도입 시 추가 데이터 확보 필요 항목 정리",
            ],
            "next_step": "전기위원회·전력감독원(가칭)은 확정 고객이 아니라 상위 감독 리포트 수요처로 설정합니다.",
            "notice": base_notice,
        }

    score_value = float(row.get("risk_score", 0))
    return {
        "title": "사업자 소명·로그 재제출 카드",
        "focus": "사업자가 어떤 자료를 제출해야 하는지와 조치 결과를 확인합니다.",
        "metrics": [
            ("위험점수", f"{risk_score} / 100"),
            ("위험등급", risk_badge(risk_level)),
            ("소명 필요 항목", "확인 필요" if score_value >= 25 else "낮음"),
            ("재제출 필요 로그", "BMS·PCS·계량 로그"),
        ],
        "evidence": [
            "요청 시간대의 BMS SoC 로그",
            "PCS 이벤트 로그 및 통신 재전송 로그",
            "계량 원천 데이터와 기존 제출자료의 일치 여부",
        ],
        "actions": [
            "BMS SoC 로그 제출",
            "PCS 이벤트 로그 제출",
            "통신 재전송 로그 제출",
            "계량 원천 데이터 재제출",
            "조치 결과 등록",
        ],
        "next_step": "제출된 소명자료는 담당자 검토 후 종결 또는 재점검으로 분류됩니다.",
        "notice": base_notice,
    }


def make_evidence_package_text(row, role_view):
    site_name = clean_label(row.get("site_name", "-"))

    lines = [
        "# GridProof ESS Evidence Package",
        "",
        "## 대상 사업지",
        f"- 사업지: {site_name}",
        f"- 지역: {row.get('municipality', '-')}",
        f"- 위험점수: {row.get('risk_score', '-')} / 100",
        f"- 위험등급: {row.get('risk_level', '-')}",
        "",
        "## 역할별 검토 관점",
        f"- {role_view['title']}",
        f"- {role_view['focus']}",
        "",
        "## 주요 단서",
    ]

    for item in role_view["evidence"]:
        lines.append(f"- {item}")

    lines += [
        "",
        "## 권고 조치",
    ]

    for action in role_view["actions"]:
        lines.append(f"- {action}")

    lines += [
        "",
        "## 다음 단계",
        f"- {role_view['next_step']}",
        "",
        "## 주의 문구",
        role_view["notice"],
        "",
        "※ 본 패키지는 공개자료 기반 환경 분석과 합성 로그 기반 MVP 검증 흐름을 보여주는 예시입니다.",
    ]

    return "\n".join(lines)


def make_report(site_row, site_logs):
    report = f"""
# GridProof ESS 담당자 검토용 감사 리포트 초안

## 1. 대상 사업지
- 사업지: {clean_label(site_row['site_name'])}
- 지역: {site_row['municipality']}
- 계약용량: {site_row['contract_kw']:,} kW
- 설치확인용량: {site_row['installed_kw']:,} kW
- 데이터 구분: 합성 운영 로그 기반 MVP 검증

## 2. 요약 판단
- 위험점수: {site_row['risk_score']} / 100
- 위험등급: {site_row['risk_level']}
- 평균 지령 이행률: {site_row['mean_fulfillment_rate']*100:.1f}%
- 주요 단서: {clean_label(site_row['main_reasons'])}

## 3. 정량 단서
- 설치/계약 용량 차이율: {site_row['capacity_gap_rate']*100:.1f}%
- 통신 로그 결측률: {site_row['comm_missing_rate']*100:.1f}%
- SoC 부족 발생률: {site_row['soc_low_rate']*100:.1f}%
- PCS·BMS 알람 발생률: {site_row['alarm_rate']*100:.1f}%
- 품질플래그 확인률: {site_row['quality_flag_rate']*100:.1f}%

## 4. 권고 조치
{chr(10).join([f"- {a}" for a in split_actions(site_row['recommended_actions'])])}

## 5. 주의 문구
본 리포트는 공개데이터 기반 환경 분석과 합성 로그 기반 End-to-End 이행검증 프로세스 구현 결과입니다.
실제 KPX 지령 로그, 실제 ESS BMS·PCS 로그, 실제 사업자 운영자료를 사용한 최종 검증 결과가 아닙니다.
AI는 고의성·부정수급 여부를 확정하지 않으며, 담당자 검토를 위한 점검 우선순위와 근거 단서만 제공합니다.
"""
    return report.strip()


sites, logs, summary, ess_capacity, curtail, solar_pattern = load_data()

st.title(APP_TITLE)

cover_path = ASSET_DIR / "cover_gridproof.png"

if cover_path.exists():
    st.image(str(cover_path), use_container_width=True)
    st.caption("이미지는 서비스 콘셉트 연출용이며, 실제 구현 화면은 아래 Streamlit 대시보드입니다.")

st.info(
    "본 MVP는 공개자료 기반 환경 분석과 합성 로그 기반 ESS 이행검증 프로세스를 구현한 시뮬레이션입니다. "
    "실제 KPX 지령 로그, ESS BMS·PCS 운영 로그, 사업자 실명 데이터는 사용하지 않았습니다."
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
            "실제 도입 시 필요": "BMS SoC 로그, PCS·BMS 이벤트 로그",
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
    "실제 KPX 지령 로그·ESS 운영 로그·SoC·PCS·BMS 알람은 합성데이터로 구현했습니다."
)

ordered = summary.sort_values("risk_score", ascending=False)

page = st.radio(
    "메뉴",
    [
        "1. Overview",
        "2. Verification Dashboard",
        "3. Public Data Context",
        "4. Action Card",
        "5. Report Generator",
    ],
    horizontal=True,
    label_visibility="collapsed",
)

if page == "1. Overview":
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
- 지령값과 실제 출력의 이행률, 로그 결측, SoC 부족, PCS·BMS 알람, 품질플래그를 사후 검증합니다.
- AI는 부정수급·고의성을 확정하지 않고 점검 우선순위와 담당자 검토용 근거만 제공합니다.
""")

    st.dataframe(summary[[
        "site_name", "municipality", "risk_score", "risk_level", "mean_fulfillment_rate",
        "comm_missing_rate", "soc_low_rate", "alarm_rate", "main_reasons"
    ]], use_container_width=True)

elif page == "2. Verification Dashboard":
    st.subheader("Verification Dashboard - 지령값 vs 실제 출력")

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

elif page == "3. Public Data Context":
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

elif page == "4. Action Card":
    st.subheader("Action Card - 담당자 확인용")

    selected_card = st.selectbox(
        "Action Card 사업지",
        ordered["site_name"].tolist(),
        key="card_select"
    )
    row = ordered[ordered["site_name"] == selected_card].iloc[0]

    selected_role = st.selectbox(
        "사용자 역할",
        ROLE_OPTIONS,
        key="role_select"
    )

    role_view = get_role_view(selected_role, row)

    st.markdown(f"### {clean_label(row['site_name'])}")
    st.caption(f"선택 역할: {selected_role}")

    st.info(role_view["focus"])

    m1, m2, m3, m4 = st.columns(4)
    metric_cols = [m1, m2, m3, m4]

    for col, metric in zip(metric_cols, role_view["metrics"]):
        label, value = metric
        col.metric(label, value)

    st.markdown("#### 주요 단서")
    for item in role_view["evidence"]:
        st.write(f"- {item}")

    st.markdown("#### 권고 조치")
    for action in role_view["actions"]:
        st.write(f"- {action}")

    st.markdown("#### 소명·검토 워크플로우")
    workflow = pd.DataFrame([
        {"단계": "1. 확인 필요", "설명": "위험점수와 주요 단서 확인", "상태": "현재"},
        {"단계": "2. 사업자 소명 요청", "설명": "필요 로그와 증빙자료 요청", "상태": "대기"},
        {"단계": "3. 로그 재제출", "설명": "BMS·PCS·계량·통신 로그 제출", "상태": "대기"},
        {"단계": "4. 담당자 검토", "설명": "제출자료와 기존 로그 대조", "상태": "대기"},
        {"단계": "5. 종결 / 재점검", "설명": "소명 인정 또는 재점검 대상 분류", "상태": "대기"},
    ])
    st.dataframe(workflow, use_container_width=True, hide_index=True)

    st.markdown("#### Evidence Package 미리보기")
    package_text = make_evidence_package_text(row, role_view)
    st.code(package_text, language="markdown")

    st.download_button(
        "Evidence Package Markdown 다운로드",
        package_text,
        file_name=f"GridProof_Evidence_Package_{row['site_id']}.md",
        mime="text/markdown"
    )

    st.warning(role_view["notice"])

elif page == "5. Report Generator":
    st.subheader("Report Generator - 감사 리포트 초안")

    selected_report = st.selectbox(
        "리포트 생성 사업지",
        ordered["site_name"].tolist(),
        key="report_select"
    )

    selected_report_role = st.selectbox(
        "리포트 관점",
        ROLE_OPTIONS,
        key="report_role_select"
    )

    row = ordered[ordered["site_name"] == selected_report].iloc[0]
    site_logs = logs[logs["site_name"] == selected_report]

    report = make_report(row, site_logs)

    st.info(f"리포트 관점: {selected_report_role}")
    st.markdown(report)

    st.download_button(
        "리포트 Markdown 다운로드",
        report,
        file_name=f"GridProof_Report_{row['site_id']}.md",
        mime="text/markdown"
    )