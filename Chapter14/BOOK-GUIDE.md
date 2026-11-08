# 14장 교재 대응 가이드 — 분산 추적

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 14 "Understanding Distributed Tracing" (p.349–372)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

Micrometer Tracing과 Zipkin으로 추적하는 구조, 리액티브 클라이언트용 컨텍스트 전파 설정(`Hooks.enableAutomaticContextPropagation()`), 사용자 정의 스팬은 책과 같습니다. 의존성 구성, 설정 키 두 개, Zipkin 서비스 이름과 버전이 바뀌었습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Adding dependencies (p.352) | `micrometer-tracing-bridge-otel`, `opentelemetry-exporter-zipkin` | 위 두 개 + Boot 4의 자동 구성 모듈 **`spring-boot-micrometer-tracing-opentelemetry`**, **`spring-boot-zipkin`** |
| SQL 추적 (p.352) | `datasource-micrometer-spring-boot:1.0.0` | **`2.2.1`** (Boot 4 지원판) |
| Zipkin 주소 (p.352) | **`management.zipkin.tracing.endpoint`**: `http://zipkin:9411/api/v2/spans` | **`management.tracing.export.zipkin.endpoint`**: `http://zipkin-server:9411/api/v2/spans` |
| 로그에 추적 ID 넣기 (p.352–353) | `logging.pattern.level: "%5p [${spring.application.name:},%X{traceId:-},%X{spanId:-}]"` | **`logging.pattern.correlation`**: `"[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "`. 로그 레벨 뒤에 같은 정보가 찍힙니다 |
| Zipkin 컨테이너 (p.353) | 서비스 이름 `zipkin`, `openzipkin/zipkin:2.24.0` | 서비스 이름 **`zipkin-server`**, **`openzipkin/zipkin:3.5.0`** |
| 사용자 정의 스팬·태그 (p.355–361) | `ObservationRegistry`, `ObservationUtil` | 같습니다 |
| Trying out distributed tracing (p.361–371) | `docker-compose build`, Zipkin UI(`http://localhost:9411`)의 **RUN QUERY** | `docker compose build`. Zipkin 3의 화면도 같은 방식으로 검색합니다 |

## 참고

- 로그 예시의 `traceparent` 헤더(W3C 형식, p.350, p.365)는 이 장에서는 그대로입니다. 18장에서 B3 헤더로 바뀝니다.

## 더 보기

- 위키: [14장 분산 추적](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/14장-분산-추적)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter14)
- 학습 이슈: [#14](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/14)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
