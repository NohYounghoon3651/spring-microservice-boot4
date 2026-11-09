# 13장 Resilience4j를 사용한 탄력성 개선

> 2부: 스프링 클라우드로 마이크로서비스 관리하기

← [12장 구성 중앙화](12장-구성-중앙화) | [목차](Home) | [14장 분산 추적](14장-분산-추적) →

## 학습 목표

- 회로 차단기, 시간 제한, 재시도를 product-composite에 적용한다
- 회로 차단기 상태(CLOSED → OPEN → HALF_OPEN)를 액추에이터로 관찰한다
- 폴백(fallback) 메서드로 장애 상황에서 응답을 제공한다

## 이 장의 기술

`Resilience4j 2.4.0 (spring-boot4)`, `Spring Boot Actuator`

## 실습 코드

- 코드: [`Chapter13`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter13)
- Boot 4 변경 내역: [`Chapter13/MIGRATION-BOOT4.md`](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter13/MIGRATION-BOOT4.md)
- 교재(영문 3판) 대응 가이드: [`Chapter13/BOOK-GUIDE.md`](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter13/BOOK-GUIDE.md) — 책의 쪽마다 이 저장소 코드와 다르게 읽어야 할 곳
- 손코딩 워크북: [`workbook/Chapter13.md`](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/workbook/Chapter13.md) — 이 장의 코드를 단계별로 직접 쳐서 완성

## 실행하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd Chapter13
./gradlew build
docker compose build
./test-em-all.bash start stop
```

**Kafka / 파티션 구성**

```bash
COMPOSE_FILE=docker-compose-kafka.yml ./test-em-all.bash start stop
COMPOSE_FILE=docker-compose-partitions.yml ./test-em-all.bash start stop
```

## 이전 장에서 달라진 점

`Chapter12` → `Chapter13` 비교 (코드에서 자동 추출)

- **새 의존성**: `io.github.resilience4j:resilience4j-reactor`, `io.github.resilience4j:resilience4j-spring-boot4`
- **파일**: 추가 0개 · 변경 9개 · 삭제 0개

많이 바뀐 파일:

- `test-em-all.bash` (62줄)
- `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java` (44줄)
- `microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java` (37줄)
- `config-repo/product-composite.yml` (34줄)
- `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java` (8줄)
- `api/src/main/java/se/magnus/api/core/product/ProductService.java` (7줄)

```bash
git diff --no-index --stat Chapter12 Chapter13   # 직접 비교
```

## 원본(Boot 3.5 / Java 24)과 달라진 점

- Spring Boot 3.5.0 → 4.0.9
- Java 24 → 21
- Spring Cloud 2025.0.0 → 2025.1.4
- Gradle 래퍼 8.14 → 8.14.6
- create-projects.bash
- 테스트 스타터 추가 (Boot 4 모듈화)
- `@AutoConfigureWebTestClient` 추가
- 테스트 애너테이션 패키지 변경
- TestRestTemplate 패키지 변경 및 `@AutoConfigureTestRestTemplate`
- 유레카 서버 헬스 테스트 수정
- Testcontainers 2.0
- Jackson 2 → Jackson 3
- `catch (IOException)` → `catch (JacksonException)`
- DTO 필드의 `final` 제거
- `server.error.*` → `spring.web.error.*`
- 원본 오타 수정
- MongoDB 프로퍼티 `spring.data.mongodb.*` → `spring.mongodb.*`
- springdoc-openapi 2.8.6 → 3.0.3
- Dockerfile: 베이스 이미지와 레이어 추출
- 헬스 API 패키지 변경
- `spring-boot-starter-webclient` 추가
- `spring-boot-starter-restclient` 추가 (유레카 클라이언트)
- 게이트웨이 액추에이터 엔드포인트
- OAuth2 리소스 서버 스타터
- 인가 서버 스타터 이름 변경
- 인가 서버 설정 클래스 패키지 변경
- 시큐리티 테스트 스타터
- `spring-boot-starter-aop` → `spring-boot-starter-aspectj`
- Resilience4j 2.3.0 → 2.4.0
- `HttpStatus.UNPROCESSABLE_ENTITY` → `UNPROCESSABLE_CONTENT`
- Jackson 3의 enum 직렬화
- StreamBridge 출력 바인딩을 기동 시점에 생성
- 실행 안정성 보강 (원본에도 있던 타이밍 문제)

## 복습 질문

**Q1. 회로 차단기가 OPEN일 때 호출은 어떻게 되나?**

<details><summary>답 보기</summary>

실제 호출을 하지 않고 바로 실패 처리되어 폴백 메서드가 응답을 만든다. 일정 시간 뒤 HALF_OPEN에서 시험 호출을 한다.

</details>

**Q2. 시간 제한과 재시도를 함께 쓸 때 주의할 점은?**

<details><summary>답 보기</summary>

재시도 횟수×대기 시간이 전체 응답 시간을 늘리고, 실패한 서비스에 부하를 더할 수 있으므로 회로 차단기와 함께 신중히 설정한다.

</details>

**Q3. 이 저장소에서 `circuitbreakerevents`의 상태 전환이 `CLOSED_TO_OPEN`으로 나오도록 한 설정은?**

<details><summary>답 보기</summary>

`spring.jackson.datatype.enum.write-enums-using-to-string: false`. Jackson 3는 기본으로 enum을 `toString()`으로 쓰기 때문이다.

</details>

## 학습 이슈

학습 이슈 [#13](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/13)의 하위 이슈(개념 · 코드 분석 · 실습 · 심화)를 순서대로 진행하며 닫아 가세요. 하위 이슈를 닫을 때마다 #13의 진행률이 올라갑니다.

← [12장 구성 중앙화](12장-구성-중앙화) | [목차](Home) | [14장 분산 추적](14장-분산-추적) →
