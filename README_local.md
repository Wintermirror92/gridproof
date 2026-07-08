# GridProof ESS MVP Scaffold

## 한 줄 정의
GridProof ESS는 ESS를 제어하는 AI가 아니라, 공공 재원이 투입된 ESS가 신청·설치·운영·지령 이행 단계에서 약속대로 작동했는지 검증하는 AI입니다.

## 데모에서 반드시 말해야 할 범위
- 공개데이터 기반 환경 분석
- 합성 로그 기반 End-to-End 이행검증 프로세스 구현
- 실제 KPX 지령 로그, 실제 ESS BMS/PCS 로그, 실제 사업자 운영자료를 사용한 검증 완료가 아님
- AI는 부정수급·고의성을 확정하지 않고 점검 우선순위와 담당자 검토용 근거를 제시함

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 포함 파일
- `app.py`: Streamlit MVP 화면
- `data/processed/ess_sites.csv`: 전남 가상 ESS 사업지 7개
- `data/processed/hourly_verification_log.csv`: 합성 지령·출력·SoC·통신·알람 로그
- `data/processed/site_summary.csv`: 사업지별 이행률·위험점수·Action Card 근거
- `data/processed/public_ess_capacity_latest.csv`: 공개 ESS 연계 설비용량 맥락 데이터
- `data/processed/public_curtailment_2025q1.csv`: 공개 출력제어 맥락 데이터
- `data/processed/public_jeonnam_solar_hourly_pattern_2025.csv`: 전남 태양광 거래량 시간대별 평균 패턴

## MVP 핵심 화면
1. Overview
2. Verification Dashboard
3. Public Data Context
4. Action Card
5. Report Generator

## 발표용 표현
> GridProof ESS는 실제 이행검증을 완료했다고 주장하지 않습니다. 공개데이터로 지역별 재생에너지·ESS 환경을 설명하고, 합성 로그로 지령 이행검증 프로세스가 끝까지 작동함을 구현한 MVP입니다.
