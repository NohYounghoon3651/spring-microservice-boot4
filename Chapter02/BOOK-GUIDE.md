# 2장 교재 대응 가이드 — 스프링 부트 소개

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 2 "Introduction to Spring Boot" (p.27–46)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

## 요약

스프링 부트, WebFlux, springdoc-openapi, Spring Data, Spring Cloud Stream, 도커를 소개하는 장입니다. 개념 설명은 그대로 유효하지만, 짧은 코드 예시 중 일부는 Spring Boot 4에서 이름이나 방식이 바뀌었습니다. 이 장에는 실습 코드가 없습니다.

## 절별 대응

| 교재 위치 | 교재 내용 | 이 저장소(Boot 4.0.9) 기준 |
|---|---|---|
| Technical requirements (p.28) | Java 17, Spring Boot 3.0 | Java 21, Spring Boot 4.0.9 (Jakarta EE 11 기반) |
| Spring Boot (p.28–34) | 스타터 의존성, `@SpringBootApplication`, 설정 파일 | 개념은 같습니다. Boot 4는 자동 구성을 기술별 모듈로 나눠서 스타터 이름이 일부 바뀌었습니다. 예: AOP는 `spring-boot-starter-aspectj`, OAuth2 리소스 서버는 `spring-boot-starter-security-oauth2-resource-server`, 테스트는 기술별 테스트 스타터 |
| Spring WebFlux (p.34–36) | `spring-boot-starter-web`에서 톰캣을 빼고 네티로 바꾸는 예 | Boot 4에서 Spring MVC 스타터는 `spring-boot-starter-webmvc`로 이름이 바뀌었습니다(기존 이름은 폐기 예정). 이 저장소는 처음부터 `spring-boot-starter-webflux`를 써서 네티로 실행합니다 |
| springdoc-openapi (p.36–38) | springdoc-openapi 2.x | 3.0.3 (Boot 4 지원판). 사용하는 애너테이션은 같습니다 |
| Spring Data (p.38–41) | JPA 엔티티, `@IdClass`, MongoDB 문서 | 개념은 같습니다. JPA는 Hibernate 7, MongoDB 연결 설정 키는 `spring.data.mongodb.*`에서 **`spring.mongodb.*`**로 바뀌었습니다 |
| Spring Cloud Stream (p.41–43) | 오래된 애너테이션 방식(`@EnableBinding`, `@Output`, `@StreamListener`) 소개 | 이 애너테이션들은 Spring Cloud Stream 4부터 **삭제**되었습니다. 이 저장소는 함수형 방식(`Consumer`/`Supplier` 빈 + `StreamBridge`)만 씁니다 |
| Docker (p.43–46) | `docker-compose` 명령 | Docker Compose v2의 **`docker compose`**(하이픈 없음) |

## 함께 알아 둘 것

- JSON 처리는 Jackson 3(`tools.jackson.*` 패키지)입니다. 책의 `com.fasterxml.jackson.databind.ObjectMapper` 같은 import는 이 저장소에서 `tools.jackson.databind.ObjectMapper`입니다. 애너테이션(`com.fasterxml.jackson.annotation.*`)은 그대로입니다.
- 테스트에서 목 빈을 등록하는 `@MockBean`은 Boot 4에서 삭제되어 `@MockitoBean`을 씁니다(3장 참고).

## 더 보기

- 위키: [2장 스프링 부트 소개](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/02장-스프링-부트-소개)
- 학습 이슈: [#2](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/2)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
