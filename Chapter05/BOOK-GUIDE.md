# 5장 교재 대응 가이드 — OpenAPI를 사용한 API 문서화

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 5 "Adding an API Description Using OpenAPI" (p.103–122)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

springdoc-openapi 버전이 2.0.2에서 3.0.3으로 올라가며 생성되는 OpenAPI 문서 버전이 3.1.0이 됐습니다. 설정 키, Swagger UI 경로, API 애너테이션 사용법은 책과 같습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Adding springdoc-openapi to the source code (p.106–107) | `springdoc-openapi-starter-common:2.0.2`, `springdoc-openapi-starter-webflux-ui:2.0.2` | 둘 다 **3.0.3** |
| 설정 (p.109) | `springdoc.swagger-ui.path`, `springdoc.api-docs.path` | 같은 키입니다. 이 저장소는 YAML을 중첩해서 `springdoc:` 아래 `api-docs.path: /openapi/v3/api-docs`, `swagger-ui.path: /openapi/swagger-ui.html`로 적었습니다 |
| API 애너테이션 (p.109–112) | `@Tag`, `@Operation`, `@ApiResponses` | 같습니다 |
| Building and starting (p.112) | `./gradlew build && docker-compose build && docker-compose up -d` | `./gradlew build && docker compose build && docker compose up -d` |
| test-em-all.bash (p.113) | OpenAPI 문서 버전 `3.0.1` 확인 | **`3.1.0`** 확인 (springdoc 3이 OpenAPI 3.1로 문서를 만듦) |
| Trying out the OpenAPI documentation (p.114–120) | Swagger UI 화면 | 주소(`http://localhost:8080/openapi/swagger-ui.html`)와 사용법은 같습니다. Swagger UI 버전이 올라 화면 모양은 조금 다를 수 있습니다 |

## 참고

- SpringFox와 `@ApiOperation` 이야기(p.104, p.115)는 배경 설명이라 그대로 읽으면 됩니다.

## 더 보기

- 위키: [5장 OpenAPI를 사용한 API 문서화](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/05장-OpenAPI를-사용한-API-문서화)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter05)
- 학습 이슈: [#5](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/5)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
