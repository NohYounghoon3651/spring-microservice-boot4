# 7장 교재 대응 가이드 — 반응형 마이크로서비스 개발

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 7 "Developing Reactive Microservices" (p.163–210)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

리액티브 코드(Mono/Flux, `StepVerifier`, 블로킹 JPA를 감싸는 스케줄러)와 이벤트 기반 메시징 구조는 책과 같습니다. 바뀐 것은 Spring Cloud 버전, 메시지 브로커 이미지 버전, 테스트 바인더 의존성, Jackson 3 패키지입니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Developing non-blocking synchronous REST APIs (p.165–177) | `ReactiveMongoRepository`, `Mono.fromCallable` + `jdbcScheduler`, `WebClient.Builder` | 같습니다 |
| Developing event-driven asynchronous services (p.177–195) | 함수형 `Consumer` 빈과 `StreamBridge` | 같습니다. 바인딩 이름 `messageProcessor-in-0`도 같습니다 |
| `Event` 클래스 (p.183) | Jackson 2의 `ZonedDateTimeSerializer` | Jackson 3의 `tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer` |
| 빌드 파일 (p.184) | `springCloudVersion = "2022.0.1"`, 테스트 바인더 `spring-cloud-stream::test-binder` | **`2025.1.4`**, **`spring-cloud-stream-test-binder`** (별도 아티팩트) |
| RabbitMQ (p.199) | `rabbitmq:3.11.8-management` | **`rabbitmq:4.0.7-management`** |
| Kafka (p.205) | `confluentinc/cp-kafka:7.3.1`, `cp-zookeeper:7.3.1` | **`7.9.0`**. 이 저장소도 책처럼 주키퍼와 함께 실행합니다 |
| Running manual tests (p.195–207) | `docker-compose ...`, `export COMPOSE_FILE=...` | `docker compose ...`. `COMPOSE_FILE` 환경 변수 사용법은 같습니다 |
| Running automated tests (p.207–208) | `./test-em-all.bash start stop` (기본·파티션·Kafka 구성) | 같습니다. 세 구성 모두 CI에서 통과합니다 |

## 참고

- 이 저장소의 `test-em-all.bash`에는 CI에서 안정적으로 통과하도록 비동기 메시지 처리가 끝나기를 기다리는 대기 로직이 추가돼 있습니다. 책의 스크립트와 몇 줄 다른 이유입니다.

## 더 보기

- 위키: [7장 반응형 마이크로서비스 개발](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/07장-반응형-마이크로서비스-개발)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter07)
- 학습 이슈: [#7](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/7)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
