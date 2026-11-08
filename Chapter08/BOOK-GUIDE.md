# 8장 교재 대응 가이드 — 스프링 클라우드 소개

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 8 "Introduction to Spring Cloud" (p.211–224)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

## 요약

스프링 클라우드 구성 요소를 소개하는 개념 장입니다. 각 구성 요소의 역할 설명은 그대로 유효하고, 바뀐 것은 버전과 일부 모듈 이름입니다. 이 장에는 실습 코드가 없습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| The evolution of Spring Cloud (p.211–213) | Spring Cloud 2022.0(Kilburn)까지의 역사 | 이 저장소는 **2025.1.4** 릴리스 트레인을 씁니다(Spring Boot 4.0 대응) |
| Using Netflix Eureka (p.213–214) | Eureka 서버·클라이언트 | 같습니다 |
| Using Spring Cloud Gateway (p.214–215) | Spring Cloud Gateway | 이제 **Spring Cloud Gateway Server WebFlux**라는 이름이고, 설정 키 접두사가 `spring.cloud.gateway.server.webflux.*`로 바뀌었습니다(10장) |
| Using Spring Cloud Config (p.215–217) | Config Server | 같습니다 |
| Using Resilience4j (p.217–219) | Resilience4j 2.0 | 2.4.0, Boot 4용 모듈 `resilience4j-spring-boot4` |
| Using Micrometer Tracing and Zipkin (p.220–223) | Micrometer Tracing + Zipkin | 같은 구조입니다. Boot 4는 추적 자동 구성을 `spring-boot-micrometer-tracing-*` 모듈로 나눴고, Zipkin 내보내기 설정 키가 `management.tracing.export.zipkin.endpoint`로 바뀌었습니다(14장) |

## 더 보기

- 위키: [8장 스프링 클라우드 소개](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/08장-스프링-클라우드-소개)
- 학습 이슈: [#8](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/8)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
