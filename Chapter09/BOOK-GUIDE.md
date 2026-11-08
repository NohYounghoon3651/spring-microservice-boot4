# 9장 교재 대응 가이드 — 넷플릭스 유레카를 사용한 서비스 검색

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 9 "Adding Service Discovery Using Netflix Eureka" (p.225–244)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

유레카 서버·클라이언트 구성과 `@LoadBalanced` WebClient, 인스턴스를 늘리고 줄이며 확인하는 실습은 책과 같습니다. 책에 있던 유레카 버그 우회 코드가 필요 없어졌고, 명령은 `docker compose`를 씁니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Problems with the DNS-based approach (p.226–229) | `docker-compose up -d --scale review=2`, `docker-compose exec --index=1 review cat /etc/hosts` | `docker compose up -d --scale review=2`, `docker compose exec --index=1 review cat /etc/hosts` |
| Setting up a Netflix Eureka server (p.230–231) | Spring Cloud 2022.0.1의 버그(spring-cloud-netflix#4145) 우회용 `CustomErrorController` | 이 저장소의 `EurekaServerApplication`에는 **없습니다**. Spring Cloud 2025.1.4에서는 필요 없습니다 |
| Connecting microservices (p.231–233) | `spring-cloud-starter-netflix-eureka-client`, `@LoadBalanced WebClient.Builder` | 같습니다 |
| Setting up the configuration (p.233–236) | `eureka.client.serviceUrl.defaultZone: http://eureka:8761/eureka/` | 같은 키입니다. 이 저장소는 호스트 이름을 `app.eureka-server` 속성으로 빼서 `http://${app.eureka-server}:8761/eureka/`로 적고, `docker` 프로필에서 `app.eureka-server: eureka`로 바꿉니다 |
| Trying out the discovery service (p.236–241) | `./gradlew build && docker-compose build`, `docker-compose up -d --scale review=3` | `docker compose build`, `docker compose up -d --scale review=3` |
| Starting up the Eureka server again (p.241–242) | `--scale eureka=0`, `--scale eureka=1` | 같은 옵션으로 `docker compose up -d ...`. 학습 이슈 #231에서 이 실습을 다룹니다 |

## 참고

- 유레카 REST API를 `curl`과 `jq`로 조회하는 방법(p.238)과 유레카 웹 화면(`http://localhost:8761`)은 책과 같습니다.

## 더 보기

- 위키: [9장 넷플릭스 유레카를 사용한 서비스 검색](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/09장-넷플릭스-유레카를-사용한-서비스-검색)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter09)
- 학습 이슈: [#9](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/9)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
