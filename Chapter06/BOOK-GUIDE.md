# 6장 교재 대응 가이드 — 영속성 추가

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 6 "Adding Persistence" (p.123–162)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

가장 많이 달라진 곳은 **Testcontainers 테스트 기반 클래스**입니다. `@DynamicPropertySource`로 접속 정보를 넘기던 방식이 Spring Boot의 `@ServiceConnection`으로 바뀌었고, Testcontainers 2.0에서 모듈 이름과 패키지가 바뀌었습니다. 데이터베이스 이미지 버전과 MongoDB 설정 키도 바뀌었습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Adding a persistence layer (p.125–131) | MapStruct `1.5.3.Final` | `1.6.3`. 엔티티·리포지터리·매퍼 코드는 같습니다 |
| Testcontainers 의존성 (p.127) | `platform('org.testcontainers:testcontainers-bom:1.15.2')`, `junit-jupiter`, `mongodb`, `mysql` | BOM 없이 Boot가 버전 관리. **`spring-boot-testcontainers`**, `testcontainers-junit-jupiter`, **`testcontainers-mongodb`**, **`testcontainers-mysql`** (2.0부터 모듈 이름에 `testcontainers-` 접두사) |
| 테스트 기반 클래스 (p.131–133) | `MySQLContainer("mysql:8.0.32")` + `@DynamicPropertySource`로 URL·계정 등록 | `MySqlTestBase`·`MongoDbTestBase`: 컨테이너 필드에 **`@ServiceConnection`**만 붙이면 Boot가 접속 정보를 자동으로 연결합니다. 패키지도 `org.testcontainers.mysql.MySQLContainer`, `org.testcontainers.mongodb.MongoDBContainer`로 바뀌었습니다 |
| 이미지 버전 (p.132, p.151) | `mysql:8.0.32`, `mongo:6.0.4` | **`mysql:9.2.0`**, **`mongo:8.0.5`** (테스트와 도커 컴포즈 모두) |
| JPA 테스트 (p.134) | `@AutoConfigureTestDatabase(replace = NONE)` | 필요 없습니다. `@ServiceConnection`으로 만든 연결은 내장 DB로 교체되지 않습니다. `@DataJpaTest`의 패키지는 `org.springframework.boot.data.jpa.test.autoconfigure`로 바뀌었습니다 |
| Using the persistence layer (p.139) | `spring.data.mongodb.host`, `spring.data.mongodb.port` | **`spring.mongodb.host`**, **`spring.mongodb.port`** |
| 에러 처리 (p.143) | `UNPROCESSABLE_ENTITY` | `UNPROCESSABLE_CONTENT` (3장 참고) |
| Adding databases to Docker Compose (p.150–153) | MongoDB 헬스체크 `mongo --eval 'db.stats().ok'`, `spring.data.mongodb:` | MongoDB 6.0부터 예전 `mongo` 셸이 빠져서 **`mongosh`**로 확인합니다. 설정 키는 `spring.mongodb:` |
| Manual tests (p.155–158) | `docker-compose ...` | `docker compose ...` |

## 그대로 따라 해도 되는 부분

- 낙관적 잠금 테스트, 페이징 테스트, `PersistenceTests` 흐름(p.135–138)
- 복합 서비스의 생성·삭제 API 확장(p.145–150)과 `test-em-all.bash` 갱신(p.158–160)

## 더 보기

- 위키: [6장 영속성 추가](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/06장-영속성-추가)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter06)
- 학습 이슈: [#6](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/6)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
