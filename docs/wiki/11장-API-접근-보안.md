# 11장 API 접근 보안

> 2부: 스프링 클라우드로 마이크로서비스 관리하기

← [10장 스프링 클라우드 게이트웨이를 에지 서버로 사용](10장-스프링-클라우드-게이트웨이를-에지-서버로-사용) | [목차](Home) | [12장 구성 중앙화](12장-구성-중앙화) →

## 학습 목표

- HTTPS로 외부 통신을 암호화한다
- Spring Authorization Server(이제 Spring Security 7의 일부)로 OAuth 2.0 / OIDC 인가 서버를 만든다
- 게이트웨이와 product-composite를 리소스 서버로 보호하고 스코프 기반 권한을 적용한다
- 유레카 서버 접근을 HTTP Basic 인증으로 보호한다
- (선택) 외부 OpenID Connect 공급자(Auth0)로도 테스트해 본다

## 이 장의 기술

`Spring Security 7`, `OAuth 2.0 / OIDC`, `JWT`

## 실습 코드

- 코드: [`Chapter11`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter11)
- Boot 4 변경 내역: [`Chapter11/MIGRATION-BOOT4.md`](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter11/MIGRATION-BOOT4.md)
- 교재(영문 3판) 대응 가이드: [`Chapter11/BOOK-GUIDE.md`](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter11/BOOK-GUIDE.md) — 책의 쪽마다 이 저장소 코드와 다르게 읽어야 할 곳
- 손코딩 워크북: [`workbook/Chapter11.md`](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/workbook/Chapter11.md) — 이 장의 코드를 단계별로 직접 쳐서 완성

## 실행하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd Chapter11
./gradlew build
docker compose build
./test-em-all.bash start stop
```

**Kafka / 파티션 구성**

```bash
COMPOSE_FILE=docker-compose-kafka.yml ./test-em-all.bash start stop
COMPOSE_FILE=docker-compose-partitions.yml ./test-em-all.bash start stop
```

## 이전 장에서 달라진 점

`Chapter10` → `Chapter11` 비교 (코드에서 자동 추출)

- **새 모듈**: `spring-cloud/authorization-server`
- **새 의존성**: `org.htmlunit:htmlunit`, `org.springframework.boot:spring-boot-starter-security`, `org.springframework.boot:spring-boot-starter-security-oauth2-authorization-server`, `org.springframework.boot:spring-boot-starter-security-oauth2-resource-server`, `org.springframework.boot:spring-boot-starter-security-test`, `org.springframework.boot:spring-boot-starter-webmvc-test`
- **파일**: 추가 19개 · 변경 23개 · 삭제 0개

많이 바뀐 파일:

- `test-em-all.bash` (61줄)
- `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeServiceImpl.java` (57줄)
- `spring-cloud/gateway/src/main/resources/application.yml` (42줄)
- `microservices/product-composite-service/src/main/resources/application.yml` (25줄)
- `docker-compose-kafka.yml` (18줄)
- `docker-compose-partitions.yml` (18줄)

<details><summary>추가된 파일 목록</summary>

- `auth0/env.bash`
- `auth0/reset-tenant.bash`
- `auth0/setup-tenant.bash`
- `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/OpenApiConfig.java`
- `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/SecurityConfig.java`
- `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/TestSecurityConfig.java`
- `spring-cloud/authorization-server/Dockerfile`
- `spring-cloud/authorization-server/build.gradle`
- `spring-cloud/authorization-server/settings.gradle`
- `spring-cloud/authorization-server/src/main/java/sample/OAuth2AuthorizationServerApplication.java`
- `spring-cloud/authorization-server/src/main/java/sample/config/AuthorizationServerConfig.java`
- `spring-cloud/authorization-server/src/main/java/sample/config/DefaultSecurityConfig.java`
- `spring-cloud/authorization-server/src/main/java/sample/jose/Jwks.java`
- `spring-cloud/authorization-server/src/main/java/sample/jose/KeyGeneratorUtils.java`
- `spring-cloud/authorization-server/src/main/resources/application.yml`
- `spring-cloud/authorization-server/src/test/java/sample/OAuth2AuthorizationServerApplicationTests.java`
- `spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/SecurityConfig.java`
- `spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/SecurityConfig.java`
- `spring-cloud/gateway/src/main/resources/keystore/edge.p12`

</details>

```bash
git diff --no-index --stat Chapter10 Chapter11   # 직접 비교
```

## 원본(Boot 3.5 / Java 24)과 달라진 점

- Spring Boot 3.5.0 → 4.0.9
- Java 24 → 21
- Spring Cloud 2025.0.0 → 2025.1.4
- Gradle 래퍼 8.14 → 8.14.6
- create-projects.bash
- 테스트 스타터 추가 (Boot 4 모듈화)
- `@AutoConfigureWebTestClient` 추가
- 테스트 애너테이션 패키지 변경
- TestRestTemplate 패키지 변경 및 `@AutoConfigureTestRestTemplate`
- 유레카 서버 헬스 테스트 수정
- Testcontainers 2.0
- Jackson 2 → Jackson 3
- `catch (IOException)` → `catch (JacksonException)`
- DTO 필드의 `final` 제거
- `server.error.*` → `spring.web.error.*`
- MongoDB 프로퍼티 `spring.data.mongodb.*` → `spring.mongodb.*`
- springdoc-openapi 2.8.6 → 3.0.3
- Dockerfile: 베이스 이미지와 레이어 추출
- 헬스 API 패키지 변경
- `spring-boot-starter-webclient` 추가
- `spring-boot-starter-restclient` 추가 (유레카 클라이언트)
- 게이트웨이 액추에이터 엔드포인트
- OAuth2 리소스 서버 스타터
- 인가 서버 스타터 이름 변경
- 인가 서버 설정 클래스 패키지 변경
- 시큐리티 테스트 스타터
- `HttpStatus.UNPROCESSABLE_ENTITY` → `UNPROCESSABLE_CONTENT`
- StreamBridge 출력 바인딩을 기동 시점에 생성
- 실행 안정성 보강 (원본에도 있던 타이밍 문제)

## 복습 질문

**Q1. 접근 토큰의 스코프는 어디서 검사하나?**

<details><summary>답 보기</summary>

product-composite(리소스 서버)의 보안 설정에서 경로·메서드별로 `SCOPE_product:read` 같은 권한을 검사한다.

</details>

**Q2. Spring Boot 4에서 리소스 서버를 쓰려면 필요한 스타터는?**

<details><summary>답 보기</summary>

`spring-boot-starter-security-oauth2-resource-server`. 리소스 서버 자동 구성이 별도 모듈로 분리됐다.

</details>

**Q3. 스코프가 없는 토큰으로 쓰기 API를 호출하면?**

<details><summary>답 보기</summary>

인증은 되지만 권한이 없어 403 Forbidden을 받는다.

</details>

## 학습 이슈

학습 이슈 [#11](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/11)의 하위 이슈(개념 · 코드 분석 · 실습 · 심화)를 순서대로 진행하며 닫아 가세요. 하위 이슈를 닫을 때마다 #11의 진행률이 올라갑니다.

← [10장 스프링 클라우드 게이트웨이를 에지 서버로 사용](10장-스프링-클라우드-게이트웨이를-에지-서버로-사용) | [목차](Home) | [12장 구성 중앙화](12장-구성-중앙화) →
