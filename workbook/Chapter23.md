# 23장 워크북 — 네이티브 컴파일 자바 마이크로서비스

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 23장 · 영문 3판 p.621–650 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter23/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter23`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter23) · 위키: [23장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/23장-네이티브-컴파일-자바-마이크로서비스)

## 이 장에서 만드는 것

**GraalVM 네이티브 이미지**로 마이크로서비스를 컴파일합니다.

- `org.graalvm.buildtools.native` 플러그인과 `bootBuildImage` 설정(GraalVM 25)
- 리플렉션 등 네이티브 이미지 힌트(`NativeHintsConfiguration`)
- 네이티브 이미지용 도커 컴포즈 파일과 헬름 환경(`dev-env-native`)

## 시작하기

20장을 끝낸 작업 폴더를 복사해서 시작합니다. 20장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter20 Chapter23          # 내가 만든 20장 결과에서 시작
# 또는: cp -r <저장소>/Chapter20 Chapter23        # 저장소의 20장 완성 코드에서 시작
cd Chapter23 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 새 파일 2 · 수정 2
2. [`product-service`](#단계-2) — 새 파일 3 · 수정 5
3. [`recommendation-service`](#단계-3) — 새 파일 3 · 수정 7
4. [`review-service`](#단계-4) — 새 파일 3 · 수정 6
5. [`product-composite-service`](#단계-5) — 새 파일 3 · 수정 7
6. [`authorization-server` — OAuth 2.0 인가 서버](#단계-6) — 수정 1
7. [`config-repo` — 중앙 구성 파일](#단계-7) — 수정 4
8. [헬름 `components` 차트 — 서비스별 차트](#단계-8) — 수정 11
9. [헬름 `environments` 차트 — 환경별 묶음](#단계-9) — 새 파일 6

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

네이티브 이미지용 컴포즈 파일(`docker-compose-native.yml`, `docker-compose-partitions-native.yml`)을 추가합니다.

#### `.gitignore` — 복사/생성

Git이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요(치지 않아도 실습에는 지장이 없습니다).

<!-- wb:file path=".gitignore" op="copy" nl="0" -->

#### `docker-compose-native.yml` — 새 파일 (166줄)

<!-- wb:file path="docker-compose-native.yml" op="write" nl="1" -->
```yaml
services:
  product:
    image: hands-on/native-product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation:
    image: hands-on/native-recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review:
    image: hands-on/native-review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-composite:
    image: hands-on/native-product-composite-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product-composite.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      rabbitmq:
        condition: service_healthy
      auth-server:
        condition: service_healthy

  mongodb:
    image: mongo:8.0.5
    restart: always
    mem_limit: 512m
    ports:
      - "27017:27017"
    command: mongod
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGODB_USR}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PWD}
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh --quiet
      interval: 5s
      timeout: 2s
      retries: 60

  mysql:
    image: mysql:9.2.0
    # restart: always
    mem_limit: 512m
    ports:
      - "3306:3306"
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PWD}
      - MYSQL_DATABASE=review-db
      - MYSQL_USER=${MYSQL_USR}
      - MYSQL_PASSWORD=${MYSQL_PWD}
    healthcheck:
      test: "/usr/bin/mysql --user=${MYSQL_USR} --password=${MYSQL_PWD} --execute \"SHOW DATABASES;\""
      interval: 5s
      timeout: 2s
      retries: 60

  rabbitmq:
    image: rabbitmq:4.0.7-management
    restart: always
    mem_limit: 512m
    ports:
      - 5672:5672
      - 15672:15672
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USR}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PWD}
    healthcheck:
      test: ["CMD", "rabbitmqctl", "status"]
      interval: 5s
      timeout: 2s
      retries: 60

  gateway:
    build: spring-cloud/gateway
    image: hands-on/gateway
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/gateway.yml
      - SPRING_SSL_BUNDLE_JKS_GATEWAY_KEYSTORE_PASSWORD=${GATEWAY_TLS_PWD}
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    ports:
      - "8443:8443"
    depends_on:
      auth-server:
        condition: service_healthy

  auth-server:
    build: spring-cloud/authorization-server
    image: hands-on/auth-server
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/auth-server.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost:4004/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

  jaeger-collector.istio-system:
    image: openzipkin/zipkin:3.5.0
    restart: always
    mem_limit: 1024m
    environment:
      - STORAGE_TYPE=mem
    ports:
      - 9411:9411
```

#### `docker-compose-partitions-native.yml` — 새 파일 (222줄)

<!-- wb:file path="docker-compose-partitions-native.yml" op="write" nl="1" -->
```yaml
services:
  product:
    image: hands-on/native-product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-p1:
    image: hands-on/native-product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation:
    image: hands-on/native-recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation-p1:
    image: hands-on/native-recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review:
    image: hands-on/native-review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review-p1:
    image: hands-on/native-review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-composite:
    image: hands-on/native-product-composite-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product-composite.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    depends_on:
      rabbitmq:
        condition: service_healthy
      auth-server:
        condition: service_healthy

  mongodb:
    image: mongo:8.0.5
    restart: always
    mem_limit: 512m
    ports:
      - "27017:27017"
    command: mongod
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGODB_USR}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PWD}
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh --quiet
      interval: 5s
      timeout: 2s
      retries: 60

  mysql:
    image: mysql:9.2.0
    restart: always
    mem_limit: 512m
    ports:
      - "3306:3306"
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PWD}
      - MYSQL_DATABASE=review-db
      - MYSQL_USER=${MYSQL_USR}
      - MYSQL_PASSWORD=${MYSQL_PWD}
    healthcheck:
      test: "/usr/bin/mysql --user=${MYSQL_USR} --password=${MYSQL_PWD} --execute \"SHOW DATABASES;\""
      interval: 5s
      timeout: 2s
      retries: 60

  rabbitmq:
    image: rabbitmq:4.0.7-management
    restart: always
    mem_limit: 512m
    ports:
      - 5672:5672
      - 15672:15672
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USR}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PWD}
    healthcheck:
      test: ["CMD", "rabbitmqctl", "status"]
      interval: 5s
      timeout: 2s
      retries: 60

  gateway:
    build: spring-cloud/gateway
    image: hands-on/gateway
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/gateway.yml
      - SPRING_SSL_BUNDLE_JKS_GATEWAY_KEYSTORE_PASSWORD=${GATEWAY_TLS_PWD}
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    ports:
      - "8443:8443"
    depends_on:
      auth-server:
        condition: service_healthy

  auth-server:
    build: spring-cloud/authorization-server
    image: hands-on/auth-server
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/auth-server.yml
      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost:4004/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

  jaeger-collector.istio-system:
    image: openzipkin/zipkin:3.5.0
    restart: always
    mem_limit: 1024m
    environment:
      - STORAGE_TYPE=mem
    ports:
      - 9411:9411
```

#### `test-em-all.bash` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -193,13 +193,15 @@
 
     if [[ $USE_K8S == "false" ]]
     then
-        EXEC="docker compose exec -T product-composite"
+        # Use the auth-server to run curl, since the product-composite is native compiled
+        EXEC="docker compose exec -T auth-server"
     else
-        EXEC="kubectl -n $NAMESPACE exec deploy/product-composite -c product-composite -- "
+        # Use the auth-server to run curl, since the product-composite is native compiled
+        EXEC="kubectl -n $NAMESPACE exec deploy/auth-server -c auth-server -- "
     fi
 
     # First, use the health - endpoint to verify that the circuit breaker is closed
-    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "CLOSED" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Open the circuit breaker by running three slow calls in a row, i.e. that cause a timeout exception
     # Also, verify that we get 500 back and a timeout related error message
@@ -211,7 +213,7 @@
     done
 
     # Verify that the circuit breaker is open
-    assertEqual "OPEN" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "OPEN" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Verify that the circuit breaker now is open by running the slow call again, verify it gets 200 back, i.e. fail fast works, and a response from the fallback method.
     assertCurl 200 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS?delay=3 $AUTH -s"
@@ -230,7 +232,7 @@
     sleep 10
 
     # Verify that the circuit breaker is in half open state
-    assertEqual "HALF_OPEN" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "HALF_OPEN" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Close the circuit breaker by running three normal calls in a row
     # Also, verify that we get 200 back and a response based on information in the product database
@@ -241,12 +243,12 @@
     done
 
     # Verify that the circuit breaker is in closed state again
-    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "CLOSED" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Verify that the expected state transitions happened in the circuit breaker
-    assertEqual "CLOSED_TO_OPEN"      "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
-    assertEqual "OPEN_TO_HALF_OPEN"   "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
-    assertEqual "HALF_OPEN_TO_CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
+    assertEqual "CLOSED_TO_OPEN"      "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
+    assertEqual "OPEN_TO_HALF_OPEN"   "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
+    assertEqual "HALF_OPEN_TO_CLOSED" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
 }
 
 set -e
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
        # Use the auth-server to run curl, since the product-composite is native compiled
        EXEC="docker compose exec -T auth-server"
    else
        # Use the auth-server to run curl, since the product-composite is native compiled
        EXEC="kubectl -n $NAMESPACE exec deploy/auth-server -c auth-server -- "
    fi

    # First, use the health - endpoint to verify that the circuit breaker is closed
    assertEqual "CLOSED" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Open the circuit breaker by running three slow calls in a row, i.e. that cause a timeout exception
    # Also, verify that we get 500 back and a timeout related error message
    for ((n=0; n<3; n++))
    do
        assertCurl 500 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS?delay=3 $AUTH -s"
        message=$(echo $RESPONSE | jq -r .message)
        assertEqual "Did not observe any item or terminal signal within 2000ms" "${message:0:57}"
    done

    # Verify that the circuit breaker is open
    assertEqual "OPEN" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

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
    assertEqual "HALF_OPEN" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Close the circuit breaker by running three normal calls in a row
    # Also, verify that we get 200 back and a response based on information in the product database
    for ((n=0; n<3; n++))
    do
        assertCurl 200 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS $AUTH -s"
        assertEqual "product name C" "$(echo "$RESPONSE" | jq -r .name)"
    done

    # Verify that the circuit breaker is in closed state again
    assertEqual "CLOSED" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Verify that the expected state transitions happened in the circuit breaker
    assertEqual "CLOSED_TO_OPEN"      "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
    assertEqual "OPEN_TO_HALF_OPEN"   "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
    assertEqual "HALF_OPEN_TO_CLOSED" "$($EXEC wget -qO - http://product-composite:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
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

네이티브 빌드 플러그인과 `bootBuildImage` 설정, `NativeHintsConfiguration`을 추가합니다. 네이티브 이미지에서 쓰는 `application.yml`과 테스트용 접근 필터가 추가되고, `Dockerfile`은 JVM AOT 모드 실습용으로 바뀝니다.

#### `microservices/product-service/Dockerfile` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/Dockerfile" op="write" nl="0" -->
```dockerfile
FROM eclipse-temurin:21-jre-noble AS builder
WORKDIR /builder
ADD ./build/libs/*.jar app.jar
RUN java -Djarmode=tools -jar app.jar extract --layers --launcher --destination extracted

FROM eclipse-temurin:21-jre-noble
WORKDIR /application
COPY --from=builder /builder/extracted/dependencies/ ./
COPY --from=builder /builder/extracted/spring-boot-loader/ ./
COPY --from=builder /builder/extracted/snapshot-dependencies/ ./
COPY --from=builder /builder/extracted/application/ ./

EXPOSE 8080

ENTRYPOINT ["java", "-Dspring.aot.enabled=false", "org.springframework.boot.loader.launch.JarLauncher"]
```

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,6 +1,7 @@
 plugins {
     id 'org.springframework.boot' version '4.0.9'
     id 'io.spring.dependency-management' version '1.1.7'
+    id 'org.graalvm.buildtools.native' version '0.11.5'
     id 'java'
 }
 
@@ -22,9 +23,11 @@
     mavenCentral()
 }
 
-jar {
-    enabled = false
-}
+// Prevents GraalVM to native compile locally, i.e. without Docker-buildpacks
+// See https://github.com/spring-projects/spring-boot/issues/33238
+//jar {
+//    enabled = false
+//}
 
 dependencies {
     implementation project(':api')
@@ -36,7 +39,6 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
     implementation 'io.micrometer:micrometer-tracing-bridge-brave'
     implementation 'org.springframework.boot:spring-boot-starter-zipkin'
-    implementation 'org.springframework.retry:spring-retry'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
     implementation 'io.micrometer:micrometer-registry-prometheus'
 
@@ -67,4 +69,14 @@
 
 tasks.named('test') {
     useJUnitPlatform()
+    // Tracing agent works with the prod service, but is disabled to avoid changes to the source code, i.e. src/main/resources/META-INF/native-image
+    // jvmArgs "-agentlib:native-image-agent=access-filter-file=src/test/resources/access-filter.json,config-output-dir=src/main/resources/META-INF/native-image"
 }
+
+tasks.named('bootBuildImage') {
+    createdDate = "now"
+    // Spring Boot 4 requires GraalVM 25 or later for native images
+    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
+    imageName = "hands-on/native-product-service"
+}
+
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'org.graalvm.buildtools.native' version '0.11.5'
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

// Prevents GraalVM to native compile locally, i.e. without Docker-buildpacks
// See https://github.com/spring-projects/spring-boot/issues/33238
//jar {
//    enabled = false
//}

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
    // Tracing agent works with the prod service, but is disabled to avoid changes to the source code, i.e. src/main/resources/META-INF/native-image
    // jvmArgs "-agentlib:native-image-agent=access-filter-file=src/test/resources/access-filter.json,config-output-dir=src/main/resources/META-INF/native-image"
}

tasks.named('bootBuildImage') {
    createdDate = "now"
    // Spring Boot 4 requires GraalVM 25 or later for native images
    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
    imageName = "hands-on/native-product-service"
}

```

</details>

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/NativeHintsConfiguration.java` — 새 파일 (23줄)

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/NativeHintsConfiguration.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ImportRuntimeHints;

@Configuration
@ImportRuntimeHints(NativeHintsConfiguration.class)
public class NativeHintsConfiguration implements RuntimeHintsRegistrar {

  private static final Logger LOG = LoggerFactory.getLogger(NativeHintsConfiguration.class);

  @Override
  public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
    LOG.info("Will register native hints for the product service");

    // Workaround for the error: "java.io.IOException: Resource not found: "org/joda/time/tz/data/ZoneInfoMap"
    hints.resources().registerPattern("org/joda/time/tz/data/**");
  }
}
```

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/ProductServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -2,6 +2,7 @@
 
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
+import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
@@ -17,10 +18,14 @@
 import org.springframework.data.mongodb.core.mapping.MongoPersistentEntity;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentProperty;
 import reactor.core.publisher.Hooks;
+import se.magnus.api.core.product.Product;
+import se.magnus.api.event.Event;
 import se.magnus.microservices.core.product.persistence.ProductEntity;
+import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;
 
 @SpringBootApplication
 @ComponentScan("se.magnus")
+@RegisterReflectionForBinding({ Event.class, ZonedDateTimeSerializer.class, Product.class})
 public class ProductServiceApplication {
 
   private static final Logger LOG = LoggerFactory.getLogger(ProductServiceApplication.class);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/ProductServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.data.mapping.context.MappingContext;
import org.springframework.data.mongodb.core.ReactiveMongoOperations;
import org.springframework.data.mongodb.core.index.IndexResolver;
import org.springframework.data.mongodb.core.index.MongoPersistentEntityIndexResolver;
import org.springframework.data.mongodb.core.index.ReactiveIndexOperations;
import org.springframework.data.mongodb.core.mapping.MongoPersistentEntity;
import org.springframework.data.mongodb.core.mapping.MongoPersistentProperty;
import reactor.core.publisher.Hooks;
import se.magnus.api.core.product.Product;
import se.magnus.api.event.Event;
import se.magnus.microservices.core.product.persistence.ProductEntity;
import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;

@SpringBootApplication
@ComponentScan("se.magnus")
@RegisterReflectionForBinding({ Event.class, ZonedDateTimeSerializer.class, Product.class})
public class ProductServiceApplication {

  private static final Logger LOG = LoggerFactory.getLogger(ProductServiceApplication.class);

  public static void main(String[] args) {
    Hooks.enableAutomaticContextPropagation();
    ConfigurableApplicationContext ctx = SpringApplication.run(ProductServiceApplication.class, args);

    String mongodDbHost = ctx.getEnvironment().getProperty("spring.mongodb.host");
    String mongodDbPort = ctx.getEnvironment().getProperty("spring.mongodb.port");
    LOG.info("Connected to MongoDb: " + mongodDbHost + ":" + mongodDbPort);
  }

  @Autowired
  ReactiveMongoOperations mongoTemplate;

  @EventListener(ContextRefreshedEvent.class)
  public void initIndicesAfterStartup() {

    MappingContext<? extends MongoPersistentEntity<?>, MongoPersistentProperty> mappingContext = mongoTemplate.getConverter().getMappingContext();
    IndexResolver resolver = new MongoPersistentEntityIndexResolver(mappingContext);

    ReactiveIndexOperations indexOps = mongoTemplate.indexOps(ProductEntity.class);
    resolver.resolveIndexFor(ProductEntity.class).forEach(e -> indexOps.createIndex(e).block());
  }
}
```

</details>

#### `microservices/product-service/src/main/resources/application.yml` — 새 파일 (16줄)

<!-- wb:file path="microservices/product-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
# Required to make the Spring AOT engine generate the appropriate infrastructure for a separate management port, prometheus and K8S probes at build time
management.server.port: 9009
management.endpoint.health.probes.enabled: true
management.endpoints.web.exposure.include: health,info,prometheus

# Native Compile: Point out that RabbitMQ is to be used when performing the native compile
spring.cloud.stream.defaultBinder: rabbit

# Native Compile: Required to disable the health check of RabbitMQ when using Kafka
# management.health.rabbit.enabled: false

# Native Compile: Required to disable the health check of Kafka when using RabbitMQ
management.health.kafka.enabled: false

# Native Compile: Required to get proper error message from Spring Rest tests
spring.web.error.include-message: always
```

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/MapperTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -3,11 +3,15 @@
 import static org.junit.jupiter.api.Assertions.*;
 
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.mapstruct.factory.Mappers;
 import se.magnus.api.core.product.Product;
 import se.magnus.microservices.core.product.persistence.ProductEntity;
 import se.magnus.microservices.core.product.services.ProductMapper;
 
+// Fails on:
+// com.oracle.svm.core.jdk.UnsupportedFeatureError: Runtime reflection is not supported for public se.magnus.microservices.core.product.services.ProductMapperImpl()
+@DisabledInNativeImage
 class MapperTests {
 
   private ProductMapper mapper = Mappers.getMapper(ProductMapper.class);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/MapperTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.mapstruct.factory.Mappers;
import se.magnus.api.core.product.Product;
import se.magnus.microservices.core.product.persistence.ProductEntity;
import se.magnus.microservices.core.product.services.ProductMapper;

// Fails on:
// com.oracle.svm.core.jdk.UnsupportedFeatureError: Runtime reflection is not supported for public se.magnus.microservices.core.product.services.ProductMapperImpl()
@DisabledInNativeImage
class MapperTests {

  private ProductMapper mapper = Mappers.getMapper(ProductMapper.class);

  @Test
  void mapperTests() {

    assertNotNull(mapper);

    Product api = new Product(1, "n", 1, "sa");

    ProductEntity entity = mapper.apiToEntity(api);

    assertEquals(api.getProductId(), entity.getProductId());
    assertEquals(api.getProductId(), entity.getProductId());
    assertEquals(api.getName(), entity.getName());
    assertEquals(api.getWeight(), entity.getWeight());

    Product api2 = mapper.entityToApi(entity);

    assertEquals(api.getProductId(), api2.getProductId());
    assertEquals(api.getProductId(), api2.getProductId());
    assertEquals(api.getName(),      api2.getName());
    assertEquals(api.getWeight(),    api2.getWeight());
    assertNull(api2.getServiceAddress());
  }
}
```

</details>

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/MongoDbTestBase.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,8 +1,13 @@
 package se.magnus.microservices.core.product;
 
+import org.springframework.aot.hint.RuntimeHints;
+import org.springframework.aot.hint.RuntimeHintsRegistrar;
+import org.springframework.aot.hint.TypeReference;
 import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
+import org.springframework.context.annotation.ImportRuntimeHints;
 import org.testcontainers.mongodb.MongoDBContainer;
 
+@ImportRuntimeHints(MongoDbTestBase.MyHints.class)
 public abstract class MongoDbTestBase {
 
   @ServiceConnection
@@ -12,4 +17,12 @@
     database.start();
   }
 
+  // Workaround for the bug in Spring Boot 3.1.4 described here https://github.com/spring-projects/spring-boot/issues/36606
+  static class MyHints implements RuntimeHintsRegistrar {
+    @Override
+    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
+      hints.reflection().registerType(TypeReference.of("com.mongodb.ConnectionString"));
+    }
+  }
+
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/MongoDbTestBase.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.aot.hint.TypeReference;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.ImportRuntimeHints;
import org.testcontainers.mongodb.MongoDBContainer;

@ImportRuntimeHints(MongoDbTestBase.MyHints.class)
public abstract class MongoDbTestBase {

  @ServiceConnection
  private static MongoDBContainer database = new MongoDBContainer("mongo:8.0.5");

  static {
    database.start();
  }

  // Workaround for the bug in Spring Boot 3.1.4 described here https://github.com/spring-projects/spring-boot/issues/36606
  static class MyHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
      hints.reflection().registerType(TypeReference.of("com.mongodb.ConnectionString"));
    }
  }

}
```

</details>

#### `microservices/product-service/src/test/resources/access-filter.json` — 새 파일 (17줄)

<!-- wb:file path="microservices/product-service/src/test/resources/access-filter.json" op="write" nl="0" -->
```json
{ "rules":
  [
    {"excludeClasses": "org.apache.maven.surefire.**"},
    {"excludeClasses": "net.bytebuddy.**"},
    {"excludeClasses": "org.apiguardian.**"},
    {"excludeClasses": "org.junit.**"},
    {"excludeClasses": "org.gradle.**"},
    {"excludeClasses": "org.mockito.**"},
    {"excludeClasses": "org.springframework.test.**"},
    {"excludeClasses": "org.springframework.boot.test.**"},
    {"excludeClasses": "org.testcontainers.**"},
    {"excludeClasses": "se.magnus.microservices.core.product.MapperTests"},
    {"excludeClasses": "se.magnus.microservices.core.product.MongoDbTestBase"},
    {"excludeClasses": "se.magnus.microservices.core.product.PersistenceTests"},
    {"excludeClasses": "se.magnus.microservices.core.product.ProductServiceApplicationTests"}
  ]
}
```

**중간 확인**

```bash
./gradlew :microservices:product-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-3"></a>

## 단계 3. `recommendation-service`

네이티브 빌드 플러그인과 `bootBuildImage` 설정, `NativeHintsConfiguration`을 추가합니다. 네이티브 이미지에서 쓰는 `application.yml`과 테스트용 접근 필터가 추가되고, `Dockerfile`은 JVM AOT 모드 실습용으로 바뀝니다.

#### `microservices/recommendation-service/Dockerfile` — 전체를 바꿉니다 (`microservices/product-service/Dockerfile`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/recommendation-service && cp microservices/product-service/Dockerfile microservices/recommendation-service/Dockerfile
```

<!-- wb:file path="microservices/recommendation-service/Dockerfile" op="cp" src="microservices/product-service/Dockerfile" -->

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,6 +1,7 @@
 plugins {
     id 'org.springframework.boot' version '4.0.9'
     id 'io.spring.dependency-management' version '1.1.7'
+    id 'org.graalvm.buildtools.native' version '0.11.5'
     id 'java'
 }
 
@@ -22,9 +23,11 @@
     mavenCentral()
 }
 
-jar {
-    enabled = false
-}
+// Prevents GraalVM to native compile locally, i.e. without Docker-buildpacks
+// See https://github.com/spring-projects/spring-boot/issues/33238
+//jar {
+//    enabled = false
+//}
 
 dependencies {
     implementation project(':api')
@@ -36,7 +39,6 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
     implementation 'io.micrometer:micrometer-tracing-bridge-brave'
     implementation 'org.springframework.boot:spring-boot-starter-zipkin'
-    implementation 'org.springframework.retry:spring-retry'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
     implementation 'io.micrometer:micrometer-registry-prometheus'
 
@@ -67,4 +69,13 @@
 
 tasks.named('test') {
     useJUnitPlatform()
+    // Tracing agent works with the recommendation service, but is disabled to avoid changes to the source code, i.e. src/main/resources/META-INF/native-image
+    // jvmArgs "-agentlib:native-image-agent=access-filter-file=src/test/resources/access-filter.json,config-output-dir=src/main/resources/META-INF/native-image"
 }
+
+tasks.named('bootBuildImage') {
+    createdDate = "now"
+    // Spring Boot 4 requires GraalVM 25 or later for native images
+    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
+    imageName = "hands-on/native-recommendation-service"
+}
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'org.graalvm.buildtools.native' version '0.11.5'
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

// Prevents GraalVM to native compile locally, i.e. without Docker-buildpacks
// See https://github.com/spring-projects/spring-boot/issues/33238
//jar {
//    enabled = false
//}

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
    // Tracing agent works with the recommendation service, but is disabled to avoid changes to the source code, i.e. src/main/resources/META-INF/native-image
    // jvmArgs "-agentlib:native-image-agent=access-filter-file=src/test/resources/access-filter.json,config-output-dir=src/main/resources/META-INF/native-image"
}

tasks.named('bootBuildImage') {
    createdDate = "now"
    // Spring Boot 4 requires GraalVM 25 or later for native images
    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
    imageName = "hands-on/native-recommendation-service"
}
```

</details>

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/NativeHintsConfiguration.java` — 새 파일 (23줄)

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/NativeHintsConfiguration.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ImportRuntimeHints;

@Configuration
@ImportRuntimeHints(NativeHintsConfiguration.class)
public class NativeHintsConfiguration implements RuntimeHintsRegistrar {

  private static final Logger LOG = LoggerFactory.getLogger(NativeHintsConfiguration.class);

  @Override
  public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
    LOG.info("Will register native hints for the recommendation service");

    // Workaround for the error: "java.io.IOException: Resource not found: "org/joda/time/tz/data/ZoneInfoMap"
    hints.resources().registerPattern("org/joda/time/tz/data/**");
  }
}
```

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -2,6 +2,7 @@
 
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
+import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
@@ -17,10 +18,14 @@
 import org.springframework.data.mongodb.core.mapping.MongoPersistentEntity;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentProperty;
 import reactor.core.publisher.Hooks;
+import se.magnus.api.core.recommendation.Recommendation;
+import se.magnus.api.event.Event;
 import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
+import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;
 
 @SpringBootApplication
 @ComponentScan("se.magnus")
+@RegisterReflectionForBinding({ Event.class, ZonedDateTimeSerializer.class, Recommendation.class})
 public class RecommendationServiceApplication {
 
   private static final Logger LOG = LoggerFactory.getLogger(RecommendationServiceApplication.class);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.data.mapping.context.MappingContext;
import org.springframework.data.mongodb.core.ReactiveMongoOperations;
import org.springframework.data.mongodb.core.index.IndexResolver;
import org.springframework.data.mongodb.core.index.MongoPersistentEntityIndexResolver;
import org.springframework.data.mongodb.core.index.ReactiveIndexOperations;
import org.springframework.data.mongodb.core.mapping.MongoPersistentEntity;
import org.springframework.data.mongodb.core.mapping.MongoPersistentProperty;
import reactor.core.publisher.Hooks;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.event.Event;
import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;

@SpringBootApplication
@ComponentScan("se.magnus")
@RegisterReflectionForBinding({ Event.class, ZonedDateTimeSerializer.class, Recommendation.class})
public class RecommendationServiceApplication {

  private static final Logger LOG = LoggerFactory.getLogger(RecommendationServiceApplication.class);

  public static void main(String[] args) {
    Hooks.enableAutomaticContextPropagation();
    ConfigurableApplicationContext ctx = SpringApplication.run(RecommendationServiceApplication.class, args);

    String mongodDbHost = ctx.getEnvironment().getProperty("spring.mongodb.host");
    String mongodDbPort = ctx.getEnvironment().getProperty("spring.mongodb.port");
    LOG.info("Connected to MongoDb: " + mongodDbHost + ":" + mongodDbPort);
  }

  @Autowired
  ReactiveMongoOperations mongoTemplate;

  @EventListener(ContextRefreshedEvent.class)
  public void initIndicesAfterStartup() {

    MappingContext<? extends MongoPersistentEntity<?>, MongoPersistentProperty> mappingContext = mongoTemplate.getConverter().getMappingContext();
    IndexResolver resolver = new MongoPersistentEntityIndexResolver(mappingContext);

    ReactiveIndexOperations indexOps = mongoTemplate.indexOps(RecommendationEntity.class);
    resolver.resolveIndexFor(RecommendationEntity.class).forEach(e -> indexOps.createIndex(e).block());
  }
}
```

</details>

#### `microservices/recommendation-service/src/main/resources/application.yml` — 새 파일 (`microservices/product-service/src/main/resources/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/recommendation-service/src/main/resources && cp microservices/product-service/src/main/resources/application.yml microservices/recommendation-service/src/main/resources/application.yml
```

<!-- wb:file path="microservices/recommendation-service/src/main/resources/application.yml" op="cp" src="microservices/product-service/src/main/resources/application.yml" -->

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MapperTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -5,11 +5,15 @@
 import java.util.Collections;
 import java.util.List;
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.mapstruct.factory.Mappers;
 import se.magnus.api.core.recommendation.Recommendation;
 import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
 import se.magnus.microservices.core.recommendation.services.RecommendationMapper;
 
+// Fails on:
+// com.oracle.svm.core.jdk.UnsupportedFeatureError: Runtime reflection is not supported for public se.magnus.microservices.core.product.services.ProductMapperImpl()
+@DisabledInNativeImage
 class MapperTests {
 
   private RecommendationMapper mapper = Mappers.getMapper(RecommendationMapper.class);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MapperTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.mapstruct.factory.Mappers;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
import se.magnus.microservices.core.recommendation.services.RecommendationMapper;

// Fails on:
// com.oracle.svm.core.jdk.UnsupportedFeatureError: Runtime reflection is not supported for public se.magnus.microservices.core.product.services.ProductMapperImpl()
@DisabledInNativeImage
class MapperTests {

  private RecommendationMapper mapper = Mappers.getMapper(RecommendationMapper.class);

  @Test
  void mapperTests() {

    assertNotNull(mapper);

    Recommendation api = new Recommendation(1, 2, "a", 4, "C", "adr");

    RecommendationEntity entity = mapper.apiToEntity(api);

    assertEquals(api.getProductId(), entity.getProductId());
    assertEquals(api.getRecommendationId(), entity.getRecommendationId());
    assertEquals(api.getAuthor(), entity.getAuthor());
    assertEquals(api.getRate(), entity.getRating());
    assertEquals(api.getContent(), entity.getContent());

    Recommendation api2 = mapper.entityToApi(entity);

    assertEquals(api.getProductId(), api2.getProductId());
    assertEquals(api.getRecommendationId(), api2.getRecommendationId());
    assertEquals(api.getAuthor(), api2.getAuthor());
    assertEquals(api.getRate(), api2.getRate());
    assertEquals(api.getContent(), api2.getContent());
    assertNull(api2.getServiceAddress());
  }

  @Test
  void mapperListTests() {

    assertNotNull(mapper);

    Recommendation api = new Recommendation(1, 2, "a", 4, "C", "adr");
    List<Recommendation> apiList = Collections.singletonList(api);

    List<RecommendationEntity> entityList = mapper.apiListToEntityList(apiList);
    assertEquals(apiList.size(), entityList.size());

    RecommendationEntity entity = entityList.get(0);

    assertEquals(api.getProductId(), entity.getProductId());
    assertEquals(api.getRecommendationId(), entity.getRecommendationId());
    assertEquals(api.getAuthor(), entity.getAuthor());
    assertEquals(api.getRate(), entity.getRating());
    assertEquals(api.getContent(), entity.getContent());

    List<Recommendation> api2List = mapper.entityListToApiList(entityList);
    assertEquals(apiList.size(), api2List.size());

    Recommendation api2 = api2List.get(0);

    assertEquals(api.getProductId(), api2.getProductId());
    assertEquals(api.getRecommendationId(), api2.getRecommendationId());
    assertEquals(api.getAuthor(), api2.getAuthor());
    assertEquals(api.getRate(), api2.getRate());
    assertEquals(api.getContent(), api2.getContent());
    assertNull(api2.getServiceAddress());
  }
}
```

</details>

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MongoDbTestBase.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,8 +1,13 @@
 package se.magnus.microservices.core.recommendation;
 
+import org.springframework.aot.hint.RuntimeHints;
+import org.springframework.aot.hint.RuntimeHintsRegistrar;
+import org.springframework.aot.hint.TypeReference;
 import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
+import org.springframework.context.annotation.ImportRuntimeHints;
 import org.testcontainers.mongodb.MongoDBContainer;
 
+@ImportRuntimeHints(MongoDbTestBase.MyHints.class)
 public abstract class MongoDbTestBase {
 
   @ServiceConnection
@@ -12,4 +17,12 @@
     database.start();
   }
 
+  // Workaround for the bug in Spring Boot 3.1.4 described here https://github.com/spring-projects/spring-boot/issues/36606
+  static class MyHints implements RuntimeHintsRegistrar {
+    @Override
+    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
+      hints.reflection().registerType(TypeReference.of("com.mongodb.ConnectionString"));
+    }
+  }
+
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MongoDbTestBase.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.aot.hint.TypeReference;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.ImportRuntimeHints;
import org.testcontainers.mongodb.MongoDBContainer;

@ImportRuntimeHints(MongoDbTestBase.MyHints.class)
public abstract class MongoDbTestBase {

  @ServiceConnection
  private static MongoDBContainer database = new MongoDBContainer("mongo:8.0.5");

  static {
    database.start();
  }

  // Workaround for the bug in Spring Boot 3.1.4 described here https://github.com/spring-projects/spring-boot/issues/36606
  static class MyHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
      hints.reflection().registerType(TypeReference.of("com.mongodb.ConnectionString"));
    }
  }

}
```

</details>

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/PersistenceTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -7,6 +7,7 @@
 import java.util.List;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.boot.data.mongodb.test.autoconfigure.DataMongoTest;
 import org.springframework.dao.DuplicateKeyException;
@@ -61,6 +62,9 @@
     assertFalse(repository.existsById(savedEntity.getId()).block());
   }
 
+  // Native tests fails on:
+  // => java.lang.Error: Cannot determine correct type for featureValueOf() method.
+  @DisabledInNativeImage
   @Test
   void getByProductId() {
     List<RecommendationEntity> entityList = repository.findByProductId(savedEntity.getProductId()).collectList().block();
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/PersistenceTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.mongodb.test.autoconfigure.DataMongoTest;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.dao.OptimisticLockingFailureException;
import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;

@DataMongoTest
class PersistenceTests extends MongoDbTestBase {

  @Autowired
  private RecommendationRepository repository;

  private RecommendationEntity savedEntity;

  @BeforeEach
  void setupDb() {
    repository.deleteAll().block();

    RecommendationEntity entity = new RecommendationEntity(1, 2, "a", 3, "c");
    savedEntity = repository.save(entity).block();

    assertEqualsRecommendation(entity, savedEntity);
  }


  @Test
  void create() {

    RecommendationEntity newEntity = new RecommendationEntity(1, 3, "a", 3, "c");
    repository.save(newEntity).block();

    RecommendationEntity foundEntity = repository.findById(newEntity.getId()).block();
    assertEqualsRecommendation(newEntity, foundEntity);

    assertEquals(2, (long)repository.count().block());
  }

  @Test
  void update() {
    savedEntity.setAuthor("a2");
    repository.save(savedEntity).block();

    RecommendationEntity foundEntity = repository.findById(savedEntity.getId()).block();
    assertEquals(1, (long)foundEntity.getVersion());
    assertEquals("a2", foundEntity.getAuthor());
  }

  @Test
  void delete() {
    repository.delete(savedEntity).block();
    assertFalse(repository.existsById(savedEntity.getId()).block());
  }

  // Native tests fails on:
  // => java.lang.Error: Cannot determine correct type for featureValueOf() method.
  @DisabledInNativeImage
  @Test
  void getByProductId() {
    List<RecommendationEntity> entityList = repository.findByProductId(savedEntity.getProductId()).collectList().block();

    assertThat(entityList, hasSize(1));
    assertEqualsRecommendation(savedEntity, entityList.get(0));
  }

  @Test
  void duplicateError() {
    assertThrows(DuplicateKeyException.class, () -> {
      RecommendationEntity entity = new RecommendationEntity(1, 2, "a", 3, "c");
      repository.save(entity).block();
    });
  }

  @Test
  void optimisticLockError() {

    // Store the saved entity in two separate entity objects
    RecommendationEntity entity1 = repository.findById(savedEntity.getId()).block();
    RecommendationEntity entity2 = repository.findById(savedEntity.getId()).block();

    // Update the entity using the first entity object
    entity1.setAuthor("a1");
    repository.save(entity1).block();

    //  Update the entity using the second entity object.
    // This should fail since the second entity now holds an old version number, i.e. an Optimistic Lock Error
    assertThrows(OptimisticLockingFailureException.class, () -> {
      entity2.setAuthor("a2");
      repository.save(entity2).block();
    });

    // Get the updated entity from the database and verify its new sate
    RecommendationEntity updatedEntity = repository.findById(savedEntity.getId()).block();
    assertEquals(1, (int)updatedEntity.getVersion());
    assertEquals("a1", updatedEntity.getAuthor());
  }

  private void assertEqualsRecommendation(RecommendationEntity expectedEntity, RecommendationEntity actualEntity) {
    assertEquals(expectedEntity.getId(),               actualEntity.getId());
    assertEquals(expectedEntity.getVersion(),          actualEntity.getVersion());
    assertEquals(expectedEntity.getProductId(),        actualEntity.getProductId());
    assertEquals(expectedEntity.getRecommendationId(), actualEntity.getRecommendationId());
    assertEquals(expectedEntity.getAuthor(),           actualEntity.getAuthor());
    assertEquals(expectedEntity.getRating(),           actualEntity.getRating());
    assertEquals(expectedEntity.getContent(),          actualEntity.getContent());
  }
}
```

</details>

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -10,6 +10,7 @@
 import java.util.function.Consumer;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.beans.factory.annotation.Qualifier;
 import org.springframework.boot.test.context.SpringBootTest;
@@ -40,6 +41,12 @@
     repository.deleteAll().block();
   }
 
+  // Fails on:
+  //  java.lang.AssertionError: No value at JSON path "$.length()"
+  //  Caused by: com.jayway.jsonpath.InvalidPathException: Function of name: length cannot be created
+  //  Caused by: java.lang.InstantiationException: com.jayway.jsonpath.internal.function.text.Length
+  //  Caused by: java.lang.NoSuchMethodException: com.jayway.jsonpath.internal.function.text.Length.<init>()
+  @DisabledInNativeImage
   @Test
   void getRecommendationsByProductId() {
 
@@ -107,6 +114,12 @@
       .jsonPath("$.message").isEqualTo("Type mismatch.");
   }
 
+  // Fails on:
+  //  java.lang.AssertionError: No value at JSON path "$.length()"
+  //  Caused by: com.jayway.jsonpath.InvalidPathException: Function of name: length cannot be created
+  //  Caused by: java.lang.InstantiationException: com.jayway.jsonpath.internal.function.text.Length
+  //  Caused by: java.lang.NoSuchMethodException: com.jayway.jsonpath.internal.function.text.Length.<init>()
+  @DisabledInNativeImage
   @Test
   void getRecommendationsNotFound() {
 
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static se.magnus.api.event.Event.Type.CREATE;
import static se.magnus.api.event.Event.Type.DELETE;

import java.util.function.Consumer;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.event.Event;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
class RecommendationServiceApplicationTests extends MongoDbTestBase {

  @Autowired
  private WebTestClient client;

  @Autowired
  private RecommendationRepository repository;

  @Autowired
  @Qualifier("messageProcessor")
  private Consumer<Event<Integer, Recommendation>> messageProcessor;

  @BeforeEach
  void setupDb() {
    repository.deleteAll().block();
  }

  // Fails on:
  //  java.lang.AssertionError: No value at JSON path "$.length()"
  //  Caused by: com.jayway.jsonpath.InvalidPathException: Function of name: length cannot be created
  //  Caused by: java.lang.InstantiationException: com.jayway.jsonpath.internal.function.text.Length
  //  Caused by: java.lang.NoSuchMethodException: com.jayway.jsonpath.internal.function.text.Length.<init>()
  @DisabledInNativeImage
  @Test
  void getRecommendationsByProductId() {

    int productId = 1;

    sendCreateRecommendationEvent(productId, 1);
    sendCreateRecommendationEvent(productId, 2);
    sendCreateRecommendationEvent(productId, 3);

    assertEquals(3, (long)repository.findByProductId(productId).count().block());

    getAndVerifyRecommendationsByProductId(productId, OK)
      .jsonPath("$.length()").isEqualTo(3)
      .jsonPath("$[2].productId").isEqualTo(productId)
      .jsonPath("$[2].recommendationId").isEqualTo(3);
  }

  @Test
  void duplicateError() {

    int productId = 1;
    int recommendationId = 1;

    sendCreateRecommendationEvent(productId, recommendationId);

    assertEquals(1, (long)repository.count().block());

    InvalidInputException thrown = assertThrows(
      InvalidInputException.class,
      () -> sendCreateRecommendationEvent(productId, recommendationId),
      "Expected a InvalidInputException here!");
    assertEquals("Duplicate key, Product Id: 1, Recommendation Id:1", thrown.getMessage());

    assertEquals(1, (long)repository.count().block());
  }

  @Test
  void deleteRecommendations() {

    int productId = 1;
    int recommendationId = 1;

    sendCreateRecommendationEvent(productId, recommendationId);
    assertEquals(1, (long)repository.findByProductId(productId).count().block());

    sendDeleteRecommendationEvent(productId);
    assertEquals(0, (long)repository.findByProductId(productId).count().block());

    sendDeleteRecommendationEvent(productId);
  }

  @Test
  void getRecommendationsMissingParameter() {

    getAndVerifyRecommendationsByProductId("", BAD_REQUEST)
      .jsonPath("$.path").isEqualTo("/recommendation")
      .jsonPath("$.message").isEqualTo("Required query parameter 'productId' is not present.");
  }

  @Test
  void getRecommendationsInvalidParameter() {

    getAndVerifyRecommendationsByProductId("?productId=no-integer", BAD_REQUEST)
      .jsonPath("$.path").isEqualTo("/recommendation")
      .jsonPath("$.message").isEqualTo("Type mismatch.");
  }

  // Fails on:
  //  java.lang.AssertionError: No value at JSON path "$.length()"
  //  Caused by: com.jayway.jsonpath.InvalidPathException: Function of name: length cannot be created
  //  Caused by: java.lang.InstantiationException: com.jayway.jsonpath.internal.function.text.Length
  //  Caused by: java.lang.NoSuchMethodException: com.jayway.jsonpath.internal.function.text.Length.<init>()
  @DisabledInNativeImage
  @Test
  void getRecommendationsNotFound() {

    getAndVerifyRecommendationsByProductId("?productId=113", OK)
      .jsonPath("$.length()").isEqualTo(0);
  }

  @Test
  void getRecommendationsInvalidParameterNegativeValue() {

    int productIdInvalid = -1;

    getAndVerifyRecommendationsByProductId("?productId=" + productIdInvalid, UNPROCESSABLE_CONTENT)
      .jsonPath("$.path").isEqualTo("/recommendation")
      .jsonPath("$.message").isEqualTo("Invalid productId: " + productIdInvalid);
  }

  private WebTestClient.BodyContentSpec getAndVerifyRecommendationsByProductId(int productId, HttpStatus expectedStatus) {
    return getAndVerifyRecommendationsByProductId("?productId=" + productId, expectedStatus);
  }

  private WebTestClient.BodyContentSpec getAndVerifyRecommendationsByProductId(String productIdQuery, HttpStatus expectedStatus) {
    return client.get()
      .uri("/recommendation" + productIdQuery)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody();
  }

  private void sendCreateRecommendationEvent(int productId, int recommendationId) {
    Recommendation recommendation = new Recommendation(productId, recommendationId, "Author " + recommendationId, recommendationId, "Content " + recommendationId, "SA");
    Event<Integer, Recommendation> event = new Event<>(CREATE, productId, recommendation);
    messageProcessor.accept(event);
  }

  private void sendDeleteRecommendationEvent(int productId) {
    Event<Integer, Recommendation> event = new Event<>(DELETE, productId, null);
    messageProcessor.accept(event);
  }
}
```

</details>

#### `microservices/recommendation-service/src/test/resources/access-filter.json` — 새 파일 (17줄)

<!-- wb:file path="microservices/recommendation-service/src/test/resources/access-filter.json" op="write" nl="0" -->
```json
{ "rules":
  [
    {"excludeClasses": "org.apache.maven.surefire.**"},
    {"excludeClasses": "net.bytebuddy.**"},
    {"excludeClasses": "org.apiguardian.**"},
    {"excludeClasses": "org.junit.**"},
    {"excludeClasses": "org.gradle.**"},
    {"excludeClasses": "org.mockito.**"},
    {"excludeClasses": "org.springframework.test.**"},
    {"excludeClasses": "org.springframework.boot.test.**"},
    {"excludeClasses": "org.testcontainers.**"},
    {"excludeClasses": "se.magnus.microservices.core.recommendation.MapperTests"},
    {"excludeClasses": "se.magnus.microservices.core.recommendation.MongoDbTestBase"},
    {"excludeClasses": "se.magnus.microservices.core.recommendation.PersistenceTests"},
    {"excludeClasses": "se.magnus.microservices.core.recommendation.ProductServiceApplicationTests"}
  ]
}
```

**중간 확인**

```bash
./gradlew :microservices:recommendation-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-4"></a>

## 단계 4. `review-service`

네이티브 빌드 플러그인과 `bootBuildImage` 설정, `NativeHintsConfiguration`을 추가합니다. 네이티브 이미지에서 쓰는 `application.yml`과 테스트용 접근 필터가 추가되고, `Dockerfile`은 JVM AOT 모드 실습용으로 바뀝니다.

#### `microservices/review-service/Dockerfile` — 전체를 바꿉니다 (`microservices/product-service/Dockerfile`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/review-service && cp microservices/product-service/Dockerfile microservices/review-service/Dockerfile
```

<!-- wb:file path="microservices/review-service/Dockerfile" op="cp" src="microservices/product-service/Dockerfile" -->

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,6 +1,7 @@
 plugins {
     id 'org.springframework.boot' version '4.0.9'
     id 'io.spring.dependency-management' version '1.1.7'
+    id 'org.graalvm.buildtools.native' version '0.11.5'
     id 'java'
 }
 
@@ -22,9 +23,11 @@
     mavenCentral()
 }
 
-jar {
-    enabled = false
-}
+// Prevents GraalVM to native compile locally, i.e. without Docker-buildpacks
+// See https://github.com/spring-projects/spring-boot/issues/33238
+//jar {
+//    enabled = false
+//}
 
 dependencies {
     implementation project(':api')
@@ -37,11 +40,9 @@
     implementation 'io.micrometer:micrometer-tracing-bridge-brave'
     implementation 'org.springframework.boot:spring-boot-starter-zipkin'
     implementation 'net.ttddyy.observation:datasource-micrometer-spring-boot:2.2.1'
-    implementation 'org.springframework.retry:spring-retry'
     implementation 'com.mysql:mysql-connector-j'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
     implementation 'io.micrometer:micrometer-registry-prometheus'
-
     compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
     annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
     testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
@@ -69,4 +70,13 @@
 
 tasks.named('test') {
     useJUnitPlatform()
+    // Tracing agent works with the review service, but is disabled to avoid changes to the source code, i.e. src/main/resources/META-INF/native-image
+    // jvmArgs "-agentlib:native-image-agent=access-filter-file=src/test/resources/access-filter.json,config-output-dir=src/main/resources/META-INF/native-image"
 }
+
+tasks.named('bootBuildImage') {
+    createdDate = "now"
+    // Spring Boot 4 requires GraalVM 25 or later for native images
+    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
+    imageName = "hands-on/native-review-service"
+}
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'org.graalvm.buildtools.native' version '0.11.5'
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

// Prevents GraalVM to native compile locally, i.e. without Docker-buildpacks
// See https://github.com/spring-projects/spring-boot/issues/33238
//jar {
//    enabled = false
//}

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
    // Tracing agent works with the review service, but is disabled to avoid changes to the source code, i.e. src/main/resources/META-INF/native-image
    // jvmArgs "-agentlib:native-image-agent=access-filter-file=src/test/resources/access-filter.json,config-output-dir=src/main/resources/META-INF/native-image"
}

tasks.named('bootBuildImage') {
    createdDate = "now"
    // Spring Boot 4 requires GraalVM 25 or later for native images
    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
    imageName = "hands-on/native-review-service"
}
```

</details>

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/NativeHintsConfiguration.java` — 새 파일 (23줄)

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/NativeHintsConfiguration.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ImportRuntimeHints;

@Configuration
@ImportRuntimeHints(NativeHintsConfiguration.class)
public class NativeHintsConfiguration implements RuntimeHintsRegistrar {

  private static final Logger LOG = LoggerFactory.getLogger(NativeHintsConfiguration.class);

  @Override
  public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
    LOG.info("Will register native hints for the review service");

    // Workaround for the error: "java.io.IOException: Resource not found: "org/joda/time/tz/data/ZoneInfoMap"
    hints.resources().registerPattern("org/joda/time/tz/data/**");
  }
}
```

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -2,6 +2,7 @@
 
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
+import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
 import org.springframework.beans.factory.annotation.Value;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
@@ -11,9 +12,13 @@
 import reactor.core.publisher.Hooks;
 import reactor.core.scheduler.Scheduler;
 import reactor.core.scheduler.Schedulers;
+import se.magnus.api.core.review.Review;
+import se.magnus.api.event.Event;
+import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;
 
 @SpringBootApplication
 @ComponentScan("se.magnus")
+@RegisterReflectionForBinding({ Event.class, ZonedDateTimeSerializer.class, Review.class})
 public class ReviewServiceApplication {
 
   private static final Logger LOG = LoggerFactory.getLogger(ReviewServiceApplication.class);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import reactor.core.publisher.Hooks;
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;
import se.magnus.api.core.review.Review;
import se.magnus.api.event.Event;
import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;

@SpringBootApplication
@ComponentScan("se.magnus")
@RegisterReflectionForBinding({ Event.class, ZonedDateTimeSerializer.class, Review.class})
public class ReviewServiceApplication {

  private static final Logger LOG = LoggerFactory.getLogger(ReviewServiceApplication.class);

  private final Integer threadPoolSize;
  private final Integer taskQueueSize;

  public ReviewServiceApplication(
    @Value("${app.threadPoolSize:10}") Integer threadPoolSize,
    @Value("${app.taskQueueSize:100}") Integer taskQueueSize
  ) {
    this.threadPoolSize = threadPoolSize;
    this.taskQueueSize = taskQueueSize;
  }

  @Bean
  public Scheduler jdbcScheduler() {
    LOG.info("Creates a jdbcScheduler with thread pool size = {}", threadPoolSize);
    return Schedulers.newBoundedElastic(threadPoolSize, taskQueueSize, "jdbc-pool");
  }

  public static void main(String[] args) {
    Hooks.enableAutomaticContextPropagation();
    ConfigurableApplicationContext ctx = SpringApplication.run(ReviewServiceApplication.class, args);

    String mysqlUri = ctx.getEnvironment().getProperty("spring.datasource.url");
    LOG.info("Connected to MySQL: " + mysqlUri);
  }
}
```

</details>

#### `microservices/review-service/src/main/resources/application.yml` — 새 파일 (13줄)

<!-- wb:file path="microservices/review-service/src/main/resources/application.yml" op="write" nl="1" -->
```yaml
# Required to make the Spring AOT engine generate the appropriate infrastructure for a separate management port, prometheus and K8S probes at build time
management.server.port: 9009
management.endpoint.health.probes.enabled: true
management.endpoints.web.exposure.include: health,info,prometheus

# Native Compile: Point out that RabbitMQ is to be used when performing the native compile
spring.cloud.stream.defaultBinder: rabbit

# Native Compile: Required to disable the health check of RabbitMQ when using Kafka
# management.health.rabbit.enabled: false

# Native Compile: Required to disable the health check of Kafka when using RabbitMQ
management.health.kafka.enabled: false
```

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/MapperTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -5,12 +5,15 @@
 import java.util.Collections;
 import java.util.List;
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.mapstruct.factory.Mappers;
 import se.magnus.api.core.review.Review;
 import se.magnus.microservices.core.review.persistence.ReviewEntity;
 import se.magnus.microservices.core.review.services.ReviewMapper;
 
-
+// Fails on:
+// com.oracle.svm.core.jdk.UnsupportedFeatureError: Runtime reflection is not supported for public se.magnus.microservices.core.product.services.ProductMapperImpl()
+@DisabledInNativeImage
 class MapperTests {
 
   private ReviewMapper mapper = Mappers.getMapper(ReviewMapper.class);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/MapperTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.mapstruct.factory.Mappers;
import se.magnus.api.core.review.Review;
import se.magnus.microservices.core.review.persistence.ReviewEntity;
import se.magnus.microservices.core.review.services.ReviewMapper;

// Fails on:
// com.oracle.svm.core.jdk.UnsupportedFeatureError: Runtime reflection is not supported for public se.magnus.microservices.core.product.services.ProductMapperImpl()
@DisabledInNativeImage
class MapperTests {

  private ReviewMapper mapper = Mappers.getMapper(ReviewMapper.class);

  @Test
  void mapperTests() {

    assertNotNull(mapper);

    Review api = new Review(1, 2, "a", "s", "C", "adr");

    ReviewEntity entity = mapper.apiToEntity(api);

    assertEquals(api.getProductId(), entity.getProductId());
    assertEquals(api.getReviewId(), entity.getReviewId());
    assertEquals(api.getAuthor(), entity.getAuthor());
    assertEquals(api.getSubject(), entity.getSubject());
    assertEquals(api.getContent(), entity.getContent());

    Review api2 = mapper.entityToApi(entity);

    assertEquals(api.getProductId(), api2.getProductId());
    assertEquals(api.getReviewId(), api2.getReviewId());
    assertEquals(api.getAuthor(), api2.getAuthor());
    assertEquals(api.getSubject(), api2.getSubject());
    assertEquals(api.getContent(), api2.getContent());
    assertNull(api2.getServiceAddress());
  }

  @Test
  void mapperListTests() {

    assertNotNull(mapper);

    Review api = new Review(1, 2, "a", "s", "C", "adr");
    List<Review> apiList = Collections.singletonList(api);

    List<ReviewEntity> entityList = mapper.apiListToEntityList(apiList);
    assertEquals(apiList.size(), entityList.size());

    ReviewEntity entity = entityList.get(0);

    assertEquals(api.getProductId(), entity.getProductId());
    assertEquals(api.getReviewId(), entity.getReviewId());
    assertEquals(api.getAuthor(), entity.getAuthor());
    assertEquals(api.getSubject(), entity.getSubject());
    assertEquals(api.getContent(), entity.getContent());

    List<Review> api2List = mapper.entityListToApiList(entityList);
    assertEquals(apiList.size(), api2List.size());

    Review api2 = api2List.get(0);

    assertEquals(api.getProductId(), api2.getProductId());
    assertEquals(api.getReviewId(), api2.getReviewId());
    assertEquals(api.getAuthor(), api2.getAuthor());
    assertEquals(api.getSubject(), api2.getSubject());
    assertEquals(api.getContent(), api2.getContent());
    assertNull(api2.getServiceAddress());
  }
}
```

</details>

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/PersistenceTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -8,6 +8,7 @@
 import java.util.List;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
 import org.springframework.dao.DataIntegrityViolationException;
@@ -16,6 +17,8 @@
 import se.magnus.microservices.core.review.persistence.ReviewEntity;
 import se.magnus.microservices.core.review.persistence.ReviewRepository;
 
+// Native tests fails on " java.lang.IllegalArgumentException: Resource with path mysql-default-conf could not be found on any of these classloaders: ..."
+@DisabledInNativeImage
 @DataJpaTest(properties = {"spring.jpa.hibernate.ddl-auto=update"})
 @Transactional(propagation = NOT_SUPPORTED)
 class PersistenceTests extends MySqlTestBase {
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/PersistenceTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.transaction.annotation.Propagation.NOT_SUPPORTED;

import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.transaction.annotation.Transactional;
import se.magnus.microservices.core.review.persistence.ReviewEntity;
import se.magnus.microservices.core.review.persistence.ReviewRepository;

// Native tests fails on " java.lang.IllegalArgumentException: Resource with path mysql-default-conf could not be found on any of these classloaders: ..."
@DisabledInNativeImage
@DataJpaTest(properties = {"spring.jpa.hibernate.ddl-auto=update"})
@Transactional(propagation = NOT_SUPPORTED)
class PersistenceTests extends MySqlTestBase {

  @Autowired
  private ReviewRepository repository;

  private ReviewEntity savedEntity;

  @BeforeEach
  void setupDb() {
    repository.deleteAll();

    ReviewEntity entity = new ReviewEntity(1, 2, "a", "s", "c");
    savedEntity = repository.save(entity);

    assertEqualsReview(entity, savedEntity);
  }


  @Test
  void create() {

    ReviewEntity newEntity = new ReviewEntity(1, 3, "a", "s", "c");
    repository.save(newEntity);

    ReviewEntity foundEntity = repository.findById(newEntity.getId()).get();
    assertEqualsReview(newEntity, foundEntity);

    assertEquals(2, repository.count());
  }

  @Test
  void update() {
    savedEntity.setAuthor("a2");
    repository.save(savedEntity);

    ReviewEntity foundEntity = repository.findById(savedEntity.getId()).get();
    assertEquals(1, (long)foundEntity.getVersion());
    assertEquals("a2", foundEntity.getAuthor());
  }

  @Test
  void delete() {
    repository.delete(savedEntity);
    assertFalse(repository.existsById(savedEntity.getId()));
  }

  @Test
  void getByProductId() {
    List<ReviewEntity> entityList = repository.findByProductId(savedEntity.getProductId());

    assertThat(entityList, hasSize(1));
    assertEqualsReview(savedEntity, entityList.get(0));
  }

  @Test
  void duplicateError() {
    assertThrows(DataIntegrityViolationException.class, () -> {
      ReviewEntity entity = new ReviewEntity(1, 2, "a", "s", "c");
      repository.save(entity);
    });

  }

  @Test
  void optimisticLockError() {

    // Store the saved entity in two separate entity objects
    ReviewEntity entity1 = repository.findById(savedEntity.getId()).get();
    ReviewEntity entity2 = repository.findById(savedEntity.getId()).get();

    // Update the entity using the first entity object
    entity1.setAuthor("a1");
    repository.save(entity1);

    // Update the entity using the second entity object.
    // This should fail since the second entity now holds an old version number, i.e. an Optimistic Lock Error
    assertThrows(OptimisticLockingFailureException.class, () -> {
      entity2.setAuthor("a2");
      repository.save(entity2);
    });

    // Get the updated entity from the database and verify its new sate
    ReviewEntity updatedEntity = repository.findById(savedEntity.getId()).get();
    assertEquals(1, (int)updatedEntity.getVersion());
    assertEquals("a1", updatedEntity.getAuthor());
  }

  private void assertEqualsReview(ReviewEntity expectedEntity, ReviewEntity actualEntity) {
    assertEquals(expectedEntity.getId(),        actualEntity.getId());
    assertEquals(expectedEntity.getVersion(),   actualEntity.getVersion());
    assertEquals(expectedEntity.getProductId(), actualEntity.getProductId());
    assertEquals(expectedEntity.getReviewId(),  actualEntity.getReviewId());
    assertEquals(expectedEntity.getAuthor(),    actualEntity.getAuthor());
    assertEquals(expectedEntity.getSubject(),   actualEntity.getSubject());
    assertEquals(expectedEntity.getContent(),   actualEntity.getContent());
  }
}
```

</details>

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -10,6 +10,7 @@
 import java.util.function.Consumer;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.beans.factory.annotation.Qualifier;
 import org.springframework.boot.test.context.SpringBootTest;
@@ -21,6 +22,8 @@
 import se.magnus.api.exceptions.InvalidInputException;
 import se.magnus.microservices.core.review.persistence.ReviewRepository;
 
+// Native tests fails on " java.lang.IllegalArgumentException: Resource with path mysql-default-conf could not be found on any of these classloaders: ..."
+@DisabledInNativeImage
 @AutoConfigureWebTestClient
 @SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
   "spring.cloud.stream.defaultBinder=rabbit",
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static se.magnus.api.event.Event.Type.CREATE;
import static se.magnus.api.event.Event.Type.DELETE;

import java.util.function.Consumer;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import se.magnus.api.core.review.Review;
import se.magnus.api.event.Event;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.microservices.core.review.persistence.ReviewRepository;

// Native tests fails on " java.lang.IllegalArgumentException: Resource with path mysql-default-conf could not be found on any of these classloaders: ..."
@DisabledInNativeImage
@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
  "spring.cloud.stream.defaultBinder=rabbit",
  "logging.level.se.magnus=DEBUG",
  "spring.jpa.hibernate.ddl-auto=update"})
class ReviewServiceApplicationTests extends MySqlTestBase {

  @Autowired
  private WebTestClient client;

  @Autowired
  private ReviewRepository repository;

  @Autowired
  @Qualifier("messageProcessor")
  private Consumer<Event<Integer, Review>> messageProcessor;

  @BeforeEach
  void setupDb() {
    repository.deleteAll();
  }

  @Test
  void getReviewsByProductId() {

    int productId = 1;

    assertEquals(0, repository.findByProductId(productId).size());

    sendCreateReviewEvent(productId, 1);
    sendCreateReviewEvent(productId, 2);
    sendCreateReviewEvent(productId, 3);

    assertEquals(3, repository.findByProductId(productId).size());

    getAndVerifyReviewsByProductId(productId, OK)
      .jsonPath("$.length()").isEqualTo(3)
      .jsonPath("$[2].productId").isEqualTo(productId)
      .jsonPath("$[2].reviewId").isEqualTo(3);
  }

  @Test
  void duplicateError() {

    int productId = 1;
    int reviewId = 1;

    assertEquals(0, repository.count());

    sendCreateReviewEvent(productId, reviewId);

    assertEquals(1, repository.count());

    InvalidInputException thrown = assertThrows(
      InvalidInputException.class,
      () -> sendCreateReviewEvent(productId, reviewId),
      "Expected a InvalidInputException here!");
    assertEquals("Duplicate key, Product Id: 1, Review Id:1", thrown.getMessage());

    assertEquals(1, repository.count());
  }

  @Test
  void deleteReviews() {

    int productId = 1;
    int reviewId = 1;

    sendCreateReviewEvent(productId, reviewId);
    assertEquals(1, repository.findByProductId(productId).size());

    sendDeleteReviewEvent(productId);
    assertEquals(0, repository.findByProductId(productId).size());

    sendDeleteReviewEvent(productId);
  }

  @Test
  void getReviewsMissingParameter() {

    getAndVerifyReviewsByProductId("", BAD_REQUEST)
      .jsonPath("$.path").isEqualTo("/review")
      .jsonPath("$.message").isEqualTo("Required query parameter 'productId' is not present.");
  }

  @Test
  void getReviewsInvalidParameter() {

    getAndVerifyReviewsByProductId("?productId=no-integer", BAD_REQUEST)
      .jsonPath("$.path").isEqualTo("/review")
      .jsonPath("$.message").isEqualTo("Type mismatch.");
  }

  @Test
  void getReviewsNotFound() {

    getAndVerifyReviewsByProductId("?productId=213", OK)
      .jsonPath("$.length()").isEqualTo(0);
  }

  @Test
  void getReviewsInvalidParameterNegativeValue() {

    int productIdInvalid = -1;

    getAndVerifyReviewsByProductId("?productId=" + productIdInvalid, UNPROCESSABLE_CONTENT)
      .jsonPath("$.path").isEqualTo("/review")
      .jsonPath("$.message").isEqualTo("Invalid productId: " + productIdInvalid);
  }

  private WebTestClient.BodyContentSpec getAndVerifyReviewsByProductId(int productId, HttpStatus expectedStatus) {
    return getAndVerifyReviewsByProductId("?productId=" + productId, expectedStatus);
  }

  private WebTestClient.BodyContentSpec getAndVerifyReviewsByProductId(String productIdQuery, HttpStatus expectedStatus) {
    return client.get()
      .uri("/review" + productIdQuery)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody();
  }

  private void sendCreateReviewEvent(int productId, int reviewId) {
    Review review = new Review(productId, reviewId, "Author " + reviewId, "Subject " + reviewId, "Content " + reviewId, "SA");
    Event<Integer, Review> event = new Event<>(CREATE, productId, review);
    messageProcessor.accept(event);
  }

  private void sendDeleteReviewEvent(int productId) {
    Event<Integer, Review> event = new Event<>(DELETE, productId, null);
    messageProcessor.accept(event);
  }
}
```

</details>

#### `microservices/review-service/src/test/resources/access-filter.json` — 새 파일 (17줄)

<!-- wb:file path="microservices/review-service/src/test/resources/access-filter.json" op="write" nl="0" -->
```json
{ "rules":
  [
    {"excludeClasses": "org.apache.maven.surefire.**"},
    {"excludeClasses": "net.bytebuddy.**"},
    {"excludeClasses": "org.apiguardian.**"},
    {"excludeClasses": "org.junit.**"},
    {"excludeClasses": "org.gradle.**"},
    {"excludeClasses": "org.mockito.**"},
    {"excludeClasses": "org.springframework.test.**"},
    {"excludeClasses": "org.springframework.boot.test.**"},
    {"excludeClasses": "org.testcontainers.**"},
    {"excludeClasses": "se.magnus.microservices.core.review.MapperTests"},
    {"excludeClasses": "se.magnus.microservices.core.review.MySqlTestBase"},
    {"excludeClasses": "se.magnus.microservices.core.review.PersistenceTests"},
    {"excludeClasses": "se.magnus.microservices.core.review.ReviewServiceApplicationTests"}
  ]
}
```

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `product-composite-service`

다른 서비스와 같이 네이티브 빌드 설정과 힌트를 추가합니다.

#### `microservices/product-composite-service/Dockerfile` — 전체를 바꿉니다 (`microservices/product-service/Dockerfile`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/product-composite-service && cp microservices/product-service/Dockerfile microservices/product-composite-service/Dockerfile
```

<!-- wb:file path="microservices/product-composite-service/Dockerfile" op="cp" src="microservices/product-service/Dockerfile" -->

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,6 +1,7 @@
 plugins {
     id 'org.springframework.boot' version '4.0.9'
     id 'io.spring.dependency-management' version '1.1.7'
+    id 'org.graalvm.buildtools.native' version '0.11.5'
     id 'java'
 }
 
@@ -21,9 +22,11 @@
     mavenCentral()
 }
 
-jar {
-    enabled = false
-}
+// Prevents GraalVM to native compile locally, i.e. without Docker-buildpacks
+// See https://github.com/spring-projects/spring-boot/issues/33238
+//jar {
+//    enabled = false
+//}
 
 springBoot {
     buildInfo()
@@ -68,4 +71,18 @@
 
 tasks.named('test') {
     useJUnitPlatform()
+    // Tracing agent works with the prod-comp service, but is disabled to avoid changes to the source code, i.e. src/main/resources/META-INF/native-image
+    // jvmArgs "-agentlib:native-image-agent=access-filter-file=src/test/resources/access-filter.json,config-output-dir=src/main/resources/META-INF/native-image"
+
+//    testLogging {
+//        outputs.upToDateWhen {false}
+//        showStandardStreams = true
+//    }
 }
+
+tasks.named('bootBuildImage') {
+    createdDate = "now"
+    // Spring Boot 4 requires GraalVM 25 or later for native images
+    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
+    imageName = "hands-on/native-product-composite-service"
+}
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/build.gradle" op="write" nl="0" -->
```groovy
plugins {
    id 'org.springframework.boot' version '4.0.9'
    id 'io.spring.dependency-management' version '1.1.7'
    id 'org.graalvm.buildtools.native' version '0.11.5'
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

// Prevents GraalVM to native compile locally, i.e. without Docker-buildpacks
// See https://github.com/spring-projects/spring-boot/issues/33238
//jar {
//    enabled = false
//}

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
    // Tracing agent works with the prod-comp service, but is disabled to avoid changes to the source code, i.e. src/main/resources/META-INF/native-image
    // jvmArgs "-agentlib:native-image-agent=access-filter-file=src/test/resources/access-filter.json,config-output-dir=src/main/resources/META-INF/native-image"

//    testLogging {
//        outputs.upToDateWhen {false}
//        showStandardStreams = true
//    }
}

tasks.named('bootBuildImage') {
    createdDate = "now"
    // Spring Boot 4 requires GraalVM 25 or later for native images
    environment = ["BP_NATIVE_IMAGE": "true", "BP_JVM_VERSION": "25"]
    imageName = "hands-on/native-product-composite-service"
}
```

</details>

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/NativeHintsConfiguration.java` — 새 파일 (57줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/NativeHintsConfiguration.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import static org.springframework.aot.hint.MemberCategory.INVOKE_DECLARED_CONSTRUCTORS;
import static org.springframework.aot.hint.MemberCategory.INVOKE_DECLARED_METHODS;

import com.fasterxml.jackson.databind.BeanDescription;
import io.swagger.v3.core.jackson.mixin.Schema31Mixin;
import io.swagger.v3.oas.models.media.JsonSchema;
import java.lang.invoke.MethodHandles;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aot.hint.BindingReflectionHintsRegistrar;
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.context.annotation.Configuration;
import org.springframework.boot.health.contributor.Health;
import org.springframework.context.annotation.ImportRuntimeHints;
import org.springframework.util.ClassUtils;

@Configuration
@ImportRuntimeHints(NativeHintsConfiguration.class)
public class NativeHintsConfiguration implements RuntimeHintsRegistrar {

  private static final Logger LOG = LoggerFactory.getLogger(NativeHintsConfiguration.class);

  @Override
  public void registerHints(RuntimeHints hints, ClassLoader classLoader) {

    LOG.info("Will register native hints for the product composite service");

    // Due to missing native hint in springdoc-openapi v2.8.3
    // See https://github.com/swagger-api/swagger-ui/issues/10220
    hints.reflection().registerType(BeanDescription.class, INVOKE_DECLARED_METHODS);

    hints.reflection().registerType(MethodHandles.Lookup.class);
    hints.reflection().registerType(Schema31Mixin.TypeSerializer.class, INVOKE_DECLARED_CONSTRUCTORS);
    hints.reflection().registerType(JsonSchema.class, INVOKE_DECLARED_CONSTRUCTORS);

    // Spring Boot 4: Resilience4j puts one Health object per circuit breaker in the details of its health
    // indicator. No binding hints are generated for these nested objects, so in a native image they were
    // serialized as {} and /actuator/health lacked components.circuitBreakers.details.product.details.state.
    BindingReflectionHintsRegistrar bindingHints = new BindingReflectionHintsRegistrar();
    bindingHints.registerReflectionHints(hints.reflection(), Health.class);

    // Same for the responses of /actuator/circuitbreakerevents
    for (String className : new String[] {
      "io.github.resilience4j.common.circuitbreaker.monitoring.endpoint.CircuitBreakerEventsEndpointResponse",
      "io.github.resilience4j.common.circuitbreaker.monitoring.endpoint.CircuitBreakerEventDTO"}) {
      if (ClassUtils.isPresent(className, classLoader)) {
        bindingHints.registerReflectionHints(hints.reflection(), ClassUtils.resolveClassName(className, classLoader));
      }
    }

    // Workaround for the error: "java.io.IOException: Resource not found: "org/joda/time/tz/data/ZoneInfoMap"
    hints.resources().registerPattern("org/joda/time/tz/data/**");
  }
}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/OpenApiConfig.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/OpenApiConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.security.OAuthFlow;
import io.swagger.v3.oas.annotations.security.OAuthFlows;
import io.swagger.v3.oas.annotations.security.OAuthScope;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springframework.context.annotation.Configuration;

@Configuration
@SecurityScheme(
  name = "security_auth", type = SecuritySchemeType.OAUTH2,
  flows = @OAuthFlows(
    authorizationCode = @OAuthFlow(
      authorizationUrl = "${springdoc.oAuthFlow.authorizationUrl}",
      tokenUrl = "${springdoc.oAuthFlow.tokenUrl}",
      scopes = {
        @OAuthScope(name = "product:read", description = "read scope"),
        @OAuthScope(name = "product:write", description = "write scope")
      }
    )
  )
)
public class OpenApiConfig {}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -7,18 +7,27 @@
 import io.swagger.v3.oas.models.info.License;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
+import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
 import org.springframework.beans.factory.annotation.Value;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
 import org.springframework.context.annotation.Bean;
 import org.springframework.context.annotation.ComponentScan;
+import org.springframework.messaging.Message;
 import org.springframework.web.reactive.function.client.WebClient;
+import org.springframework.web.reactive.function.client.WebClientResponseException;
 import reactor.core.publisher.Hooks;
 import reactor.core.scheduler.Scheduler;
 import reactor.core.scheduler.Schedulers;
+import se.magnus.api.core.product.Product;
+import se.magnus.api.core.recommendation.Recommendation;
+import se.magnus.api.core.review.Review;
+import se.magnus.api.event.Event;
+import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;
 
 @SpringBootApplication
 @ComponentScan("se.magnus")
+@RegisterReflectionForBinding({ Event.class, ZonedDateTimeSerializer.class, Product.class, Recommendation.class, Review.class, Message.class, WebClientResponseException.InternalServerError.class})
 public class ProductCompositeServiceApplication {
 
   private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeServiceApplication.class);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import io.swagger.v3.oas.models.ExternalDocumentation;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.messaging.Message;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Hooks;
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.review.Review;
import se.magnus.api.event.Event;
import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;

@SpringBootApplication
@ComponentScan("se.magnus")
@RegisterReflectionForBinding({ Event.class, ZonedDateTimeSerializer.class, Product.class, Recommendation.class, Review.class, Message.class, WebClientResponseException.InternalServerError.class})
public class ProductCompositeServiceApplication {

  private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeServiceApplication.class);

  @Value("${api.common.version}")         String apiVersion;
  @Value("${api.common.title}")           String apiTitle;
  @Value("${api.common.description}")     String apiDescription;
  @Value("${api.common.termsOfService}")  String apiTermsOfService;
  @Value("${api.common.license}")         String apiLicense;
  @Value("${api.common.licenseUrl}")      String apiLicenseUrl;
  @Value("${api.common.externalDocDesc}") String apiExternalDocDesc;
  @Value("${api.common.externalDocUrl}")  String apiExternalDocUrl;
  @Value("${api.common.contact.name}")    String apiContactName;
  @Value("${api.common.contact.url}")     String apiContactUrl;
  @Value("${api.common.contact.email}")   String apiContactEmail;

  /**
  * Will exposed on $HOST:$PORT/swagger-ui.html
  *
  * @return the common OpenAPI documentation
  */
  @Bean
  public OpenAPI getOpenApiDocumentation() {
    return new OpenAPI()
      .info(new Info().title(apiTitle)
        .description(apiDescription)
        .version(apiVersion)
        .contact(new Contact()
          .name(apiContactName)
          .url(apiContactUrl)
          .email(apiContactEmail))
        .termsOfService(apiTermsOfService)
        .license(new License()
          .name(apiLicense)
          .url(apiLicenseUrl)))
      .externalDocs(new ExternalDocumentation()
        .description(apiExternalDocDesc)
        .url(apiExternalDocUrl));
  }

  private final Integer threadPoolSize;
  private final Integer taskQueueSize;

  public ProductCompositeServiceApplication(
    @Value("${app.threadPoolSize:10}") Integer threadPoolSize,
    @Value("${app.taskQueueSize:100}") Integer taskQueueSize
  ) {
    this.threadPoolSize = threadPoolSize;
    this.taskQueueSize = taskQueueSize;
  }

  @Bean
  public Scheduler publishEventScheduler() {
    LOG.info("Creates a messagingScheduler with connectionPoolSize = {}", threadPoolSize);
    return Schedulers.newBoundedElastic(threadPoolSize, taskQueueSize, "publish-pool");
  }

  @Bean
  public WebClient webClient(WebClient.Builder builder) {
    return builder.build();
  }

  public static void main(String[] args) {
    Hooks.enableAutomaticContextPropagation();
    SpringApplication.run(ProductCompositeServiceApplication.class, args);
  }

}
```

</details>

#### `microservices/product-composite-service/src/main/resources/application.yml` — 새 파일 (61줄)

<!-- wb:file path="microservices/product-composite-service/src/main/resources/application.yml" op="write" nl="1" -->
```yaml
# Required to make Springdoc handling forward headers correctly when native compiled
server.forward-headers-strategy: framework

# Required to make the Spring AOT engine generate the appropriate infrastructure for a separate management port, prometheus and K8S probes at build time
management.server.port: 9009
management.endpoint.health.probes.enabled: true
management.endpoints.web.exposure.include: health,info,circuitbreakerevents,prometheus

# Required to make the Spring AOT engine generate a ReactiveJwtDecoder for the OIDC Issuer
spring.security.oauth2.resourceserver.jwt.issuer-uri: http://someissuer

# See https://github.com/springdoc/springdoc-openapi/issues/1284#issuecomment-1279854219
springdoc.enable-native-support: true

# Native Compile: Point out that RabbitMQ is to be used when performing the native compile
spring.cloud.stream.defaultBinder: rabbit

# Native Compile: Required to disable the health check of RabbitMQ when using Kafka
# management.health.rabbit.enabled: false

# Native Compile: Required to disable the health check of Kafka when using RabbitMQ
management.health.kafka.enabled: false

# Native Compile: Required to get the Circuit Breaker's healthcheck work properly
management.health.circuitbreakers.enabled: true

# Spring Boot 4 / Jackson 3 writes enums using toString() by default. Write them by name, as with
# Jackson 2, so /actuator/circuitbreakerevents reports state transitions like CLOSED_TO_OPEN.
spring.jackson.datatype.enum.write-enums-using-to-string: false

resilience4j.circuitbreaker:
  instances:
    product:
      allowHealthIndicatorToFail: false
      registerHealthIndicator: true
      slidingWindowType: COUNT_BASED
      slidingWindowSize: 5
      failureRateThreshold: 50
      waitDurationInOpenState: 10000
      permittedNumberOfCallsInHalfOpenState: 3
      automaticTransitionFromOpenToHalfOpenEnabled: true
      ignoreExceptions:
        - se.magnus.api.exceptions.InvalidInputException
        - se.magnus.api.exceptions.NotFoundException

# TODO: To make nativeTests work?
api:

  common:
    version:
    title:
    description:
    termsOfService:
    license:
    licenseUrl:
    externalDocDesc:
    externalDocUrl:
    contact:
      name:
      url:
      email:
```

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/IsSameEventTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -8,6 +8,7 @@
 import static se.magnus.microservices.composite.product.IsSameEvent.sameEventExceptCreatedAt;
 
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import se.magnus.api.core.product.Product;
 import se.magnus.api.event.Event;
 import tools.jackson.core.JacksonException;
@@ -17,6 +18,9 @@
 
   ObjectMapper mapper = new ObjectMapper();
 
+  // Due to error like:
+  // - java.lang.Error: Cannot determine correct type for matchesSafely() method.
+  @DisabledInNativeImage
   @Test
   void testEventObjectCompare() throws JacksonException {
 
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/IsSameEventTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;
import static org.hamcrest.Matchers.not;
import static se.magnus.api.event.Event.Type.CREATE;
import static se.magnus.api.event.Event.Type.DELETE;
import static se.magnus.microservices.composite.product.IsSameEvent.sameEventExceptCreatedAt;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import se.magnus.api.core.product.Product;
import se.magnus.api.event.Event;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

class IsSameEventTests {

  ObjectMapper mapper = new ObjectMapper();

  // Due to error like:
  // - java.lang.Error: Cannot determine correct type for matchesSafely() method.
  @DisabledInNativeImage
  @Test
  void testEventObjectCompare() throws JacksonException {

    // Event #1 and #2 are the same event, but occurs as different times
    // Event #3 and #4 are different events
    Event<Integer, Product> event1 = new Event<>(CREATE, 1, new Product(1, "name", 1, null));
    Event<Integer, Product> event2 = new Event<>(CREATE, 1, new Product(1, "name", 1, null));
    Event<Integer, Product> event3 = new Event<>(DELETE, 1, null);
    Event<Integer, Product> event4 = new Event<>(CREATE, 1, new Product(2, "name", 1, null));

    String event1Json = mapper.writeValueAsString(event1);

    assertThat(event1Json, is(sameEventExceptCreatedAt(event2)));
    assertThat(event1Json, not(sameEventExceptCreatedAt(event3)));
    assertThat(event1Json, not(sameEventExceptCreatedAt(event4)));
  }
}
```

</details>

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/MessagingTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -15,6 +15,7 @@
 import java.util.List;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
 import org.springframework.beans.factory.annotation.Autowired;
@@ -60,6 +61,9 @@
     purgeMessages("reviews");
   }
 
+  // Due to error like:
+  // - java.lang.AssertionError: Status expected:<202 ACCEPTED> but was:<500 INTERNAL_SERVER_ERROR>
+  @DisabledInNativeImage
   @Test
   void createCompositeProduct1() {
 
@@ -82,6 +86,9 @@
     assertEquals(0, reviewMessages.size());
   }
 
+  // Due to error like:
+  // - java.lang.AssertionError: Status expected:<202 ACCEPTED> but was:<500 INTERNAL_SERVER_ERROR>
+  @DisabledInNativeImage
   @Test
   void createCompositeProduct2() {
 
@@ -119,6 +126,9 @@
     assertThat(reviewMessages.get(0), is(sameEventExceptCreatedAt(expectedReviewEvent)));
   }
 
+  // Due to error like:
+  // - java.lang.AssertionError: Status expected:<202 ACCEPTED> but was:<500 INTERNAL_SERVER_ERROR>
+  @DisabledInNativeImage
   @Test
   void deleteCompositeProduct() {
     deleteAndVerifyProduct(1, ACCEPTED);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/MessagingTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import static java.util.Collections.singletonList;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.ACCEPTED;
import static reactor.core.publisher.Mono.just;
import static se.magnus.api.event.Event.Type.CREATE;
import static se.magnus.api.event.Event.Type.DELETE;
import static se.magnus.microservices.composite.product.IsSameEvent.sameEventExceptCreatedAt;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.cloud.stream.binder.test.OutputDestination;
import org.springframework.cloud.stream.binder.test.TestChannelBinderConfiguration;
import org.springframework.context.annotation.Import;
import org.springframework.http.HttpStatus;
import org.springframework.messaging.Message;
import org.springframework.test.web.reactive.server.WebTestClient;
import se.magnus.api.composite.product.ProductAggregate;
import se.magnus.api.composite.product.RecommendationSummary;
import se.magnus.api.composite.product.ReviewSummary;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.review.Review;
import se.magnus.api.event.Event;

@AutoConfigureWebTestClient
@SpringBootTest(
  webEnvironment = RANDOM_PORT,
  classes = {TestSecurityConfig.class},
  properties = {
    "spring.security.oauth2.resourceserver.jwt.issuer-uri=",
    "spring.main.allow-bean-definition-overriding=true",
    "spring.cloud.stream.defaultBinder=rabbit"})
@Import({TestChannelBinderConfiguration.class})
class MessagingTests {

  private static final Logger LOG = LoggerFactory.getLogger(MessagingTests.class);

  @Autowired
  private WebTestClient client;

  @Autowired
  private OutputDestination target;

  @BeforeEach
  void setUp() {
    purgeMessages("products");
    purgeMessages("recommendations");
    purgeMessages("reviews");
  }

  // Due to error like:
  // - java.lang.AssertionError: Status expected:<202 ACCEPTED> but was:<500 INTERNAL_SERVER_ERROR>
  @DisabledInNativeImage
  @Test
  void createCompositeProduct1() {

    ProductAggregate composite = new ProductAggregate(1, "name", 1, null, null, null);
    postAndVerifyProduct(composite, ACCEPTED);

    final List<String> productMessages = getMessages("products");
    final List<String> recommendationMessages = getMessages("recommendations");
    final List<String> reviewMessages = getMessages("reviews");

    // Assert one expected new product event queued up
    assertEquals(1, productMessages.size());

    Event<Integer, Product> expectedEvent =
      new Event<>(CREATE, composite.getProductId(), new Product(composite.getProductId(), composite.getName(), composite.getWeight(), null));
    assertThat(productMessages.get(0), is(sameEventExceptCreatedAt(expectedEvent)));

    // Assert no recommendation and review events
    assertEquals(0, recommendationMessages.size());
    assertEquals(0, reviewMessages.size());
  }

  // Due to error like:
  // - java.lang.AssertionError: Status expected:<202 ACCEPTED> but was:<500 INTERNAL_SERVER_ERROR>
  @DisabledInNativeImage
  @Test
  void createCompositeProduct2() {

    ProductAggregate composite = new ProductAggregate(1, "name", 1,
      singletonList(new RecommendationSummary(1, "a", 1, "c")),
      singletonList(new ReviewSummary(1, "a", "s", "c")), null);
    postAndVerifyProduct(composite, ACCEPTED);

    final List<String> productMessages = getMessages("products");
    final List<String> recommendationMessages = getMessages("recommendations");
    final List<String> reviewMessages = getMessages("reviews");

    // Assert one create product event queued up
    assertEquals(1, productMessages.size());

    Event<Integer, Product> expectedProductEvent =
      new Event<>(CREATE, composite.getProductId(), new Product(composite.getProductId(), composite.getName(), composite.getWeight(), null));
    assertThat(productMessages.get(0), is(sameEventExceptCreatedAt(expectedProductEvent)));

    // Assert one create recommendation event queued up
    assertEquals(1, recommendationMessages.size());

    RecommendationSummary rec = composite.getRecommendations().get(0);
    Event<Integer, Recommendation> expectedRecommendationEvent =
      new Event<>(CREATE, composite.getProductId(),
        new Recommendation(composite.getProductId(), rec.getRecommendationId(), rec.getAuthor(), rec.getRate(), rec.getContent(), null));
    assertThat(recommendationMessages.get(0), is(sameEventExceptCreatedAt(expectedRecommendationEvent)));

    // Assert one create review event queued up
    assertEquals(1, reviewMessages.size());

    ReviewSummary rev = composite.getReviews().get(0);
    Event<Integer, Review> expectedReviewEvent =
      new Event<>(CREATE, composite.getProductId(), new Review(composite.getProductId(), rev.getReviewId(), rev.getAuthor(), rev.getSubject(), rev.getContent(), null));
    assertThat(reviewMessages.get(0), is(sameEventExceptCreatedAt(expectedReviewEvent)));
  }

  // Due to error like:
  // - java.lang.AssertionError: Status expected:<202 ACCEPTED> but was:<500 INTERNAL_SERVER_ERROR>
  @DisabledInNativeImage
  @Test
  void deleteCompositeProduct() {
    deleteAndVerifyProduct(1, ACCEPTED);

    final List<String> productMessages = getMessages("products");
    final List<String> recommendationMessages = getMessages("recommendations");
    final List<String> reviewMessages = getMessages("reviews");

    // Assert one delete product event queued up
    assertEquals(1, productMessages.size());

    Event<Integer, Product> expectedProductEvent = new Event<>(DELETE, 1, null);
    assertThat(productMessages.get(0), is(sameEventExceptCreatedAt(expectedProductEvent)));

    // Assert one delete recommendation event queued up
    assertEquals(1, recommendationMessages.size());

    Event<Integer, Recommendation> expectedRecommendationEvent = new Event<>(DELETE, 1, null);
    assertThat(recommendationMessages.get(0), is(sameEventExceptCreatedAt(expectedRecommendationEvent)));

    // Assert one delete review event queued up
    assertEquals(1, reviewMessages.size());

    Event<Integer, Review> expectedReviewEvent = new Event<>(DELETE, 1, null);
    assertThat(reviewMessages.get(0), is(sameEventExceptCreatedAt(expectedReviewEvent)));
  }

  private void purgeMessages(String bindingName) {
    getMessages(bindingName);
  }

  private List<String> getMessages(String bindingName) {
    List<String> messages = new ArrayList<>();
    boolean anyMoreMessages = true;

    while (anyMoreMessages) {
      Message<byte[]> message = getMessage(bindingName);

      if (message == null) {
        anyMoreMessages = false;

      } else {
        messages.add(new String(message.getPayload()));
      }
    }
    return messages;
  }

  private Message<byte[]> getMessage(String bindingName) {
    try {
      return target.receive(0, bindingName);
    } catch (NullPointerException npe) {
      // If the messageQueues member variable in the target object contains no queues when the receive method is called, it will cause a NPE to be thrown.
      // So we catch the NPE here and return null to indicate that no messages were found.
      LOG.error("getMessage() received a NPE with binding = {}", bindingName);
      return null;
    }
  }

  private void postAndVerifyProduct(ProductAggregate compositeProduct, HttpStatus expectedStatus) {
    client.post()
      .uri("/product-composite")
      .body(just(compositeProduct), ProductAggregate.class)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus);
  }

  private void deleteAndVerifyProduct(int productId, HttpStatus expectedStatus) {
    client.delete()
      .uri("/product-composite/" + productId)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus);
  }
}
```

</details>

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -9,6 +9,7 @@
 
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
+import org.junit.jupiter.api.condition.DisabledInNativeImage;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.boot.test.context.SpringBootTest;
 import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
@@ -24,6 +25,12 @@
 import se.magnus.api.exceptions.NotFoundException;
 import se.magnus.microservices.composite.product.services.ProductCompositeIntegration;
 
+// Due to mockito not supported in native tests?
+// java.lang.IllegalStateException: Failed to load AOT ApplicationContextInitializer class for test class
+// [se.magnus.microservices.composite.product.ProductCompositeServiceApplicationTests].
+// This can occur if AOT processing has not taken place for the test suite.
+// It can also occur if AOT processing failed for the test class, in which case you can consult the logs generated during AOT processing.
+@DisabledInNativeImage
 @AutoConfigureWebTestClient
 @SpringBootTest(
   webEnvironment = RANDOM_PORT,
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import static java.util.Collections.singletonList;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledInNativeImage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.review.Review;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.api.exceptions.NotFoundException;
import se.magnus.microservices.composite.product.services.ProductCompositeIntegration;

// Due to mockito not supported in native tests?
// java.lang.IllegalStateException: Failed to load AOT ApplicationContextInitializer class for test class
// [se.magnus.microservices.composite.product.ProductCompositeServiceApplicationTests].
// This can occur if AOT processing has not taken place for the test suite.
// It can also occur if AOT processing failed for the test class, in which case you can consult the logs generated during AOT processing.
@DisabledInNativeImage
@AutoConfigureWebTestClient
@SpringBootTest(
  webEnvironment = RANDOM_PORT,
  classes = {TestSecurityConfig.class},
  properties = {
    "spring.security.oauth2.resourceserver.jwt.issuer-uri=",
    "spring.main.allow-bean-definition-overriding=true"})
class ProductCompositeServiceApplicationTests {

  private static final int PRODUCT_ID_OK = 1;
  private static final int PRODUCT_ID_NOT_FOUND = 2;
  private static final int PRODUCT_ID_INVALID = 3;

  @Autowired
  private WebTestClient client;

  @MockitoBean
  private ProductCompositeIntegration compositeIntegration;

  @BeforeEach
  void setUp() {

    when(compositeIntegration.getProduct(any(), eq(PRODUCT_ID_OK), anyInt(), anyInt()))
      .thenReturn(Mono.just(new Product(PRODUCT_ID_OK, "name", 1, "mock-address")));

    when(compositeIntegration.getRecommendations(any(), eq(PRODUCT_ID_OK)))
      .thenReturn(Flux.fromIterable(singletonList(new Recommendation(PRODUCT_ID_OK, 1, "author", 1, "content", "mock address"))));

    when(compositeIntegration.getReviews(any(), eq(PRODUCT_ID_OK)))
      .thenReturn(Flux.fromIterable(singletonList(new Review(PRODUCT_ID_OK, 1, "author", "subject", "content", "mock address"))));

    when(compositeIntegration.getProduct(any(), eq(PRODUCT_ID_NOT_FOUND), anyInt(), anyInt())).thenThrow(new NotFoundException("NOT FOUND: " + PRODUCT_ID_NOT_FOUND));

    when(compositeIntegration.getProduct(any(), eq(PRODUCT_ID_INVALID), anyInt(), anyInt())).thenThrow(new InvalidInputException("INVALID: " + PRODUCT_ID_INVALID));
  }

  @Test
  void contextLoads() {
  }

  @Test
  void getProductById() {

    getAndVerifyProduct(PRODUCT_ID_OK, OK)
      .jsonPath("$.productId").isEqualTo(PRODUCT_ID_OK)
      .jsonPath("$.recommendations.length()").isEqualTo(1)
      .jsonPath("$.reviews.length()").isEqualTo(1);
  }

  @Test
  void getProductNotFound() {

    getAndVerifyProduct(PRODUCT_ID_NOT_FOUND, NOT_FOUND)
      .jsonPath("$.path").isEqualTo("/product-composite/" + PRODUCT_ID_NOT_FOUND)
      .jsonPath("$.message").isEqualTo("NOT FOUND: " + PRODUCT_ID_NOT_FOUND);
  }

  @Test
  void getProductInvalidInput() {

    getAndVerifyProduct(PRODUCT_ID_INVALID, UNPROCESSABLE_CONTENT)
      .jsonPath("$.path").isEqualTo("/product-composite/" + PRODUCT_ID_INVALID)
      .jsonPath("$.message").isEqualTo("INVALID: " + PRODUCT_ID_INVALID);
  }

  private WebTestClient.BodyContentSpec getAndVerifyProduct(int productId, HttpStatus expectedStatus) {
    return client.get()
      .uri("/product-composite/" + productId)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody();
  }
}
```

</details>

#### `microservices/product-composite-service/src/test/resources/access-filter.json` — 새 파일 (18줄)

<!-- wb:file path="microservices/product-composite-service/src/test/resources/access-filter.json" op="write" nl="1" -->
```json
{ "rules":
  [
    {"excludeClasses": "org.apache.maven.surefire.**"},
    {"excludeClasses": "net.bytebuddy.**"},
    {"excludeClasses": "org.apiguardian.**"},
    {"excludeClasses": "org.junit.**"},
    {"excludeClasses": "org.gradle.**"},
    {"excludeClasses": "org.mockito.**"},
    {"excludeClasses": "org.springframework.test.**"},
    {"excludeClasses": "org.springframework.boot.test.**"},
    {"excludeClasses": "org.springframework.boot.SpringApplication"},
    {"excludeClasses": "org.testcontainers.**"},
    {"excludeClasses": "se.magnus.microservices.composite.product.IsSameEventTests"},
    {"excludeClasses": "se.magnus.microservices.composite.product.MessagingTests"},
    {"excludeClasses": "se.magnus.microservices.composite.product.ProductCompositeServiceApplicationTests"},
    {"excludeClasses": "se.magnus.microservices.composite.product.TestSecurityConfig"}
  ]
}
```

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-6"></a>

## 단계 6. `authorization-server` — OAuth 2.0 인가 서버

사용하지 않는 import를 정리합니다.

#### `spring-cloud/authorization-server/src/main/java/sample/config/AuthorizationServerConfig.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -43,7 +43,6 @@
 import org.springframework.core.Ordered;
 import org.springframework.core.annotation.Order;
 import org.springframework.security.config.annotation.web.builders.HttpSecurity;
-import org.springframework.security.config.annotation.web.configurers.oauth2.server.resource.OAuth2ResourceServerConfigurer;
 import org.springframework.security.oauth2.core.AuthorizationGrantType;
 import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
 import org.springframework.security.oauth2.core.oidc.OidcScopes;
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/authorization-server/src/main/java/sample/config/AuthorizationServerConfig.java" op="write" nl="1" -->
```java
//CHECKSTYLE:OFF
/*
 * Copyright 2020-2022 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package sample.config;

import java.time.Duration;
import java.util.List;
import java.util.UUID;
import java.util.function.Consumer;

import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.source.JWKSource;
import com.nimbusds.jose.proc.SecurityContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.config.Customizer;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.OAuth2ErrorCodes;
import org.springframework.security.oauth2.server.authorization.authentication.*;
import org.springframework.security.oauth2.server.authorization.client.InMemoryRegisteredClientRepository;
import org.springframework.security.config.annotation.web.configurers.oauth2.server.authorization.OAuth2AuthorizationServerConfigurer;
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;
import org.springframework.security.web.util.matcher.RequestMatcher;
import sample.jose.Jwks;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.core.oidc.OidcScopes;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;
import org.springframework.security.config.annotation.web.configuration.OAuth2AuthorizationServerConfiguration;
import org.springframework.security.oauth2.server.authorization.settings.AuthorizationServerSettings;
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.LoginUrlAuthenticationEntryPoint;

/**
 * @author Joe Grandja
 * @since 0.0.1
 */
@Configuration(proxyBeanMethods = false)
public class AuthorizationServerConfig {

  private static final Logger LOG = LoggerFactory.getLogger(AuthorizationServerConfig.class);

  @Bean
  @Order(Ordered.HIGHEST_PRECEDENCE)
  public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {

    // Replaced this call with the implementation of applyDefaultSecurity() to be able to add a custom redirect_uri validator
    // OAuth2AuthorizationServerConfiguration.applyDefaultSecurity(http);

    OAuth2AuthorizationServerConfigurer authorizationServerConfigurer =
      new OAuth2AuthorizationServerConfigurer();

    // Register a custom redirect_uri validator, that allows redirect uris based on https://localhost during development
    authorizationServerConfigurer
      .authorizationEndpoint(authorizationEndpoint ->
        authorizationEndpoint
          .authenticationProviders(configureAuthenticationValidator())
      );

    RequestMatcher endpointsMatcher = authorizationServerConfigurer
      .getEndpointsMatcher();

    http
      .securityMatcher(endpointsMatcher)
      .authorizeHttpRequests(authorize ->
        authorize.anyRequest().authenticated()
      )
      .csrf(csrf -> csrf.ignoringRequestMatchers(endpointsMatcher))
      .with(authorizationServerConfigurer, Customizer.withDefaults());

    http.getConfigurer(OAuth2AuthorizationServerConfigurer.class)
      .oidc(Customizer.withDefaults()); // Enable OpenID Connect 1.0

    http
      .exceptionHandling(exceptions ->
        exceptions.authenticationEntryPoint(new LoginUrlAuthenticationEntryPoint("/login"))
      )
      .oauth2ResourceServer(t -> t.jwt(Customizer.withDefaults()));

    return http.build();
  }

  @Bean
  public RegisteredClientRepository registeredClientRepository() {
    RegisteredClient writerClient = RegisteredClient.withId(UUID.randomUUID().toString())
      .clientId("writer")
      .clientSecret("{noop}secret-writer")
      .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
      .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
      .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
      .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
      .redirectUri("https://my.redirect.uri")
      .redirectUri("https://localhost:8443/openapi/swagger-ui/oauth2-redirect.html")
      .scope(OidcScopes.OPENID)
      .scope("product:read")
      .scope("product:write")
      .clientSettings(ClientSettings.builder().requireAuthorizationConsent(true).build())
      .tokenSettings(TokenSettings.builder().accessTokenTimeToLive(Duration.ofHours(1)).build())
      .build();

    RegisteredClient readerClient = RegisteredClient.withId(UUID.randomUUID().toString())
      .clientId("reader")
      .clientSecret("{noop}secret-reader")
      .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
      .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
      .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
      .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
      .redirectUri("https://my.redirect.uri")
      .redirectUri("https://localhost:8443/openapi/swagger-ui/oauth2-redirect.html")
      .scope(OidcScopes.OPENID)
      .scope("product:read")
      .clientSettings(ClientSettings.builder().requireAuthorizationConsent(true).build())
      .tokenSettings(TokenSettings.builder().accessTokenTimeToLive(Duration.ofHours(1)).build())
      .build();

    return new InMemoryRegisteredClientRepository(writerClient, readerClient);

  }

  @Bean
  public JWKSource<SecurityContext> jwkSource() {
    RSAKey rsaKey = Jwks.generateRsa();
    JWKSet jwkSet = new JWKSet(rsaKey);
    return (jwkSelector, securityContext) -> jwkSelector.select(jwkSet);
  }

  @Bean
  public JwtDecoder jwtDecoder(JWKSource<SecurityContext> jwkSource) {
    return OAuth2AuthorizationServerConfiguration.jwtDecoder(jwkSource);
  }

  @Bean
  public AuthorizationServerSettings authorizationServerSettings() {
    return AuthorizationServerSettings.builder().issuer("http://auth-server").build();
  }

  private Consumer<List<AuthenticationProvider>> configureAuthenticationValidator() {
    return (authenticationProviders) ->
      authenticationProviders.forEach((authenticationProvider) -> {
        if (authenticationProvider instanceof OAuth2AuthorizationCodeRequestAuthenticationProvider) {
          Consumer<OAuth2AuthorizationCodeRequestAuthenticationContext> authenticationValidator =
            // Override default redirect_uri validator
            new CustomRedirectUriValidator()
              // Reuse default scope validator
              .andThen(OAuth2AuthorizationCodeRequestAuthenticationValidator.DEFAULT_SCOPE_VALIDATOR);

          ((OAuth2AuthorizationCodeRequestAuthenticationProvider) authenticationProvider)
            .setAuthenticationValidator(authenticationValidator);
        }
      });
  }

  static class CustomRedirectUriValidator implements Consumer<OAuth2AuthorizationCodeRequestAuthenticationContext> {

    @Override
    public void accept(OAuth2AuthorizationCodeRequestAuthenticationContext authenticationContext) {
      OAuth2AuthorizationCodeRequestAuthenticationToken authorizationCodeRequestAuthentication =
        authenticationContext.getAuthentication();
      RegisteredClient registeredClient = authenticationContext.getRegisteredClient();
      String requestedRedirectUri = authorizationCodeRequestAuthentication.getRedirectUri();

      LOG.trace("Will validate the redirect uri {}", requestedRedirectUri);

      // Use exact string matching when comparing client redirect URIs against pre-registered URIs
      if (!registeredClient.getRedirectUris().contains(requestedRedirectUri)) {
        LOG.trace("Redirect uri is invalid!");
        OAuth2Error error = new OAuth2Error(OAuth2ErrorCodes.INVALID_REQUEST);
        throw new OAuth2AuthorizationCodeRequestAuthenticationException(error, null);
      }
      LOG.trace("Redirect uri is OK!");
    }
  }
}
//CHECKSTYLE:ON
```

</details>

**중간 확인**

```bash
./gradlew :spring-cloud:authorization-server:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-7"></a>

## 단계 7. `config-repo` — 중앙 구성 파일

MySQL 접속 URL에 문자셋 옵션을 추가합니다.

#### `config-repo/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff

```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/application.yml" op="write" nl="0" -->
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

#### `config-repo/auth-server.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="config-repo/auth-server.yml" op="write" nl="0" -->
```yaml
server.port: 9999
spring.application.name: auth-server
server.forward-headers-strategy: framework

logging:
  level:
    root: INFO

---
spring.config.activate.on-profile: docker

server.port: 80

---
spring.config.activate.on-profile: prod

logging.level.root: WARN
```

#### `config-repo/gateway.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -15,7 +15,6 @@
     location: classpath:keystore/edge.p12
 
 server.ssl.bundle: gateway
-
 
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

#### `config-repo/review.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -9,7 +9,7 @@
 spring.jpa.hibernate.ddl-auto: update
 
 spring.datasource:
-  url: jdbc:mysql://localhost/review-db
+  url: jdbc:mysql://localhost/review-db?useUnicode=true&connectionCollation=utf8_general_ci&characterSetResults=utf8&characterEncoding=utf-8
 
 spring.datasource.hikari.initializationFailTimeout: 60000
 
@@ -46,7 +46,7 @@
 
 server.port: 80
 
-spring.datasource.url: jdbc:mysql://mysql/review-db
+spring.datasource.url: jdbc:mysql://mysql/review-db?useUnicode=true&connectionCollation=utf8_general_ci&characterSetResults=utf8&characterEncoding=utf-8
 
 ---
 spring.config.activate.on-profile: streaming_partitioned
@@ -73,7 +73,8 @@
 ---
 spring.config.activate.on-profile: prod
 
-spring.datasource.url: jdbc:mysql://172.17.0.1:3306/review-db
+spring.datasource.url: jdbc:mysql://172.17.0.1:3306/review-db?useUnicode=true&connectionCollation=utf8_general_ci&characterSetResults=utf8&characterEncoding=utf-8
+
 
 logging:
   level:
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/review.yml" op="write" nl="1" -->
```yaml
server.port: 7004
spring.web.error.include-message: always

spring.application.name: review

management.endpoint.health.group.readiness.include: readinessState, rabbit, db

# Strongly recommend to set this property to "none" in a production environment!
spring.jpa.hibernate.ddl-auto: update

spring.datasource:
  url: jdbc:mysql://localhost/review-db?useUnicode=true&connectionCollation=utf8_general_ci&characterSetResults=utf8&characterEncoding=utf-8

spring.datasource.hikari.initializationFailTimeout: 60000

spring.cloud.function.definition: messageProcessor

spring.cloud.stream:
  default.contentType: application/json
  bindings.messageProcessor-in-0:
    destination: reviews
    group: reviewsGroup

spring.cloud.stream.bindings.messageProcessor-in-0.consumer:
  maxAttempts: 3
  backOffInitialInterval: 500
  backOffMaxInterval: 1000
  backOffMultiplier: 2.0

spring.cloud.stream.rabbit.bindings.messageProcessor-in-0.consumer:
  autoBindDlq: true
  republishToDlq: true

spring.cloud.stream.kafka.bindings.messageProcessor-in-0.consumer:
  enableDlq: true

logging:
  level:
    root: INFO
    se.magnus: INFO
    org.hibernate.SQL: DEBUG
    org.hibernate.type.descriptor.sql.BasicBinder: TRACE

---
spring.config.activate.on-profile: docker

server.port: 80

spring.datasource.url: jdbc:mysql://mysql/review-db?useUnicode=true&connectionCollation=utf8_general_ci&characterSetResults=utf8&characterEncoding=utf-8

---
spring.config.activate.on-profile: streaming_partitioned

spring.cloud.stream.bindings.messageProcessor-in-0.consumer:
  partitioned: true
  instanceCount: 2

---
spring.config.activate.on-profile: streaming_instance_0

spring.cloud.stream.bindings.messageProcessor-in-0.consumer.instanceIndex: 0

---
spring.config.activate.on-profile: streaming_instance_1

spring.cloud.stream.bindings.messageProcessor-in-0.consumer.instanceIndex: 1

---
spring.config.activate.on-profile: kafka

management.endpoint.health.group.readiness.include: readinessState, db

---
spring.config.activate.on-profile: prod

spring.datasource.url: jdbc:mysql://172.17.0.1:3306/review-db?useUnicode=true&connectionCollation=utf8_general_ci&characterSetResults=utf8&characterEncoding=utf-8


logging:
  level:
    root: WARN
    se.magnus: WARN
    org.hibernate.SQL: WARN
    org.hibernate.type.descriptor.sql.BasicBinder: WARN
```

</details>

<a id="단계-8"></a>

## 단계 8. 헬름 `components` 차트 — 서비스별 차트

네이티브 이미지 설정입니다.

#### `kubernetes/helm/components/auth-server/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/auth-server/config-repo && cp config-repo/application.yml kubernetes/helm/components/auth-server/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/auth-server/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/auth-server/config-repo/auth-server.yml` — 전체를 바꿉니다 (`config-repo/auth-server.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/auth-server/config-repo && cp config-repo/auth-server.yml kubernetes/helm/components/auth-server/config-repo/auth-server.yml
```

<!-- wb:file path="kubernetes/helm/components/auth-server/config-repo/auth-server.yml" op="cp" src="config-repo/auth-server.yml" -->

#### `kubernetes/helm/components/product-composite/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product-composite/config-repo && cp config-repo/application.yml kubernetes/helm/components/product-composite/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/product-composite/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

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

#### `kubernetes/helm/components/review-green/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review-green/config-repo && cp config-repo/application.yml kubernetes/helm/components/review-green/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/review-green/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/review-green/config-repo/review.yml` — 전체를 바꿉니다 (`config-repo/review.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review-green/config-repo && cp config-repo/review.yml kubernetes/helm/components/review-green/config-repo/review.yml
```

<!-- wb:file path="kubernetes/helm/components/review-green/config-repo/review.yml" op="cp" src="config-repo/review.yml" -->

#### `kubernetes/helm/components/review/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review/config-repo && cp config-repo/application.yml kubernetes/helm/components/review/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/review/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/review/config-repo/review.yml` — 전체를 바꿉니다 (`config-repo/review.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review/config-repo && cp config-repo/review.yml kubernetes/helm/components/review/config-repo/review.yml
```

<!-- wb:file path="kubernetes/helm/components/review/config-repo/review.yml" op="cp" src="config-repo/review.yml" -->

<a id="단계-9"></a>

## 단계 9. 헬름 `environments` 차트 — 환경별 묶음

네이티브 이미지를 쓰는 `dev-env-native` 환경 차트를 추가합니다.

#### `kubernetes/helm/environments/dev-env-native/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/environments/dev-env-native/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/environments/dev-env-native/Chart.yaml` — 새 파일 (43줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env-native/Chart.yaml" op="write" nl="1" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for native compiled HANDS-ON MICROSERVICES WITH SPRING BOOT AND SPRING CLOUD running in a Dev and Test Environment
name: dev-env-native
version: 1.0.0

dependencies:

  - name: common
    version: 1.0.0
    repository: file://../../common

  - name: rabbitmq
    version: 1.0.0
    repository: file://../../components/rabbitmq

  - name: mongodb
    version: 1.0.0
    repository: file://../../components/mongodb

  - name: mysql
    version: 1.0.0
    repository: file://../../components/mysql

  - name: auth-server
    version: 1.0.0
    repository: file://../../components/auth-server

  - name: product
    version: 1.0.0
    repository: file://../../components/product

  - name: recommendation
    version: 1.0.0
    repository: file://../../components/recommendation

  - name: review
    version: 1.0.0
    repository: file://../../components/review

  - name: product-composite
    version: 1.0.0
    repository: file://../../components/product-composite
```

#### `kubernetes/helm/environments/dev-env-native/templates/istio_base.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env-native/templates/istio_base.yaml" op="write" nl="0" -->
```yaml
{{- template "common.istio_base" . -}}
```

#### `kubernetes/helm/environments/dev-env-native/templates/istio_dr_mutual_tls.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env-native/templates/istio_dr_mutual_tls.yaml" op="write" nl="0" -->
```yaml
{{- template "common.istio_dr_mutual_tls" . -}}
```

#### `kubernetes/helm/environments/dev-env-native/templates/secrets.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env-native/templates/secrets.yaml" op="write" nl="0" -->
```yaml
{{- template "common.secrets" . -}}
```

#### `kubernetes/helm/environments/dev-env-native/values.yaml` — 새 파일 (81줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env-native/values.yaml" op="write" nl="1" -->
```yaml
secrets:

  rabbitmq-server-credentials:
    RABBITMQ_DEFAULT_USER: rabbit-user-dev
    RABBITMQ_DEFAULT_PASS: rabbit-pwd-dev

  rabbitmq-credentials:
    SPRING_RABBITMQ_USERNAME: rabbit-user-dev
    SPRING_RABBITMQ_PASSWORD: rabbit-pwd-dev

  mongodb-server-credentials:
    MONGO_INITDB_ROOT_USERNAME: mongodb-user-dev
    MONGO_INITDB_ROOT_PASSWORD: mongodb-pwd-dev

  mongodb-credentials:
    SPRING_MONGODB_AUTHENTICATION_DATABASE: admin
    SPRING_MONGODB_USERNAME: mongodb-user-dev
    SPRING_MONGODB_PASSWORD: mongodb-pwd-dev

  mysql-server-credentials:
    MYSQL_ROOT_PASSWORD: rootpwd
    MYSQL_DATABASE: review-db
    MYSQL_USER: mysql-user-dev
    MYSQL_PASSWORD: mysql-pwd-dev

  mysql-credentials:
    SPRING_DATASOURCE_USERNAME: mysql-user-dev
    SPRING_DATASOURCE_PASSWORD: mysql-pwd-dev

rabbitmq:
  envFromSecretRefs:
    - rabbitmq-server-credentials

mongodb:
  envFromSecretRefs:
    - mongodb-server-credentials

mysql:
  envFromSecretRefs:
    - mysql-server-credentials

auth-server:
  envFromSecretRefs:
    - rabbitmq-credentials

product:
  image:
    name: native-product-service
  envFromSecretRefs:
    - rabbitmq-credentials
    - mongodb-credentials

recommendation:
  image:
    name: native-recommendation-service
  envFromSecretRefs:
    - rabbitmq-credentials
    - mongodb-credentials

review:
  image:
    name: native-review-service
  envFromSecretRefs:
    - rabbitmq-credentials
    - mysql-credentials

product-composite:
  image:
    name: native-product-composite-service
  envFromSecretRefs:
    - rabbitmq-credentials
  readinessProbe:
    httpGet:
      path: /actuator/info

destinationRules:
  - name: product-composite
  - name: auth-server
  - name: product
  - name: recommendation
  - name: review
```

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter23
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

**네이티브 이미지로 실행** (빌드팩이 GraalVM 25를 사용, 서비스당 수 분 소요)

```bash
for s in product recommendation review product-composite; do
  ./gradlew :microservices:$s-service:bootBuildImage
done
COMPOSE_FILE=docker-compose-native.yml HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 USE_K8S=false ./test-em-all.bash start stop
COMPOSE_FILE=docker-compose-partitions-native.yml HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 USE_K8S=false ./test-em-all.bash start stop
```

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter23
```

---

← [20장 워크북](Chapter20.md) · [워크북 목차](README.md)
