# 10장 교재 대응 가이드 — 스프링 클라우드 게이트웨이를 에지 서버로 사용

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 10 "Using Spring Cloud Gateway to Hide Microservices behind an Edge Server" (p.245–262)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

게이트웨이의 라우팅 규칙 자체는 책과 같지만, Spring Cloud Gateway의 설정 키 접두사가 바뀌었습니다. 책의 `spring.cloud.gateway.routes`를 그대로 쓰면 라우트가 등록되지 않으니 꼭 바꿔 읽으세요.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Setting up Spring Cloud Gateway (p.247–249) | `spring-cloud-starter-gateway` | `spring-cloud-starter-gateway-server-webflux` (Spring Cloud 2025.0부터 이름이 바뀜) |
| Configuring routing rules (p.250–254) | **`spring.cloud.gateway.routes:`** | **`spring.cloud.gateway.server.webflux.routes:`**. 그 아래 `id`, `uri`, `predicates`, `filters` 작성법은 같습니다 |
| 프록시 헤더 | (책에 없음) | `spring.cloud.gateway.server.webflux.trusted-proxies: ".*"`. 2025년 보안 패치(CVE-2025-41235) 이후 `X-Forwarded-*` 헤더를 믿을 프록시를 명시해야 합니다. 운영 환경에서는 특정 IP 대역으로 좁히세요 |
| 액추에이터 `gateway` 엔드포인트 (p.255) | 노출만 하면 사용 가능 | Boot 4의 접근 제어 방식에 맞춰 `management.endpoint.gateway.access: unrestricted`를 함께 설정합니다 |
| Trying out the edge server (p.254–261) | `docker-compose build`, `docker-compose logs -f --tail=0 gateway` | `docker compose build`, `docker compose logs -f --tail=0 gateway` |
| Host 헤더 기반 라우팅 (p.259–261) | `/etc/hosts`에 `i.feel.lucky`, `im.a.teapot` 추가, `httpstat.us`로 전달 | 같습니다. 단, 외부 서비스 `httpstat.us`는 응답이 불안정할 때가 있어 이 실습이 실패해도 게이트웨이 설정 문제가 아닐 수 있습니다 |

## 참고

- Swagger UI를 게이트웨이 뒤에서 여는 설정(p.251)은 책과 같습니다.

## 더 보기

- 위키: [10장 스프링 클라우드 게이트웨이를 에지 서버로 사용](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/10장-스프링-클라우드-게이트웨이를-에지-서버로-사용)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter10)
- 학습 이슈: [#10](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/10)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
