# 19장 워크북 — EFK 스택을 사용한 중앙 집중식 로깅

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 19장 · 영문 3판 p.523–562 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter19/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter19`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter19) · 위키: [19장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/19장-EFK-스택을-사용한-중앙-집중식-로깅)

## 이 장에서 만드는 것

**EFK 스택**(Elasticsearch, Fluentd, Kibana)으로 로그를 모읍니다.

- Fluentd 이미지와 데몬셋, 설정 ConfigMap
- `logging` 환경 차트로 Elasticsearch·Kibana 배포

## 시작하기

18장을 끝낸 작업 폴더를 복사해서 시작합니다. 18장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter18 Chapter19          # 내가 만든 18장 결과에서 시작
# 또는: cp -r <저장소>/Chapter18 Chapter19        # 저장소의 18장 완성 코드에서 시작
cd Chapter19 && ./gradlew clean -q
```

## 단계 목록

1. [`kubernetes/efk` — Fluentd 이미지와 설정](#단계-1) — 새 파일 4
2. [헬름 `environments` 차트 — 환경별 묶음](#단계-2) — 새 파일 6

<a id="단계-1"></a>

## 단계 1. `kubernetes/efk` — Fluentd 이미지와 설정

Fluentd 이미지를 만드는 `Dockerfile`, 노드마다 실행되는 데몬셋, 로그를 해석하는 설정(`fluentd-hands-on-configmap.yml`)입니다.

#### `kubernetes/efk/Dockerfile` — 새 파일 (6줄)

<!-- wb:file path="kubernetes/efk/Dockerfile" op="write" nl="1" -->
```dockerfile
FROM fluent/fluentd-kubernetes-daemonset:v1.4.2-debian-elasticsearch-1.1

RUN gem install fluent-plugin-detect-exceptions -v 0.0.12 \
 && gem sources --clear-all \
 && rm -rf /var/lib/apt/lists/* \
           /home/fluent/.gem/ruby/2.3.0/cache/*.gem
```

#### `kubernetes/efk/fluentd-ds.yml` — 새 파일 (66줄)

<!-- wb:file path="kubernetes/efk/fluentd-ds.yml" op="write" nl="1" -->
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
  labels:
    app: fluentd
    version: v1
spec:
  selector:
    matchLabels:
        app: fluentd
        version: v1
  template:
    metadata:
      labels:
        app: fluentd
        version: v1
    spec:
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: fluentd
        image: hands-on/fluentd:v1
        env:
          - name:  FLUENT_ELASTICSEARCH_HOST
            value: "elasticsearch.logging"
          - name:  FLUENT_ELASTICSEARCH_PORT
            value: "9200"
          - name: FLUENT_ELASTICSEARCH_SCHEME
            value: "http"
          - name: FLUENT_ELASTICSEARCH_SED_DISABLE
            value: "true"
        resources:
          limits:
            cpu: 500m
            memory: 500Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: journal
          mountPath: /var/log/journal
          readOnly: true
        - name: fluentd-extra-config
          mountPath: /fluentd/etc/conf.d
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: journal
        hostPath:
          path: /run/log/journal
      - name: fluentd-extra-config
        configMap:
          name: "fluentd-hands-on-config"
      terminationGracePeriodSeconds: 30
```

#### `kubernetes/efk/fluentd-hands-on-configmap.yml` — 새 파일 (92줄)

<!-- wb:file path="kubernetes/efk/fluentd-hands-on-configmap.yml" op="write" nl="1" -->
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-hands-on-config
  namespace: kube-system
data:
  fluentd-hands-on.conf: |

    <match kubernetes.**istio**>
      @type rewrite_tag_filter
      <rule>
        key log
        pattern ^(.*)$
        tag istio.${tag}
      </rule>
    </match>

    <match kubernetes.**hands-on**>
      @type rewrite_tag_filter
      <rule>
        key log
        pattern ^(.*)$
        tag spring-boot.${tag}
      </rule>
    </match>

    <match spring-boot.**>
      @type rewrite_tag_filter
      <rule>
        key log
        pattern /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}([-+]\d{2}:\d{2}|Z).*/
        tag parse.${tag}
      </rule>
      # Get rid of Reactor debug info:
      #
      #   Suppressed: reactor.core.publisher.FluxOnAssembly$OnAssemblyException:
      # Error has been observed at the following site(s):
      #   *__checkpoint ⇢ Handler se.magnus.microservices.core.product.services.ProductServiceImpl#getProduct(HttpHeaders, int, int, int) [DispatcherHandler]
      #   *__checkpoint ⇢ org.springframework.web.filter.reactive.ServerHttpObservationFilter [DefaultWebFilterChain]
      #   *__checkpoint ⇢ HTTP GET "/product/1?faultPercent=100" [ExceptionHandlingWebHandler]
      # Original Stack Trace:
      <rule>
        key log
        pattern /^\s+Suppressed:.*$/
        tag skip.${tag}
      </rule>
      <rule>
        key log
        pattern /^Error has been observed at the following site.*/
        tag skip.${tag}
      </rule>
      <rule>
        key log
        pattern /^\s+\*__checkpoint.*/
        tag skip.${tag}
      </rule>
      <rule>
        key log
        pattern /^Original Stack Trace:.*/
        tag skip.${tag}
      </rule>

      <rule>
        key log
        pattern /^.*/
        tag check.exception.${tag}
      </rule>
    </match>

    <match skip.spring-boot.**>
      @type null
    </match>

    <match check.exception.spring-boot.**>
      @type detect_exceptions
      languages java
      remove_tag_prefix check
      message log
      multiline_flush_interval 5
    </match>

    <filter parse.spring-boot.**>
      @type parser
      key_name log
      time_key time
      time_format %Y-%m-%dT%H:%M:%S.%N
      reserve_data true
      # Sample log messages:
      # 2025-03-12T20:03:53.168+01:00  INFO 1 --- [     parallel-3] [product-composite,67d1e8a919c841e2c7a0fc30e2585f78,0522b62d4c2f4998] s.m.m.c.p.s.ProductCompositeServiceImpl  : Will get composite product info for product.id=1
      # 2025-03-12T20:03:53.168Z  INFO 1 --- [     parallel-3] [product-composite,67d1e8a919c841e2c7a0fc30e2585f78,0522b62d4c2f4998] s.m.m.c.p.s.ProductCompositeServiceImpl  : Will get composite product info for product.id=1
      format /^(?<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}([-+]\d{2}:\d{2}|Z))\s+(?<spring.level>[^\s]+)\s+(?<spring.pid>\d+)\s+---\s+\[\s*(?<spring.thread>[^\]]+)\]\s+(\[(?<spring.service>[^,]*),(?<spring.trace>[^,]*),(?<spring.span>[^\]]*)]*\])\s+(?<spring.class>[^\s]+)\s*:\s+(?<log>.*)$/
    </filter>
```

#### `kubernetes/efk/kibana-api-exported-objects.ndjson` — 복사/생성

Kibana에서 내보낸 객체입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/efk/kibana-api-exported-objects.ndjson" op="copy" nl="0" -->

<a id="단계-2"></a>

## 단계 2. 헬름 `environments` 차트 — 환경별 묶음

Elasticsearch·Kibana를 배포하고 노출하는 `logging` 환경 차트를 추가합니다.

#### `kubernetes/helm/environments/logging/Chart.yaml` — 새 파일 (6줄)

<!-- wb:file path="kubernetes/helm/environments/logging/Chart.yaml" op="write" nl="1" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for added definitions in the logging namespace
name: logging
version: 1.0.0

```

#### `kubernetes/helm/environments/logging/templates/elasticsearch.yml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/environments/logging/templates/elasticsearch.yml" op="write" nl="0" -->
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: elasticsearch
spec:
  selector:
    matchLabels:
      component: elasticsearch
  template:
    metadata:
      labels:
        component: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.17.28
        env:
        - name: discovery.type
          value: single-node
        ports:
        - containerPort: 9200
          name: http
          protocol: TCP
        resources:
          limits:
            cpu: 500m
            memory: 2Gi
          requests:
            cpu: 500m
            memory: 2Gi

---

apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  labels:
    service: elasticsearch
spec:
  type: ClusterIP
  selector:
    component: elasticsearch
  ports:
  - port: 9200
    targetPort: 9200
```

#### `kubernetes/helm/environments/logging/templates/expose-elasticsearch.yml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/environments/logging/templates/expose-elasticsearch.yml" op="write" nl="1" -->
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: elasticsearch-gateway
  namespace: logging
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - "elasticsearch.minikube.me"
    port:
      number: 443
      name: https-tracing
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: hands-on-certificate
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: elasticsearch-vs
  namespace: logging
spec:
  hosts:
  - "elasticsearch.minikube.me"
  gateways:
  - elasticsearch-gateway
  http:
  - route:
    - destination:
        host: elasticsearch
        port:
          number: 9200
---
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: elasticsearch
  namespace: logging
spec:
  host: elasticsearch
  trafficPolicy:
    tls:
      mode: DISABLE
```

#### `kubernetes/helm/environments/logging/templates/expose-kibana.yml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/environments/logging/templates/expose-kibana.yml" op="write" nl="1" -->
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: kibana-gateway
  namespace: logging
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - "kibana.minikube.me"
    port:
      number: 443
      name: https-tracing
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: hands-on-certificate
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: kibana-vs
  namespace: logging
spec:
  hosts:
  - "kibana.minikube.me"
  gateways:
  - kibana-gateway
  http:
  - route:
    - destination:
        host: kibana
        port:
          number: 5601
---
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: kibana
  namespace: logging
spec:
  host: kibana
  trafficPolicy:
    tls:
      mode: DISABLE
```

#### `kubernetes/helm/environments/logging/templates/kibana.yml` — 새 파일 (39줄)

<!-- wb:file path="kubernetes/helm/environments/logging/templates/kibana.yml" op="write" nl="0" -->
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
spec:
  selector:
    matchLabels:
      run: kibana
  template:
    metadata:
      labels:
        run: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:7.17.28
        env:
        - name: ELASTICSEARCH_URL
          value: http://elasticsearch:9200
        ports:
        - containerPort: 5601
          name: http
          protocol: TCP

---

apiVersion: v1
kind: Service
metadata:
  name: kibana
  labels:
    service: kibana
spec:
  type: ClusterIP
  selector:
    run: kibana
  ports:
  - port: 5601
    targetPort: 5601
```

#### `kubernetes/helm/environments/logging/values.yaml` — 빈 파일

내용이 없는 파일입니다.

```bash
mkdir -p kubernetes/helm/environments/logging && touch kubernetes/helm/environments/logging/values.yaml
```

<!-- wb:file path="kubernetes/helm/environments/logging/values.yaml" op="empty" -->

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter19
./gradlew build
docker compose build
HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 USE_K8S=false ./test-em-all.bash start stop
```

**Kafka / 파티션 구성**

```bash
COMPOSE_FILE=docker-compose-kafka.yml HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 USE_K8S=false ./test-em-all.bash start stop
COMPOSE_FILE=docker-compose-partitions.yml HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 USE_K8S=false ./test-em-all.bash start stop
```

**쿠버네티스 + 이스티오에 배포** (테스트 스크립트의 기본값이 이 구성입니다)

```bash
minikube start --driver=docker --container-runtime=docker --cpus=4 --memory=12g
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager --create-namespace -n cert-manager --set crds.enabled=true --wait
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.31.4 sh -
istioctl install --skip-confirmation --set profile=demo \
  --set meshConfig.accessLogFile=/dev/stdout --set meshConfig.accessLogEncoding=JSON \
  --set values.pilot.env.PILOT_JWT_PUB_KEY_REFRESH_INTERVAL=15s -f kubernetes/istio-tracing.yml
kubectl apply -n istio-system -f kubernetes/istio-telemetry.yml
for a in kiali jaeger prometheus grafana; do kubectl apply -n istio-system -f istio-1.31.4/samples/addons/$a.yaml; done
for f in kubernetes/helm/components/*; do helm dep up $f; done
for f in kubernetes/helm/environments/*; do helm dep up $f; done
helm upgrade --install istio-hands-on-addons kubernetes/helm/environments/istio-system -n istio-system --wait
minikube tunnel   # 별도 터미널에서 실행
INGRESS_IP=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "$INGRESS_IP minikube.me health.minikube.me grafana.minikube.me kiali.minikube.me prometheus.minikube.me tracing.minikube.me" | sudo tee -a /etc/hosts
eval $(minikube docker-env) && docker compose build
kubectl apply -f kubernetes/hands-on-namespace.yml
helm install hands-on-dev-env kubernetes/helm/environments/dev-env -n hands-on
kubectl wait --timeout=900s --for=condition=ready pod --all -n hands-on
./test-em-all.bash
```

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter19
```

---

← [18장 워크북](Chapter18.md) · [워크북 목차](README.md) · [20장 워크북](Chapter20.md) →
