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

### 2-1. `HttpStatus.UNPROCESSABLE_ENTITY` → `HttpStatus.UNPROCESSABLE_CONTENT` (GitHub Actions 빌드로 발견)

Spring Framework 7은 422 상태 코드의 이름을 RFC 9110에 맞춰 `UNPROCESSABLE_CONTENT`로 바꾸고, `UNPROCESSABLE_ENTITY`는 사용 중단(deprecated)으로 남겼습니다. 둘 다 값은 422지만 `HttpStatus.resolve(422)`/`valueOf(422)`는 **새 상수**를 반환합니다. 그래서 옛 상수를 그대로 쓰면 다음 두 곳이 깨집니다.

- 테스트의 `expectStatus().isEqualTo(UNPROCESSABLE_ENTITY)`가 실패합니다(서로 다른 enum 상수).
- product-composite의 `switch (HttpStatus.resolve(...)) { case UNPROCESSABLE_ENTITY: ... }`가 실행 중에 매칭되지 않습니다. 이 경우 `InvalidInputException`으로 변환되지 않아, 422 대신 500 응답이 나갑니다.

모든 자바 코드(108개 파일)에서 `UNPROCESSABLE_CONTENT`로 바꿨습니다. 응답 본문의 `error` 값도 `"Unprocessable Entity"`에서 `"Unprocessable Content"`로 바뀝니다.

### 2-2. Jackson 3의 enum 직렬화 (13장 이후, test-em-all.bash로 발견)

Jackson 3는 `EnumFeature.WRITE_ENUMS_USING_TO_STRING`이 기본으로 켜져 있어, enum을 `name()`이 아닌 `toString()`으로 씁니다. Resilience4j의 `/actuator/circuitbreakerevents` 응답은 애플리케이션의 `JsonMapper`로 직렬화됩니다(Boot의 액추에이터 전용 매퍼는 `OperationResponseBody` 응답에만 적용됨). 그래서 `stateTransition` 값이 `CLOSED_TO_OPEN`에서 `State transition from CLOSED to OPEN`으로 바뀌었고, 서킷 브레이커 검증이 실패했습니다.

13~23장의 product-composite 설정(`config-repo/product-composite.yml`, 헬름 차트 안의 사본, 23장 `application.yml`)에 다음을 추가해 Jackson 2와 같은 출력으로 되돌렸습니다.

```yaml
spring.jackson.datatype.enum.write-enums-using-to-string: false
```

### 2-3. StreamBridge 출력 바인딩을 기동 시점에 생성 (7장 이후, Kafka 구성 E2E 테스트로 발견)

product-composite는 상품 하나를 만들 때 이벤트 3개(products, recommendations, reviews)를 `publish-pool` 스레드에서 병렬로 `StreamBridge.send()`합니다. `StreamBridge`는 출력 바인딩을 첫 전송 때 만들기 때문에, 바인딩 생성이 느린 Kafka 바인더에서는 가끔 아직 준비되지 않은 채널로 메시지가 보내집니다. 이때 `MessageDeliveryException: Dispatcher has no subscribers for channel`과 함께 500 응답이 납니다(같은 코드의 다른 장에서는 통과한, 타이밍에 따른 실패).

Spring Cloud Stream 문서의 방법대로 출력 바인딩을 기동 시점에 미리 만들도록 product-composite 설정에 다음을 추가했습니다.

```yaml
spring.cloud.stream.output-bindings: products-out-0;recommendations-out-0;reviews-out-0
```

이 밖에, Boot 4는 liveness/readiness 프로브가 기본으로 켜져 있어 `/actuator/health` 응답에 `"groups":["liveness","readiness"]`가 추가됩니다. 응답 전체를 문자열로 비교하던 유레카 서버 테스트는 `"status":"UP"` 포함 여부만 확인하도록 고쳤습니다.

### 2-4. CodeQL 알림 정리 (동작 변화 없음)

GitHub CodeQL 분석에서 나온 알림 가운데 코드를 고치는 편이 나은 것만 반영했습니다(#206).

- 11~23장 authorization-server의 `KeyGeneratorUtils`: `KeyGenerator.getInstance("HmacSha256")` → `"HmacSHA256"`. 자바의 알고리즘 이름은 대소문자를 구분하지 않아 같은 HMAC-SHA256이지만, CodeQL은 표준 표기만 안전한 알고리즘으로 인식합니다.
- 3·4·5장 product-composite의 `ProductCompositeIntegration`: `getProduct`·`getRecommendations`·`getReviews`에 `@Override` 추가(6장부터는 교재에도 있음).
- 7~23장 product-service의 `PersistenceTests`: `Integer` 버전 값을 `==`로 비교하던 것을 `Objects.equals`로 고침(#219). `==`는 객체 참조를 비교하므로 -128~127 범위를 벗어나면 같은 값이어도 다르다고 판정합니다. 지금은 버전이 작아 통과했던 잠재 버그입니다(교재 원본에도 있음).

CSRF 해제, `withDefaultPasswordEncoder` 같은 나머지 알림은 교재 예제의 의도라 그대로 두었습니다. 기준은 [CONTRIBUTING.md](CONTRIBUTING.md#codeql-알림-처리-기준)에 있습니다.

## 3. 설정 (application.yml, config-repo, docker-compose, 헬름)

| 원본 | 변경 후 |
|---|---|
| `spring.data.mongodb.host/port/database` | `spring.mongodb.host/port/database` |
| `SPRING_DATA_MONGODB_USERNAME/PASSWORD/AUTHENTICATION_DATABASE` | `SPRING_MONGODB_USERNAME/PASSWORD/AUTHENTICATION_DATABASE` |
| `server.error.include-message` | `spring.web.error.include-message` |
| `management.zipkin.tracing.endpoint` | `management.tracing.export.zipkin.endpoint` |
| `management.endpoint.gateway.enabled: true` | `management.endpoint.gateway.access: unrestricted` |

헬스 그룹에 쓰는 기여자 이름(`mongo`, `rabbit`, `db`)과 `management.health.rabbit/kafka.enabled`는 바뀌지 않았습니다.

### 3-1. 실행 안정성 보강 (교재 원본에도 있던 타이밍 문제)

전체 시스템 테스트를 여러 구성으로 반복 실행하자, 실행할 때마다 다른 곳에서 간헐적으로 실패하는 지점이 있었습니다. 모두 기동 순서나 비동기 처리 시간 때문이었고, 다음과 같이 보강했습니다.

- **Kafka 헬스체크** (7~20장, 23장 `docker-compose-kafka.yml`): Kafka 컨테이너에 `kafka-topics --list` 헬스체크를 추가했습니다. 의존 서비스는 `condition: service_healthy`로, 브로커가 준비된 뒤에 시작합니다. 전에는 컨테이너가 '시작'만 되면 서비스가 붙었습니다.
- **메시지 처리 대기** (7~20장, 23장 `test-em-all.bash`의 `testCompositeCreated`): 상품 1뿐 아니라 113(추천 없음), 213(리뷰 없음)의 메시지 처리도 기다립니다. Kafka에서는 컨슈머 그룹 재조정(rebalance) 중에 이 메시지들이 늦게 처리될 수 있습니다.
- **유레카 등록 대기** (9~15장 `test-em-all.bash`): 헬스체크가 통과한 직후에는 서비스 등록이 아직 끝나지 않았을 수 있습니다. 그래서 등록된 앱 수를 검사하기 전에 최대 60초 동안 기다립니다. 인스턴스가 많은 파티션 구성에서 실패했던 부분입니다.

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

## 7. 검증 결과

모든 검증은 이 저장소의 GitHub Actions 워크플로로 자동 실행됩니다(자바 21, Docker, `ubuntu-latest` 러너).

**`.github/workflows/build.yml`**

| 검증 | 범위 | 결과 |
|---|---|---|
| 빌드 + 단위·통합 테스트 (`./gradlew build`, Testcontainers 포함) | 19개 프로젝트 | 테스트 933개 통과, 실패·건너뜀 0 |
| 전체 시스템 테스트 `test-em-all.bash` (docker compose, RabbitMQ) | 3~23장 18개 | 검사 877개 통과 |
| 전체 시스템 테스트 — Kafka 구성 (`docker-compose-kafka.yml`) | 7~20장, 23장 | 14개 장 통과 |
| 전체 시스템 테스트 — 파티션 구성 (`docker-compose-partitions.yml`) | 7~20장, 23장 | 14개 장 통과 |
| 23장 네이티브 이미지 (GraalVM 25 빌드팩) + 시스템 테스트 | `docker-compose-native.yml`, `docker-compose-partitions-native.yml` | 통과 |

**`.github/workflows/kubernetes.yml`**

| 검증 | 범위 | 결과 |
|---|---|---|
| 헬름 차트 `helm lint` + `helm template` + `kubeconform` 스키마 검증 | 16~23장 헬름 환경 20개, 리소스 588개 | 모두 유효, 건너뜀 0 (Istio·cert-manager CRD 포함) |
| minikube 배포 + `test-em-all.bash` | 16장 (NodePort, Spring Cloud 인프라) | 검사 68개 통과 |
| minikube 배포 + `test-em-all.bash` | 17장 (Ingress, cert-manager) | 검사 65개 통과 |
| minikube + Istio 1.31 배포 + `test-em-all.bash` | 18·19·20·23장 (사이드카 주입, Istio 인그레스 게이트웨이) | 장마다 검사 65~66개 통과 |

컴파일 경고 가운데 사용 중단(deprecated) API 경고는 0건이고, Gradle 사용 중단 기능 경고도 0건입니다. 실행 로그에 남는 WARN은 의도된 것이거나 무해합니다. 테스트가 일부러 일으키는 오류(타임아웃, 폴백), 기동 순서에서 오는 일시적 경고, 원본에도 있던 경고(`withDefaultPasswordEncoder`), springdoc 3의 안내 메시지가 여기에 해당합니다. Micrometer의 "MeterFilter is being configured after a Meter has been registered" 경고도 14장 이후 장마다 한 번씩 나오는데, 정보성 경고라 동작에 영향은 없습니다.

**검증 범위 밖**: 19장 이후의 EFK 로깅 스택(Elasticsearch·Fluentd·Kibana) 설치와, 18장 이후의 무중단 배포·라우팅 실습 스크립트(`kubernetes/routing-tests`, `resilience-tests`)는 CI에서 실행하지 않았습니다. 이 실습들이 쓰는 애플리케이션과 헬름 차트는 위 검증에 포함되어 있습니다.

변환 초기에는 오프라인으로도 확인했습니다. 변경된 자바 파일의 `javac` 구문 검사, import 4,239개를 대상 버전의 실제 클래스 목록과 대조, YAML 567개 파싱 검사입니다.
