# Spring Boot 4 마이그레이션 요약

교재(Java 24 / Spring Boot 3.5 / Spring Cloud 2025.0)와 이 저장소 코드의 차이 중 학습할 때 알아 두면 좋은 것들입니다. 전체 목록은 [MIGRATION-BOOT4.md](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/MIGRATION-BOOT4.md)에 있습니다.

## 원본 코드와 직접 비교하기

교재 원본 코드는 [`original-boot3`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3) 브랜치에 그대로 있습니다. 장별 차이는 다음처럼 확인하세요.

```bash
git clone https://github.com/NohYounghoon3651/spring-microservice-boot4.git && cd spring-microservice-boot4
git fetch origin original-boot3
git diff origin/original-boot3 origin/main --stat -- Chapter13   # 바뀐 파일 목록
git diff origin/original-boot3 origin/main -- Chapter13          # 전체 차이
```

웹에서는 [전체 비교 화면](https://github.com/NohYounghoon3651/spring-microservice-boot4/compare/original-boot3...boot4-migration-diff)으로 볼 수 있지만, 변경 파일이 1,000개가 넘어 일부만 표시됩니다.

## 교재 본문과 다르게 보이는 부분

| 위치 | 교재 | 이 저장소 |
|---|---|---|
| Dockerfile (4장~) | `-Djarmode=layertools` | `-Djarmode=tools extract --layers --launcher` |
| MongoDB 설정 (6장~) | `spring.data.mongodb.host` | `spring.mongodb.host` |
| 오류 메시지 설정 | `server.error.include-message` | `spring.web.error.include-message` |
| 422 상태 코드 | `HttpStatus.UNPROCESSABLE_ENTITY` | `HttpStatus.UNPROCESSABLE_CONTENT` |
| Jackson | `com.fasterxml.jackson.databind.*` | `tools.jackson.databind.*` (Jackson 3) |
| 인가 서버 설정 클래스 (11장~) | `...oauth2.server.authorization.config.annotation...` | `org.springframework.security.config.annotation...` |
| AOP 스타터 (12장~) | `spring-boot-starter-aop` | `spring-boot-starter-aspectj` |
| Resilience4j (13장~) | `resilience4j-spring-boot3` | `resilience4j-spring-boot4` |
| Zipkin 설정 (14장~) | `management.zipkin.tracing.endpoint` | `management.tracing.export.zipkin.endpoint` |
| 테스트 | `@SpringBootTest`만으로 WebTestClient 주입 | `@AutoConfigureWebTestClient` 추가 |

## 동작이 달라진 부분

- **DTO의 `final` 필드**: Jackson 3는 `final` 필드를 역직렬화하지 않아 api 모듈 DTO의 `final`을 제거했습니다.
- **enum 직렬화**: Jackson 3는 enum을 `toString()`으로 씁니다. 회로 차단기 이벤트를 교재와 같은 `CLOSED_TO_OPEN` 형태로 유지하려고 `spring.jackson.datatype.enum.write-enums-using-to-string: false`를 설정했습니다(13장~).
- **헬스 응답**: liveness/readiness 프로브가 기본으로 켜져 `/actuator/health`에 `groups`가 추가됩니다.
- **네이티브 이미지 (23장)**: GraalVM 25 이상이 필요합니다(빌드팩에 `BP_JVM_VERSION=25`).

## 교재·Boot 4.0.9 기본값과 다른 라이브러리 버전 (보안 패치)

Spring Boot는 **4.0.9 그대로**지만, 알려진 취약점이 있는 일부 라이브러리는 각 장의 루트 `settings.gradle` 끝에 있는 `securityPatches` 표에서 패치 버전으로 올렸습니다(v1.0.5). 그래서 `./gradlew dependencies`로 보면 Boot 4.0.9의 기본 버전과 다르게 나옵니다.

| 라이브러리 | Boot 4.0.9 기본 | 이 저장소 |
|---|---|---|
| RabbitMQ 클라이언트 `com.rabbitmq:amqp-client` | 5.27.1 | 5.37.1 |
| Kafka 압축 `lz4-java` · `snappy-java` | 1.10.1 · 1.1.10.7 | 1.11.4 · 1.1.10.9 |
| Guava (Eureka) | 16.0 / 33.0.0-jre | 33.7.2-jre |
| Apache HttpClient 4 · 5 | 4.5.3 · 5.5.2 | 4.5.14 · 5.6.3 |
| OpenTelemetry (추적) | 1.55.0 | 1.67.0 (Zipkin exporter 1.64.0) |

예제 코드와 실행 방법은 바뀌지 않습니다. 이유와 전체 표는 [MIGRATION-BOOT4.md 2-5절](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/MIGRATION-BOOT4.md), 새 취약점이 나왔을 때의 처리 방법은 [CONTRIBUTING.md](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/CONTRIBUTING.md#dependabot-취약점-알림-처리-기준)에 있습니다.
