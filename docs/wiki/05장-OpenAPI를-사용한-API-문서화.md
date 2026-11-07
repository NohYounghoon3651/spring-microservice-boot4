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

## 학습 체크리스트

이 장의 체크리스트는 학습 이슈 [#5](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/5)에서 체크하며 진행하세요. 다 마치면 이슈를 닫으면 됩니다.

← [4장 도커를 사용한 배포](04장-도커를-사용한-배포) | [목차](Home) | [6장 영속성 추가](06장-영속성-추가) →
