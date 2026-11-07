# 3장 협업 마이크로서비스 생성 — Spring Boot 4.0.9 / Java 21 변경 사항

이 장의 코드를 Spring Boot 3.5.0 / Java 24 / Spring Cloud 2025.0.0에서 **Spring Boot 4.0.9 / Java 21 / Spring Cloud 2025.1.4**로 옮기면서 바꾼 내용입니다. 전체 배경 설명은 저장소 최상위의 `MIGRATION-BOOT4.md`를 참고하세요.

변경 파일 수: build.gradle 10개, 자바 13개, 설정/스크립트 4개, Dockerfile 0개

## 1. Spring Boot 3.5.0 → 4.0.9

`org.springframework.boot` 플러그인과 `springBootVersion`(api/util의 BOM)을 4.0.9로 변경.

대상: `1-spring-init/microservices/product-composite-service/build.gradle`, `1-spring-init/microservices/product-service/build.gradle`, `1-spring-init/microservices/recommendation-service/build.gradle`, `1-spring-init/microservices/review-service/build.gradle`, `2-basic-rest-services/api/build.gradle`, `2-basic-rest-services/microservices/product-composite-service/build.gradle` 외 4개

## 2. Java 24 → 21

`JavaLanguageVersion.of(24)` → `of(21)`. 코드에 Java 22 이상 전용 문법/API는 없음을 확인함.

대상: `1-spring-init/microservices/product-composite-service/build.gradle`, `1-spring-init/microservices/product-service/build.gradle`, `1-spring-init/microservices/recommendation-service/build.gradle`, `1-spring-init/microservices/review-service/build.gradle`, `2-basic-rest-services/api/build.gradle`, `2-basic-rest-services/microservices/product-composite-service/build.gradle` 외 4개

## 3. Gradle 래퍼 8.14 → 8.14.6

Boot 4 Gradle 플러그인은 Gradle 8.14 이상(또는 9.x)이 필요. 8.14 최신 패치로 변경.

대상: `1-spring-init/gradle/wrapper/gradle-wrapper.properties`, `2-basic-rest-services/gradle/wrapper/gradle-wrapper.properties`

## 4. create-projects.bash

`spring init --boot-version=4.0.9 --java-version=21`로 변경.

대상: `1-spring-init/create-projects.bash`, `2-basic-rest-services/create-projects.bash`

## 5. 테스트 스타터 추가 (Boot 4 모듈화)

Boot 4는 테스트 인프라도 모듈로 분리됨. 테스트가 사용하는 기능에 맞춰 `spring-boot-starter-webflux-test`(WebTestClient), `spring-boot-starter-data-mongodb(-reactive)-test`(@DataMongoTest), `spring-boot-starter-data-jpa-test`(@DataJpaTest), `spring-boot-starter-webmvc-test`(MockMvc), `spring-boot-resttestclient`+`spring-boot-restclient`(TestRestTemplate)를 추가.

대상: `2-basic-rest-services/microservices/product-composite-service/build.gradle`, `2-basic-rest-services/microservices/product-service/build.gradle`, `2-basic-rest-services/microservices/recommendation-service/build.gradle`, `2-basic-rest-services/microservices/review-service/build.gradle`

## 6. `@AutoConfigureWebTestClient` 추가

Boot 4에서는 `@SpringBootTest`만으로 `WebTestClient` 빈이 만들어지지 않음. WebTestClient를 주입받는 테스트 클래스에 `@AutoConfigureWebTestClient`(`org.springframework.boot.webtestclient.autoconfigure`)를 추가.

대상: `2-basic-rest-services/microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java`, `2-basic-rest-services/microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java`, `2-basic-rest-services/microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java`, `2-basic-rest-services/microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java`

## 7. Jackson 2 → Jackson 3

Boot 4와 Spring Cloud Stream/Function 5는 Jackson 3를 사용. `com.fasterxml.jackson.databind/core` → `tools.jackson.*`, `JsonProcessingException` → `JacksonException`, `ZonedDateTimeSerializer` → `tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer`(Java Time 지원이 databind에 내장됨). 애너테이션 패키지 `com.fasterxml.jackson.annotation`은 그대로.

대상: `2-basic-rest-services/microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java`

## 8. `catch (IOException)` → `catch (JacksonException)`

Jackson 3의 `readValue()`는 checked 예외인 `IOException`을 던지지 않으므로(언체크 `JacksonException`) 그대로 두면 컴파일 오류.

대상: `2-basic-rest-services/microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java`

## 9. DTO 필드의 `final` 제거

Jackson 3는 `MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS`가 기본 비활성이라 `final` 필드를 역직렬화하지 못함(오류 없이 값이 비어 버림). `Event`, `HttpErrorInfo`, `ProductAggregate`, `*Summary`, `ServiceAddresses` 등 기본 생성자 + getter 구조의 DTO에서 `final`을 제거. 직렬화 형태(JSON)는 동일.

대상: `2-basic-rest-services/api/src/main/java/se/magnus/api/composite/product/ProductAggregate.java`, `2-basic-rest-services/api/src/main/java/se/magnus/api/composite/product/RecommendationSummary.java`, `2-basic-rest-services/api/src/main/java/se/magnus/api/composite/product/ReviewSummary.java`, `2-basic-rest-services/api/src/main/java/se/magnus/api/composite/product/ServiceAddresses.java`, `2-basic-rest-services/api/src/main/java/se/magnus/api/core/product/Product.java`, `2-basic-rest-services/api/src/main/java/se/magnus/api/core/recommendation/Recommendation.java` 외 2개

## 10. `server.error.*` → `spring.web.error.*`

`server.error.include-message: always` → `spring.web.error.include-message: always`.

대상: `2-basic-rest-services/microservices/product-composite-service/src/main/resources/application.yml`, `2-basic-rest-services/microservices/product-service/src/main/resources/application.yml`, `2-basic-rest-services/microservices/recommendation-service/src/main/resources/application.yml`, `2-basic-rest-services/microservices/review-service/src/main/resources/application.yml`

## 11. `HttpStatus.UNPROCESSABLE_ENTITY` → `UNPROCESSABLE_CONTENT`

Spring Framework 7에서 422 상수 이름이 바뀌었고, `HttpStatus.resolve(422)`는 새 상수를 반환합니다. 옛 상수를 쓰면 422 검사 테스트가 실패하고, 복합 서비스의 `switch` 분기가 매칭되지 않아 500 응답이 나갑니다. (GitHub Actions 빌드에서 발견)

대상: 자바 파일 6개
