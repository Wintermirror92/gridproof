# GridProof ESS 위험점수 산식 초안

## 1. 기본 원칙
위험점수는 부정수급·고의성·법적 책임을 확정하는 값이 아니다. 담당자가 먼저 확인할 사업지를 정하기 위한 우선순위 점수다.

## 2. 점수 구성
최종 위험점수는 0~100점으로 제한한다.

```text
EvidenceRisk = min(1, 용량차이율*4 + GPS불일치*0.35 + 서류누락*0.35)
ComplianceRisk = min(1, max(0, (0.95 - 평균이행률) / 0.35))
CommRisk = 지령 발생 시간 중 통신 결측률
SoCRisk = 지령 발생 시간 중 SoC 20% 미만 비율
AlarmRisk = 지령 발생 시간 중 PCS 또는 BMS 알람 발생률
QualityRisk = 지령 발생 시간 중 CHECK/MISSING/BAD 품질플래그 비율
RepeatRisk = max(이행률 85% 미만 비율, 응답지연 10분 초과 비율)

RiskScore =
100 * (
  0.20*EvidenceRisk +
  0.35*ComplianceRisk +
  0.15*CommRisk +
  0.10*SoCRisk +
  0.08*AlarmRisk +
  0.05*QualityRisk +
  0.07*RepeatRisk
)
+ min(3, 기상특보_비율*3)
```

## 3. 해석
- 60점 이상: 높음. 현장점검 또는 원시 로그 요청 우선.
- 25점 이상 60점 미만: 중간. 담당자 확인 및 사업자 소명/로그 대조 후보.
- 25점 미만: 낮음. 정기 모니터링 유지.

## 4. 발표 방어 문구
기상특보는 고의성 단서가 아니라 이행률 저하를 해석할 때 함께 봐야 하는 환경 맥락이다. 점수에 아주 작게만 반영하고, 실제 판단은 담당자가 한다.
