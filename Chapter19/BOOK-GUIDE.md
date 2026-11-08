# 19장 교재 대응 가이드 — EFK 스택을 사용한 중앙 집중식 로깅

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 19 "Centralized Logging with the EFK Stack" (p.523–562)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

Fluentd 설정과 EFK 스택 배포·사용 방법은 책과 같습니다. Elasticsearch·Kibana의 패치 버전만 올라갔습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Introducing Fluentd (p.524–533) | `fluentd-hands-on-configmap.yml`의 설정 | 같습니다 |
| Deploying the EFK stack (p.533–542) | `elasticsearch:7.17.10`, `kibana:7.17.10` | **`7.17.28`** (`docker pull` 명령의 태그도 바꿔서 실행) |
| Fluentd 이미지 (p.538–541) | `fluent/fluentd-kubernetes-daemonset:v1.4.2-debian-elasticsearch-1.1`, `fluent-plugin-detect-exceptions 0.0.12` | 같습니다(`kubernetes/efk/Dockerfile`) |
| 배포 명령 (p.533–541) | `helm install logging-hands-on-add-on kubernetes/helm/environments/logging`, `kubectl apply -f kubernetes/efk/...` | 같습니다 |
| Trying out the EFK stack (p.542–558) | Kibana 7 화면에서 인덱스 패턴·검색·시각화 | Kibana 7.17 계열이라 화면이 거의 같습니다. 미리 만든 객체는 `kubernetes/efk/kibana-api-exported-objects.ndjson`에 있습니다 |

## 참고

- 로그에 찍히는 추적 ID 형식은 18장과 같은 B3 형식입니다.

## 더 보기

- 위키: [19장 EFK 스택을 사용한 중앙 집중식 로깅](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/19장-EFK-스택을-사용한-중앙-집중식-로깅)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter19)
- 학습 이슈: [#19](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/19)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
