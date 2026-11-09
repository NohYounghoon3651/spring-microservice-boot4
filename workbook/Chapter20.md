# 20장 워크북 — 마이크로서비스 모니터링

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 20장 · 영문 3판 p.563–598 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter20/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter20`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter20) · 위키: [20장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/20장-마이크로서비스-모니터링)

## 이 장에서 만드는 것

**Prometheus와 Grafana**로 마이크로서비스를 모니터링합니다.

- 모든 서비스에 `micrometer-registry-prometheus` 추가, `/actuator/prometheus` 노출
- 메일 서버 노출 설정과 Grafana 대시보드

## 시작하기

19장을 끝낸 작업 폴더를 복사해서 시작합니다. 19장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter19 Chapter20          # 내가 만든 19장 결과에서 시작
# 또는: cp -r <저장소>/Chapter19 Chapter20        # 저장소의 19장 완성 코드에서 시작
cd Chapter20 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 수정 1
2. [`product-service`](#단계-2) — 수정 1
3. [`recommendation-service`](#단계-3) — 수정 1
4. [`review-service`](#단계-4) — 수정 1
5. [`product-composite-service`](#단계-5) — 수정 1
6. [`authorization-server` — OAuth 2.0 인가 서버](#단계-6) — 수정 1
7. [`config-repo` — 중앙 구성 파일](#단계-7) — 수정 2
8. [`kubernetes/grafana` — 대시보드](#단계-8) — 새 파일 1
9. [헬름 `components` 차트 — 서비스별 차트](#단계-9) — 수정 13
10. [헬름 `environments` 차트 — 환경별 묶음](#단계-10) — 새 파일 1

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

`test-em-all.bash`에 쿠버네티스에서 `/actuator/prometheus` 지표를 확인하는 테스트를 추가합니다.

#### `test-em-all.bash` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -336,6 +336,13 @@
 fi
 assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/v3/api-docs.yaml"
 
+if [[ $USE_K8S == "true" ]]
+then
+  # Verify access to Prometheus formatted metrics
+  echo "Prometheus metrics tests"
+  assertCurl 200 "curl -ks https://health.minikube.me/actuator/prometheus"
+fi
+
 if [[ $SKIP_CB_TESTS == "false" ]]
 then
     testCircuitBreaker
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="test-em-all.bash" op="write" nl="1" -->
```bash
#!/usr/bin/env bash
#
# With Docker Compose:
#
#   HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 USE_K8S=false ./test-em-all.bash
#
# With Kubernetes:
#
#   ./test-em-all.bash
#
: ${HOST=minikube.me}
: ${PORT=443}
: ${USE_K8S=true}
: ${HEALTH_URL=https://health.minikube.me}
: ${MGM_PORT=4004}
: ${PROD_ID_REVS_RECS=1}
: ${PROD_ID_NOT_FOUND=13}
: ${PROD_ID_NO_RECS=113}
: ${PROD_ID_NO_REVS=213}
: ${SKIP_CB_TESTS=false}
: ${NAMESPACE=hands-on}

function assertCurl() {

  local expectedHttpCode=$1
  local curlCmd="$2 -w \"%{http_code}\""
  local result=$(eval $curlCmd)
  local httpCode="${result:(-3)}"
  RESPONSE='' && (( ${#result} > 3 )) && RESPONSE="${result%???}"

  if [ "$httpCode" = "$expectedHttpCode" ]
  then
    if [ "$httpCode" = "200" ]
    then
      echo "Test OK (HTTP Code: $httpCode)"
    else
      echo "Test OK (HTTP Code: $httpCode, $RESPONSE)"
    fi
  else
    echo  "Test FAILED, EXPECTED HTTP Code: $expectedHttpCode, GOT: $httpCode, WILL ABORT!"
    echo  "- Failing command: $curlCmd"
    echo  "- Response Body: $RESPONSE"
    exit 1
  fi
}

function assertEqual() {

  local expected=$1
  local actual=$2

  if [ "$actual" = "$expected" ]
  then
    echo "Test OK (actual value: $actual)"
  else
    echo "Test FAILED, EXPECTED VALUE: $expected, ACTUAL VALUE: $actual, WILL ABORT"
    exit 1
  fi
}

function testUrl() {
  url=$@
  if $url -ks -f -o /dev/null
  then
    return 0
  else
    return 1
  fi;
}

function waitForService() {
  url=$@
  echo -n "Wait for: $url... "
  n=0
  until testUrl $url
  do
    n=$((n + 1))
    if [[ $n == 100 ]]
    then
      echo " Give up"
      exit 1
    else
      sleep 3
      echo -n ", retry #$n "
    fi
  done
  echo "DONE, continues..."
}

function testCompositeCreated() {

    # Expect that the Product Composite for productId $PROD_ID_REVS_RECS has been created with three recommendations and three reviews
    if ! assertCurl 200 "curl $AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"
    then
        echo -n "FAIL"
        return 1
    fi

    set +e
    assertEqual "$PROD_ID_REVS_RECS" $(echo $RESPONSE | jq .productId)
    if [ "$?" -eq "1" ] ; then return 1; fi

    assertEqual 3 $(echo $RESPONSE | jq ".recommendations | length")
    if [ "$?" -eq "1" ] ; then return 1; fi

    assertEqual 3 $(echo $RESPONSE | jq ".reviews | length")
    if [ "$?" -eq "1" ] ; then return 1; fi

    # Also wait for the products without recommendations and reviews. With Kafka their messages
    # can be processed later than the ones above, e.g. while consumer groups are rebalanced.
    if ! assertCurl 200 "curl $AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_NO_RECS -s"
    then
        echo -n "FAIL"
        return 1
    fi
    if ! assertCurl 200 "curl $AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_NO_REVS -s"
    then
        echo -n "FAIL"
        return 1
    fi
    set -e
}

function waitForMessageProcessing() {
    echo "Wait for messages to be processed... "

    # Give background processing some time to complete...
    sleep 1

    n=0
    until (testCompositeCreated)
    do
        n=$((n + 1))
        if [[ $n == 40 ]]
        then
            echo " Give up"
            exit 1
        else
            sleep 6
            echo -n ", retry #$n "
        fi
    done
    echo "All messages are now processed!"
}

function recreateComposite() {
  local productId=$1
  local composite=$2

  assertCurl 202 "curl -X DELETE $AUTH -k https://$HOST:$PORT/product-composite/${productId} -s"
  assertEqual 202 $(curl -X POST -s -k https://$HOST:$PORT/product-composite -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS_TOKEN" --data "$composite" -w "%{http_code}")
}

function setupTestdata() {

  body="{\"productId\":$PROD_ID_NO_RECS"
  body+=\
',"name":"product name A","weight":100, "reviews":[
  {"reviewId":1,"author":"author 1","subject":"subject 1","content":"content 1"},
  {"reviewId":2,"author":"author 2","subject":"subject 2","content":"content 2"},
  {"reviewId":3,"author":"author 3","subject":"subject 3","content":"content 3"}
]}'
  recreateComposite "$PROD_ID_NO_RECS" "$body"

  body="{\"productId\":$PROD_ID_NO_REVS"
  body+=\
',"name":"product name B","weight":200, "recommendations":[
  {"recommendationId":1,"author":"author 1","rate":1,"content":"content 1"},
  {"recommendationId":2,"author":"author 2","rate":2,"content":"content 2"},
  {"recommendationId":3,"author":"author 3","rate":3,"content":"content 3"}
]}'
  recreateComposite "$PROD_ID_NO_REVS" "$body"


  body="{\"productId\":$PROD_ID_REVS_RECS"
  body+=\
',"name":"product name C","weight":300, "recommendations":[
      {"recommendationId":1,"author":"author 1","rate":1,"content":"content 1"},
      {"recommendationId":2,"author":"author 2","rate":2,"content":"content 2"},
      {"recommendationId":3,"author":"author 3","rate":3,"content":"content 3"}
  ], "reviews":[
      {"reviewId":1,"author":"author 1","subject":"subject 1","content":"content 1"},
      {"reviewId":2,"author":"author 2","subject":"subject 2","content":"content 2"},
      {"reviewId":3,"author":"author 3","subject":"subject 3","content":"content 3"}
  ]}'
  recreateComposite "$PROD_ID_REVS_RECS" "$body"

}

function testCircuitBreaker() {

    echo "Start Circuit Breaker tests!"

    if [[ $USE_K8S == "false" ]]
    then
        EXEC="docker compose exec -T product-composite"
    else
        EXEC="kubectl -n $NAMESPACE exec deploy/product-composite -c product-composite -- "
    fi

    # First, use the health - endpoint to verify that the circuit breaker is closed
    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Open the circuit breaker by running three slow calls in a row, i.e. that cause a timeout exception
    # Also, verify that we get 500 back and a timeout related error message
    for ((n=0; n<3; n++))
    do
        assertCurl 500 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS?delay=3 $AUTH -s"
        message=$(echo $RESPONSE | jq -r .message)
        assertEqual "Did not observe any item or terminal signal within 2000ms" "${message:0:57}"
    done

    # Verify that the circuit breaker is open
    assertEqual "OPEN" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Verify that the circuit breaker now is open by running the slow call again, verify it gets 200 back, i.e. fail fast works, and a response from the fallback method.
    assertCurl 200 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS?delay=3 $AUTH -s"
    assertEqual "Fallback product$PROD_ID_REVS_RECS" "$(echo "$RESPONSE" | jq -r .name)"

    # Also, verify that the circuit breaker is open by running a normal call, verify it also gets 200 back and a response from the fallback method.
    assertCurl 200 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS $AUTH -s"
    assertEqual "Fallback product$PROD_ID_REVS_RECS" "$(echo "$RESPONSE" | jq -r .name)"

    # Verify that a 404 (Not Found) error is returned for a non existing productId ($PROD_ID_NOT_FOUND) from the fallback method.
    assertCurl 404 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_NOT_FOUND $AUTH -s"
    assertEqual "Product Id: $PROD_ID_NOT_FOUND not found in fallback cache!" "$(echo $RESPONSE | jq -r .message)"

    # Wait for the circuit breaker to transition to the half open state (i.e. max 10 sec)
    echo "Will sleep for 10 sec waiting for the CB to go Half Open..."
    sleep 10

    # Verify that the circuit breaker is in half open state
    assertEqual "HALF_OPEN" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Close the circuit breaker by running three normal calls in a row
    # Also, verify that we get 200 back and a response based on information in the product database
    for ((n=0; n<3; n++))
    do
        assertCurl 200 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS $AUTH -s"
        assertEqual "product name C" "$(echo "$RESPONSE" | jq -r .name)"
    done

    # Verify that the circuit breaker is in closed state again
    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Verify that the expected state transitions happened in the circuit breaker
    assertEqual "CLOSED_TO_OPEN"      "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
    assertEqual "OPEN_TO_HALF_OPEN"   "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
    assertEqual "HALF_OPEN_TO_CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
}

set -e

echo "Start Tests:" `date`

echo "HOST=${HOST}"
echo "PORT=${PORT}"
echo "USE_K8S=${USE_K8S}"
echo "HEALTH_URL=${HEALTH_URL}"
echo "MGM_PORT=${MGM_PORT}"
echo "SKIP_CB_TESTS=${SKIP_CB_TESTS}"

if [[ $@ == *"start"* ]]
then
  echo "Restarting the test environment..."
  echo "$ docker compose down --remove-orphans"
  docker compose down --remove-orphans
  echo "$ docker compose up -d"
  docker compose up -d
fi

waitForService curl -k $HEALTH_URL/actuator/health

ACCESS_TOKEN=$(curl -k https://writer:secret-writer@$HOST:$PORT/oauth2/token -d grant_type=client_credentials -d scope="product:read product:write" -s | jq .access_token -r)
echo ACCESS_TOKEN=$ACCESS_TOKEN
AUTH="-H \"Authorization: Bearer $ACCESS_TOKEN\""

setupTestdata

waitForMessageProcessing

# Verify that a normal request works, expect three recommendations and three reviews
assertCurl 200 "curl $AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"
assertEqual $PROD_ID_REVS_RECS $(echo $RESPONSE | jq .productId)
assertEqual 3 $(echo $RESPONSE | jq ".recommendations | length")
assertEqual 3 $(echo $RESPONSE | jq ".reviews | length")

# Verify that a 404 (Not Found) error is returned for a non-existing productId ($PROD_ID_NOT_FOUND)
assertCurl 404 "curl $AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_NOT_FOUND -s"
assertEqual "No product found for productId: $PROD_ID_NOT_FOUND" "$(echo $RESPONSE | jq -r .message)"

# Verify that no recommendations are returned for productId $PROD_ID_NO_RECS
assertCurl 200 "curl $AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_NO_RECS -s"
assertEqual $PROD_ID_NO_RECS $(echo $RESPONSE | jq .productId)
assertEqual 0 $(echo $RESPONSE | jq ".recommendations | length")
assertEqual 3 $(echo $RESPONSE | jq ".reviews | length")

# Verify that no reviews are returned for productId $PROD_ID_NO_REVS
assertCurl 200 "curl $AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_NO_REVS -s"
assertEqual $PROD_ID_NO_REVS $(echo $RESPONSE | jq .productId)
assertEqual 3 $(echo $RESPONSE | jq ".recommendations | length")
assertEqual 0 $(echo $RESPONSE | jq ".reviews | length")

# Verify that a 422 (Unprocessable Entity) error is returned for a productId that is out of range (-1)
assertCurl 422 "curl $AUTH -k https://$HOST:$PORT/product-composite/-1 -s"
assertEqual "\"Invalid productId: -1\"" "$(echo $RESPONSE | jq .message)"

# Verify that a 400 (Bad Request) error error is returned for a productId that is not a number, i.e. invalid format
assertCurl 400 "curl $AUTH -k https://$HOST:$PORT/product-composite/invalidProductId -s"
assertEqual "\"Type mismatch.\"" "$(echo $RESPONSE | jq .message)"

# Verify that a request without access token fails on 401, Unauthorized
assertCurl 401 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"

# Verify that the reader - client with only read scope can call the read API but not delete API.
READER_ACCESS_TOKEN=$(curl -k https://reader:secret-reader@$HOST:$PORT/oauth2/token -d grant_type=client_credentials -d scope="product:read" -s | jq .access_token -r)
echo READER_ACCESS_TOKEN=$READER_ACCESS_TOKEN
READER_AUTH="-H \"Authorization: Bearer $READER_ACCESS_TOKEN\""

assertCurl 200 "curl $READER_AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"
assertCurl 403 "curl -X DELETE $READER_AUTH -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"

# Verify access to Swagger and OpenAPI URLs
echo "Swagger/OpenAPI tests"
assertCurl 302 "curl -ks  https://$HOST:$PORT/openapi/swagger-ui.html"
assertCurl 200 "curl -ksL https://$HOST:$PORT/openapi/swagger-ui.html"
assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/swagger-ui/index.html"
# Verify the redirect URL
assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/swagger-ui/oauth2-redirect.html"
assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/v3/api-docs"
assertEqual "3.1.0" "$(echo $RESPONSE | jq -r .openapi)"
# Skip this test since the server url is missing the port when deployed on Kubernetes
if [[ $USE_K8S == "false" ]]
then
  assertEqual "https://$HOST:$PORT" "$(echo $RESPONSE | jq -r '.servers[0].url')"
fi
assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/v3/api-docs.yaml"

if [[ $USE_K8S == "true" ]]
then
  # Verify access to Prometheus formatted metrics
  echo "Prometheus metrics tests"
  assertCurl 200 "curl -ks https://health.minikube.me/actuator/prometheus"
fi

if [[ $SKIP_CB_TESTS == "false" ]]
then
    testCircuitBreaker
fi

if [[ $@ == *"stop"* ]]
then
    echo "We are done, stopping the test environment..."
    echo "$ docker compose down"
    docker compose down
fi

echo "End, all tests OK:" `date`
```

</details>

<a id="단계-2"></a>

## 단계 2. `product-service`

`micrometer-registry-prometheus` 의존성을 추가합니다.

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -38,6 +38,7 @@
     implementation 'org.springframework.boot:spring-boot-starter-zipkin'
     implementation 'org.springframework.retry:spring-retry'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
+    implementation 'io.micrometer:micrometer-registry-prometheus'
 
     compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
     annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'java'
}

group = 'se.magnus.microservices.core.product'
version = '1.0.0-SNAPSHOT'

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

ext {
    mapstructVersion = '1.6.3'
    springCloudVersion = '2025.1.4'
}

repositories {
    mavenCentral()
}

jar {
    enabled = false
}

dependencies {
    implementation project(':api')
    implementation project(':util')
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
    implementation 'org.springframework.retry:spring-retry'
    implementation "org.mapstruct:mapstruct:${mapstructVersion}"
    implementation 'io.micrometer:micrometer-registry-prometheus'

    compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'

    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
    testImplementation 'org.testcontainers:testcontainers-mongodb'
}

dependencyManagement {
    imports {
        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
    }
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

**중간 확인**

```bash
./gradlew :microservices:product-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-3"></a>

## 단계 3. `recommendation-service`

`micrometer-registry-prometheus` 의존성을 추가합니다.

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -38,6 +38,7 @@
     implementation 'org.springframework.boot:spring-boot-starter-zipkin'
     implementation 'org.springframework.retry:spring-retry'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
+    implementation 'io.micrometer:micrometer-registry-prometheus'
 
     compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
     annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'java'
}

group = 'se.magnus.microservices.core.recommendation'
version = '1.0.0-SNAPSHOT'

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

ext {
    mapstructVersion = '1.6.3'
    springCloudVersion = '2025.1.4'
}

repositories {
    mavenCentral()
}

jar {
    enabled = false
}

dependencies {
    implementation project(':api')
    implementation project(':util')
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
    implementation 'org.springframework.retry:spring-retry'
    implementation "org.mapstruct:mapstruct:${mapstructVersion}"
    implementation 'io.micrometer:micrometer-registry-prometheus'

    compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'

    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
    testImplementation 'org.testcontainers:testcontainers-mongodb'
}

dependencyManagement {
    imports {
        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
    }
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

**중간 확인**

```bash
./gradlew :microservices:recommendation-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-4"></a>

## 단계 4. `review-service`

`micrometer-registry-prometheus` 의존성을 추가합니다.

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -40,6 +40,7 @@
     implementation 'org.springframework.retry:spring-retry'
     implementation 'com.mysql:mysql-connector-j'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
+    implementation 'io.micrometer:micrometer-registry-prometheus'
 
     compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
     annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'java'
}

group = 'se.magnus.microservices.core.review'
version = '1.0.0-SNAPSHOT'

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

ext {
    mapstructVersion = '1.6.3'
    springCloudVersion = '2025.1.4'
}

repositories {
    mavenCentral()
}

jar {
    enabled = false
}

dependencies {
    implementation project(':api')
    implementation project(':util')
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
    implementation 'net.ttddyy.observation:datasource-micrometer-spring-boot:2.2.1'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'com.mysql:mysql-connector-j'
    implementation "org.mapstruct:mapstruct:${mapstructVersion}"
    implementation 'io.micrometer:micrometer-registry-prometheus'

    compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-data-jpa-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'

    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
    testImplementation 'org.testcontainers:testcontainers-mysql'
}

dependencyManagement {
    imports {
        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
    }
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `product-composite-service`

`micrometer-registry-prometheus` 의존성을 추가합니다.

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -46,6 +46,7 @@
     implementation "io.github.resilience4j:resilience4j-spring-boot4:${resilience4jVersion}"
     implementation "io.github.resilience4j:resilience4j-reactor:${resilience4jVersion}"
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
+    implementation 'io.micrometer:micrometer-registry-prometheus'
 
     // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
     // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'java'
}

group = 'se.magnus.microservices.composite.product'
version = '1.0.0-SNAPSHOT'

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

ext {
    springCloudVersion = '2025.1.4'
    resilience4jVersion = '2.4.0'
}
repositories {
    mavenCentral()
}

jar {
    enabled = false
}

springBoot {
    buildInfo()
}

dependencies {
    implementation project(':api')
    implementation project(':util')
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
    implementation 'org.springframework.boot:spring-boot-starter-webclient'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:3.0.3'
    implementation "io.github.resilience4j:resilience4j-spring-boot4:${resilience4jVersion}"
    implementation "io.github.resilience4j:resilience4j-reactor:${resilience4jVersion}"
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
    implementation 'io.micrometer:micrometer-registry-prometheus'

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'org.springframework.cloud:spring-cloud-stream-test-binder'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

dependencyManagement {
    imports {
        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
        mavenBom "io.github.resilience4j:resilience4j-bom:${resilience4jVersion}"
    }
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-6"></a>

## 단계 6. `authorization-server` — OAuth 2.0 인가 서버

`micrometer-registry-prometheus` 의존성을 추가합니다.

#### `spring-cloud/authorization-server/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -23,6 +23,7 @@
     implementation 'org.springframework.boot:spring-boot-starter-security'
     implementation 'io.micrometer:micrometer-tracing-bridge-brave'
     implementation 'org.springframework.boot:spring-boot-starter-zipkin'
+    implementation 'io.micrometer:micrometer-registry-prometheus'
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-starter-webmvc-test'
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/authorization-server/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'java'
}

group = 'se.magnus.springcloud'
version = '1.0.0-SNAPSHOT'

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-authorization-server'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
    implementation 'io.micrometer:micrometer-registry-prometheus'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webmvc-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-security-test'
    testImplementation 'org.htmlunit:htmlunit'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

**중간 확인**

```bash
./gradlew :spring-cloud:authorization-server:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-7"></a>

## 단계 7. `config-repo` — 중앙 구성 파일

`/actuator/prometheus`를 노출하고 지표에 `application` 태그를 붙입니다.

#### `config-repo/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -16,6 +16,7 @@
 management.endpoint.health.show-details: "ALWAYS"
 management.endpoints.web.exposure.include: "*"
 management.endpoint.health.probes.enabled: true
+management.metrics.tags.application: ${spring.application.name}
 management.health.rabbit.enabled: true
 management.health.kafka.enabled: false
 
@@ -51,5 +52,5 @@
 spring.config.activate.on-profile: prod
 spring.rabbitmq.host: 172.17.0.1
 
-# Only allow management endpoints over http in production for info, health and circuitbreakerevents
-management.endpoints.web.exposure.include: health,info,circuitbreakerevents
+# Only allow management endpoints over http in production for health, info, circuitbreakerevents and prometheus metrics
+management.endpoints.web.exposure.include: health,info,circuitbreakerevents,prometheus
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/application.yml" op="write" nl="1" -->
```yaml
app:
  auth-server: localhost

spring.rabbitmq:
  host: 127.0.0.1
  port: 5672

spring.cloud.stream.kafka.binder:
  brokers: 127.0.0.1
  defaultBrokerPort: 9092

spring.cloud.stream.defaultBinder: rabbit

# WARNING: Exposing all management endpoints over http should only be used during development, must be locked down in production!
management.server.port: 4004
management.endpoint.health.show-details: "ALWAYS"
management.endpoints.web.exposure.include: "*"
management.endpoint.health.probes.enabled: true
management.metrics.tags.application: ${spring.application.name}
management.health.rabbit.enabled: true
management.health.kafka.enabled: false

management.tracing.export.zipkin.endpoint: http://jaeger-collector.istio-system:9411/api/v2/spans
management.tracing.sampling.probability: 1.0
logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
logging.include-application-name: false

server.shutdown: graceful
spring.lifecycle.timeout-per-shutdown-phase: 10s

---
spring.config.activate.on-profile: docker

spring.rabbitmq.host: rabbitmq

spring.cloud.stream.kafka.binder.brokers: kafka

app:
  auth-server: auth-server

---
spring.config.activate.on-profile: kafka

spring.cloud.stream.defaultBinder: kafka
spring.kafka.bootstrap-servers: kafka:9092
spring.cloud.stream.kafka.binder.replication-factor: 1

management.health.rabbit.enabled: false
management.health.kafka.enabled: true

---
spring.config.activate.on-profile: prod
spring.rabbitmq.host: 172.17.0.1

# Only allow management endpoints over http in production for health, info, circuitbreakerevents and prometheus metrics
management.endpoints.web.exposure.include: health,info,circuitbreakerevents,prometheus
```

</details>

#### `config-repo/gateway.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -15,6 +15,7 @@
     location: classpath:keystore/edge.p12
 
 server.ssl.bundle: gateway
+
 
 spring.cloud.gateway.server.webflux.routes:
 
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/gateway.yml" op="write" nl="1" -->
```yaml
server.port: 8443
management.server.port: 8443
spring.application.name: gateway

# During development, allow forwarding the X-Forwarded-* and Forwarded headers from any proxies.
# When usd in QA and production, this should be set to a specific IP address or CIDR range, e.g. 10\.0\.0\..* (Java Regular Expression).
# For more information, see https://spring.io/security/cve-2025-41235
spring.cloud.gateway.server.webflux.trusted-proxies: ".*"

spring.ssl.bundle.jks.gateway:
  key:
    alias: localhost
  keystore:
    type: PKCS12
    location: classpath:keystore/edge.p12

server.ssl.bundle: gateway


spring.cloud.gateway.server.webflux.routes:

- id: product-composite
  uri: http://product-composite
  predicates:
  - Path=/product-composite/**

- id: oauth2-server
  uri: http://${app.auth-server}
  predicates:
  - Path=/oauth2/**

- id: oauth2-login
  uri: http://${app.auth-server}
  predicates:
  - Path=/login/**

- id: oauth2-error
  uri: http://${app.auth-server}
  predicates:
  - Path=/error/**

- id: product-composite-swagger-ui
  uri: http://product-composite
  predicates:
  - Path=/openapi/**

spring.security.oauth2.resourceserver.jwt.issuer-uri: http://${app.auth-server}

management.endpoint.gateway.access: unrestricted

logging:
  level:
    root: INFO
    org.springframework.cloud.gateway.route.RouteDefinitionRouteLocator: INFO
    org.springframework.cloud.gateway: TRACE
    org.springframework.web.server.adapter.HttpWebHandlerAdapter: TRACE

---
spring.config.activate.on-profile: prod

logging:
  level:
    root: WARN
    org.springframework.cloud.gateway.route.RouteDefinitionRouteLocator: WARN
    org.springframework.cloud.gateway: WARN
    org.springframework.web.server.adapter.HttpWebHandlerAdapter: WARN
```

</details>

<a id="단계-8"></a>

## 단계 8. `kubernetes/grafana` — 대시보드

직접 만든 대시보드를 내보낸 파일입니다.

#### `kubernetes/grafana/api-export-import/Hands-on-Dashboard.json` — 복사/생성

Grafana에서 내보낸 대시보드입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/grafana/api-export-import/Hands-on-Dashboard.json" op="copy" nl="0" -->

<a id="단계-9"></a>

## 단계 9. 헬름 `components` 차트 — 서비스별 차트

서비스 차트에 Prometheus 수집 애너테이션과 설정 파일을 추가합니다.

#### `kubernetes/helm/components/auth-server/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/auth-server/config-repo && cp config-repo/application.yml kubernetes/helm/components/auth-server/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/auth-server/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/auth-server/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/auth-server/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: auth-server

annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "4004"
  prometheus.io/scheme: http
  prometheus.io/path: "/actuator/prometheus"

image:
  name: auth-server

env:
  SPRING_PROFILES_ACTIVE: "docker"
  SPRING_CONFIG_LOCATION: file:/config-repo/application.yml,file:/config-repo/auth-server.yml

livenessProbe_enabled: true

readinessProbe_enabled: true

configmap:
  enabled: true
  volumeMounts:
    mountPath: /config-repo
```

#### `kubernetes/helm/components/product-composite/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product-composite/config-repo && cp config-repo/application.yml kubernetes/helm/components/product-composite/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/product-composite/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/product-composite/values.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,4 +1,10 @@
 fullnameOverride: product-composite
+
+annotations:
+  prometheus.io/scrape: "true"
+  prometheus.io/port: "4004"
+  prometheus.io/scheme: http
+  prometheus.io/path: "/actuator/prometheus"
 
 image:
   name: product-composite-service
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="kubernetes/helm/components/product-composite/values.yaml" op="write" nl="0" -->
```yaml
fullnameOverride: product-composite

annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "4004"
  prometheus.io/scheme: http
  prometheus.io/path: "/actuator/prometheus"

image:
  name: product-composite-service

ports:
  - name: http
    containerPort: 80
    protocol: TCP
  - name: http-mgm
    containerPort: 4004
    protocol: TCP

env:
  SPRING_PROFILES_ACTIVE: "docker"
  SPRING_CONFIG_LOCATION: file:/config-repo/application.yml,file:/config-repo/product-composite.yml

livenessProbe_enabled: true

readinessProbe_enabled: true

configmap:
  enabled: true
  volumeMounts:
    mountPath: /config-repo

service:
  ports:
    - port: 80
      name: http
      targetPort: 80
    - port: 4004
      name: http-mgm
      targetPort: 4004
```

</details>

#### `kubernetes/helm/components/product-green/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product-green/config-repo && cp config-repo/application.yml kubernetes/helm/components/product-green/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/product-green/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/product/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product/config-repo && cp config-repo/application.yml kubernetes/helm/components/product/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/product/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/product/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/product/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: product

annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "4004"
  prometheus.io/scheme: http
  prometheus.io/path: "/actuator/prometheus"

image:
  name: product-service

env:
  SPRING_PROFILES_ACTIVE: "docker"
  SPRING_CONFIG_LOCATION: file:/config-repo/application.yml,file:/config-repo/product.yml

livenessProbe_enabled: true

readinessProbe_enabled: true

configmap:
  enabled: true
  volumeMounts:
    mountPath: /config-repo
```

#### `kubernetes/helm/components/recommendation-green/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/recommendation-green/config-repo && cp config-repo/application.yml kubernetes/helm/components/recommendation-green/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/recommendation-green/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/recommendation/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/recommendation/config-repo && cp config-repo/application.yml kubernetes/helm/components/recommendation/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/recommendation/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/recommendation/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/recommendation/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: recommendation

annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "4004"
  prometheus.io/scheme: http
  prometheus.io/path: "/actuator/prometheus"

image:
  name: recommendation-service

env:
  SPRING_PROFILES_ACTIVE: "docker"
  SPRING_CONFIG_LOCATION: file:/config-repo/application.yml,file:/config-repo/recommendation.yml

livenessProbe_enabled: true

readinessProbe_enabled: true

configmap:
  enabled: true
  volumeMounts:
    mountPath: /config-repo
```

#### `kubernetes/helm/components/review-green/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review-green/config-repo && cp config-repo/application.yml kubernetes/helm/components/review-green/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/review-green/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/review/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review/config-repo && cp config-repo/application.yml kubernetes/helm/components/review/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/review/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/review/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/review/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: review

annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "4004"
  prometheus.io/scheme: http
  prometheus.io/path: "/actuator/prometheus"

image:
  name: review-service

env:
  SPRING_PROFILES_ACTIVE: "docker"
  SPRING_CONFIG_LOCATION: file:/config-repo/application.yml,file:/config-repo/review.yml

livenessProbe_enabled: true

readinessProbe_enabled: true

configmap:
  enabled: true
  volumeMounts:
    mountPath: /config-repo
```

<a id="단계-10"></a>

## 단계 10. 헬름 `environments` 차트 — 환경별 묶음

테스트 메일 서버를 노출하는 `expose-mail.yml`을 추가합니다.

#### `kubernetes/helm/environments/istio-system/templates/expose-mail.yml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/environments/istio-system/templates/expose-mail.yml" op="write" nl="1" -->
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: mail-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - "mail.minikube.me"
    port:
      number: 443
      name: https-mail
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: hands-on-certificate
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: mail-vs
  namespace: istio-system
spec:
  hosts:
  - "mail.minikube.me"
  gateways:
  - mail-gateway
  http:
  - route:
    - destination:
        host: mail-server
        port:
          number: 1080
---
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: mail
  namespace: istio-system
spec:
  host: mail-server
  trafficPolicy:
    tls:
      mode: DISABLE
```

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter20
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
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter20
```

---

← [19장 워크북](Chapter19.md) · [워크북 목차](README.md) · [23장 워크북](Chapter23.md) →
