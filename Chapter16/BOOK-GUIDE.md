# 16장 교재 대응 가이드 — 쿠버네티스에 마이크로서비스 배포

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 16 "Deploying Our Microservices to Kubernetes" (p.395–438)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

유레카를 쿠버네티스 서비스로 대체하는 구조, 그레이스풀 셧다운과 프로브, 헬름 차트 구성은 책과 같습니다. 바꿔 읽을 것은 컨테이너 이미지 버전, MongoDB 설정 키, minikube 접근 주소입니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Replacing Netflix Eureka with Kubernetes Services (p.396–398) | `http://product` 같은 서비스 이름 주소, `eureka.client.enabled=false` | 같습니다 |
| Graceful shutdown·probes (p.398–399) | `server.shutdown: graceful`, `spring.lifecycle.timeout-per-shutdown-phase: 10s`, 프로브 설정 | 같습니다. 책의 링크는 Boot 3.0.4 문서이니 Boot 4 문서로 보세요 |
| Introducing Helm (p.399–420) | `common`·`components`·`environments` 차트, `helm template ... -s templates/...` | 구조와 명령이 같습니다. 출력의 `helm.sh/chart` 버전 표시(1.0.0)도 같습니다 |
| MongoDB 차트 (p.417) | `mongo:6.0.4` | **`mongo:8.0.5`** (`components/mongodb/values.yaml`) |
| Deploying for development and test (p.420–431) | `docker pull mysql:8.0.32`, `mongo:6.0.4`, `rabbitmq:3.11.8-management`, `openzipkin/zipkin:2.24.0` | **`mysql:9.2.0`**, **`mongo:8.0.5`**, **`rabbitmq:4.0.7-management`**, **`openzipkin/zipkin:3.5.0`** |
| 접근 주소 (p.427–429) | `https://localhost:30443/...` (minikube `--ports`로 연결) | 같습니다. 리눅스에서 `--ports` 없이 만들었다면 `https://$(minikube ip):30443/...`을 쓰세요. CI는 `HOST=$(minikube ip) PORT=30443 USE_K8S=true ./test-em-all.bash`로 검증합니다 |
| Deploying for staging and production (p.432–436) | `config-repo`의 `spring.data.mongodb.host: 172.17.0.1` | **`spring.mongodb.host: 172.17.0.1`** (Boot 4 키). `docker compose`로 데이터베이스를 띄우고 `docker tag ...:v1`로 이미지를 준비하는 절차는 같습니다 |

## 그대로 따라 해도 되는 부분

- `siege`로 부하를 주며 롤링 업그레이드와 프로브 동작을 보는 실습(p.427–431)
- `kubectl logs`, `kubectl exec`로 문제를 살펴보는 방법

## 더 보기

- 위키: [16장 쿠버네티스에 마이크로서비스 배포](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/16장-쿠버네티스에-마이크로서비스-배포)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter16)
- 학습 이슈: [#16](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/16)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
