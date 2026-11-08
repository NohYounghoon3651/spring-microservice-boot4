# 4장 교재 대응 가이드 — 도커를 사용한 배포

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 4 "Deploying Our Microservices Using Docker" (p.79–102)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

Dockerfile의 기본 이미지(Java 17 → 21)와 레이어 추출 방식, 런처 클래스 이름이 바뀌었고, 명령은 `docker compose`를 씁니다. 도커 컴포즈로 시스템을 띄우고 `test-em-all.bash`로 검증하는 흐름은 같습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Running Java in Docker (p.82–85) | `eclipse-temurin:17`로 CPU·메모리 확인 | 같은 실험을 `eclipse-temurin:21`로 하면 됩니다. 컨테이너 자원 제한을 인식하는 원리는 같습니다 |
| Dockerfile (p.86–88) | `FROM eclipse-temurin:17.0.5_8-jre-focal`, `java -Djarmode=layertools -jar app.jar extract` | `FROM eclipse-temurin:21-jre-noble`, **`java -Djarmode=tools -jar app.jar extract --layers --launcher --destination extracted`** |
| ENTRYPOINT (p.88) | `org.springframework.boot.loader.JarLauncher` | **`org.springframework.boot.loader.launch.JarLauncher`** (Boot 3.2부터 패키지 이동) |
| Using Docker with one microservice (p.88–92) | `docker build -t product-service .`, `docker run ... -e "SPRING_PROFILES_ACTIVE=docker"` | 같습니다 |
| Managing a landscape ... Docker Compose (p.92–97) | `docker-compose build`, `docker-compose up -d`, `docker-compose logs -f` | **`docker compose build`**, `docker compose up -d`, `docker compose logs -f` |
| Automating tests (p.97–101) | `./test-em-all.bash start stop` | 같습니다. 스크립트 안의 명령도 `docker compose`로 바뀌어 있습니다 |
| 문제 해결 (p.100–101) | `docker-compose up -d --scale product=1` | `docker compose up -d --scale product=1` |

## 참고

- 레이어 추출 결과 폴더는 책과 같이 `dependencies`, `spring-boot-loader`, `snapshot-dependencies`, `application` 네 개입니다.
- JRE 이미지 이름의 `noble`은 Ubuntu 24.04 기반이라는 뜻입니다. 책의 `focal`(20.04)과 같은 역할입니다.

## 더 보기

- 위키: [4장 도커를 사용한 배포](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/04장-도커를-사용한-배포)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter04)
- 학습 이슈: [#4](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/4)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
