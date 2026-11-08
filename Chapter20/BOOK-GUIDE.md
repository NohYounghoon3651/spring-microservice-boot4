# 20장 교재 대응 가이드 — 마이크로서비스 모니터링

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 20 "Monitoring Microservices" (p.563–598)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

Micrometer로 지표를 내보내고 Prometheus·Grafana로 대시보드를 보는 부분은 책과 같습니다. 크게 달라진 곳은 **Grafana 알림**입니다. 이스티오 1.31.4 애드온의 Grafana는 12.0.1이고, 책이 쓰는 예전 알림 시스템은 Grafana 11에서 삭제되었습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Introduction (p.564–565) | 이스티오 1.17 + Grafana 9.0.1 + Prometheus 2.34.0 | 이스티오 1.31.4 + **Grafana 12.0.1** + **Prometheus 3.10.0** |
| Changes in source code (p.565–566) | `micrometer-registry-prometheus`, `/actuator/prometheus` 노출 | 같습니다 |
| Building and deploying (p.566–568) | `helm upgrade istio-hands-on-addons ...` 등 | 같습니다 |
| 테스트 메일 서버 (p.568–569) | `kubectl -n istio-system create deployment mail-server --image maildev/maildev:2.0.5` | 같은 명령을 쓰면 됩니다. 저장소에는 메일 서버를 외부로 노출하는 `expose-mail.yml`만 있고, 메일 서버 자체는 책처럼 직접 만듭니다 |
| Configuring Grafana (p.569) | `GF_ALERTING_ENABLED=true`, **`GF_UNIFIED_ALERTING_ENABLED=false`**, `GF_SMTP_*` | Grafana 12에는 예전 알림 시스템이 없으니 **`GF_SMTP_ENABLED`, `GF_SMTP_SKIP_VERIFY`, `GF_SMTP_HOST`, `GF_SMTP_FROM_ADDRESS`만** 설정하세요. 앞의 두 변수는 빼야 합니다 |
| Monitoring using Grafana dashboards (p.568–585) | Kiali·Grafana 기본 대시보드, 커뮤니티 대시보드(ID 11955) 가져오기, 직접 만든 대시보드 | 같은 방식입니다. 패널 편집 화면은 Grafana 12에서 모양이 다릅니다. `kubernetes/grafana/api-export-import/Hands-on-Dashboard.json`도 가져올 수 있지만, Grafana 9에서 만든 것이라 일부 패널이 다르게 보일 수 있습니다 |
| Setting up alarms in Grafana (p.585–596) | 대시보드 패널의 Alert 탭에서 알림 규칙, `/api/alert-notifications`로 메일 채널 생성 | **통합 알림(Unified Alerting)**을 씁니다: Alerting → Contact points에서 Email 연락처(maildev 주소)를 만들고, Alerting → Alert rules에서 `resilience4j_circuitbreaker_state{state="closed"}` 같은 조건으로 규칙을 만듭니다. `/api/alert-notifications` API는 없어졌고, API로 만들려면 `/api/v1/provisioning/contact-points`를 씁니다 |

## 참고

- 알림 실습은 CI에서 검증하지 않았습니다. 화면과 메뉴 이름은 Grafana 12 기준으로 찾아보세요.
- 서킷 브레이커·재시도 지표 이름(`resilience4j_circuitbreaker_state` 등)과 부하 테스트(`siege`) 명령은 책과 같습니다.

## 더 보기

- 위키: [20장 마이크로서비스 모니터링](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/20장-마이크로서비스-모니터링)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter20)
- 학습 이슈: [#20](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/20)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
