"""Hand-written explanations for the workbook (tools/workbook/build.py).

NOTES[n]:
  pages   - (first, last) printed page of the English 3rd edition chapter
  intro   - what the student builds in this chapter
  modules - explanation shown at the top of each step (key = module path)
  files   - extra note for a specific file
  check   - extra text before the run commands
The code itself is never written here; it is always taken from the chapter folders.
"""

MODULE_TITLES = {
    "(root)": "루트 빌드 파일·도커 컴포즈·테스트 스크립트",
    "api": "`api` 프로젝트 — 서비스 간 API와 DTO",
    "util": "`util` 프로젝트 — 공통 유틸리티",
    "microservices/product-service": "`product-service`",
    "microservices/recommendation-service": "`recommendation-service`",
    "microservices/review-service": "`review-service`",
    "microservices/product-composite-service": "`product-composite-service`",
    "spring-cloud/eureka-server": "`eureka-server` — 서비스 검색 서버",
    "spring-cloud/gateway": "`gateway` — 에지 서버",
    "spring-cloud/authorization-server": "`authorization-server` — OAuth 2.0 인가 서버",
    "spring-cloud/config-server": "`config-server` — 구성 서버",
    "config-repo": "`config-repo` — 중앙 구성 파일",
    "auth0": "`auth0` — 외부 OIDC 공급자 설정 스크립트",
    "kubernetes": "`kubernetes` — 클러스터 설정 파일",
    "kubernetes/helm": "`kubernetes/helm` — 헬름 공통 파일",
    "kubernetes/helm/common": "헬름 `common` 라이브러리 차트",
    "kubernetes/helm/components": "헬름 `components` 차트 — 서비스별 차트",
    "kubernetes/helm/environments": "헬름 `environments` 차트 — 환경별 묶음",
    "kubernetes/first-attempts": "`kubernetes/first-attempts` — 첫 쿠버네티스 매니페스트",
    "kubernetes/resilience-tests": "`kubernetes/resilience-tests` — 장애·지연 주입",
    "kubernetes/routing-tests": "`kubernetes/routing-tests` — 트래픽 분할",
    "kubernetes/efk": "`kubernetes/efk` — Fluentd 이미지와 설정",
    "kubernetes/grafana": "`kubernetes/grafana` — 대시보드",
}

SERVICES3 = ("microservices/product-service", "microservices/recommendation-service", "microservices/review-service")


def same(note, keys=SERVICES3):
    return {k: note for k in keys}


NOTES = {
3: dict(pages=(47, 78),
  init="""
교재처럼 Spring Initializr(`spring init`)로 서비스 4개의 골격을 만듭니다. 먼저 작업 폴더를 만들고
스크립트와 루트 `settings.gradle`을 직접 칩니다.
""",
  intro="""
서로 협력하는 마이크로서비스 4개(`product`, `recommendation`, `review`, `product-composite`)를 처음부터 만듭니다.

- 서비스 간 API를 담는 `api` 프로젝트와 공통 코드를 담는 `util` 프로젝트
- 각 핵심 서비스의 REST API 구현(아직 데이터베이스 없이 고정 데이터를 돌려줌)
- 핵심 서비스 3개를 호출해 결과를 합치는 복합 서비스
- 예외 처리와 테스트, 전체 시스템을 확인하는 `test-em-all.bash`

이 장의 코드가 이후 모든 장의 바탕이 됩니다.
""",
  modules={
    "(root)": "루트 `settings.gradle`에 `api`, `util`을 추가하고, 서비스 4개를 띄운 뒤 API를 호출해 보는 `test-em-all.bash`를 만듭니다.",
    "api": "서비스들이 공유하는 인터페이스와 DTO입니다. `@GetMapping` 같은 매핑은 인터페이스에 두고, 구현은 각 서비스가 합니다. 예외 클래스도 여기 둡니다.",
    "util": "모든 서비스가 함께 쓰는 코드입니다. `ServiceUtil`은 응답에 서비스 주소를 넣고, `GlobalControllerExceptionHandler`는 예외를 HTTP 상태 코드로 바꿉니다.",
    **same("핵심 서비스입니다. `spring init`이 만든 골격에 `api`·`util` 의존성을 추가하고, 서비스 구현 클래스와 테스트를 작성합니다. 지금은 고정 데이터를 돌려줍니다."),
    "microservices/product-composite-service": "핵심 서비스 3개를 `RestTemplate`으로 호출하는 `ProductCompositeIntegration`과, 결과를 하나로 합치는 `ProductCompositeServiceImpl`을 만듭니다. 테스트는 통합 클래스를 `@MockitoBean`으로 바꿔 끼웁니다.",
  }),
4: dict(pages=(79, 102),
  intro="""
3장에서 만든 서비스들을 **도커 컨테이너**로 만들고 **도커 컴포즈**로 한 번에 띄웁니다.

- 서비스마다 `Dockerfile` (레이어로 나눈 JAR, Java 21 JRE)
- `docker` 프로필: 컨테이너 안에서 쓸 포트와 다른 서비스 주소
- `docker-compose.yml`과, 시스템을 띄우고 내리는 기능을 더한 `test-em-all.bash`
""",
  modules={
    "(root)": "`docker-compose.yml`로 서비스 4개를 한 번에 띄웁니다. `test-em-all.bash`에는 `start`/`stop` 인자로 컴포즈를 올리고 내리는 기능과, 서비스가 준비될 때까지 기다리는 함수가 추가됩니다.",
    **same("`Dockerfile`을 추가하고, `application.yml`에 `docker` 프로필(포트 8080)을 추가합니다. 네 서비스의 `Dockerfile`은 내용이 같습니다."),
    "microservices/product-composite-service": "`Dockerfile`을 추가하고, `docker` 프로필에서 핵심 서비스 주소를 컨테이너 이름(`product`, `recommendation`, `review`)으로 바꿉니다.",
  }),
5: dict(pages=(103, 122),
  intro="""
복합 서비스에 **OpenAPI 문서와 Swagger UI**를 붙입니다(springdoc-openapi 3).

- API 인터페이스에 `@Tag`, `@Operation`, `@ApiResponses` 설명 추가
- 복합 서비스에서 OpenAPI 문서 정보를 설정하고, `application.yml`에 설명 문구 정의
- `test-em-all.bash`에서 Swagger UI와 OpenAPI 문서를 확인
""",
  modules={
    "(root)": "`test-em-all.bash`에 Swagger UI·OpenAPI 문서(`/openapi/v3/api-docs`, 버전 3.1.0) 확인을 추가합니다.",
    "api": "`springdoc-openapi-starter-common` 의존성을 추가하고, `ProductCompositeService` 인터페이스에 API 설명 애너테이션을 붙입니다. 잘못된 요청을 뜻하는 `BadRequestException`도 추가합니다.",
    "util": "`BadRequestException`을 400 응답으로 바꾸는 처리를 추가합니다.",
    "microservices/product-composite-service": "`springdoc-openapi-starter-webflux-ui` 의존성을 추가하고, 애플리케이션 클래스에 `OpenAPI` 빈을 정의합니다. 설명 문구는 `application.yml`의 `api.*` 속성에서 읽습니다.",
  }),
6: dict(pages=(123, 162),
  intro="""
핵심 서비스에 **데이터베이스**를 붙입니다. `product`·`recommendation`은 MongoDB, `review`는 MySQL을 씁니다.

- 엔티티와 Spring Data 리포지터리, MapStruct 매퍼
- Testcontainers로 실제 데이터베이스를 띄우는 영속성 테스트(`@ServiceConnection`)
- 생성·삭제 API 추가와 복합 서비스의 생성·삭제 구현
- 도커 컴포즈에 MongoDB·MySQL 추가
""",
  modules={
    "(root)": "`docker-compose.yml`에 MongoDB(`mongo:8.0.5`)와 MySQL(`mysql:9.2.0`)을 추가합니다. `test-em-all.bash`는 테스트 데이터를 직접 만들고 지우도록 바뀝니다.",
    "api": "핵심 서비스 API에 `createXxx`, `deleteXxx`를 추가하고, DTO에 setter를 추가합니다(MapStruct가 객체를 채울 때 씁니다).",
    "microservices/product-service": "MongoDB용 `ProductEntity`(`@Document`, `@Version`)와 `ProductRepository`, `ProductMapper`를 만들고 서비스 구현이 리포지터리를 쓰도록 바꿉니다. 테스트에는 `MongoDbTestBase`(Testcontainers)와 `PersistenceTests`, `MapperTests`가 추가됩니다.",
    "microservices/recommendation-service": "`product-service`와 같은 구조로 MongoDB 영속성을 추가합니다. `RecommendationEntity`에는 `productId`+`recommendationId` 복합 인덱스가 있습니다.",
    "microservices/review-service": "MySQL(JPA)을 씁니다. `ReviewEntity`(`@Entity`, `@Table`), `ReviewRepository`(`CrudRepository`)와 `MySqlTestBase`를 만듭니다. `spring.jpa.hibernate.ddl-auto`로 테이블을 만듭니다.",
    "microservices/product-composite-service": "통합 클래스에 핵심 서비스의 생성·삭제 호출을 추가하고, 복합 서비스에 `createProduct`, `deleteProduct`를 구현합니다.",
  }),
7: dict(pages=(163, 210),
  intro="""
서비스를 **리액티브**로 바꾸고 **이벤트 기반 비동기 통신**을 추가합니다.

- 조회 API를 `Mono`/`Flux`로 바꾸고, MongoDB는 리액티브 리포지터리 사용
- 블로킹인 JPA 코드는 별도 스케줄러에서 실행
- 생성·삭제는 Spring Cloud Stream으로 이벤트를 보내고, 핵심 서비스가 받아 처리
- RabbitMQ 기본 구성, 파티션 구성, Kafka 구성의 도커 컴포즈 파일
""",
  modules={
    "(root)": "`docker-compose.yml`에 RabbitMQ를 추가하고, 파티션 구성(`docker-compose-partitions.yml`)과 Kafka 구성(`docker-compose-kafka.yml`)을 새로 만듭니다. `test-em-all.bash`는 비동기 처리를 기다리는 대기와 함께 바뀝니다.",
    "api": "서비스 인터페이스가 `Mono`/`Flux`를 돌려주도록 바꾸고, 이벤트를 나타내는 `Event`와 `EventProcessingException`을 추가합니다.",
    "util": "Reactor의 동작을 확인하는 `ReactorTests`를 추가합니다.",
    **same("메시지를 받아 생성·삭제를 처리하는 `MessageProcessorConfig`(`Consumer<Event>` 빈)를 추가하고, 서비스 구현과 테스트를 리액티브로 바꿉니다. `application.yml`에 Spring Cloud Stream 바인딩, RabbitMQ·Kafka 설정이 추가됩니다."),
    "microservices/review-service": "JPA는 블로킹이라 `jdbcScheduler`(애플리케이션 클래스에 정의)에서 실행하도록 감쌉니다. 메시지 처리용 `MessageProcessorConfig`도 추가합니다.",
    "microservices/product-composite-service": "통합 클래스를 `WebClient`(조회)와 `StreamBridge`(생성·삭제 이벤트 전송)로 다시 씁니다. 핵심 서비스 상태를 모으는 `HealthCheckConfiguration`과, 보낸 메시지를 확인하는 `MessagingTests`·`IsSameEvent` 테스트가 추가됩니다.",
  }),
9: dict(pages=(225, 244),
  intro="""
**넷플릭스 유레카**로 서비스 검색을 추가합니다. 서비스 주소를 고정하지 않고, 유레카에 등록된 인스턴스 중에서 골라 호출합니다.

- `eureka-server` 프로젝트
- 각 서비스를 유레카 클라이언트로 등록
- 복합 서비스는 `@LoadBalanced` WebClient로 `http://product` 같은 서비스 이름을 호출
""",
  modules={
    "(root)": "`settings.gradle`에 `eureka-server`를 추가하고, 세 컴포즈 파일에 `eureka` 컨테이너를 추가합니다. `test-em-all.bash`는 서비스가 유레카에 등록될 때까지 기다립니다.",
    **same("`spring-cloud-starter-netflix-eureka-client` 의존성과 유레카 서버 주소 설정을 추가합니다."),
    "microservices/product-composite-service": "`@LoadBalanced WebClient.Builder` 빈을 정의하고, 통합 클래스에서 서비스 주소 대신 `http://product` 같은 서비스 이름을 씁니다.",
    "spring-cloud/eureka-server": "새 프로젝트입니다. `@EnableEurekaServer` 하나로 유레카 서버가 됩니다.",
  }),
10: dict(pages=(245, 262),
  intro="""
**Spring Cloud Gateway**로 에지 서버를 만들어 마이크로서비스를 외부에서 숨깁니다. 외부 요청은 게이트웨이(포트 8080)만 받습니다.

- `gateway` 프로젝트와 라우팅 규칙(`spring.cloud.gateway.server.webflux.routes`)
- 시스템 상태 확인을 복합 서비스에서 게이트웨이로 옮김
""",
  modules={
    "(root)": "`settings.gradle`에 `gateway`를 추가합니다. 컴포즈 파일에서 외부 포트는 게이트웨이만 열고, `test-em-all.bash`는 게이트웨이를 통해 호출합니다.",
    **same("`build.gradle`의 주석만 조금 바뀝니다(동작 변화 없음)."),
    "microservices/product-composite-service": "`HealthCheckConfiguration`을 지웁니다(게이트웨이로 옮겨 감). 관련 코드도 통합 클래스에서 뺍니다.",
    "spring-cloud/gateway": "새 프로젝트입니다. `application.yml`에 라우트(복합 서비스, 유레카, Swagger UI, 호스트 헤더 예제)를 정의하고, 전체 시스템 상태를 모으는 `HealthCheckConfiguration`을 둡니다.",
  }),
11: dict(pages=(263, 308),
  intro="""
API 접근을 **OAuth 2.0 / OpenID Connect**로 보호합니다.

- 게이트웨이에 HTTPS 적용(자체 서명 인증서, SSL 번들)
- 유레카 서버를 HTTP Basic 인증으로 보호
- `authorization-server`(Spring Security 7의 인가 서버) 추가
- 게이트웨이와 복합 서비스를 리소스 서버로 만들고 스코프(`product:read`, `product:write`)로 권한 부여
""",
  files={
    "spring-cloud/gateway/src/main/resources/keystore/edge.p12":
      "자체 서명 인증서입니다. 직접 만들어 보세요. 비밀번호를 물으면 `password`를 입력합니다(이름 등은 아무 값이나 괜찮습니다).\n\n"
      "```bash\nmkdir -p spring-cloud/gateway/src/main/resources/keystore\n"
      "keytool -genkeypair -alias localhost -keyalg RSA -keysize 2048 -storetype PKCS12 \\\n"
      "  -keystore spring-cloud/gateway/src/main/resources/keystore/edge.p12 -validity 3650\n```\n\n"
      "직접 만든 인증서는 저장소의 파일과 내용이 다르지만 실습에는 지장이 없습니다.",
  },
  modules={
    "(root)": "`settings.gradle`에 `authorization-server`를 추가합니다. 컴포즈 파일에 `auth-server`를 추가하고 게이트웨이 포트를 8443(HTTPS)으로 바꿉니다. `test-em-all.bash`는 토큰을 받아 호출하도록 바뀝니다.",
    "api": "API 문서에 보안 요구 사항 표시를 추가합니다.",
    "auth0": "외부 OIDC 공급자(Auth0)로 테스트할 때 쓰는 스크립트입니다(선택 실습, 학습 이슈 #233).",
    **same("유레카 서버 주소에 사용자·비밀번호를 넣습니다(`http://u:p@eureka:8761/eureka/` 형태)."),
    "microservices/product-composite-service": "리소스 서버 의존성을 추가하고 `SecurityConfig`에서 메서드·경로별로 필요한 스코프를 지정합니다. Swagger UI에서 OAuth 로그인을 쓰도록 `OpenApiConfig`를 추가합니다. 테스트는 `TestSecurityConfig`로 보안을 끕니다.",
    "spring-cloud/eureka-server": "`SecurityConfig`로 HTTP Basic 인증을 겁니다(람다 DSL).",
    "spring-cloud/gateway": "HTTPS(SSL 번들)와 리소스 서버 보안을 추가합니다. `SecurityConfig`에서 공개 경로와 인증이 필요한 경로를 나눕니다.",
    "spring-cloud/authorization-server": "새 프로젝트입니다. 클라이언트(`reader`, `writer`)와 스코프, 토큰 서명 키(JWK)를 설정합니다. 코드가 길지만 구조는 `AuthorizationServerConfig`(인가 서버 설정)·`DefaultSecurityConfig`(로그인 사용자)·`jose`(키 생성)로 나뉩니다.",
  }),
12: dict(pages=(309, 322),
  intro="""
**Spring Cloud Config Server**로 설정을 한곳에 모읍니다.

- `config-server` 프로젝트(파일 기반 저장소, 암호화, 기본 인증)
- 서비스별 `application.yml`을 `config-repo/`로 옮기고, 각 서비스는 `bootstrap.yml`로 구성 서버에 접속
- 비밀 값은 `.env` 파일과 환경 변수로 전달
""",
  modules={
    "(root)": "`settings.gradle`에 `config-server`를 추가하고, 비밀 값을 담은 `.env`를 만듭니다. 컴포즈 파일에 `config-server`를 추가하고 각 서비스에 구성 서버 접속 정보를 넘깁니다.",
    "config-repo": "각 서비스의 `application.yml`에 있던 설정이 여기로 옮겨 옵니다. 파일 이름은 서비스의 `spring.application.name`과 같습니다.",
    **same("`application.yml`을 지우고 구성 서버 접속용 `bootstrap.yml`을 만듭니다. 테스트에서는 `src/test/resources/application.yml`로 구성 서버를 끕니다."),
    "microservices/product-composite-service": "다른 서비스와 같이 `application.yml` → `bootstrap.yml`로 바꿉니다.",
    "spring-cloud/eureka-server": "다른 서비스와 같이 `bootstrap.yml`로 바꿉니다.",
    "spring-cloud/gateway": "다른 서비스와 같이 `bootstrap.yml`로 바꿉니다.",
    "spring-cloud/authorization-server": "다른 서비스와 같이 `bootstrap.yml`로 바꿉니다.",
    "spring-cloud/config-server": "새 프로젝트입니다. `@EnableConfigServer`와 기본 인증 `SecurityConfig`가 전부입니다. 저장소 위치는 `application.yml`에서 지정합니다.",
  }),
13: dict(pages=(323, 348),
  intro="""
**Resilience4j**로 복합 서비스를 튼튼하게 만듭니다.

- 서킷 브레이커와 폴백 메서드, 재시도, 시간 제한
- 실습용으로 핵심 서비스에 지연(`delay`)과 오류(`faultPercent`)를 넣는 파라미터 추가
""",
  modules={
    "(root)": "`test-em-all.bash`에 서킷 브레이커가 열리고 닫히는 과정을 확인하는 테스트를 추가합니다.",
    "api": "조회 API에 `delay`, `faultPercent` 파라미터를 추가합니다.",
    "config-repo": "`product-composite.yml`에 서킷 브레이커·재시도·시간 제한 설정을 추가합니다.",
    "microservices/product-service": "`delay`, `faultPercent`에 따라 응답을 늦추거나 오류를 내는 코드를 추가합니다.",
    "microservices/product-composite-service": "`resilience4j-spring-boot4`와 `spring-boot-starter-aspectj` 의존성을 추가하고, 상품 조회에 `@CircuitBreaker`, `@Retry`, `@TimeLimiter`와 폴백 메서드를 붙입니다.",
  }),
14: dict(pages=(349, 372),
  intro="""
**Micrometer Tracing과 Zipkin**으로 분산 추적을 추가합니다.

- 모든 서비스에 추적 의존성과 Zipkin 주소 설정
- 로그에 추적 ID 넣기
- 복합 서비스에서 사용자 정의 스팬과 태그 만들기
""",
  modules={
    "(root)": "세 컴포즈 파일에 Zipkin 서버(`openzipkin/zipkin:3.5.0`)를 추가합니다.",
    "config-repo": "`management.tracing.export.zipkin.endpoint`와 샘플링 비율, 로그 패턴(`logging.pattern.correlation`)을 설정합니다.",
    **same("추적 의존성을 추가하고, 리액티브 코드에서 추적 정보가 이어지도록 애플리케이션 클래스에서 `Hooks.enableAutomaticContextPropagation()`을 호출합니다."),
    "microservices/product-composite-service": "추적 의존성과 함께 `ObservationUtil`(사용자 정의 스팬), `BuildInfoObservationFilter`(빌드 정보 태그), `ObservationRegistryConfig`를 추가합니다.",
    "spring-cloud/eureka-server": "추적 의존성을 추가합니다.",
    "spring-cloud/gateway": "추적 의존성을 추가하고 컨텍스트 전파를 켭니다.",
    "spring-cloud/authorization-server": "추적 의존성을 추가합니다.",
  }),
15: dict(pages=(373, 394),
  intro="""
쿠버네티스를 처음 써 보는 장입니다. 마이크로서비스 코드는 거의 그대로이고, nginx 예제로 디플로이먼트와 서비스를 만들어 봅니다.
""",
  modules={
    "kubernetes/first-attempts": "nginx 디플로이먼트(파드 3개)와 NodePort 서비스입니다. `kubectl apply -f`로 적용해 봅니다.",
    "microservices/product-composite-service": "테스트 로그 설정과 메서드 접근 제한자를 정리합니다(동작 변화 없음).",
    "spring-cloud/eureka-server": "주석만 바뀝니다.",
    "spring-cloud/authorization-server": "테스트 한 줄을 정리합니다.",
  },
  check="""
nginx 예제는 minikube에서 확인합니다.

```bash
minikube start --driver=docker
kubectl create namespace first-attempts
kubectl config set-context $(kubectl config current-context) --namespace=first-attempts
kubectl apply -f kubernetes/first-attempts/nginx-deployment.yaml
kubectl apply -f kubernetes/first-attempts/nginx-service.yaml
kubectl get all
```
"""),
16: dict(pages=(395, 438),
  intro="""
마이크로서비스를 **쿠버네티스에 배포**합니다. 유레카는 쿠버네티스 서비스로 대체하고, 배포는 **헬름 차트**로 만듭니다.

- 유레카 서버 삭제, 서비스 이름으로 직접 호출
- 그레이스풀 셧다운, 활성·준비 상태 프로브
- 헬름 차트: `common`(공통 템플릿) → `components`(서비스별) → `environments`(개발·운영 묶음)
""",
  modules={
    "(root)": "`settings.gradle`에서 `eureka-server`를 빼고, 컴포즈 파일에서 `eureka`를 지웁니다. `test-em-all.bash`에 쿠버네티스에서 실행하는 경우(`USE_K8S=true`)가 추가됩니다.",
    "config-repo": "유레카 설정을 지우고, 그레이스풀 셧다운과 프로브(`management.endpoint.health.probes`) 설정을 추가합니다. 서비스 주소는 쿠버네티스 서비스 이름을 씁니다.",
    "kubernetes/helm": "헬름이 만든 의존 차트 폴더를 Git에서 제외합니다.",
    "kubernetes/helm/common": "모든 서비스 차트가 같이 쓰는 템플릿입니다. `_deployment.yaml`, `_service.yaml`, `_configmap_from_file.yaml`, `_secrets.yaml`과 기본값 `values.yaml`을 만듭니다.",
    "kubernetes/helm/components": "서비스마다 작은 차트를 만듭니다. 대부분 `common`의 템플릿을 한 줄로 불러오고, 이미지 이름과 포트 같은 값만 `values.yaml`에 적습니다. `config-server` 차트에는 `config-repo` 파일을 담습니다.",
    "kubernetes/helm/environments": "`dev-env`(개발·테스트용, 데이터베이스까지 모두)와 `prod-env`(데이터베이스는 클러스터 밖)를 만듭니다. 비밀 값은 `secrets.yaml`에서 만듭니다.",
    **same("유레카 클라이언트 의존성을 지웁니다."),
    "microservices/product-composite-service": "유레카 관련 코드를 지우고, `app.resilience.enabled` 값으로 Resilience4j를 끌 수 있게 하는 `ResilienceConfig`를 추가합니다.",
    "spring-cloud/eureka-server": "쿠버네티스 서비스가 서비스 검색을 대신하므로 프로젝트를 통째로 지웁니다: `rm -r spring-cloud/eureka-server`",
    "spring-cloud/gateway": "유레카 관련 의존성과 설정을 지웁니다.",
    "spring-cloud/authorization-server": "유레카 관련 의존성을 지우고, `Dockerfile`의 노출 포트를 80으로 바꿉니다(쿠버네티스 서비스 포트와 맞춤).",
    "spring-cloud/config-server": "쿠버네티스의 프로브 경로를 인증 없이 열어 둡니다.",
  }),
17: dict(pages=(439, 464),
  intro="""
쿠버네티스 기능으로 시스템을 단순하게 만듭니다.

- Config Server 대신 **ConfigMap·Secret**: 서비스별 차트에 설정 파일을 담고 `SPRING_CONFIG_LOCATION`으로 읽음
- 게이트웨이 대신 **Ingress**, 인증서는 **cert-manager**가 발급
- 구성 서버 프로젝트와 `bootstrap.yml` 삭제
""",
  modules={
    "(root)": "`settings.gradle`에서 `config-server`를 빼고, 컴포즈 파일에서 구성 서버 대신 `config-repo`를 마운트해 읽도록 바꿉니다. `.env`에 데이터베이스 계정이 추가됩니다.",
    "config-repo": "RabbitMQ 계정처럼 암호화해 두던 비밀 값을 빼고(이제 쿠버네티스 Secret이나 `.env`로 전달), 로그 패턴을 정리합니다.",
    "kubernetes/helm/common": "Ingress와 cert-manager `Issuer` 템플릿(`_ingress.yaml`, `_issuer.yaml`)을 추가합니다.",
    "kubernetes/helm/components": "`config-server` 차트를 지우고, 서비스별 차트에 `config-repo` 파일과 ConfigMap 템플릿을 넣습니다. `config-repo` 파일은 루트의 `config-repo`와 내용이 같아 복사하면 됩니다.",
    "kubernetes/helm/environments": "환경 차트에서 `config-server`를 빼고 Ingress·Issuer를 추가합니다. `Chart.lock`은 `helm dep up`으로 다시 만듭니다.",
    **same("`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다."),
    "microservices/product-composite-service": "`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다.",
    "spring-cloud/gateway": "`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다. 쿠버네티스에서는 Ingress가 외부 요청을 받지만, 도커 컴포즈 실행을 위해 게이트웨이 프로젝트는 남겨 둡니다.",
    "spring-cloud/authorization-server": "`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다.",
    "spring-cloud/config-server": "ConfigMap이 대신하므로 프로젝트를 통째로 지웁니다: `rm -r spring-cloud/config-server`",
  }),
18: dict(pages=(465, 522),
  intro="""
**이스티오 서비스 메시**를 도입합니다. 코드 변경은 적고, 대부분 쿠버네티스·헬름 설정입니다.

- 추적을 Jaeger로 보내고 B3 헤더로 전파(`TracingConfig`)
- 이스티오 리소스: Gateway, VirtualService, DestinationRule, mTLS, JWT 인증
- 장애·지연 주입과 블루/그린 배포 실습 파일
""",
  modules={
    "(root)": "컴포즈 파일은 관리 포트 분리(4004)에 맞춰 헬스 체크를 바꾸고 Zipkin을 뺍니다(추적은 이스티오의 Jaeger가 받음). `test-em-all.bash`는 기본값이 쿠버네티스(`minikube.me`) 실행으로 바뀝니다.",
    "api": "핵심 서비스 API가 요청 헤더(`HttpHeaders`)를 받도록 바꿉니다. 복합 서비스가 받은 헤더를 핵심 서비스로 넘겨, 블루/그린 배포의 `X-group` 헤더 라우팅이 끝까지 이어지게 합니다.",
    "config-repo": "추적 주소를 Jaeger(`jaeger-collector.istio-system:9411`)로 바꾸고, 관리 엔드포인트를 별도 포트(4004, 게이트웨이는 8443)로 분리합니다.",
    "kubernetes": "네임스페이스(사이드카 자동 주입 라벨), 이스티오 추적 설정(`istio-tracing.yml`), Telemetry API(`istio-telemetry.yml`)입니다.",
    "kubernetes/helm/common": "Ingress·Issuer 템플릿을 지우고 이스티오 템플릿(`_istio_base.yaml`, `_istio_dr_mutual_tls.yaml`, `_istio_vs_green_blue_deploy.yaml`)을 추가합니다.",
    "kubernetes/helm/components": "서비스 차트 값을 이스티오에 맞추고, 블루/그린 배포용 차트를 추가합니다.",
    "kubernetes/helm/environments": "`istio-system` 환경 차트(Kiali·Jaeger·Grafana·Prometheus 노출, 인증서)를 추가하고 개발·운영 환경에 이스티오 리소스를 넣습니다.",
    "kubernetes/resilience-tests": "상품 서비스에 장애와 지연을 넣는 VirtualService입니다.",
    "kubernetes/routing-tests": "구버전과 새 버전 사이에 트래픽을 나누는 스크립트입니다.",
    **same("`TracingConfig`로 B3 헤더 전파를 설정하고, 추적 의존성을 Brave + `spring-boot-starter-zipkin`으로 바꿉니다."),
    "microservices/product-composite-service": "다른 서비스와 같이 `TracingConfig`와 추적 의존성 변경입니다.",
    "spring-cloud/gateway": "다른 서비스와 같이 추적 의존성을 Brave로 바꾸고, B3 헤더 전파를 애플리케이션 클래스에서 설정합니다.",
    "spring-cloud/authorization-server": "추적 의존성을 Brave로 바꿉니다.",
  }),
19: dict(pages=(523, 562),
  intro="""
**EFK 스택**(Elasticsearch, Fluentd, Kibana)으로 로그를 모읍니다.

- Fluentd 이미지와 데몬셋, 설정 ConfigMap
- `logging` 환경 차트로 Elasticsearch·Kibana 배포
""",
  modules={
    "kubernetes/efk": "Fluentd 이미지를 만드는 `Dockerfile`, 노드마다 실행되는 데몬셋, 로그를 해석하는 설정(`fluentd-hands-on-configmap.yml`)입니다.",
    "kubernetes/helm/environments": "Elasticsearch·Kibana를 배포하고 노출하는 `logging` 환경 차트를 추가합니다.",
  }),
20: dict(pages=(563, 598),
  intro="""
**Prometheus와 Grafana**로 마이크로서비스를 모니터링합니다.

- 모든 서비스에 `micrometer-registry-prometheus` 추가, `/actuator/prometheus` 노출
- 메일 서버 노출 설정과 Grafana 대시보드
""",
  modules={
    "(root)": "`test-em-all.bash`에 쿠버네티스에서 `/actuator/prometheus` 지표를 확인하는 테스트를 추가합니다.",
    "config-repo": "`/actuator/prometheus`를 노출하고 지표에 `application` 태그를 붙입니다.",
    "kubernetes/grafana": "직접 만든 대시보드를 내보낸 파일입니다.",
    "kubernetes/helm/components": "서비스 차트에 Prometheus 수집 애너테이션과 설정 파일을 추가합니다.",
    "kubernetes/helm/environments": "테스트 메일 서버를 노출하는 `expose-mail.yml`을 추가합니다.",
    **same("`micrometer-registry-prometheus` 의존성을 추가합니다."),
    "microservices/product-composite-service": "`micrometer-registry-prometheus` 의존성을 추가합니다.",
    "spring-cloud/authorization-server": "`micrometer-registry-prometheus` 의존성을 추가합니다.",
  }),
23: dict(pages=(621, 650),
  intro="""
**GraalVM 네이티브 이미지**로 마이크로서비스를 컴파일합니다.

- `org.graalvm.buildtools.native` 플러그인과 `bootBuildImage` 설정(GraalVM 25)
- 리플렉션 등 네이티브 이미지 힌트(`NativeHintsConfiguration`)
- 네이티브 이미지용 도커 컴포즈 파일과 헬름 환경(`dev-env-native`)
""",
  modules={
    "(root)": "네이티브 이미지용 컴포즈 파일(`docker-compose-native.yml`, `docker-compose-partitions-native.yml`)을 추가합니다.",
    "config-repo": "MySQL 접속 URL에 문자셋 옵션을 추가합니다.",
    "kubernetes/helm/components": "네이티브 이미지 설정입니다.",
    "kubernetes/helm/environments": "네이티브 이미지를 쓰는 `dev-env-native` 환경 차트를 추가합니다.",
    **same("네이티브 빌드 플러그인과 `bootBuildImage` 설정, `NativeHintsConfiguration`을 추가합니다. 네이티브 이미지에서 쓰는 `application.yml`과 테스트용 접근 필터가 추가되고, `Dockerfile`은 JVM AOT 모드 실습용으로 바뀝니다."),
    "microservices/product-composite-service": "다른 서비스와 같이 네이티브 빌드 설정과 힌트를 추가합니다.",
    "spring-cloud/authorization-server": "사용하지 않는 import를 정리합니다.",
  }),
}

README_TEXT = """
# 손코딩 워크북

『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』의 예제를 **처음부터 직접 쳐서** 완성하는 워크북입니다.
코드는 이 저장소의 Spring Boot 4.0.9 / Java 21 버전입니다.

## 진행 방식

1. **3장은 처음부터** 만듭니다. `spring init`으로 골격을 만든 뒤 파일을 하나씩 칩니다.
2. **4장부터는 이전 장 결과를 복사해서** 그 장에서 바뀌는 부분만 칩니다. 이전 장을 끝내지 못했다면 저장소의 완성 코드를 복사해 시작해도 됩니다.
3. 각 장은 **단계**(프로젝트 단위)로 나뉘어 있습니다. 단계마다
   - **새 파일**은 전체 코드를,
   - **수정할 파일**은 바뀐 부분(diff)을 보여 줍니다. 완성된 파일 전체는 펼쳐 볼 수 있습니다.
   - **지울 파일**은 `rm` 명령으로 안내합니다.
4. 단계가 끝나면 **중간 확인**으로 컴파일만 해 보고, 장 끝의 **확인하기**에서 테스트와 전체 시스템 실행으로 검증합니다.

복사·붙여넣기보다 **직접 치는 것**을 권합니다. 치면서 클래스 이름, 애너테이션, 설정 키를 손에 익히는 것이 이 워크북의 목적입니다.
막히면 저장소의 완성 코드와 `diff -r`로 비교해 보세요.

## 준비

- JDK 21, Docker(Compose v2), Git, `curl`, `jq` — 15장부터 `kubectl`, `minikube`, `helm`, 18장부터 `istioctl` 1.31.4
- 설치 방법: 위키 [실습 환경 준비]({gh}/wiki/실습-환경-준비)와 교재 21·22장 대응 가이드
- 이 저장소를 클론해 두세요. Gradle 래퍼(`gradlew`, `gradle/wrapper`)와 바이너리 파일은 저장소에서 복사합니다.

```bash
git clone {gh}.git ~/spring-microservice-boot4     # <저장소>
mkdir -p ~/my-work                                  # 직접 치는 작업 폴더
```

워크북 명령에 나오는 `<저장소>`는 클론한 폴더(`~/spring-microservice-boot4`)를 뜻합니다.

## 장별 워크북

| 장 | 만들거나 바꾸는 파일 | 직접 칠 코드(줄) |
|---|---:|---:|
{table}

예제 코드가 없는 장({no_code})은 교재와 교재 대응 가이드로 공부하세요.

## 교재와 함께 보기

- 워크북은 **무엇을 치는지**에 집중합니다. **왜 그렇게 하는지**는 교재 본문을 보세요. 각 장 머리에 영문 3판 쪽 범위와 [교재 대응 가이드](../Chapter03/BOOK-GUIDE.md) 링크가 있습니다.
- 교재(Spring Boot 3.x)와 코드가 다른 곳은 각 장의 `BOOK-GUIDE.md`와 `MIGRATION-BOOT4.md`에 정리돼 있습니다.

## 워크북 갱신

워크북의 코드는 `tools/workbook/build.py`가 각 장 폴더에서 만들어 내고, `tools/workbook/verify.py`가 워크북만으로 각 장을 다시 만들어 저장소 코드와 똑같은지 확인합니다. 코드가 바뀌면 CI가 워크북도 최신인지 검사합니다.
"""
