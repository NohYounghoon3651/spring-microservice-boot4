# 13장 교재 대응 가이드 — Resilience4j를 사용한 탄력성 개선

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 13 "Improving Resilience Using Resilience4j" (p.323–348)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

서킷 브레이커·재시도·시간 제한 설정과 실습 시나리오는 책과 같습니다. Boot 4용 Resilience4j 모듈과 AOP 스타터 이름만 바꿔 읽으면 됩니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Adding the resilience mechanisms (p.329–334) | `resilience4jVersion = "2.0.2"`, `resilience4j-spring-boot3` | **`2.4.0`**, **`resilience4j-spring-boot4`** (BOM `resilience4j-bom`으로 버전 관리) |
| AOP 의존성 (p.333) | `spring-boot-starter-aop` | **`spring-boot-starter-aspectj`** (Boot 4에서 이름이 바뀜) |
| 애너테이션과 설정 (p.334–340) | `@CircuitBreaker`, `@Retry`, `@TimeLimiter`, `resilience4j.*` 설정 | 같습니다 |
| Trying out (p.340–346) | `docker-compose build`, `docker-compose exec product-composite curl ...` | `docker compose build`, `docker compose exec product-composite curl ...`. `delay`, `faultPercent` 파라미터로 하는 실습은 같습니다 |

## 참고

- 액추에이터의 `/actuator/health`, `/actuator/circuitbreakerevents`로 상태를 보는 방법(p.326, p.342–345)은 같습니다.

## 더 보기

- 위키: [13장 Resilience4j를 사용한 탄력성 개선](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/13장-Resilience4j를-사용한-탄력성-개선)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter13)
- 학습 이슈: [#13](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/13)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
