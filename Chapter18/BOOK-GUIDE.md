# 18장 교재 대응 가이드 — 서비스 메시를 사용한 관찰 가능성 및 관리 편의성 향상

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 18 "Using a Service Mesh to Improve Observability and Management" (p.465–522)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

이스티오로 서비스 메시를 만들고 관찰·보안·탄력성·무중단 배포를 실습하는 흐름은 책과 같습니다. 바뀐 것은 이스티오 버전(1.17 → 1.31.4)과 그에 따른 **추적 설정 방식**, 추적 의존성 이름입니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Simplifying the landscape — Zipkin을 Jaeger로 (p.472–473) | `micrometer-tracing-bridge-brave` + `zipkin-reporter-brave`, B3 헤더로 전환 | `micrometer-tracing-bridge-brave` + Boot 4의 **`spring-boot-starter-zipkin`**. B3(multi) 헤더 전환은 각 서비스의 `TracingConfig` 클래스에서 합니다 |
| Zipkin 주소 (p.473) | `management.zipkin.tracing.endpoint: http://jaeger-collector.istio-system:9411/...` | **`management.tracing.export.zipkin.endpoint`**, 주소는 같습니다. 이스티오 1.31.4의 Jaeger 애드온(Jaeger 2.17)도 `jaeger-collector` 서비스에서 9411 포트를 받습니다 |
| Deploying Istio (p.473–475) | `istioctl install --set profile=demo ... -f kubernetes/istio-tracing.yml` | 같은 명령에 이스티오 **1.31.4**를 씁니다(`curl -L https://istio.io/downloadIstio \| ISTIO_VERSION=1.31.4 sh -`) |
| `istio-tracing.yml` (p.475) | `meshConfig.defaultConfig.tracing.sampling: 100` | 새 방식: `meshConfig.extensionProviders`에 `zipkin` 공급자(`zipkin.istio-system:9411`)를 정의하고, **`kubernetes/istio-telemetry.yml`**(Telemetry API, `randomSamplingPercentage: 100`)을 `kubectl apply -n istio-system -f kubernetes/istio-telemetry.yml`로 적용합니다. 예전 `tracing.sampling` 설정은 최신 이스티오에서 쓰지 않습니다 |
| 애드온 설치 (p.475) | `istio/${istio_version}/samples/addons/{kiali,jaeger,prometheus,grafana}.yaml` | 같은 방법이 1.31.4에서도 됩니다. CI는 내려받은 `istio-1.31.4/samples/addons`의 파일을 적용합니다. Kiali v2.31, Jaeger 2.17, Grafana 12.0.1, Prometheus 3.10.0이라 화면이 책과 다를 수 있습니다 |
| Setting up access to Istio services (p.477–480) | `helm upgrade --install istio-hands-on-addons ...`, `minikube tunnel`, `/etc/hosts` | 같습니다 |
| Creating the service mesh (p.480–487) | 로그의 `X-B3-TraceId`, `X-B3-SpanId` 헤더 | 같습니다(`TracingConfig`가 B3 multi 형식으로 내보냄) |
| Observing the service mesh (p.487–492) | Kiali 그래프, Jaeger 추적 | 같은 기능입니다. 메뉴 이름과 배치는 새 버전에서 조금 다릅니다 |
| Securing a service mesh (p.492–499) | `PeerAuthentication`(mTLS), `RequestAuthentication`, `AuthorizationPolicy`, Auth0 추가 연습 | 같습니다. 리소스는 `kubernetes/helm/common/templates/_istio_base.yaml`에 있습니다(학습 이슈 #235) |
| Ensuring that a service mesh is resilient (p.499–504) | `kubernetes/resilience-tests/*` 장애·지연 주입 | 같습니다 |
| Performing zero-downtime updates (p.504–520) | v1/v2 이미지 태그, `prod-env`, `kubernetes/routing-tests/split-traffic-between-old-and-new-services.bash` | 같습니다 |
| Running tests with Docker Compose (p.520) | `USE_K8S=false HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 ./test-em-all.bash start stop` | 같습니다 |

## 참고

- `istioctl experimental precheck`(p.474)는 `istioctl x precheck`로 줄여 쓸 수 있습니다.
- 메시 리소스의 `apiVersion`(`networking.istio.io/v1beta1`, `security.istio.io/v1beta1`)은 1.31.4에서도 그대로 동작합니다(CI 통과).

## 더 보기

- 위키: [18장 서비스 메시를 사용한 관찰 가능성 및 관리 편의성 향상](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/18장-서비스-메시를-사용한-관찰-가능성-및-관리-편의성-향상)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter18)
- 학습 이슈: [#18](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/18)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
