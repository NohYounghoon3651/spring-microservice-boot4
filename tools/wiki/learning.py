#!/usr/bin/env python3
"""Chapter data for the learning flow + generators for wiki pages and issue bodies.

Usage: python3 tools/wiki/learning.py [--issues OUT.json]
  -> regenerates docs/wiki/*.md (Home, _Sidebar, _Footer, chapter pages).
  Hand-maintained pages (실습-환경-준비, Spring-Boot-4-마이그레이션-요약, 자주-발생하는-문제,
  브랜치-전략, Codespaces와-컨테이너-이미지) are never overwritten.
  --issues writes the chapter learning-issue bodies as JSON (used once to create issues #1~#23).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from review_qa import QA  # noqa: E402
import delta  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DELTA = delta.compute(ROOT)
REPO = "NohYounghoon3651/spring-microservice-boot4"
GH = f"https://github.com/{REPO}"

PARTS = {
    1: ("1부: 스프링 부트로 마이크로서비스 개발하기", "1~7장. 스프링 부트로 협업하는 마이크로서비스를 만들고, 도커·OpenAPI·영속성·반응형 프로그래밍을 더한다."),
    2: ("2부: 스프링 클라우드로 마이크로서비스 관리하기", "8~14장. 서비스 검색, 에지 서버, 보안, 구성 중앙화, 탄력성, 분산 추적을 스프링 클라우드로 구현한다."),
    3: ("3부: 쿠버네티스로 경량 마이크로서비스 개발하기", "15~23장. 쿠버네티스·헬름·이스티오로 배포하고, 로깅·모니터링·네이티브 컴파일까지 다룬다."),
}

# key: chapter number -> dict
C = {
 1: dict(t="마이크로서비스 소개", part=1, code=False,
   goals=["모놀리식에서 마이크로서비스로 넘어가는 동기와 장단점을 이해한다",
          "마이크로서비스 설계 원칙과 분산 시스템의 함정을 정리한다",
          "이 책에서 다루는 디자인 패턴(서비스 검색, 에지 서버, 반응형, 구성 중앙화, 회로 차단기 등)의 큰 그림을 잡는다"],
   tech=[]),
 2: dict(t="스프링 부트 소개", part=1, code=False,
   goals=["스프링 부트, 스프링 웹플럭스, springdoc-openapi, 스프링 데이터, 스프링 클라우드 스트림, 도커의 역할을 익힌다",
          "이 책의 실습에서 쓰는 기술 스택 전체를 미리 훑어본다"],
   tech=["Spring Boot 4.0.9", "Spring WebFlux", "Spring Data", "Spring Cloud Stream", "Docker"]),
 3: dict(t="협업 마이크로서비스 생성", part=1, code=True,
   goals=["Spring Initializr(`spring init`)로 멀티 프로젝트 그레이들 빌드를 만든다",
          "product / recommendation / review 핵심 서비스와 product-composite 복합 서비스를 구현한다",
          "api·util 공통 모듈과 전역 예외 처리(`GlobalControllerExceptionHandler`)를 이해한다",
          "WebTestClient 기반 자동화 테스트와 `test-em-all.bash`로 수동 테스트를 실행한다"],
   tech=["Spring Boot", "WebFlux", "WebTestClient", "Gradle 멀티 프로젝트"]),
 4: dict(t="도커를 사용한 배포", part=1, code=True,
   goals=["마이크로서비스를 도커 이미지로 만든다(레이어 추출을 쓰는 Dockerfile)",
          "`docker compose`로 전체 시스템을 기동하고 테스트한다",
          "`docker` 스프링 프로필로 컨테이너 환경 설정을 분리한다"],
   tech=["Docker", "Docker Compose", "Spring 프로필"]),
 5: dict(t="OpenAPI를 사용한 API 문서화", part=1, code=True,
   goals=["springdoc-openapi로 API 문서를 생성한다",
          "API 인터페이스에 OpenAPI 애너테이션을 추가하고 설명을 외부 설정으로 분리한다",
          "Swagger UI로 API를 직접 호출해 본다"],
   tech=["springdoc-openapi 3.0.3", "Swagger UI"]),
 6: dict(t="영속성 추가", part=1, code=True,
   goals=["MongoDB(product, recommendation)와 MySQL(review)에 데이터를 저장한다",
          "MapStruct로 API 모델과 엔티티를 변환한다",
          "Testcontainers로 실제 데이터베이스를 띄워 영속성 테스트를 작성한다"],
   tech=["Spring Data MongoDB", "Spring Data JPA (Hibernate 7)", "MapStruct", "Testcontainers 2"]),
 7: dict(t="반응형 마이크로서비스 개발", part=1, code=True,
   goals=["논블로킹 동기 API(WebFlux, 반응형 MongoDB)와 블로킹 JPA 코드를 섞어 쓰는 방법을 익힌다",
          "Spring Cloud Stream으로 이벤트 기반 비동기 서비스를 구현한다(RabbitMQ / Kafka)",
          "파티션, 재시도, 데드 레터 큐를 구성한다"],
   tech=["Project Reactor", "Spring Cloud Stream 5", "RabbitMQ", "Kafka"]),
 8: dict(t="스프링 클라우드 소개", part=2, code=False,
   goals=["스프링 클라우드의 발전 과정과 주요 프로젝트를 이해한다",
          "서비스 검색, 에지 서버, 구성 중앙화, 회로 차단기, 분산 추적이 2부에서 어떻게 구현되는지 정리한다"],
   tech=["Spring Cloud 2025.1.4"]),
 9: dict(t="넷플릭스 유레카를 사용한 서비스 검색", part=2, code=True,
   goals=["유레카 서버를 구성하고 마이크로서비스를 등록한다",
          "Spring Cloud LoadBalancer로 클라이언트 측 로드 밸런싱을 사용한다",
          "인스턴스를 늘리고 줄이며 서비스 검색 동작을 확인한다"],
   tech=["Spring Cloud Netflix Eureka 5", "Spring Cloud LoadBalancer"]),
 10: dict(t="스프링 클라우드 게이트웨이를 에지 서버로 사용", part=2, code=True,
   goals=["Spring Cloud Gateway를 에지 서버로 추가하고 내부 서비스를 숨긴다",
          "라우팅 규칙과 술어(predicate)·필터를 구성한다",
          "게이트웨이에서 헬스 체크를 집계한다"],
   tech=["Spring Cloud Gateway Server WebFlux 5"]),
 11: dict(t="API 접근 보안", part=2, code=True,
   goals=["HTTPS로 외부 통신을 암호화한다",
          "Spring Authorization Server(이제 Spring Security 7의 일부)로 OAuth 2.0 / OIDC 인가 서버를 만든다",
          "게이트웨이와 product-composite를 리소스 서버로 보호하고 스코프 기반 권한을 적용한다"],
   tech=["Spring Security 7", "OAuth 2.0 / OIDC", "JWT"]),
 12: dict(t="구성 중앙화", part=2, code=True,
   goals=["Spring Cloud Config Server로 설정을 한곳에 모은다",
          "config-repo의 공통 설정과 서비스별 설정 구조를 이해한다",
          "민감한 설정을 암호화한다"],
   tech=["Spring Cloud Config 5"]),
 13: dict(t="Resilience4j를 사용한 탄력성 개선", part=2, code=True,
   goals=["회로 차단기, 시간 제한, 재시도를 product-composite에 적용한다",
          "회로 차단기 상태(CLOSED → OPEN → HALF_OPEN)를 액추에이터로 관찰한다",
          "폴백(fallback) 메서드로 장애 상황에서 응답을 제공한다"],
   tech=["Resilience4j 2.4.0 (spring-boot4)", "Spring Boot Actuator"]),
 14: dict(t="분산 추적", part=2, code=True,
   goals=["Micrometer Tracing으로 동기·비동기 호출의 추적 정보를 전파한다",
          "Zipkin으로 추적 정보를 수집하고 시각화한다",
          "반응형 코드에서 컨텍스트 전파를 다룬다"],
   tech=["Micrometer Tracing", "OpenTelemetry", "Zipkin"]),
 15: dict(t="쿠버네티스 소개", part=3, code=True,
   goals=["쿠버네티스의 핵심 개념(파드, 디플로이먼트, 서비스, 네임스페이스)을 익힌다",
          "minikube로 로컬 클러스터를 만들고 간단한 배포를 해 본다"],
   tech=["Kubernetes", "minikube", "kubectl"]),
 16: dict(t="쿠버네티스에 마이크로서비스 배포", part=3, code=True,
   goals=["헬름 차트(common·components·environments)로 배포를 패키징한다",
          "개발·운영 환경을 헬름 values로 구분한다",
          "liveness / readiness 프로브와 정상 종료(graceful shutdown)를 적용한다"],
   tech=["Helm", "Kubernetes 프로브"]),
 17: dict(t="쿠버네티스 기능으로 시스템 환경 단순화", part=3, code=True,
   goals=["컨피그 서버를 쿠버네티스 ConfigMap·Secret으로 대체한다",
          "유레카를 쿠버네티스 Service로 대체한다",
          "게이트웨이를 Ingress로 대체하고 cert-manager로 인증서를 발급한다"],
   tech=["ConfigMap / Secret", "Ingress (NGINX)", "cert-manager"]),
 18: dict(t="서비스 메시를 사용한 관찰 가능성 및 관리 편의성 향상", part=3, code=True,
   goals=["이스티오를 설치하고 사이드카를 주입한다",
          "Kiali·Jaeger로 서비스 메시를 관찰한다",
          "mTLS, 요청 인증, 장애 주입, 지연 주입, 블루/그린 배포를 실습한다"],
   tech=["Istio 1.31", "Kiali", "Jaeger"]),
 19: dict(t="EFK 스택을 사용한 중앙 집중식 로깅", part=3, code=True,
   goals=["Elasticsearch·Fluentd·Kibana로 로그를 한곳에 모은다",
          "Fluentd 구성으로 자바 로그와 이스티오 로그를 파싱한다",
          "추적 ID로 여러 서비스의 로그를 묶어 조회한다"],
   tech=["Elasticsearch", "Fluentd", "Kibana"]),
 20: dict(t="마이크로서비스 모니터링", part=3, code=True,
   goals=["Micrometer로 Prometheus 메트릭을 노출한다",
          "Grafana 대시보드로 CPU·메모리·회로 차단기·재시도 지표를 본다",
          "Grafana 알림을 구성한다"],
   tech=["Micrometer", "Prometheus", "Grafana"]),
 21: dict(t="macOS 설치 안내", part=3, code=False,
   goals=["macOS에 JDK 21, Docker, jq, minikube, helm, istioctl 등 실습 도구를 설치한다"],
   tech=[]),
 22: dict(t="WSL 2와 우분투를 사용한 윈도우 설치 안내", part=3, code=False,
   goals=["윈도우 WSL 2 + 우분투 환경에 실습 도구를 설치한다"],
   tech=[]),
 23: dict(t="네이티브 컴파일 자바 마이크로서비스", part=3, code=True,
   goals=["Spring AOT와 GraalVM으로 마이크로서비스를 네이티브 이미지로 컴파일한다",
          "네이티브 힌트(RuntimeHints)로 리플렉션이 필요한 부분을 알려 준다",
          "JVM 이미지와 네이티브 이미지의 기동 시간·메모리를 비교한다"],
   tech=["Spring AOT", "GraalVM 25 (빌드팩)", "Cloud Native Buildpacks"]),
}

DC = 'HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 USE_K8S=false '


def page_name(n):
    return f"{n:02d}장-" + re.sub(r"[ /·]+", "-", C[n]["t"])


def link(n):
    return f"[{n}장 {C[n]['t']}]({page_name(n)})"


def run_section(n):
    d = f"Chapter{n:02d}"
    s = []
    if n == 3:
        s += ["**3-1. Spring Initializr로 만든 골격** (`Chapter03/1-spring-init`)", "",
              "```bash", "cd Chapter03/1-spring-init", "./gradlew build", "```", "",
              "**3-2. 기본 REST 서비스** (`Chapter03/2-basic-rest-services`): 서비스 4개를 직접 띄우고 테스트합니다.", "",
              "```bash", "cd Chapter03/2-basic-rest-services", "./gradlew build",
              "for s in product recommendation review product-composite; do",
              "  java -jar microservices/$s-service/build/libs/*.jar &", "done",
              "./test-em-all.bash", "kill $(jobs -p)   # 끝나면 서비스 종료", "```"]
        return s
    if n == 15:
        s += ["```bash", "cd Chapter15", "./gradlew build", "docker compose build",
              "./test-em-all.bash start stop      # 14장과 같은 시스템을 도커 컴포즈로 확인", "```", "",
              "쿠버네티스 첫 실습 매니페스트는 `kubernetes/first-attempts`에 있습니다(minikube 필요)."]
        return s
    k8s_default = n >= 18
    s += ["**도커 컴포즈로 실행** (RabbitMQ)", "", "```bash", f"cd {d}", "./gradlew build", "docker compose build",
          (DC if k8s_default else "") + "./test-em-all.bash start stop", "```"]
    if n >= 7:
        s += ["", "**Kafka / 파티션 구성**", "", "```bash",
              "COMPOSE_FILE=docker-compose-kafka.yml " + (DC if k8s_default else "") + "./test-em-all.bash start stop",
              "COMPOSE_FILE=docker-compose-partitions.yml " + (DC if k8s_default else "") + "./test-em-all.bash start stop", "```"]
    if n == 16:
        s += ["", "**쿠버네티스(minikube)에 배포**", "", "```bash",
              "minikube start --driver=docker --container-runtime=docker --cpus=4 --memory=10g",
              "eval $(minikube docker-env) && docker compose build",
              "for f in kubernetes/helm/components/*; do helm dep up $f; done",
              "for f in kubernetes/helm/environments/*; do helm dep up $f; done",
              "helm install hands-on-dev-env kubernetes/helm/environments/dev-env -n hands-on --create-namespace",
              "kubectl wait --timeout=900s --for=condition=ready pod --all -n hands-on",
              "HOST=$(minikube ip) PORT=30443 USE_K8S=true ./test-em-all.bash", "```"]
    if n == 17:
        s += ["", "**쿠버네티스(minikube)에 배포** — Ingress와 cert-manager 사용", "", "```bash",
              "minikube start --driver=docker --container-runtime=docker --cpus=4 --memory=10g",
              "minikube addons enable ingress",
              "helm repo add jetstack https://charts.jetstack.io",
              "helm install cert-manager jetstack/cert-manager --create-namespace -n cert-manager --set crds.enabled=true --wait",
              "eval $(minikube docker-env) && docker compose build",
              "for f in kubernetes/helm/components/*; do helm dep up $f; done",
              "for f in kubernetes/helm/environments/*; do helm dep up $f; done",
              "helm install hands-on-dev-env kubernetes/helm/environments/dev-env -n hands-on --create-namespace",
              "kubectl wait --timeout=900s --for=condition=ready pod --all -n hands-on",
              'echo "$(minikube ip) minikube.me" | sudo tee -a /etc/hosts',
              "HOST=minikube.me PORT=443 USE_K8S=true ./test-em-all.bash", "```"]
    if n >= 18:
        s += ["", "**쿠버네티스 + 이스티오에 배포** (테스트 스크립트의 기본값이 이 구성입니다)", "", "```bash",
              "minikube start --driver=docker --container-runtime=docker --cpus=4 --memory=12g",
              "helm repo add jetstack https://charts.jetstack.io",
              "helm install cert-manager jetstack/cert-manager --create-namespace -n cert-manager --set crds.enabled=true --wait",
              "curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.31.4 sh -",
              "istioctl install --skip-confirmation --set profile=demo \\",
              "  --set meshConfig.accessLogFile=/dev/stdout --set meshConfig.accessLogEncoding=JSON \\",
              "  --set values.pilot.env.PILOT_JWT_PUB_KEY_REFRESH_INTERVAL=15s -f kubernetes/istio-tracing.yml",
              "kubectl apply -n istio-system -f kubernetes/istio-telemetry.yml",
              "for a in kiali jaeger prometheus grafana; do kubectl apply -n istio-system -f istio-1.31.4/samples/addons/$a.yaml; done",
              "for f in kubernetes/helm/components/*; do helm dep up $f; done",
              "for f in kubernetes/helm/environments/*; do helm dep up $f; done",
              "helm upgrade --install istio-hands-on-addons kubernetes/helm/environments/istio-system -n istio-system --wait",
              "minikube tunnel   # 별도 터미널에서 실행",
              "INGRESS_IP=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')",
              'echo "$INGRESS_IP minikube.me health.minikube.me grafana.minikube.me kiali.minikube.me prometheus.minikube.me tracing.minikube.me" | sudo tee -a /etc/hosts',
              "eval $(minikube docker-env) && docker compose build",
              "kubectl apply -f kubernetes/hands-on-namespace.yml",
              "helm install hands-on-dev-env kubernetes/helm/environments/dev-env -n hands-on",
              "kubectl wait --timeout=900s --for=condition=ready pod --all -n hands-on",
              "./test-em-all.bash", "```"]
    if n == 23:
        s += ["", "**네이티브 이미지로 실행** (빌드팩이 GraalVM 25를 사용, 서비스당 수 분 소요)", "", "```bash",
              "for s in product recommendation review product-composite; do",
              "  ./gradlew :microservices:$s-service:bootBuildImage", "done",
              "COMPOSE_FILE=docker-compose-native.yml " + DC + "./test-em-all.bash start stop",
              "COMPOSE_FILE=docker-compose-partitions-native.yml " + DC + "./test-em-all.bash start stop", "```"]
    return s


def migration_headings(n):
    f = os.path.join(ROOT, f"Chapter{n:02d}", "MIGRATION-BOOT4.md")
    if not os.path.exists(f):
        return []
    return [re.sub(r"^## \d+\. ", "", l).strip() for l in open(f, encoding="utf-8") if l.startswith("## ")]


def chapter_page(n):
    c = C[n]
    p = PARTS[c["part"]][0]
    out = [f"# {n}장 {c['t']}", "", f"> {p}", ""]
    prev_n = n - 1 if n > 1 else None
    next_n = n + 1 if n < 23 else None
    nav = []
    if prev_n: nav.append("← " + link(prev_n))
    nav.append("[목차](Home)")
    if next_n: nav.append(link(next_n) + " →")
    out += [" | ".join(nav), "", "## 학습 목표", ""] + [f"- {g}" for g in c["goals"]] + [""]
    if c["tech"]:
        out += ["## 이 장의 기술", "", ", ".join(f"`{t}`" for t in c["tech"]), ""]
    if not c["code"]:
        out += ["## 실습 코드", "", "이 장은 개념 설명 장이라 별도 예제 코드가 없습니다."]
        if n in (21, 22):
            out += ["", "이 저장소 코드가 검증된 도구 버전은 [실습 환경 준비](실습-환경-준비) 페이지를 참고하세요. "
                    "macOS·윈도우(WSL 2) 환경 자체는 CI에서 검증하지 않았습니다."]
        out += [""]
    else:
        d = f"Chapter{n:02d}"
        out += ["## 실습 코드", "", f"- 코드: [`{d}`]({GH}/tree/main/{d})",
                f"- Boot 4 변경 내역: [`{d}/MIGRATION-BOOT4.md`]({GH}/blob/main/{d}/MIGRATION-BOOT4.md)", "",
                "## 실행하기", ""] + run_section(n) + [""]
        key = "Chapter03/2-basic-rest-services" if n == 3 else d
        if key in DELTA:
            x = DELTA[key]
            out += ["## 이전 장에서 달라진 점", "", f"`{x['prev']}` → `{key}` 비교 (코드에서 자동 추출)", ""]
            if x["new_modules"]:
                out.append("- **새 모듈**: " + ", ".join(f"`{m}`" for m in x["new_modules"]))
            if x["new_deps"]:
                out.append("- **새 의존성**: " + ", ".join(f"`{m}`" for m in x["new_deps"]))
            out.append(f"- **파일**: 추가 {len(x['added'])}개 · 변경 {len(x['changed'])}개 · 삭제 {len(x['removed'])}개")
            if x["changed"]:
                out += ["", "많이 바뀐 파일:", ""] + [f"- `{p}` ({c}줄)" for p, c in x["changed"][:6]]
            if x["added"]:
                out += ["", "<details><summary>추가된 파일 목록</summary>", ""] + [f"- `{p}`" for p in x["added"][:40]] + (["- …"] if len(x["added"]) > 40 else []) + ["", "</details>"]
            out += ["", "```bash", f"git diff --no-index --stat {x['prev']} {key}   # 직접 비교", "```", ""]
        mh = migration_headings(n)
        if mh:
            out += ["## 원본(Boot 3.5 / Java 24)과 달라진 점", ""] + [f"- {h}" for h in mh] + [""]
    if n in QA:
        out += ["## 복습 질문", ""]
        for i, (q, a) in enumerate(QA[n], 1):
            out += [f"**Q{i}. {q}**", "", "<details><summary>답 보기</summary>", "", a, "", "</details>", ""]
    out += ["## 학습 이슈", "", f"학습 이슈 [#{n}]({GH}/issues/{n})의 하위 이슈(개념 · 코드 분석 · 실습 · 심화)를 순서대로 진행하며 닫아 가세요. 하위 이슈를 닫을 때마다 #{n}의 진행률이 올라갑니다.", ""]
    out += [" | ".join(nav)]
    return "\n".join(out) + "\n"


def issue_body(n):
    c = C[n]
    tasks = []
    if c["code"]:
        d = f"Chapter{n:02d}"
        tasks += [f"교재 {n}장 읽기", f"`{d}` 코드 구조 살펴보기 (새로 추가된 모듈·설정 확인)",
                  "`./gradlew build`로 빌드와 테스트 통과 확인"]
        if n == 3:
            tasks += ["서비스 4개를 띄우고 `./test-em-all.bash` 실행"]
        else:
            tasks += ["`./test-em-all.bash start stop`으로 도커 컴포즈 전체 테스트 실행"]
        if n >= 7:
            tasks += ["Kafka 구성(`COMPOSE_FILE=docker-compose-kafka.yml`)으로 실행해 보기"]
        if n in (16, 17):
            tasks += ["minikube에 헬름으로 배포하고 테스트 실행"]
        if n >= 18:
            tasks += ["minikube + 이스티오에 배포하고 `./test-em-all.bash` 실행"]
        if n == 23:
            tasks += ["네이티브 이미지 빌드 후 `docker-compose-native.yml`로 테스트", "JVM 이미지와 기동 시간·메모리 비교"]
        tasks += [f"`{d}/MIGRATION-BOOT4.md`에서 Boot 4 변경점 확인"]
    else:
        tasks += [f"교재 {n}장 읽기", "핵심 개념 정리하기"]
    body = [f"## {n}장 {c['t']}", "", f"**{PARTS[c['part']][0]}**", "", "### 학습 목표", ""]
    body += [f"- {g}" for g in c["goals"]]
    body += ["", "### 체크리스트", ""] + [f"- [ ] {t}" for t in tasks]
    body += ["", "### 참고", "", f"- 위키: {GH}/wiki/{page_name(n)}"]
    if c["code"]:
        body += [f"- 코드: {GH}/tree/main/Chapter{n:02d}"]
    body += ["", "진행하면서 막히는 부분은 이 이슈에 댓글로 남기거나, `질문` 템플릿으로 새 이슈를 만들어 주세요."]
    return "\n".join(body) + "\n"


def home():
    out = ["# 스프링 부트 4 마이크로서비스 학습 가이드", "",
           "『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 예제를 **Spring Boot 4.0.9 / Java 21 / Spring Cloud 2025.1.4**로 옮긴 코드로 장별 학습을 진행하는 가이드입니다.", "",
           "## 진행 방법", "",
           "1. [실습 환경 준비](실습-환경-준비)에서 도구를 설치합니다.",
           "2. 아래 목차를 따라 장별 페이지에서 학습 목표와 실행 방법을 확인합니다.",
           f"3. [장별 학습 이슈]({GH}/issues?q=is%3Aissue+label%3A학습+sort%3Acreated-asc)(#1 = 1장 … #23 = 23장)의 하위 이슈(`개념` · `코드 분석` · `실습` · `심화`)를 순서대로 진행하며 닫습니다. 하위 이슈를 닫을 때마다 상위 이슈의 진행률이 올라갑니다.",
           f"4. 진도는 [마일스톤]({GH}/milestones)(1부·2부·3부)에서, 장·부별 이슈는 라벨 `chXX` · `1부`/`2부`/`3부`로 걸러 볼 수 있습니다.",
           "5. 설치 없이 실습하려면 [Codespaces와 컨테이너 이미지](Codespaces와-컨테이너-이미지)를 참고하세요.",
           f"6. 궁금한 점은 [Discussions]({GH}/discussions)에, 재현되는 실행 오류는 [자주 발생하는 문제](자주-발생하는-문제)를 확인한 뒤 이슈로 남겨 주세요.", "",
           "## 목차", ""]
    for p in (1, 2, 3):
        out += [f"### {PARTS[p][0]}", "", PARTS[p][1], ""]
        for n in sorted(k for k in C if C[k]["part"] == p):
            out.append(f"- {link(n)}" + ("" if C[n]["code"] else " _(개념)_"))
        out.append("")
    out += ["## 참고", "", "- [Spring Boot 4 마이그레이션 요약](Spring-Boot-4-마이그레이션-요약)",
            "- [자주 발생하는 문제](자주-발생하는-문제)",
            "- [브랜치 전략](브랜치-전략)",
            f"- 전체 변경 내역: [MIGRATION-BOOT4.md]({GH}/blob/main/MIGRATION-BOOT4.md)",
            f"- CI 실행 결과: [Actions]({GH}/actions)"]
    return "\n".join(out) + "\n"


def sidebar():
    out = ["**[홈](Home)**", "", "[실습 환경 준비](실습-환경-준비)", ""]
    for p in (1, 2, 3):
        out += [f"**{PARTS[p][0].split(':')[0]}**", ""]
        for n in sorted(k for k in C if C[k]["part"] == p):
            out.append(f"- [{n}장 {C[n]['t']}]({page_name(n)})")
        out.append("")
    out += ["**참고**", "", "- [Boot 4 마이그레이션 요약](Spring-Boot-4-마이그레이션-요약)", "- [자주 발생하는 문제](자주-발생하는-문제)", "- [브랜치 전략](브랜치-전략)", "- [Codespaces와 이미지](Codespaces와-컨테이너-이미지)"]
    return "\n".join(out) + "\n"


ENV_PAGE = f"""# 실습 환경 준비

이 저장소의 코드는 아래 버전으로 GitHub Actions(우분투)에서 빌드·테스트·배포가 검증되었습니다.

| 도구 | 버전 | 용도 |
|---|---|---|
| JDK | 21 (Temurin) | 모든 장 |
| Gradle | 8.14.6 (래퍼 포함, 설치 불필요) | 모든 장 |
| Docker / Docker Compose | Docker Engine + compose v2 | 4장 이후 |
| curl, jq | 최신 | `test-em-all.bash` |
| minikube | 최신 (`--driver=docker --container-runtime=docker`) | 15장 이후 |
| kubectl, Helm | 최신 (Helm 3) | 16장 이후 |
| cert-manager | jetstack 차트 최신 | 17장 이후 |
| Istio | 1.31.4 | 18장 이후 |
| GraalVM | 25 (빌드팩이 자동 사용, 로컬 설치 불필요) | 23장 |

## 메모리

- 도커 컴포즈 실습: Docker에 메모리 8GB 이상 할당을 권장합니다(Kafka 구성은 더 필요).
- minikube 실습: `--memory=10g` 이상, 이스티오 장은 `--memory=12g`를 권장합니다.

## 확인

```bash
java -version          # 21
docker compose version
jq --version
```

macOS·윈도우(WSL 2) 설치 절차는 교재 21장·22장을 따르되, JDK는 **21**을 설치하세요. 이 두 환경은 CI에서 직접 검증하지 않았습니다.
"""

MIG_PAGE = f"""# Spring Boot 4 마이그레이션 요약

교재 원본(Java 24 / Spring Boot 3.5 / Spring Cloud 2025.0)과 이 저장소 코드의 차이 중 학습할 때 알아 두면 좋은 것들입니다. 전체 목록은 [MIGRATION-BOOT4.md]({GH}/blob/main/MIGRATION-BOOT4.md)에 있습니다.

## 교재 본문과 다르게 보이는 부분

| 위치 | 교재 | 이 저장소 |
|---|---|---|
| Dockerfile (4장~) | `-Djarmode=layertools` | `-Djarmode=tools extract --layers --launcher` |
| MongoDB 설정 (6장~) | `spring.data.mongodb.host` | `spring.mongodb.host` |
| 오류 메시지 설정 | `server.error.include-message` | `spring.web.error.include-message` |
| 422 상태 코드 | `HttpStatus.UNPROCESSABLE_ENTITY` | `HttpStatus.UNPROCESSABLE_CONTENT` |
| Jackson | `com.fasterxml.jackson.databind.*` | `tools.jackson.databind.*` (Jackson 3) |
| 인가 서버 설정 클래스 (11장~) | `...oauth2.server.authorization.config.annotation...` | `org.springframework.security.config.annotation...` |
| AOP 스타터 (12장~) | `spring-boot-starter-aop` | `spring-boot-starter-aspectj` |
| Resilience4j (13장~) | `resilience4j-spring-boot3` | `resilience4j-spring-boot4` |
| Zipkin 설정 (14장~) | `management.zipkin.tracing.endpoint` | `management.tracing.export.zipkin.endpoint` |
| 테스트 | `@SpringBootTest`만으로 WebTestClient 주입 | `@AutoConfigureWebTestClient` 추가 |

## 동작이 달라진 부분

- **DTO의 `final` 필드**: Jackson 3는 `final` 필드를 역직렬화하지 않아 api 모듈 DTO의 `final`을 제거했습니다.
- **enum 직렬화**: Jackson 3는 enum을 `toString()`으로 씁니다. 회로 차단기 이벤트를 교재와 같은 `CLOSED_TO_OPEN` 형태로 유지하려고 `spring.jackson.datatype.enum.write-enums-using-to-string: false`를 설정했습니다(13장~).
- **헬스 응답**: liveness/readiness 프로브가 기본으로 켜져 `/actuator/health`에 `groups`가 추가됩니다.
- **네이티브 이미지 (23장)**: GraalVM 25 이상이 필요합니다(빌드팩에 `BP_JVM_VERSION=25`).
"""

TROUBLE_PAGE = """# 자주 발생하는 문제

CI에서 반복 실행하며 실제로 겪은 문제와 해결 방법입니다.

## `test-em-all.bash`가 간헐적으로 실패한다 (Kafka·파티션 구성)

기동 직후 메시지 처리나 유레카 등록이 아직 끝나지 않아 생기는 타이밍 문제입니다. 이 저장소에서는 다음을 보강했습니다.

- Kafka 헬스체크 후 서비스 기동 (`docker-compose-kafka.yml`)
- 상품 113·213의 메시지 처리까지 대기 (`testCompositeCreated`)
- 유레카 등록 완료까지 최대 60초 대기 (9~15장)

그래도 실패하면 `docker compose down` 후 다시 실행해 보고, Docker 메모리 할당을 늘려 보세요.

## `eval $(minikube docker-env)` 후 이미지 빌드가 실패한다

minikube가 containerd 런타임으로 시작된 경우입니다. 교재처럼 Docker 런타임으로 다시 만드세요.

```bash
minikube delete
minikube start --driver=docker --container-runtime=docker --cpus=4 --memory=12g
```

## Istio 설치 스크립트가 버전을 찾지 못한다

`Unable to get latest Istio version`이 나오면 버전을 지정합니다.

```bash
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.31.4 sh -
```

## 네이티브 이미지 빌드가 실패한다 (23장)

Spring Boot 4는 GraalVM 25 이상이 필요합니다. `bootBuildImage`는 빌드팩이 GraalVM 25를 받아 쓰도록 설정되어 있습니다. 로컬에서 `./gradlew nativeCompile`을 쓰려면 GraalVM 25를 설치하고 그 JDK로 Gradle을 실행하세요. 네이티브 빌드는 메모리를 많이 쓰므로 Docker에 8GB 이상을 할당하세요.

## 422 대신 500이 나온다 / `Unprocessable Entity` 문자열이 다르다

Spring Framework 7에서 422의 이름이 `UNPROCESSABLE_CONTENT`(`"Unprocessable Content"`)로 바뀌었습니다. 이 저장소 코드는 이미 반영되어 있습니다. 교재 코드를 직접 옮겨 적을 때 주의하세요.
"""


def main():
    wd = os.path.join(ROOT, "docs", "wiki")
    os.makedirs(wd, exist_ok=True)
    files = {"Home.md": home(), "_Sidebar.md": sidebar(),
             "_Footer.md": f"Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4 — [저장소]({GH}) · [이슈]({GH}/issues) · [Discussions]({GH}/discussions) · [릴리스]({GH}/releases) · [CI]({GH}/actions)\n"}
    # Hand-maintained pages are created only once and never overwritten
    for k, v in {"실습-환경-준비.md": ENV_PAGE, "Spring-Boot-4-마이그레이션-요약.md": MIG_PAGE, "자주-발생하는-문제.md": TROUBLE_PAGE}.items():
        if not os.path.exists(os.path.join(wd, k)):
            files[k] = v
    for n in C:
        files[page_name(n) + ".md"] = chapter_page(n)
    for k, v in files.items():
        open(os.path.join(wd, k), "w", encoding="utf-8").write(v)
    issues = [{"n": n, "title": f"[{n:02d}장] {C[n]['t']}", "body": issue_body(n),
               "labels": ["학습", f"ch{n:02d}"] + ([] if C[n]["code"] else ["개념"]),
               "part": C[n]["part"]} for n in sorted(C)]
    if "--issues" in sys.argv:
        out = sys.argv[sys.argv.index("--issues") + 1]
        json.dump({"parts": {k: v for k, v in PARTS.items()}, "issues": issues},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wiki pages:", len(files), "issues:", len(issues))


main()
