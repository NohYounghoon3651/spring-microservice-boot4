# 5장 OpenAPI를 사용한 API 문서화

> 1부: 스프링 부트로 마이크로서비스 개발하기

← [4장 도커를 사용한 배포](04장-도커를-사용한-배포) | [목차](Home) | [6장 영속성 추가](06장-영속성-추가) →

## 학습 목표

- springdoc-openapi로 API 문서를 생성한다
- API 인터페이스에 OpenAPI 애너테이션을 추가하고 설명을 외부 설정으로 분리한다
- Swagger UI로 API를 직접 호출해 본다

## 이 장의 기술

`springdoc-openapi 3.0.3`, `Swagger UI`

## 실습 코드

- 코드: [`Chapter05`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter05)
- Boot 4 변경 내역: [`Chapter05/MIGRATION-BOOT4.md`](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter05/MIGRATION-BOOT4.md)

## 실행하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd Chapter05
./gradlew build
docker compose build
./test-em-all.bash start stop
```

## 이전 장에서 달라진 점

`Chapter04` → `Chapter05` 비교 (코드에서 자동 추출)

- **새 의존성**: `org.springdoc:springdoc-openapi-starter-common`, `org.springdoc:springdoc-openapi-starter-webflux-ui`
- **파일**: 추가 1개 · 변경 7개 · 삭제 0개

많이 바뀐 파일:

- `microservices/product-composite-service/src/main/resources/application.yml` (59줄)
- `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java` (42줄)
- `api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java` (14줄)
- `test-em-all.bash` (12줄)
- `util/src/main/java/se/magnus/util/http/GlobalControllerExceptionHandler.java` (10줄)
- `api/build.gradle` (1줄)

<details><summary>추가된 파일 목록</summary>

- `api/src/main/java/se/magnus/api/exceptions/BadRequestException.java`

</details>

```bash
git diff --no-index --stat Chapter04 Chapter05   # 직접 비교
```

## 원본(Boot 3.5 / Java 24)과 달라진 점

- Spring Boot 3.5.0 → 4.0.9
- Java 24 → 21
- Gradle 래퍼 8.14 → 8.14.6
- create-projects.bash
- 테스트 스타터 추가 (Boot 4 모듈화)
- `@AutoConfigureWebTestClient` 추가
- Jackson 2 → Jackson 3
- `catch (IOException)` → `catch (JacksonException)`
- DTO 필드의 `final` 제거
- `server.error.*` → `spring.web.error.*`
- springdoc-openapi 2.8.6 → 3.0.3
- Dockerfile: 베이스 이미지와 레이어 추출
- `HttpStatus.UNPROCESSABLE_ENTITY` → `UNPROCESSABLE_CONTENT`

## 복습 질문

**Q1. API 설명을 애너테이션에 직접 쓰지 않고 application.yml에 두는 이유는?**

<details><summary>답 보기</summary>

코드 변경 없이 문서를 고칠 수 있고, 긴 설명으로 코드가 지저분해지는 것을 막기 위해서다.

</details>

**Q2. Swagger UI는 어떤 경로로 열리나?**

<details><summary>답 보기</summary>

product-composite의 `/openapi/swagger-ui.html`(설정의 `springdoc.swagger-ui.path`).

</details>

## 학습 이슈

학습 이슈 [#5](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/5)의 하위 이슈(개념 · 코드 분석 · 실습 · 심화)를 순서대로 진행하며 닫아 가세요. 하위 이슈를 닫을 때마다 #5의 진행률이 올라갑니다.

← [4장 도커를 사용한 배포](04장-도커를-사용한-배포) | [목차](Home) | [6장 영속성 추가](06장-영속성-추가) →
