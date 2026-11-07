# 17장 쿠버네티스 기능으로 시스템 환경 단순화 — Spring Boot 4.0.9 / Java 21 변경 사항

이 장의 코드를 Spring Boot 3.5.0 / Java 24 / Spring Cloud 2025.0.0에서 **Spring Boot 4.0.9 / Java 21 / Spring Cloud 2025.1.4**로 옮기면서 바꾼 내용입니다. 전체 배경 설명은 저장소 최상위의 `MIGRATION-BOOT4.md`를 참고하세요.

변경 파일 수: build.gradle 8개, 자바 24개, 설정/스크립트 26개, Dockerfile 6개

## 1. Spring Boot 3.5.0 → 4.0.9

`org.springframework.boot` 플러그인과 `springBootVersion`(api/util의 BOM)을 4.0.9로 변경.

대상: `api/build.gradle`, `microservices/product-composite-service/build.gradle`, `microservices/product-service/build.gradle`, `microservices/recommendation-service/build.gradle`, `microservices/review-service/build.gradle`, `spring-cloud/authorization-server/build.gradle` 외 2개

## 2. Java 24 → 21

`JavaLanguageVersion.of(24)` → `of(21)`. 코드에 Java 22 이상 전용 문법/API는 없음을 확인함.

대상: `api/build.gradle`, `microservices/product-composite-service/build.gradle`, `microservices/product-service/build.gradle`, `microservices/recommendation-service/build.gradle`, `microservices/review-service/build.gradle`, `spring-cloud/authorization-server/build.gradle` 외 2개

## 3. Spring Cloud 2025.0.0 → 2025.1.4

Spring Cloud 2025.1.4는 Spring Boot 4.0.9를 기준으로 빌드된 릴리스 트레인.

대상: `microservices/product-composite-service/build.gradle`, `microservices/product-service/build.gradle`, `microservices/recommendation-service/build.gradle`, `microservices/review-service/build.gradle`, `spring-cloud/gateway/build.gradle`

## 4. Gradle 래퍼 8.14 → 8.14.6

Boot 4 Gradle 플러그인은 Gradle 8.14 이상(또는 9.x)이 필요. 8.14 최신 패치로 변경.

대상: `gradle/wrapper/gradle-wrapper.properties`

## 5. create-projects.bash

`spring init --boot-version=4.0.9 --java-version=21`로 변경.

대상: `create-projects.bash`

## 6. 테스트 스타터 추가 (Boot 4 모듈화)

Boot 4는 테스트 인프라도 모듈로 분리됨. 테스트가 사용하는 기능에 맞춰 `spring-boot-starter-webflux-test`(WebTestClient), `spring-boot-starter-data-mongodb(-reactive)-test`(@DataMongoTest), `spring-boot-starter-data-jpa-test`(@DataJpaTest), `spring-boot-starter-webmvc-test`(MockMvc), `spring-boot-resttestclient`+`spring-boot-restclient`(TestRestTemplate)를 추가.

대상: `microservices/product-composite-service/build.gradle`, `microservices/product-service/build.gradle`, `microservices/recommendation-service/build.gradle`, `microservices/review-service/build.gradle`, `spring-cloud/authorization-server/build.gradle`

## 7. `@AutoConfigureWebTestClient` 추가

Boot 4에서는 `@SpringBootTest`만으로 `WebTestClient` 빈이 만들어지지 않음. WebTestClient를 주입받는 테스트 클래스에 `@AutoConfigureWebTestClient`(`org.springframework.boot.webtestclient.autoconfigure`)를 추가.

대상: `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/MessagingTests.java`, `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java`, `microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java`, `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java`, `microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java`

## 8. 테스트 애너테이션 패키지 변경

`@DataMongoTest` → `org.springframework.boot.data.mongodb.test.autoconfigure`, `@DataJpaTest` → `org.springframework.boot.data.jpa.test.autoconfigure`, `@AutoConfigureMockMvc` → `org.springframework.boot.webmvc.test.autoconfigure`.

대상: `microservices/product-service/src/test/java/se/magnus/microservices/core/product/PersistenceTests.java`, `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/PersistenceTests.java`, `microservices/review-service/src/test/java/se/magnus/microservices/core/review/PersistenceTests.java`, `spring-cloud/authorization-server/src/test/java/sample/OAuth2AuthorizationServerApplicationTests.java`

## 9. Testcontainers 2.0

아티팩트명 변경(`junit-jupiter` → `testcontainers-junit-jupiter`, `mongodb` → `testcontainers-mongodb`, `mysql` → `testcontainers-mysql`), 클래스 패키지 변경(`org.testcontainers.mongodb.MongoDBContainer`, `org.testcontainers.mysql.MySQLContainer`).

대상: `microservices/product-service/build.gradle`, `microservices/product-service/src/test/java/se/magnus/microservices/core/product/MongoDbTestBase.java`, `microservices/recommendation-service/build.gradle`, `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MongoDbTestBase.java`, `microservices/review-service/build.gradle`, `microservices/review-service/src/test/java/se/magnus/microservices/core/review/MySqlTestBase.java`

## 10. Jackson 2 → Jackson 3

Boot 4와 Spring Cloud Stream/Function 5는 Jackson 3를 사용. `com.fasterxml.jackson.databind/core` → `tools.jackson.*`, `JsonProcessingException` → `JacksonException`, `ZonedDateTimeSerializer` → `tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer`(Java Time 지원이 databind에 내장됨). 애너테이션 패키지 `com.fasterxml.jackson.annotation`은 그대로.

대상: `api/src/main/java/se/magnus/api/event/Event.java`, `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java`, `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/IsSameEvent.java`, `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/IsSameEventTests.java`

## 11. `catch (IOException)` → `catch (JacksonException)`

Jackson 3의 `readValue()`는 checked 예외인 `IOException`을 던지지 않으므로(언체크 `JacksonException`) 그대로 두면 컴파일 오류.

대상: `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java`, `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/IsSameEvent.java`

## 12. DTO 필드의 `final` 제거

Jackson 3는 `MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS`가 기본 비활성이라 `final` 필드를 역직렬화하지 못함(오류 없이 값이 비어 버림). `Event`, `HttpErrorInfo`, `ProductAggregate`, `*Summary`, `ServiceAddresses` 등 기본 생성자 + getter 구조의 DTO에서 `final`을 제거. 직렬화 형태(JSON)는 동일.

대상: `api/src/main/java/se/magnus/api/composite/product/ProductAggregate.java`, `api/src/main/java/se/magnus/api/composite/product/RecommendationSummary.java`, `api/src/main/java/se/magnus/api/composite/product/ReviewSummary.java`, `api/src/main/java/se/magnus/api/composite/product/ServiceAddresses.java`, `api/src/main/java/se/magnus/api/event/Event.java`, `util/src/main/java/se/magnus/util/http/HttpErrorInfo.java`

## 13. `server.error.*` → `spring.web.error.*`

`server.error.include-message: always` → `spring.web.error.include-message: always`.

대상: `config-repo/product-composite.yml`, `config-repo/product.yml`, `config-repo/recommendation.yml`, `config-repo/review.yml`, `kubernetes/helm/components/product-composite/config-repo/product-composite.yml`, `kubernetes/helm/components/product/config-repo/product.yml` 외 6개

## 14. 원본 오타 수정

`authorization-server/src/test/resources/application.yml`의 `ml.server.error.include-message`(원본의 오타로 효과 없던 키)를 `spring.web.error.include-message`로 수정.

대상: `spring-cloud/authorization-server/src/test/resources/application.yml`

## 15. MongoDB 프로퍼티 `spring.data.mongodb.*` → `spring.mongodb.*`

`host`, `port`, `database`, `username`, `password`, `authentication-database`가 `spring.mongodb.*`로 이동. 환경 변수도 `SPRING_DATA_MONGODB_*` → `SPRING_MONGODB_*`(docker-compose, 헬름 values 포함). `ProductServiceApplication` 등의 시작 로그용 `getProperty("spring.data.mongodb.host")`도 변경.

대상: `config-repo/product.yml`, `config-repo/recommendation.yml`, `docker-compose-kafka.yml`, `docker-compose-partitions.yml`, `docker-compose.yml`, `kubernetes/helm/components/product/config-repo/product.yml` 외 5개

## 16. springdoc-openapi 2.8.6 → 3.0.3

springdoc 3.x가 Boot 4용. 3.1 이상은 Boot 4.1 기준이라 Boot 4.0.x에 맞는 3.0.3을 선택.

대상: `api/build.gradle`, `microservices/product-composite-service/build.gradle`

## 17. Dockerfile: 베이스 이미지와 레이어 추출

`eclipse-temurin:24_36-jre-noble` → `eclipse-temurin:21-jre-noble`. 사용 중단된 `-Djarmode=layertools` 대신 `-Djarmode=tools -jar app.jar extract --layers --launcher --destination extracted` 사용(디렉터리 구조와 `JarLauncher` 진입점은 동일).

대상: `microservices/product-composite-service/Dockerfile`, `microservices/product-service/Dockerfile`, `microservices/recommendation-service/Dockerfile`, `microservices/review-service/Dockerfile`, `spring-cloud/authorization-server/Dockerfile`, `spring-cloud/gateway/Dockerfile`

## 18. 헬스 API 패키지 변경

`org.springframework.boot.actuate.health.*` → `org.springframework.boot.health.contributor.*` (`Health`, `ReactiveHealthIndicator`, `ReactiveHealthContributor`, `CompositeReactiveHealthContributor`).

대상: `spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/HealthCheckConfiguration.java`

## 19. `spring-boot-starter-webclient` 추가

Boot 4에서 `WebClient.Builder` 자동 구성(관찰/추적 계측 포함)은 `spring-boot-webclient` 모듈로 분리되어 `spring-boot-starter-webflux`에 포함되지 않음. `WebClient`를 사용하는 product-composite와 gateway에 추가.

대상: `microservices/product-composite-service/build.gradle`, `spring-cloud/gateway/build.gradle`

## 20. 게이트웨이 액추에이터 엔드포인트

사용 중단된 `management.endpoint.gateway.enabled: true` → `management.endpoint.gateway.access: unrestricted`.

대상: `config-repo/gateway.yml`

## 21. OAuth2 리소스 서버 스타터

`spring-security-oauth2-resource-server` + `spring-security-oauth2-jose` → `spring-boot-starter-security-oauth2-resource-server`. Boot 4에서는 리소스 서버 자동 구성(`issuer-uri`로 JwtDecoder 생성)이 별도 모듈에 있어 스프링 시큐리티 jar만으로는 동작하지 않음.

대상: `microservices/product-composite-service/build.gradle`, `spring-cloud/gateway/build.gradle`

## 22. 인가 서버 스타터 이름 변경

`spring-boot-starter-oauth2-authorization-server` → `spring-boot-starter-security-oauth2-authorization-server`.

대상: `spring-cloud/authorization-server/build.gradle`

## 23. 인가 서버 설정 클래스 패키지 변경

Spring Authorization Server가 Spring Security 7에 통합됨. `OAuth2AuthorizationServerConfigurer` → `org.springframework.security.config.annotation.web.configurers.oauth2.server.authorization`, `OAuth2AuthorizationServerConfiguration` → `org.springframework.security.config.annotation.web.configuration`. 설정 코드 자체(`new OAuth2AuthorizationServerConfigurer()`, `http.with(...)`, `jwtDecoder(...)`)는 그대로 사용 가능.

대상: `spring-cloud/authorization-server/src/main/java/sample/config/AuthorizationServerConfig.java`

## 24. 시큐리티 테스트 스타터

`spring-security-test` → `spring-boot-starter-security-test`.

대상: `spring-cloud/authorization-server/build.gradle`

## 25. `spring-boot-starter-aop` → `spring-boot-starter-aspectj`

Boot 4에서 스타터 이름 변경. Resilience4j 애너테이션과 컨피그 클라이언트 재시도(spring-retry)에 필요.

대상: `microservices/product-composite-service/build.gradle`

## 26. spring-retry 버전 명시

Boot 4는 spring-retry 버전 관리를 제거함. Spring Cloud BOM을 쓰지 않는 모듈이라 `2.0.13`(Spring Cloud 2025.1.4가 관리하는 버전)을 명시.

대상: `spring-cloud/authorization-server/build.gradle`

## 27. Resilience4j 2.3.0 → 2.4.0

`resilience4j-spring-boot3` → `resilience4j-spring-boot4`.

대상: `microservices/product-composite-service/build.gradle`

## 28. `ObservationRegistryCustomizer` 패키지 변경

→ `org.springframework.boot.micrometer.observation.autoconfigure.ObservationRegistryCustomizer`.

대상: `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/tracing/ObservationRegistryConfig.java`

## 29. 분산 추적(OpenTelemetry + Zipkin) 의존성

Boot 4에서 추적 자동 구성이 액추에이터에서 분리됨. 브리지/익스포터 jar만으로는 추적이 활성화되지 않으므로 `spring-boot-micrometer-tracing-opentelemetry`와 `spring-boot-zipkin` 모듈을 추가.

대상: `microservices/product-composite-service/build.gradle`, `microservices/product-service/build.gradle`, `microservices/recommendation-service/build.gradle`, `microservices/review-service/build.gradle`, `spring-cloud/authorization-server/build.gradle`, `spring-cloud/gateway/build.gradle`

## 30. Zipkin 프로퍼티 이름 변경

`management.zipkin.tracing.endpoint` → `management.tracing.export.zipkin.endpoint`.

대상: `config-repo/application.yml`, `kubernetes/helm/components/auth-server/config-repo/application.yml`, `kubernetes/helm/components/product-composite/config-repo/application.yml`, `kubernetes/helm/components/product/config-repo/application.yml`, `kubernetes/helm/components/recommendation/config-repo/application.yml`, `kubernetes/helm/components/review/config-repo/application.yml`

## 31. datasource-micrometer 1.0.0 → 2.2.1

2.x가 Boot 4용(2.2.1은 Boot 4.0.x 기준).

대상: `microservices/review-service/build.gradle`

## 32. `HttpStatus.UNPROCESSABLE_ENTITY` → `UNPROCESSABLE_CONTENT`

Spring Framework 7에서 422 상수 이름이 바뀌었고, `HttpStatus.resolve(422)`는 새 상수를 반환합니다. 옛 상수를 쓰면 422 검사 테스트가 실패하고, 복합 서비스의 `switch` 분기가 매칭되지 않아 500 응답이 나갑니다. (GitHub Actions 빌드에서 발견)

대상: 자바 파일 6개
