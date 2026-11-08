# 12장 교재 대응 가이드 — 구성 중앙화

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 12 "Centralized Configuration" (p.309–322)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

Config Server 쪽 구성(파일 기반 저장소, 암호화, 기본 인증)은 책과 같습니다. 다른 점은 **클라이언트가 Config Server에 접속하는 설정의 위치**입니다. 책은 `application.yml`의 `spring.config.import: "configserver:"`를 쓰지만, 이 저장소는 `bootstrap.yml`을 씁니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Setting up a config server (p.312–315) | `@EnableConfigServer`, 기본 인증, `ENCRYPT_KEY` | 같습니다. `.env`의 `CONFIG_SERVER_ENCRYPT_KEY`, `CONFIG_SERVER_USR`, `CONFIG_SERVER_PWD`도 같습니다 |
| Configuring clients of a config server (p.315–316) | `src/main/resources/application.yml`에 `spring.config.import: "configserver:"` | **`src/main/resources/bootstrap.yml`**에 같은 접속 정보(`spring.cloud.config.uri`, `username`, `password`, `failFast`, `retry`)를 둡니다. 이를 위해 `spring-cloud-starter-bootstrap` 의존성이 추가돼 있습니다 |
| 테스트에서 Config Server 끄기 (p.315) | `@DataMongoTest`·`@DataJpaTest`·`@SpringBootTest`에 `spring.cloud.config.enabled=false` | 같습니다. 애너테이션 패키지만 Boot 4의 모듈별 패키지로 바뀌었습니다(예: `org.springframework.boot.data.mongodb.test.autoconfigure.DataMongoTest`) |
| Structuring the configuration repository (p.316–317) | `config-repo/` 아래 서비스별 YAML | 같습니다. 단, 저장소 안의 MongoDB 설정 키는 `spring.mongodb.*`입니다(6장 참고) |
| Trying out the Spring Cloud Config Server (p.317–320) | `docker-compose build`, `/actuator/env`, `/encrypt`·`/decrypt` 호출 | `docker compose build`. 나머지 `curl` 명령은 같습니다 |

## 참고

- 두 방식 모두 서비스가 기동할 때 Config Server에서 설정을 받아옵니다. 책의 방식으로 바꿔 보고 싶다면 `bootstrap.yml` 내용을 `application.yml` 맨 위로 옮기고 `spring.config.import: "configserver:"`를 추가한 뒤 `spring-cloud-starter-bootstrap`을 빼면 됩니다.

## 더 보기

- 위키: [12장 구성 중앙화](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/12장-구성-중앙화)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter12)
- 학습 이슈: [#12](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/12)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
