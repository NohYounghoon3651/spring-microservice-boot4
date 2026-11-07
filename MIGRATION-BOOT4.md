# 스프링 부트 4.0.9 / 자바 21 마이그레이션 가이드

이 저장소의 모든 장(3~7, 9~20, 23장) 예제 코드를 다음 환경으로 옮겼습니다. 각 장 폴더의 `MIGRATION-BOOT4.md`에 그 장에서 실제로 바뀐 파일 목록이 있습니다.

| 항목 | 교재 원본 | 변경 후 |
|---|---|---|
| Java | 24 | **21** (LTS) |
| Spring Boot | 3.5.0 | **4.0.9** |
| Spring Cloud | 2025.0.0 | **2025.1.4** (Boot 4.0.9 기준 릴리스 트레인) |
| Spring Framework / Security | 6.2 / 6.5 | 7.0.10 / 7.0.8 (Boot 관리) |
| Jackson | 2.x | **3.1** (Boot 관리) |
| Testcontainers | 1.x | **2.0.5** (Boot 관리) |
| springdoc-openapi | 2.8.6 | **3.0.3** |
| Resilience4j | 2.3.0 (`spring-boot3`) | **2.4.0** (`spring-boot4`) |
| datasource-micrometer | 1.0.0 | **2.2.1** |
| GraalVM Native Build Tools | 0.10.6 | **0.11.5** |
| Gradle 래퍼 | 8.14 | **8.14.6** |
| 도커 베이스 이미지 | `eclipse-temurin:24_36-jre-noble` | **`eclipse-temurin:21-jre-noble`** |

모든 버전과 패키지명은 각 프로젝트의 해당 릴리스 소스(Spring Boot v4.0.9 태그, Spring Cloud 2025.1.4 BOM, Spring Security 7.0.8, Jackson 3.1.7, Testcontainers 2.0.5 등)와 Spring Boot 4.0 공식 마이그레이션 가이드로 확인했습니다.

---

## 1. 빌드 (build.gradle)

**스타터 이름 변경**
- `spring-boot-starter-aop` → `spring-boot-starter-aspectj`
- `spring-boot-starter-oauth2-authorization-server` → `spring-boot-starter-security-oauth2-authorization-server`
- `spring-security-oauth2-resource-server` + `spring-security-oauth2-jose` → `spring-boot-starter-security-oauth2-resource-server`
  Boot 4에서는 `issuer-uri`로 `JwtDecoder`를 만드는 자동 구성이 별도 모듈에 있어, 시큐리티 jar만 두면 애플리케이션이 시작되지 않습니다.

**Boot 4 모듈화로 새로 필요한 의존성**
- `spring-boot-starter-webclient` (product-composite, gateway): `WebClient.Builder` 자동 구성과 추적 계측이 WebFlux 스타터에서 분리되었습니다.
- `spring-boot-starter-restclient` (유레카 클라이언트를 쓰는 모든 모듈): Spring Cloud Netflix 5 유레카 클라이언트의 기본 전송 방식이 `RestClient`입니다.
- 분산 추적: 브리지 jar만으로는 추적이 켜지지 않습니다.
  - 14~17장(OpenTelemetry): `spring-boot-micrometer-tracing-opentelemetry` + `spring-boot-zipkin` 추가
  - 18~23장(Brave): `zipkin-reporter-brave` → `spring-boot-starter-zipkin`
- 테스트 스타터: `spring-boot-starter-webflux-test`, `spring-boot-starter-data-mongodb-reactive-test`(6장은 `data-mongodb-test`), `spring-boot-starter-data-jpa-test`, `spring-boot-starter-webmvc-test`, `spring-boot-starter-security-test`, `spring-boot-resttestclient`/`spring-boot-restclient`

**기타**
- Testcontainers 2 아티팩트: `testcontainers-junit-jupiter`, `testcontainers-mongodb`, `testcontainers-mysql`
- spring-retry: Boot 4가 버전 관리를 중단했지만 Spring Cloud BOM이 2.0.13을 관리하므로 대부분 그대로 둡니다. BOM이 없는 17장 인가 서버만 `2.0.13`을 명시했습니다.

## 2. 자바 코드

| 원본 | 변경 후 |
|---|---|
| `com.fasterxml.jackson.databind.ObjectMapper`, `JsonNode` | `tools.jackson.databind.*` |
| `com.fasterxml.jackson.core.type.TypeReference` | `tools.jackson.core.type.TypeReference` |
| `com.fasterxml.jackson.core.JsonProcessingException` | `tools.jackson.core.JacksonException` |
| `com.fasterxml.jackson.databind.annotation.JsonSerialize` | `tools.jackson.databind.annotation.JsonSerialize` |
| `com.fasterxml.jackson.datatype.jsr310.ser.ZonedDateTimeSerializer` | `tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer` |
| `catch (IOException e)` (Jackson 호출) | `catch (JacksonException e)` |
| `org.springframework.boot.actuate.health.*` | `org.springframework.boot.health.contributor.*` |
| `org.springframework.boot.actuate.autoconfigure.observation.ObservationRegistryCustomizer` | `org.springframework.boot.micrometer.observation.autoconfigure.ObservationRegistryCustomizer` |
| `...oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer` | `org.springframework.security.config.annotation.web.configurers.oauth2.server.authorization.OAuth2AuthorizationServerConfigurer` |
| `...oauth2.server.authorization.config.annotation.web.configuration.OAuth2AuthorizationServerConfiguration` | `org.springframework.security.config.annotation.web.configuration.OAuth2AuthorizationServerConfiguration` |
| `org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest` | `org.springframework.boot.data.mongodb.test.autoconfigure.DataMongoTest` |
| `org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest` | `org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest` |
| `org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc` | `org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc` |
| `org.springframework.boot.test.web.client.TestRestTemplate` | `org.springframework.boot.resttestclient.TestRestTemplate` (+ `@AutoConfigureTestRestTemplate`) |
| `org.testcontainers.containers.MongoDBContainer` / `MySQLContainer` | `org.testcontainers.mongodb.MongoDBContainer` / `org.testcontainers.mysql.MySQLContainer` |

**꼭 알아야 할 동작 변화 두 가지**

1. **DTO의 `final` 필드 제거.** Jackson 3는 `MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS`가 기본값 `false`입니다. 교재의 `Event`, `HttpErrorInfo`, `ProductAggregate`, `RecommendationSummary`, `ReviewSummary`, `ServiceAddresses`(3~5장은 `Product`, `Recommendation`, `Review`도)는 "기본 생성자 + `private final` 필드 + getter" 구조라서, 그대로 두면 **예외 없이 빈 객체로 역직렬화**됩니다. 메시지 소비자가 `eventType == null` 오류를 내거나 POST 본문이 비는 식으로 나타납니다. 그래서 이 클래스들의 필드에서 `final`만 뺐습니다(JSON 형태는 같음).
2. **`@SpringBootTest`가 더 이상 `WebTestClient`/`TestRestTemplate`을 만들지 않습니다.** 해당 테스트 클래스에 `@AutoConfigureWebTestClient` 또는 `@AutoConfigureTestRestTemplate`을 붙였습니다.

이 밖에, Boot 4는 liveness/readiness 프로브가 기본으로 켜져 있어 `/actuator/health` 응답에 `"groups":["liveness","readiness"]`가 추가됩니다. 응답 전체를 문자열로 비교하던 유레카 서버 테스트는 `"status":"UP"` 포함 여부만 확인하도록 고쳤습니다.

## 3. 설정 (application.yml, config-repo, docker-compose, 헬름)

| 원본 | 변경 후 |
|---|---|
| `spring.data.mongodb.host/port/database` | `spring.mongodb.host/port/database` |
| `SPRING_DATA_MONGODB_USERNAME/PASSWORD/AUTHENTICATION_DATABASE` | `SPRING_MONGODB_USERNAME/PASSWORD/AUTHENTICATION_DATABASE` |
| `server.error.include-message` | `spring.web.error.include-message` |
| `management.zipkin.tracing.endpoint` | `management.tracing.export.zipkin.endpoint` |
| `management.endpoint.gateway.enabled: true` | `management.endpoint.gateway.access: unrestricted` |

헬스 그룹에 쓰는 기여자 이름(`mongo`, `rabbit`, `db`)과 `management.health.rabbit/kafka.enabled`는 바뀌지 않았습니다.

## 4. Dockerfile

```dockerfile
FROM eclipse-temurin:21-jre-noble AS builder
WORKDIR /builder
ADD ./build/libs/*.jar app.jar
RUN java -Djarmode=tools -jar app.jar extract --layers --launcher --destination extracted

FROM eclipse-temurin:21-jre-noble
WORKDIR /application
COPY --from=builder /builder/extracted/dependencies/ ./
COPY --from=builder /builder/extracted/spring-boot-loader/ ./
COPY --from=builder /builder/extracted/snapshot-dependencies/ ./
COPY --from=builder /builder/extracted/application/ ./
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

`layertools` 모드는 3.3부터 사용 중단 상태라 `tools extract --layers --launcher`로 바꿨습니다. 결과 디렉터리 구조와 진입점은 같습니다.

## 5. 23장 네이티브 컴파일

Spring Boot 4 네이티브 이미지는 **GraalVM 25 이상**이 필요합니다. 코드는 자바 21로 컴파일하되, `bootBuildImage`에서 빌드팩이 GraalVM(Liberica NIK) 25를 쓰도록 지정했습니다.

```groovy
tasks.named('bootBuildImage') {
    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
    ...
}
```

빌드팩 없이 로컬에서 `./gradlew nativeCompile`을 쓰려면 GraalVM 25를 설치하고 그 JDK로 Gradle을 실행해야 합니다(자바 21 툴체인을 그대로 찾으면 GraalVM 21이 선택됩니다).

## 6. 교재 본문과 다른 부분 (읽을 때 참고)

- 4장 Dockerfile 설명의 `layertools` 명령 → 위 4절의 `tools extract` 명령
- 6장 MongoDB 설정 키 → `spring.mongodb.*`
- 11장 인가 서버 설정 클래스의 import 경로 (위 2절 표)
- 12장 컨피그 클라이언트 재시도에 필요한 의존성 `spring-boot-starter-aop` → `spring-boot-starter-aspectj`
- 14장 이후 Zipkin 엔드포인트 키 → `management.tracing.export.zipkin.endpoint`, 추적 모듈 의존성 추가
- 각 장 테스트 코드의 Jackson 클래스는 `tools.jackson` 패키지

## 7. 검증한 것과 하지 못한 것

이 변환 작업 환경에서는 Maven Central에 접속할 수 없어 **Gradle 빌드와 테스트를 실제로 실행하지는 못했습니다.** 대신 다음을 확인했습니다.

- 변경된 자바 파일 418개 전부 `javac` 구문 검사 통과
- 자바 import 4,239개(스프링, Jackson 3, Testcontainers, Resilience4j, Micrometer, Brave 네임스페이스)를 대상 버전의 실제 클래스 목록과 대조 — 미해결 0개 (같은 검사를 원본 코드에 돌리면 옛 패키지 19종이 잡힘)
- YAML 파일 567개 파싱 오류 없음
- 바뀐 메서드 시그니처(예: `HttpHeaders`, `CompositeReactiveHealthContributor.fromMap`, `ReactiveIndexOperations.createIndex`, 인가 서버 `jwtDecoder`)를 대상 버전 소스에서 확인

처음 빌드할 때는 각 장에서 `./gradlew build`로 확인해 주세요. 남은 위험 요소는 실행해 봐야 드러나는 것들입니다. 예를 들어 유레카 서버 테스트의 `/eureka/apps` 응답 문자열 비교, 13장 Resilience4j 2.4.0의 동작, Spring Cloud Stream 5와 Jackson 3 조합에서의 메시지 형식 같은 부분입니다.
