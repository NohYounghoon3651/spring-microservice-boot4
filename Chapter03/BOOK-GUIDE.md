# 3장 교재 대응 가이드 — 협업 마이크로서비스 생성

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 3 "Creating a Set of Cooperating Microservices" (p.47–78)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

서비스 골격 생성 명령과 빌드 파일의 버전, 에러 처리에 쓰는 HTTP 상태 상수, 테스트의 목(mock) 애너테이션이 바뀌었습니다. REST API 구조, 복합 서비스, `test-em-all.bash` 흐름은 책과 같습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Generating skeleton microservices (p.50–51) | `spring init --boot-version=3.0.4` (Java 17) | `1-spring-init/create-projects.bash`: `--boot-version=4.0.9 --java-version=21`. start.spring.io가 이미 4.0.9를 내렸다면 가장 최신 4.0.x를 지정한 뒤 `build.gradle`의 버전을 4.0.9로 고쳐도 됩니다 |
| 빌드 파일 (p.53) | `org.springframework.boot` 3.0.4, `io.spring.dependency-management` 1.1.0 | 4.0.9, 1.1.7. 자바 툴체인 `JavaLanguageVersion.of(21)`. Gradle 래퍼 8.14.6 |
| 멀티 프로젝트 빌드 (p.54–55) | 서비스마다 `./gradlew build` 후 루트 `settings.gradle` 생성 | 같습니다 |
| api·util 프로젝트 (p.57) | `springBootVersion = '3.0.4'` | `springBootVersion = '4.0.9'` |
| Adding a composite microservice (p.61–68) | `RestTemplate`, Jackson `ObjectMapper` | `RestTemplate`은 그대로입니다. `ObjectMapper`는 Jackson 3의 `tools.jackson.databind.ObjectMapper`, 읽기 예외는 `JacksonException`(언체크 예외) |
| Adding error handling (p.68–69) | `@ResponseStatus(UNPROCESSABLE_ENTITY)`, `case UNPROCESSABLE_ENTITY` | **`UNPROCESSABLE_CONTENT`**. 상태 코드는 똑같이 422이고 상수 이름만 바뀌었습니다 |
| 에러 메시지 노출 | (책에 없음) | `spring.web.error.include-message: always`. Boot 4에서 `server.error.*` 키가 `spring.web.error.*`로 옮겨졌습니다 |
| Adding automated microservice tests in isolation (p.73–75) | `APPLICATION_JSON_UTF8`, `@MockBean` | **`APPLICATION_JSON`**, **`@MockitoBean`**(`org.springframework.test.context.bean.override.mockito`) |
| Adding semi-automated tests (p.76–78) | `test-em-all.bash` | 같습니다. 422 응답 검증도 그대로 통과합니다 |

## 그대로 따라 해도 되는 부분

- 서비스 기동(`java -jar microservices/*/build/libs/*.jar &`)과 `curl`로 수동 테스트하는 절차(p.70–72)
- `build/libs`에 실행 JAR과 plain JAR이 함께 생기는 이야기(p.61)

## 더 보기

- 위키: [3장 협업 마이크로서비스 생성](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/03장-협업-마이크로서비스-생성)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter03)
- 학습 이슈: [#3](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/3)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
