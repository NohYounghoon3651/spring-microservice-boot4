# 11장 교재 대응 가이드 — API 접근 보안

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 11 "Securing Access to APIs" (p.263–308)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

OAuth 2.0 / OIDC 개념과 실습 흐름은 같지만, **보안 설정 코드의 작성법(람다 DSL)**, HTTPS 인증서 설정 방식(SSL 번들), 의존성 이름이 바뀌었습니다. 책의 코드 조각을 그대로 붙여 넣으면 컴파일되지 않는 곳이 많으니 저장소 코드를 기준으로 보세요.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Protecting external communication with HTTPS (p.269–270) | `server.ssl.key-store`, `key-store-password`, `key-store-type`, `key-alias` | **SSL 번들**: `spring.ssl.bundle.jks.gateway.keystore.location/password/type`, `spring.ssl.bundle.jks.gateway.key.alias`를 정의하고 `server.ssl.bundle: gateway`로 연결합니다. `keytool`로 `edge.p12`를 만드는 명령은 같습니다 |
| 런타임에 인증서 바꾸기 (p.271–272) | 환경 변수 `SERVER_SSL_KEY_STORE`, `SERVER_SSL_KEY_STORE_PASSWORD` | SSL 번들 키를 환경 변수로 쓰면 `SPRING_SSL_BUNDLE_JKS_GATEWAY_KEYSTORE_LOCATION=file:/keystore/edge-test.p12`, `SPRING_SSL_BUNDLE_JKS_GATEWAY_KEYSTORE_PASSWORD=testtest`입니다. 볼륨 마운트와 `docker compose up -d --scale gateway=0/1` 절차는 같습니다 |
| Securing access to the discovery server (p.272–274) | `.authorizeRequests()...and().httpBasic()` 체이닝 | `SecurityFilterChain` 빈에서 **람다 DSL**: `.csrf(csrf -> csrf.disable())`, `.authorizeHttpRequests(r -> r.anyRequest().authenticated())`, `.httpBasic(Customizer.withDefaults())`. 람다 없이 `and()`로 잇는 방식은 Spring Security 7에서 삭제됐습니다 |
| 테스트의 `TestRestTemplate` (p.274) | Boot 3의 `TestRestTemplate`을 주입해 유레카 서버 테스트 | **`org.springframework.boot.resttestclient.TestRestTemplate`** + 테스트 클래스에 `@AutoConfigureTestRestTemplate` |
| Adding a local authorization server (p.274–276) | Spring Authorization Server 1.0 | Spring Authorization Server가 **Spring Security 7에 합쳐졌고**, 스타터 `spring-boot-starter-security-oauth2-authorization-server`를 씁니다 |
| Swagger UI 리다이렉트 URI (p.275) | `https://localhost:8443/webjars/swagger-ui/oauth2-redirect.html` | `https://localhost:8443/openapi/swagger-ui/oauth2-redirect.html` |
| Protecting APIs (p.276–282) | `spring-security-oauth2-resource-server`, `spring-security-oauth2-jose` | 스타터 하나: **`spring-boot-starter-security-oauth2-resource-server`** |
| 게이트웨이·product-composite 보안 설정 (p.277–279) | `.authorizeExchange().pathMatchers(...)...and().oauth2ResourceServer().jwt()`, `http.csrf().disable()` | `.authorizeExchange(exchange -> exchange.pathMatchers(...)...)`, `.oauth2ResourceServer(server -> server.jwt(Customizer.withDefaults()))`, **`.csrf(csrf -> csrf.disable())`** |
| Testing with the local authorization server (p.282–293) | client credentials·authorization code 흐름, `curl` 명령 | 같습니다. 주소·클라이언트 ID(`reader`, `writer`)·스코프도 같습니다 |
| Testing with an external OpenID Connect provider (p.293–306) | Auth0 설정 | `auth0/` 폴더의 `setup-tenant.bash`, `reset-tenant.bash`, `env.bash`가 그대로 있습니다. Auth0 관리 화면은 책 이후 바뀌었을 수 있고, 이 실습은 CI에서 검증하지 않았습니다(학습 이슈 #233) |

## 그대로 따라 해도 되는 부분

- 인가 코드를 받아 토큰으로 바꾸는 브라우저 실습(p.285–289)
- 잘못된 토큰·스코프가 부족한 토큰으로 401·403을 확인하는 실습(p.289–291)

## 더 보기

- 위키: [11장 API 접근 보안](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/11장-API-접근-보안)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter11)
- 학습 이슈: [#11](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/11)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
