# 7장 워크북 — 반응형 마이크로서비스 개발

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 7장 · 영문 3판 p.163–210 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter07/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter07`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter07) · 위키: [7장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/07장-반응형-마이크로서비스-개발)

## 이 장에서 만드는 것

서비스를 **리액티브**로 바꾸고 **이벤트 기반 비동기 통신**을 추가합니다.

- 조회 API를 `Mono`/`Flux`로 바꾸고, MongoDB는 리액티브 리포지터리 사용
- 블로킹인 JPA 코드는 별도 스케줄러에서 실행
- 생성·삭제는 Spring Cloud Stream으로 이벤트를 보내고, 핵심 서비스가 받아 처리
- RabbitMQ 기본 구성, 파티션 구성, Kafka 구성의 도커 컴포즈 파일

## 시작하기

6장을 끝낸 작업 폴더를 복사해서 시작합니다. 6장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter06 Chapter07          # 내가 만든 6장 결과에서 시작
# 또는: cp -r <저장소>/Chapter06 Chapter07        # 저장소의 6장 완성 코드에서 시작
cd Chapter07 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 새 파일 2 · 수정 2
2. [`api` 프로젝트 — 서비스 간 API와 DTO](#단계-2) — 새 파일 2 · 수정 4
3. [`util` 프로젝트 — 공통 유틸리티](#단계-3) — 새 파일 1
4. [`product-service`](#단계-4) — 새 파일 1 · 수정 8
5. [`recommendation-service`](#단계-5) — 새 파일 1 · 수정 8
6. [`review-service`](#단계-6) — 새 파일 1 · 수정 6
7. [`product-composite-service`](#단계-7) — 새 파일 4 · 수정 6

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

`docker-compose.yml`에 RabbitMQ를 추가하고, 파티션 구성(`docker-compose-partitions.yml`)과 Kafka 구성(`docker-compose-kafka.yml`)을 새로 만듭니다. `test-em-all.bash`는 비동기 처리를 기다리는 대기와 함께 바뀝니다.

#### `docker-compose-kafka.yml` — 새 파일 (134줄)

<!-- wb:file path="docker-compose-kafka.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
    depends_on:
      mongodb:
        condition: service_healthy
      kafka:
        condition: service_healthy

  product-p1:
    build: microservices/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
    depends_on:
      mongodb:
        condition: service_healthy
      kafka:
        condition: service_healthy

  recommendation:
    build: microservices/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
    depends_on:
      mongodb:
        condition: service_healthy
      kafka:
        condition: service_healthy

  recommendation-p1:
    build: microservices/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
    depends_on:
      mongodb:
        condition: service_healthy
      kafka:
        condition: service_healthy

  review:
    build: microservices/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
    depends_on:
      mysql:
        condition: service_healthy
      kafka:
        condition: service_healthy

  review-p1:
    build: microservices/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
    depends_on:
      mysql:
        condition: service_healthy
      kafka:
        condition: service_healthy

  product-composite:
    build: microservices/product-composite-service
    mem_limit: 512m
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,kafka
    depends_on:
      kafka:
        condition: service_healthy

  mongodb:
    image: mongo:8.0.5
    mem_limit: 512m
    ports:
      - "27017:27017"
    command: mongod
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh --quiet
      interval: 5s
      timeout: 2s
      retries: 60

  mysql:
    image: mysql:9.2.0
    mem_limit: 512m
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=rootpwd
      - MYSQL_DATABASE=review-db
      - MYSQL_USER=user
      - MYSQL_PASSWORD=pwd
    healthcheck:
      test: "/usr/bin/mysql --user=user --password=pwd --execute \"SHOW DATABASES;\""
      interval: 5s
      timeout: 2s
      retries: 60

  kafka:
    image: confluentinc/cp-kafka:7.9.0
    restart: always
    mem_limit: 1024m
    ports:
      - "9092:9092"
    environment:
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_BROKER_ID=1
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
    depends_on:
      - zookeeper
    healthcheck:
      test: ["CMD-SHELL", "kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1"]
      interval: 5s
      timeout: 10s
      retries: 30
      start_period: 10s

  zookeeper:
    image: confluentinc/cp-zookeeper:7.9.0
    restart: always
    mem_limit: 512m
    ports:
      - "2181:2181"
    environment:
      - ZOOKEEPER_CLIENT_PORT=2181
```

#### `docker-compose-partitions.yml` — 새 파일 (117줄)

<!-- wb:file path="docker-compose-partitions.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-p1:
    build: microservices/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation:
    build: microservices/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation-p1:
    build: microservices/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review:
    build: microservices/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review-p1:
    build: microservices/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-composite:
    build: microservices/product-composite-service
    mem_limit: 512m
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned
    depends_on:
      rabbitmq:
        condition: service_healthy

  mongodb:
    image: mongo:8.0.5
    mem_limit: 512m
    ports:
      - "27017:27017"
    command: mongod
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh --quiet
      interval: 5s
      timeout: 2s
      retries: 60

  mysql:
    image: mysql:9.2.0
    mem_limit: 512m
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=rootpwd
      - MYSQL_DATABASE=review-db
      - MYSQL_USER=user
      - MYSQL_PASSWORD=pwd
    healthcheck:
      test: "/usr/bin/mysql --user=user --password=pwd --execute \"SHOW DATABASES;\""
      interval: 5s
      timeout: 2s
      retries: 60

  rabbitmq:
    image: rabbitmq:4.0.7-management
    mem_limit: 512m
    ports:
      - 5672:5672
      - 15672:15672
    healthcheck:
      test: ["CMD", "rabbitmqctl", "status"]
      interval: 5s
      timeout: 2s
      retries: 60
```

#### `docker-compose.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -6,6 +6,8 @@
       - SPRING_PROFILES_ACTIVE=docker
     depends_on:
       mongodb:
+        condition: service_healthy
+      rabbitmq:
         condition: service_healthy
 
   recommendation:
@@ -16,6 +18,8 @@
     depends_on:
       mongodb:
         condition: service_healthy
+      rabbitmq:
+        condition: service_healthy
 
   review:
     build: microservices/review-service
@@ -25,6 +29,8 @@
     depends_on:
       mysql:
         condition: service_healthy
+      rabbitmq:
+        condition: service_healthy
 
   product-composite:
     build: microservices/product-composite-service
@@ -33,6 +39,9 @@
       - "8080:8080"
     environment:
       - SPRING_PROFILES_ACTIVE=docker
+    depends_on:
+      rabbitmq:
+        condition: service_healthy
 
   mongodb:
     image: mongo:8.0.5
@@ -61,3 +70,15 @@
       interval: 5s
       timeout: 2s
       retries: 60
+
+  rabbitmq:
+    image: rabbitmq:4.0.7-management
+    mem_limit: 512m
+    ports:
+      - 5672:5672
+      - 15672:15672
+    healthcheck:
+      test: ["CMD", "rabbitmqctl", "status"]
+      interval: 5s
+      timeout: 2s
+      retries: 60
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose.yml" op="write" nl="0" -->
```yaml
services:
  product:
    build: microservices/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation:
    build: microservices/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review:
    build: microservices/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-composite:
    build: microservices/product-composite-service
    mem_limit: 512m
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=docker
    depends_on:
      rabbitmq:
        condition: service_healthy

  mongodb:
    image: mongo:8.0.5
    mem_limit: 512m
    ports:
      - "27017:27017"
    command: mongod
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh --quiet
      interval: 5s
      timeout: 2s
      retries: 60

  mysql:
    image: mysql:9.2.0
    mem_limit: 512m
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=rootpwd
      - MYSQL_DATABASE=review-db
      - MYSQL_USER=user
      - MYSQL_PASSWORD=pwd
    healthcheck:
      test: "/usr/bin/mysql --user=user --password=pwd --execute \"SHOW DATABASES;\""
      interval: 5s
      timeout: 2s
      retries: 60

  rabbitmq:
    image: rabbitmq:4.0.7-management
    mem_limit: 512m
    ports:
      - 5672:5672
      - 15672:15672
    healthcheck:
      test: ["CMD", "rabbitmqctl", "status"]
      interval: 5s
      timeout: 2s
      retries: 60
```

</details>

#### `test-em-all.bash` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -78,12 +78,68 @@
   echo "DONE, continues..."
 }
 
+function testCompositeCreated() {
+
+    # Expect that the Product Composite for productId $PROD_ID_REVS_RECS has been created with three recommendations and three reviews
+    if ! assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"
+    then
+        echo -n "FAIL"
+        return 1
+    fi
+
+    set +e
+    assertEqual "$PROD_ID_REVS_RECS" $(echo $RESPONSE | jq .productId)
+    if [ "$?" -eq "1" ] ; then return 1; fi
+
+    assertEqual 3 $(echo $RESPONSE | jq ".recommendations | length")
+    if [ "$?" -eq "1" ] ; then return 1; fi
+
+    assertEqual 3 $(echo $RESPONSE | jq ".reviews | length")
+    if [ "$?" -eq "1" ] ; then return 1; fi
+
+    # Also wait for the products without recommendations and reviews. With Kafka their messages
+    # can be processed later than the ones above, e.g. while consumer groups are rebalanced.
+    if ! assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_NO_RECS -s"
+    then
+        echo -n "FAIL"
+        return 1
+    fi
+    if ! assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_NO_REVS -s"
+    then
+        echo -n "FAIL"
+        return 1
+    fi
+    set -e
+}
+
+function waitForMessageProcessing() {
+    echo "Wait for messages to be processed... "
+
+    # Give background processing some time to complete...
+    sleep 1
+
+    n=0
+    until (testCompositeCreated)
+    do
+        n=$((n + 1))
+        if [[ $n == 40 ]]
+        then
+            echo " Give up"
+            exit 1
+        else
+            sleep 6
+            echo -n ", retry #$n "
+        fi
+    done
+    echo "All messages are now processed!"
+}
+
 function recreateComposite() {
   local productId=$1
   local composite=$2
 
-  assertCurl 200 "curl -X DELETE http://$HOST:$PORT/product-composite/${productId} -s"
-  curl -X POST http://$HOST:$PORT/product-composite -H "Content-Type: application/json" --data "$composite"
+  assertCurl 202 "curl -X DELETE http://$HOST:$PORT/product-composite/${productId} -s"
+  assertEqual 202 $(curl -X POST -s http://$HOST:$PORT/product-composite -H "Content-Type: application/json" --data "$composite" -w "%{http_code}")
 }
 
 function setupTestdata() {
@@ -138,9 +194,10 @@
   docker compose up -d
 fi
 
-waitForService curl -X DELETE http://$HOST:$PORT/product-composite/$PROD_ID_NOT_FOUND
-
+waitForService curl http://$HOST:$PORT/actuator/health
 setupTestdata
+
+waitForMessageProcessing
 
 # Verify that a normal request works, expect three recommendations and three reviews
 assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="test-em-all.bash" op="write" nl="1" -->
```bash
#!/usr/bin/env bash
#
# Sample usage:
#
#   HOST=localhost PORT=7001 ./test-em-all.bash
#
: ${HOST=localhost}
: ${PORT=8080}
: ${PROD_ID_REVS_RECS=1}
: ${PROD_ID_NOT_FOUND=13}
: ${PROD_ID_NO_RECS=113}
: ${PROD_ID_NO_REVS=213}

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
    if ! assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"
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
    if ! assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_NO_RECS -s"
    then
        echo -n "FAIL"
        return 1
    fi
    if ! assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_NO_REVS -s"
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

  assertCurl 202 "curl -X DELETE http://$HOST:$PORT/product-composite/${productId} -s"
  assertEqual 202 $(curl -X POST -s http://$HOST:$PORT/product-composite -H "Content-Type: application/json" --data "$composite" -w "%{http_code}")
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

set -e

echo "Start Tests:" `date`

echo "HOST=${HOST}"
echo "PORT=${PORT}"

if [[ $@ == *"start"* ]]
then
  echo "Restarting the test environment..."
  echo "$ docker compose down --remove-orphans"
  docker compose down --remove-orphans
  echo "$ docker compose up -d"
  docker compose up -d
fi

waitForService curl http://$HOST:$PORT/actuator/health
setupTestdata

waitForMessageProcessing

# Verify that a normal request works, expect three recommendations and three reviews
assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"
assertEqual $PROD_ID_REVS_RECS $(echo $RESPONSE | jq .productId)
assertEqual 3 $(echo $RESPONSE | jq ".recommendations | length")
assertEqual 3 $(echo $RESPONSE | jq ".reviews | length")

# Verify that a 404 (Not Found) error is returned for a non-existing productId ($PROD_ID_NOT_FOUND)
assertCurl 404 "curl http://$HOST:$PORT/product-composite/$PROD_ID_NOT_FOUND -s"
assertEqual "No product found for productId: $PROD_ID_NOT_FOUND" "$(echo $RESPONSE | jq -r .message)"

# Verify that no recommendations are returned for productId $PROD_ID_NO_RECS
assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_NO_RECS -s"
assertEqual $PROD_ID_NO_RECS $(echo $RESPONSE | jq .productId)
assertEqual 0 $(echo $RESPONSE | jq ".recommendations | length")
assertEqual 3 $(echo $RESPONSE | jq ".reviews | length")

# Verify that no reviews are returned for productId $PROD_ID_NO_REVS
assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_NO_REVS -s"
assertEqual $PROD_ID_NO_REVS $(echo $RESPONSE | jq .productId)
assertEqual 3 $(echo $RESPONSE | jq ".recommendations | length")
assertEqual 0 $(echo $RESPONSE | jq ".reviews | length")

# Verify that a 422 (Unprocessable Entity) error is returned for a productId that is out of range (-1)
assertCurl 422 "curl http://$HOST:$PORT/product-composite/-1 -s"
assertEqual "\"Invalid productId: -1\"" "$(echo $RESPONSE | jq .message)"

# Verify that a 400 (Bad Request) error error is returned for a productId that is not a number, i.e. invalid format
assertCurl 400 "curl http://$HOST:$PORT/product-composite/invalidProductId -s"
assertEqual "\"Type mismatch.\"" "$(echo $RESPONSE | jq .message)"

# Verify access to Swagger and OpenAPI URLs
echo "Swagger/OpenAPI tests"
assertCurl 302 "curl -s  http://$HOST:$PORT/openapi/swagger-ui.html"
assertCurl 200 "curl -sL http://$HOST:$PORT/openapi/swagger-ui.html"
assertCurl 200 "curl -s  http://$HOST:$PORT/openapi/swagger-ui/index.html"
# Verify the redirect URL
assertCurl 200 "curl -s  http://$HOST:$PORT/openapi/swagger-ui/oauth2-redirect.html"
assertCurl 200 "curl -s  http://$HOST:$PORT/openapi/v3/api-docs"
assertEqual "3.1.0" "$(echo $RESPONSE | jq -r .openapi)"
assertEqual "http://$HOST:$PORT" "$(echo $RESPONSE | jq -r '.servers[0].url')"
assertCurl 200 "curl -s  http://$HOST:$PORT/openapi/v3/api-docs.yaml"

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

## 단계 2. `api` 프로젝트 — 서비스 간 API와 DTO

서비스 인터페이스가 `Mono`/`Flux`를 돌려주도록 바꾸고, 이벤트를 나타내는 `Event`와 `EventProcessingException`을 추가합니다.

#### `api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -4,7 +4,9 @@
 import io.swagger.v3.oas.annotations.responses.ApiResponse;
 import io.swagger.v3.oas.annotations.responses.ApiResponses;
 import io.swagger.v3.oas.annotations.tags.Tag;
+import org.springframework.http.HttpStatus;
 import org.springframework.web.bind.annotation.*;
+import reactor.core.publisher.Mono;
 
 @Tag(name = "ProductComposite", description = "REST API for composite product information.")
 public interface ProductCompositeService {
@@ -25,10 +27,11 @@
     @ApiResponse(responseCode = "400", description = "${api.responseCodes.badRequest.description}"),
     @ApiResponse(responseCode = "422", description = "${api.responseCodes.unprocessableEntity.description}")
   })
+  @ResponseStatus(HttpStatus.ACCEPTED)
   @PostMapping(
     value    = "/product-composite",
     consumes = "application/json")
-  void createProduct(@RequestBody ProductAggregate body);
+  Mono<Void> createProduct(@RequestBody ProductAggregate body);
 
   /**
    * Sample usage: "curl $HOST:$PORT/product-composite/1".
@@ -48,7 +51,7 @@
   @GetMapping(
     value = "/product-composite/{productId}",
     produces = "application/json")
-  ProductAggregate getProduct(@PathVariable int productId);
+  Mono<ProductAggregate> getProduct(@PathVariable int productId);
 
   /**
    * Sample usage: "curl -X DELETE $HOST:$PORT/product-composite/1".
@@ -62,6 +65,7 @@
     @ApiResponse(responseCode = "400", description = "${api.responseCodes.badRequest.description}"),
     @ApiResponse(responseCode = "422", description = "${api.responseCodes.unprocessableEntity.description}")
   })
+  @ResponseStatus(HttpStatus.ACCEPTED)
   @DeleteMapping(value = "/product-composite/{productId}")
-  void deleteProduct(@PathVariable int productId);
+  Mono<Void> deleteProduct(@PathVariable int productId);
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@Tag(name = "ProductComposite", description = "REST API for composite product information.")
public interface ProductCompositeService {

  /**
   * Sample usage, see below.
   *
   * curl -X POST $HOST:$PORT/product-composite \
   *   -H "Content-Type: application/json" --data \
   *   '{"productId":123,"name":"product 123","weight":123}'
   *
   * @param body A JSON representation of the new composite product
   */
  @Operation(
    summary = "${api.product-composite.create-composite-product.description}",
    description = "${api.product-composite.create-composite-product.notes}")
  @ApiResponses(value = {
    @ApiResponse(responseCode = "400", description = "${api.responseCodes.badRequest.description}"),
    @ApiResponse(responseCode = "422", description = "${api.responseCodes.unprocessableEntity.description}")
  })
  @ResponseStatus(HttpStatus.ACCEPTED)
  @PostMapping(
    value    = "/product-composite",
    consumes = "application/json")
  Mono<Void> createProduct(@RequestBody ProductAggregate body);

  /**
   * Sample usage: "curl $HOST:$PORT/product-composite/1".
   *
   * @param productId Id of the product
   * @return the composite product info, if found, else null
   */
  @Operation(
    summary = "${api.product-composite.get-composite-product.description}",
    description = "${api.product-composite.get-composite-product.notes}")
  @ApiResponses(value = {
    @ApiResponse(responseCode = "200", description = "${api.responseCodes.ok.description}"),
    @ApiResponse(responseCode = "400", description = "${api.responseCodes.badRequest.description}"),
    @ApiResponse(responseCode = "404", description = "${api.responseCodes.notFound.description}"),
    @ApiResponse(responseCode = "422", description = "${api.responseCodes.unprocessableEntity.description}")
  })
  @GetMapping(
    value = "/product-composite/{productId}",
    produces = "application/json")
  Mono<ProductAggregate> getProduct(@PathVariable int productId);

  /**
   * Sample usage: "curl -X DELETE $HOST:$PORT/product-composite/1".
   *
   * @param productId Id of the product
   */
  @Operation(
    summary = "${api.product-composite.delete-composite-product.description}",
    description = "${api.product-composite.delete-composite-product.notes}")
  @ApiResponses(value = {
    @ApiResponse(responseCode = "400", description = "${api.responseCodes.badRequest.description}"),
    @ApiResponse(responseCode = "422", description = "${api.responseCodes.unprocessableEntity.description}")
  })
  @ResponseStatus(HttpStatus.ACCEPTED)
  @DeleteMapping(value = "/product-composite/{productId}")
  Mono<Void> deleteProduct(@PathVariable int productId);
}
```

</details>

#### `api/src/main/java/se/magnus/api/core/product/ProductService.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="api/src/main/java/se/magnus/api/core/product/ProductService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.product;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import reactor.core.publisher.Mono;

public interface ProductService {

  Mono<Product> createProduct(Product body);

  /**
   * Sample usage: "curl $HOST:$PORT/product/1".
   *
   * @param productId Id of the product
   * @return the product, if found, else null
   */
  @GetMapping(
    value = "/product/{productId}",
    produces = "application/json")
  Mono<Product> getProduct(@PathVariable int productId);

  Mono<Void> deleteProduct(int productId);
}
```

#### `api/src/main/java/se/magnus/api/core/recommendation/RecommendationService.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="api/src/main/java/se/magnus/api/core/recommendation/RecommendationService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.recommendation;

import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface RecommendationService {

  Mono<Recommendation> createRecommendation(Recommendation body);

  /**
   * Sample usage: "curl $HOST:$PORT/recommendation?productId=1".
   *
   * @param productId Id of the product
   * @return the recommendations of the product
   */
  @GetMapping(
    value = "/recommendation",
    produces = "application/json")
  Flux<Recommendation> getRecommendations(
    @RequestParam(value = "productId", required = true) int productId);

  Mono<Void> deleteRecommendations(int productId);
}
```

#### `api/src/main/java/se/magnus/api/core/review/ReviewService.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="api/src/main/java/se/magnus/api/core/review/ReviewService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.review;

import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ReviewService {

  Mono<Review> createReview(Review body);

  /**
   * Sample usage: "curl $HOST:$PORT/review?productId=1".
   *
   * @param productId Id of the product
   * @return the reviews of the product
   */
  @GetMapping(
    value = "/review",
    produces = "application/json")
  Flux<Review> getReviews(@RequestParam(value = "productId", required = true) int productId);

  Mono<Void> deleteReviews(int productId);
}
```

#### `api/src/main/java/se/magnus/api/event/Event.java` — 새 파일 (53줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/event/Event.java" op="write" nl="1" -->
```java
package se.magnus.api.event;

import static java.time.ZonedDateTime.now;

import java.time.ZonedDateTime;
import tools.jackson.databind.annotation.JsonSerialize;
import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;

public class Event<K, T> {

  public enum Type {
    CREATE,
    DELETE
  }

  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private Type eventType;
  private K key;
  private T data;
  private ZonedDateTime eventCreatedAt;

  public Event() {
    this.eventType = null;
    this.key = null;
    this.data = null;
    this.eventCreatedAt = null;
  }

  public Event(Type eventType, K key, T data) {
    this.eventType = eventType;
    this.key = key;
    this.data = data;
    this.eventCreatedAt = now();
  }

  public Type getEventType() {
    return eventType;
  }

  public K getKey() {
    return key;
  }

  public T getData() {
    return data;
  }

  @JsonSerialize(using = ZonedDateTimeSerializer.class)
  public ZonedDateTime getEventCreatedAt() {
    return eventCreatedAt;
  }
}
```

#### `api/src/main/java/se/magnus/api/exceptions/EventProcessingException.java` — 새 파일 (18줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/exceptions/EventProcessingException.java" op="write" nl="1" -->
```java
package se.magnus.api.exceptions;

public class EventProcessingException extends RuntimeException {
  public EventProcessingException() {
  }

  public EventProcessingException(String message) {
    super(message);
  }

  public EventProcessingException(String message, Throwable cause) {
    super(message, cause);
  }

  public EventProcessingException(Throwable cause) {
    super(cause);
  }
}
```

**중간 확인**

```bash
./gradlew :api:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-3"></a>

## 단계 3. `util` 프로젝트 — 공통 유틸리티

Reactor의 동작을 확인하는 `ReactorTests`를 추가합니다.

#### `util/src/test/java/se/magnus/util/reactor/ReactorTests.java` — 새 파일 (37줄)

<!-- wb:file path="util/src/test/java/se/magnus/util/reactor/ReactorTests.java" op="write" nl="1" -->
```java
package se.magnus.util.reactor;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;

class ReactorTests {

  @Test
  void testFlux() {

    List<Integer> list = new ArrayList<>();

    Flux.just(1, 2, 3, 4)
      .filter(n -> n % 2 == 0)
      .map(n -> n * 2)
      .log()
      .subscribe(n -> list.add(n));

    assertThat(list).containsExactly(4, 8);
  }

  @Test
  void testFluxBlocking() {

    List<Integer> list = Flux.just(1, 2, 3, 4)
      .filter(n -> n % 2 == 0)
      .map(n -> n * 2)
      .log()
      .collectList().block();

    assertThat(list).containsExactly(4, 8);
  }
}
```

**중간 확인**

```bash
./gradlew :util:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-4"></a>

## 단계 4. `product-service`

메시지를 받아 생성·삭제를 처리하는 `MessageProcessorConfig`(`Consumer<Event>` 빈)를 추가하고, 서비스 구현과 테스트를 리액티브로 바꿉니다. `application.yml`에 Spring Cloud Stream 바인딩, RabbitMQ·Kafka 설정이 추가됩니다.

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -15,6 +15,7 @@
 
 ext {
     mapstructVersion = '1.6.3'
+    springCloudVersion = '2025.1.4'
 }
 
 repositories {
@@ -30,7 +31,10 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
-    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'
+    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
+    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
+    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
+
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
 
     compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
@@ -43,7 +47,7 @@
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
-    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
 
@@ -52,6 +56,12 @@
     testImplementation 'org.testcontainers:testcontainers-mongodb'
 }
 
+dependencyManagement {
+    imports {
+        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
+    }
+}
+
 tasks.named('test') {
     useJUnitPlatform()
 }
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

    implementation "org.mapstruct:mapstruct:${mapstructVersion}"

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

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/ProductServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -10,10 +10,10 @@
 import org.springframework.context.event.ContextRefreshedEvent;
 import org.springframework.context.event.EventListener;
 import org.springframework.data.mapping.context.MappingContext;
-import org.springframework.data.mongodb.core.MongoOperations;
-import org.springframework.data.mongodb.core.index.IndexOperations;
+import org.springframework.data.mongodb.core.ReactiveMongoOperations;
 import org.springframework.data.mongodb.core.index.IndexResolver;
 import org.springframework.data.mongodb.core.index.MongoPersistentEntityIndexResolver;
+import org.springframework.data.mongodb.core.index.ReactiveIndexOperations;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentEntity;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentProperty;
 import se.magnus.microservices.core.product.persistence.ProductEntity;
@@ -33,7 +33,7 @@
   }
 
   @Autowired
-  MongoOperations mongoTemplate;
+  ReactiveMongoOperations mongoTemplate;
 
   @EventListener(ContextRefreshedEvent.class)
   public void initIndicesAfterStartup() {
@@ -41,7 +41,7 @@
     MappingContext<? extends MongoPersistentEntity<?>, MongoPersistentProperty> mappingContext = mongoTemplate.getConverter().getMappingContext();
     IndexResolver resolver = new MongoPersistentEntityIndexResolver(mappingContext);
 
-    IndexOperations indexOps = mongoTemplate.indexOps(ProductEntity.class);
-    resolver.resolveIndexFor(ProductEntity.class).forEach(e -> indexOps.createIndex(e));
+    ReactiveIndexOperations indexOps = mongoTemplate.indexOps(ProductEntity.class);
+    resolver.resolveIndexFor(ProductEntity.class).forEach(e -> indexOps.createIndex(e).block());
   }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/ProductServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
import se.magnus.microservices.core.product.persistence.ProductEntity;

@SpringBootApplication
@ComponentScan("se.magnus")
public class ProductServiceApplication {

  private static final Logger LOG = LoggerFactory.getLogger(ProductServiceApplication.class);

  public static void main(String[] args) {
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

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/persistence/ProductEntity.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,4 +1,6 @@
 package se.magnus.microservices.core.product.persistence;
+
+import static java.lang.String.format;
 
 import org.springframework.data.annotation.Id;
 import org.springframework.data.annotation.Version;
@@ -24,6 +26,11 @@
     this.productId = productId;
     this.name = name;
     this.weight = weight;
+  }
+
+  @Override
+  public String toString() {
+    return format("ProductEntity: %s", productId);
   }
 
   public String getId() {
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/persistence/ProductEntity.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.persistence;

import static java.lang.String.format;

import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Version;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

@Document(collection = "products")
public class ProductEntity {

  @Id private String id;

  @Version private Integer version;

  @Indexed(unique = true)
  private int productId;

  private String name;
  private int weight;

  public ProductEntity() {}

  public ProductEntity(int productId, String name, int weight) {
    this.productId = productId;
    this.name = name;
    this.weight = weight;
  }

  @Override
  public String toString() {
    return format("ProductEntity: %s", productId);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public Integer getVersion() {
    return version;
  }

  public void setVersion(Integer version) {
    this.version = version;
  }

  public int getProductId() {
    return productId;
  }

  public void setProductId(int productId) {
    this.productId = productId;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public int getWeight() {
    return weight;
  }

  public void setWeight(int weight) {
    this.weight = weight;
  }
}
```

</details>

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/persistence/ProductRepository.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/persistence/ProductRepository.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.persistence;

import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import reactor.core.publisher.Mono;

public interface ProductRepository extends ReactiveCrudRepository<ProductEntity, String> {
  Mono<ProductEntity> findByProductId(int productId);
}
```

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/MessageProcessorConfig.java` — 새 파일 (53줄)

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/MessageProcessorConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.services;

import java.util.function.Consumer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.product.ProductService;
import se.magnus.api.event.Event;
import se.magnus.api.exceptions.EventProcessingException;

@Configuration
public class MessageProcessorConfig {

  private static final Logger LOG = LoggerFactory.getLogger(MessageProcessorConfig.class);

  private final ProductService productService;

  public MessageProcessorConfig(ProductService productService) {
    this.productService = productService;
  }

  @Bean
  public Consumer<Event<Integer, Product>> messageProcessor() {
    return event -> {
      LOG.info("Process message created at {}...", event.getEventCreatedAt());

      switch (event.getEventType()) {

        case CREATE:
          Product product = event.getData();
          LOG.info("Create product with ID: {}", product.getProductId());
          productService.createProduct(product).block();
          break;

        case DELETE:
          int productId = event.getKey();
          LOG.info("Delete product with ProductID: {}", productId);
          productService.deleteProduct(productId).block();
          break;

        default:
          String errorMessage = "Incorrect event type: " + event.getEventType() + ", expected a CREATE or DELETE event";
          LOG.warn(errorMessage);
          throw new EventProcessingException(errorMessage);
      }

      LOG.info("Message processing done!");

    };
  }
}
```

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,9 +1,12 @@
 package se.magnus.microservices.core.product.services;
+
+import static java.util.logging.Level.FINE;
 
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
 import org.springframework.dao.DuplicateKeyException;
 import org.springframework.web.bind.annotation.RestController;
+import reactor.core.publisher.Mono;
 import se.magnus.api.core.product.Product;
 import se.magnus.api.core.product.ProductService;
 import se.magnus.api.exceptions.InvalidInputException;
@@ -30,40 +33,52 @@
   }
 
   @Override
-  public Product createProduct(Product body) {
-    try {
-      ProductEntity entity = mapper.apiToEntity(body);
-      ProductEntity newEntity = repository.save(entity);
+  public Mono<Product> createProduct(Product body) {
 
-      LOG.debug("createProduct: entity created for productId: {}", body.getProductId());
-      return mapper.entityToApi(newEntity);
+    if (body.getProductId() < 1) {
+      throw new InvalidInputException("Invalid productId: " + body.getProductId());
+    }
 
-    } catch (DuplicateKeyException dke) {
-      throw new InvalidInputException("Duplicate key, Product Id: " + body.getProductId());
-    }
+    ProductEntity entity = mapper.apiToEntity(body);
+    Mono<Product> newEntity = repository.save(entity)
+      .log(LOG.getName(), FINE)
+      .onErrorMap(
+        DuplicateKeyException.class,
+        ex -> new InvalidInputException("Duplicate key, Product Id: " + body.getProductId()))
+      .map(e -> mapper.entityToApi(e));
+
+    return newEntity;
   }
 
   @Override
-  public Product getProduct(int productId) {
+  public Mono<Product> getProduct(int productId) {
 
     if (productId < 1) {
       throw new InvalidInputException("Invalid productId: " + productId);
     }
 
-    ProductEntity entity = repository.findByProductId(productId)
-      .orElseThrow(() -> new NotFoundException("No product found for productId: " + productId));
+    LOG.info("Will get product info for id={}", productId);
 
-    Product response = mapper.entityToApi(entity);
-    response.setServiceAddress(serviceUtil.getServiceAddress());
-
-    LOG.debug("getProduct: found productId: {}", response.getProductId());
-
-    return response;
+    return repository.findByProductId(productId)
+      .switchIfEmpty(Mono.error(new NotFoundException("No product found for productId: " + productId)))
+      .log(LOG.getName(), FINE)
+      .map(e -> mapper.entityToApi(e))
+      .map(e -> setServiceAddress(e));
   }
 
   @Override
-  public void deleteProduct(int productId) {
+  public Mono<Void> deleteProduct(int productId) {
+
+    if (productId < 1) {
+      throw new InvalidInputException("Invalid productId: " + productId);
+    }
+
     LOG.debug("deleteProduct: tries to delete an entity with productId: {}", productId);
-    repository.findByProductId(productId).ifPresent(e -> repository.delete(e));
+    return repository.findByProductId(productId).log(LOG.getName(), FINE).map(e -> repository.delete(e)).flatMap(e -> e);
+  }
+
+  private Product setServiceAddress(Product e) {
+    e.setServiceAddress(serviceUtil.getServiceAddress());
+    return e;
   }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java" op="write" nl="0" -->
```java
package se.magnus.microservices.core.product.services;

import static java.util.logging.Level.FINE;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.product.ProductService;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.api.exceptions.NotFoundException;
import se.magnus.microservices.core.product.persistence.ProductEntity;
import se.magnus.microservices.core.product.persistence.ProductRepository;
import se.magnus.util.http.ServiceUtil;

@RestController
public class ProductServiceImpl implements ProductService {

  private static final Logger LOG = LoggerFactory.getLogger(ProductServiceImpl.class);

  private final ServiceUtil serviceUtil;

  private final ProductRepository repository;

  private final ProductMapper mapper;

  public ProductServiceImpl(ProductRepository repository, ProductMapper mapper, ServiceUtil serviceUtil) {
    this.repository = repository;
    this.mapper = mapper;
    this.serviceUtil = serviceUtil;
  }

  @Override
  public Mono<Product> createProduct(Product body) {

    if (body.getProductId() < 1) {
      throw new InvalidInputException("Invalid productId: " + body.getProductId());
    }

    ProductEntity entity = mapper.apiToEntity(body);
    Mono<Product> newEntity = repository.save(entity)
      .log(LOG.getName(), FINE)
      .onErrorMap(
        DuplicateKeyException.class,
        ex -> new InvalidInputException("Duplicate key, Product Id: " + body.getProductId()))
      .map(e -> mapper.entityToApi(e));

    return newEntity;
  }

  @Override
  public Mono<Product> getProduct(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    LOG.info("Will get product info for id={}", productId);

    return repository.findByProductId(productId)
      .switchIfEmpty(Mono.error(new NotFoundException("No product found for productId: " + productId)))
      .log(LOG.getName(), FINE)
      .map(e -> mapper.entityToApi(e))
      .map(e -> setServiceAddress(e));
  }

  @Override
  public Mono<Void> deleteProduct(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    LOG.debug("deleteProduct: tries to delete an entity with productId: {}", productId);
    return repository.findByProductId(productId).log(LOG.getName(), FINE).map(e -> repository.delete(e)).flatMap(e -> e);
  }

  private Product setServiceAddress(Product e) {
    e.setServiceAddress(serviceUtil.getServiceAddress());
    return e;
  }
}
```

</details>

#### `microservices/product-service/src/main/resources/application.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7002
spring.web.error.include-message: always

spring.mongodb:
  host: localhost
  port: 27017
  database: product-db

spring.cloud.function.definition: messageProcessor

spring.cloud.stream:
  defaultBinder: rabbit
  default.contentType: application/json
  bindings.messageProcessor-in-0:
    destination: products
    group: productsGroup

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

spring.cloud.stream.kafka.binder:
  brokers: 127.0.0.1
  defaultBrokerPort: 9092

spring.rabbitmq:
  host: 127.0.0.1
  port: 5672
  username: guest
  password: guest

logging:
  level:
    root: INFO
    se.magnus: DEBUG
    org.springframework.data.mongodb.core.ReactiveMongoTemplate: DEBUG

management.endpoint.health.show-details: "ALWAYS"
management.endpoints.web.exposure.include: "*"
---
spring.config.activate.on-profile: docker

server.port: 8080

spring.mongodb.host: mongodb

spring.rabbitmq.host: rabbitmq

spring.cloud.stream.kafka.binder.brokers: kafka

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

management.health.rabbit.enabled: false
spring.cloud.stream.defaultBinder: kafka
spring.kafka.bootstrap-servers: kafka:9092
spring.cloud.stream.kafka.binder.replication-factor: 1
```

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/PersistenceTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/PersistenceTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import java.util.Objects;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.mongodb.test.autoconfigure.DataMongoTest;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.dao.OptimisticLockingFailureException;
import reactor.test.StepVerifier;
import se.magnus.microservices.core.product.persistence.ProductEntity;
import se.magnus.microservices.core.product.persistence.ProductRepository;

@DataMongoTest
class PersistenceTests extends MongoDbTestBase {

  @Autowired
  private ProductRepository repository;

  private ProductEntity savedEntity;

  @BeforeEach
  void setupDb() {
    StepVerifier.create(repository.deleteAll()).verifyComplete();

    ProductEntity entity = new ProductEntity(1, "n", 1);
    StepVerifier.create(repository.save(entity))
      .expectNextMatches(createdEntity -> {
        savedEntity = createdEntity;
        return areProductEqual(entity, savedEntity);
      })
      .verifyComplete();
  }


  @Test
  void create() {
    ProductEntity newEntity = new ProductEntity(2, "n", 2);

    StepVerifier.create(repository.save(newEntity))
      .expectNextMatches(createdEntity -> newEntity.getProductId() == createdEntity.getProductId())
      .verifyComplete();

    StepVerifier.create(repository.findById(newEntity.getId()))
      .expectNextMatches(foundEntity -> areProductEqual(newEntity, foundEntity))
      .verifyComplete();

    StepVerifier.create(repository.count()).expectNext(2L).verifyComplete();
  }

  @Test
  void update() {
    savedEntity.setName("n2");
    StepVerifier.create(repository.save(savedEntity))
      .expectNextMatches(updatedEntity -> updatedEntity.getName().equals("n2"))
      .verifyComplete();

    StepVerifier.create(repository.findById(savedEntity.getId()))
      .expectNextMatches(foundEntity ->
        foundEntity.getVersion() == 1
        && foundEntity.getName().equals("n2"))
      .verifyComplete();
  }

  @Test
  void delete() {
    StepVerifier.create(repository.delete(savedEntity)).verifyComplete();
    StepVerifier.create(repository.existsById(savedEntity.getId())).expectNext(false).verifyComplete();
  }

  @Test
  void getByProductId() {

    StepVerifier.create(repository.findByProductId(savedEntity.getProductId()))
      .expectNextMatches(foundEntity -> areProductEqual(savedEntity, foundEntity))
      .verifyComplete();
  }

  @Test
  void duplicateError() {
    ProductEntity entity = new ProductEntity(savedEntity.getProductId(), "n", 1);
    StepVerifier.create(repository.save(entity)).expectError(DuplicateKeyException.class).verify();
  }

  @Test
  void optimisticLockError() {

    // Store the saved entity in two separate entity objects
    ProductEntity entity1 = repository.findById(savedEntity.getId()).block();
    ProductEntity entity2 = repository.findById(savedEntity.getId()).block();

    // Update the entity using the first entity object
    entity1.setName("n1");
    repository.save(entity1).block();

    //  Update the entity using the second entity object.
    // This should fail since the second entity now holds a old version number, i.e. a Optimistic Lock Error
    StepVerifier.create(repository.save(entity2)).expectError(OptimisticLockingFailureException.class).verify();

    // Get the updated entity from the database and verify its new sate
    StepVerifier.create(repository.findById(savedEntity.getId()))
      .expectNextMatches(foundEntity ->
        foundEntity.getVersion() == 1
        && foundEntity.getName().equals("n1"))
      .verifyComplete();
  }

  private boolean areProductEqual(ProductEntity expectedEntity, ProductEntity actualEntity) {
    return
      (expectedEntity.getId().equals(actualEntity.getId()))
      && (Objects.equals(expectedEntity.getVersion(), actualEntity.getVersion()))
      && (expectedEntity.getProductId() == actualEntity.getProductId())
      && (expectedEntity.getName().equals(actualEntity.getName()))
      && (expectedEntity.getWeight() == actualEntity.getWeight());
  }
}
```

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,33 +1,43 @@
 package se.magnus.microservices.core.product;
 
-import static org.junit.jupiter.api.Assertions.assertFalse;
-import static org.junit.jupiter.api.Assertions.assertTrue;
+import static org.junit.jupiter.api.Assertions.*;
 import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
 import static org.springframework.http.HttpStatus.*;
 import static org.springframework.http.MediaType.APPLICATION_JSON;
-import static reactor.core.publisher.Mono.just;
+import static se.magnus.api.event.Event.Type.CREATE;
+import static se.magnus.api.event.Event.Type.DELETE;
 
+import java.util.function.Consumer;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
 import org.springframework.beans.factory.annotation.Autowired;
+import org.springframework.beans.factory.annotation.Qualifier;
 import org.springframework.boot.test.context.SpringBootTest;
 import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
 import org.springframework.http.HttpStatus;
 import org.springframework.test.web.reactive.server.WebTestClient;
 import se.magnus.api.core.product.Product;
+import se.magnus.api.event.Event;
+import se.magnus.api.exceptions.InvalidInputException;
 import se.magnus.microservices.core.product.persistence.ProductRepository;
 
 @AutoConfigureWebTestClient
 @SpringBootTest(webEnvironment = RANDOM_PORT)
 class ProductServiceApplicationTests extends MongoDbTestBase {
 
-  @Autowired private WebTestClient client;
+  @Autowired
+  private WebTestClient client;
 
-  @Autowired private ProductRepository repository;
+  @Autowired
+  private ProductRepository repository;
+
+  @Autowired
+  @Qualifier("messageProcessor")
+  private Consumer<Event<Integer, Product>> messageProcessor;
 
   @BeforeEach
   void setupDb() {
-    repository.deleteAll();
+    repository.deleteAll().block();
   }
 
   @Test
@@ -35,11 +45,16 @@
 
     int productId = 1;
 
-    postAndVerifyProduct(productId, OK);
+    assertNull(repository.findByProductId(productId).block());
+    assertEquals(0, (long)repository.count().block());
 
-    assertTrue(repository.findByProductId(productId).isPresent());
+    sendCreateProductEvent(productId);
 
-    getAndVerifyProduct(productId, OK).jsonPath("$.productId").isEqualTo(productId);
+    assertNotNull(repository.findByProductId(productId).block());
+    assertEquals(1, (long)repository.count().block());
+
+    getAndVerifyProduct(productId, OK)
+      .jsonPath("$.productId").isEqualTo(productId);
   }
 
   @Test
@@ -47,13 +62,17 @@
 
     int productId = 1;
 
-    postAndVerifyProduct(productId, OK);
+    assertNull(repository.findByProductId(productId).block());
 
-    assertTrue(repository.findByProductId(productId).isPresent());
+    sendCreateProductEvent(productId);
 
-    postAndVerifyProduct(productId, UNPROCESSABLE_CONTENT)
-      .jsonPath("$.path").isEqualTo("/product")
-      .jsonPath("$.message").isEqualTo("Duplicate key, Product Id: " + productId);
+    assertNotNull(repository.findByProductId(productId).block());
+
+    InvalidInputException thrown = assertThrows(
+      InvalidInputException.class,
+      () -> sendCreateProductEvent(productId),
+      "Expected a InvalidInputException here!");
+    assertEquals("Duplicate key, Product Id: " + productId, thrown.getMessage());
   }
 
   @Test
@@ -61,13 +80,13 @@
 
     int productId = 1;
 
-    postAndVerifyProduct(productId, OK);
-    assertTrue(repository.findByProductId(productId).isPresent());
+    sendCreateProductEvent(productId);
+    assertNotNull(repository.findByProductId(productId).block());
 
-    deleteAndVerifyProduct(productId, OK);
-    assertFalse(repository.findByProductId(productId).isPresent());
+    sendDeleteProductEvent(productId);
+    assertNull(repository.findByProductId(productId).block());
 
-    deleteAndVerifyProduct(productId, OK);
+    sendDeleteProductEvent(productId);
   }
 
   @Test
@@ -111,24 +130,14 @@
       .expectBody();
   }
 
-  private WebTestClient.BodyContentSpec postAndVerifyProduct(int productId, HttpStatus expectedStatus) {
+  private void sendCreateProductEvent(int productId) {
     Product product = new Product(productId, "Name " + productId, productId, "SA");
-    return client.post()
-      .uri("/product")
-      .body(just(product), Product.class)
-      .accept(APPLICATION_JSON)
-      .exchange()
-      .expectStatus().isEqualTo(expectedStatus)
-      .expectHeader().contentType(APPLICATION_JSON)
-      .expectBody();
+    Event<Integer, Product> event = new Event<>(CREATE, productId, product);
+    messageProcessor.accept(event);
   }
 
-  private WebTestClient.BodyContentSpec deleteAndVerifyProduct(int productId, HttpStatus expectedStatus) {
-    return client.delete()
-      .uri("/product/" + productId)
-      .accept(APPLICATION_JSON)
-      .exchange()
-      .expectStatus().isEqualTo(expectedStatus)
-      .expectBody();
+  private void sendDeleteProductEvent(int productId) {
+    Event<Integer, Product> event = new Event<>(DELETE, productId, null);
+    messageProcessor.accept(event);
   }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java" op="write" nl="0" -->
```java
package se.magnus.microservices.core.product;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static se.magnus.api.event.Event.Type.CREATE;
import static se.magnus.api.event.Event.Type.DELETE;

import java.util.function.Consumer;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import se.magnus.api.core.product.Product;
import se.magnus.api.event.Event;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.microservices.core.product.persistence.ProductRepository;

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
class ProductServiceApplicationTests extends MongoDbTestBase {

  @Autowired
  private WebTestClient client;

  @Autowired
  private ProductRepository repository;

  @Autowired
  @Qualifier("messageProcessor")
  private Consumer<Event<Integer, Product>> messageProcessor;

  @BeforeEach
  void setupDb() {
    repository.deleteAll().block();
  }

  @Test
  void getProductById() {

    int productId = 1;

    assertNull(repository.findByProductId(productId).block());
    assertEquals(0, (long)repository.count().block());

    sendCreateProductEvent(productId);

    assertNotNull(repository.findByProductId(productId).block());
    assertEquals(1, (long)repository.count().block());

    getAndVerifyProduct(productId, OK)
      .jsonPath("$.productId").isEqualTo(productId);
  }

  @Test
  void duplicateError() {

    int productId = 1;

    assertNull(repository.findByProductId(productId).block());

    sendCreateProductEvent(productId);

    assertNotNull(repository.findByProductId(productId).block());

    InvalidInputException thrown = assertThrows(
      InvalidInputException.class,
      () -> sendCreateProductEvent(productId),
      "Expected a InvalidInputException here!");
    assertEquals("Duplicate key, Product Id: " + productId, thrown.getMessage());
  }

  @Test
  void deleteProduct() {

    int productId = 1;

    sendCreateProductEvent(productId);
    assertNotNull(repository.findByProductId(productId).block());

    sendDeleteProductEvent(productId);
    assertNull(repository.findByProductId(productId).block());

    sendDeleteProductEvent(productId);
  }

  @Test
  void getProductInvalidParameterString() {

    getAndVerifyProduct("/no-integer", BAD_REQUEST)
      .jsonPath("$.path").isEqualTo("/product/no-integer")
      .jsonPath("$.message").isEqualTo("Type mismatch.");
  }

  @Test
  void getProductNotFound() {

    int productIdNotFound = 13;
    getAndVerifyProduct(productIdNotFound, NOT_FOUND)
      .jsonPath("$.path").isEqualTo("/product/" + productIdNotFound)
      .jsonPath("$.message").isEqualTo("No product found for productId: " + productIdNotFound);
  }

  @Test
  void getProductInvalidParameterNegativeValue() {

    int productIdInvalid = -1;

    getAndVerifyProduct(productIdInvalid, UNPROCESSABLE_CONTENT)
      .jsonPath("$.path").isEqualTo("/product/" + productIdInvalid)
      .jsonPath("$.message").isEqualTo("Invalid productId: " + productIdInvalid);
  }

  private WebTestClient.BodyContentSpec getAndVerifyProduct(int productId, HttpStatus expectedStatus) {
    return getAndVerifyProduct("/" + productId, expectedStatus);
  }

  private WebTestClient.BodyContentSpec getAndVerifyProduct(String productIdPath, HttpStatus expectedStatus) {
    return client.get()
      .uri("/product" + productIdPath)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody();
  }

  private void sendCreateProductEvent(int productId) {
    Product product = new Product(productId, "Name " + productId, productId, "SA");
    Event<Integer, Product> event = new Event<>(CREATE, productId, product);
    messageProcessor.accept(event);
  }

  private void sendDeleteProductEvent(int productId) {
    Event<Integer, Product> event = new Event<>(DELETE, productId, null);
    messageProcessor.accept(event);
  }
}
```

</details>

**중간 확인**

```bash
./gradlew :microservices:product-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `recommendation-service`

메시지를 받아 생성·삭제를 처리하는 `MessageProcessorConfig`(`Consumer<Event>` 빈)를 추가하고, 서비스 구현과 테스트를 리액티브로 바꿉니다. `application.yml`에 Spring Cloud Stream 바인딩, RabbitMQ·Kafka 설정이 추가됩니다.

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -15,6 +15,7 @@
 
 ext {
     mapstructVersion = '1.6.3'
+    springCloudVersion = '2025.1.4'
 }
 
 repositories {
@@ -30,7 +31,9 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
-    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'
+    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
+    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
+    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
 
     compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
@@ -43,7 +46,7 @@
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
-    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
 
@@ -52,6 +55,12 @@
     testImplementation 'org.testcontainers:testcontainers-mongodb'
 }
 
+dependencyManagement {
+    imports {
+        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
+    }
+}
+
 tasks.named('test') {
     useJUnitPlatform()
 }
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
    implementation "org.mapstruct:mapstruct:${mapstructVersion}"

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

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -10,10 +10,10 @@
 import org.springframework.context.event.ContextRefreshedEvent;
 import org.springframework.context.event.EventListener;
 import org.springframework.data.mapping.context.MappingContext;
-import org.springframework.data.mongodb.core.MongoOperations;
-import org.springframework.data.mongodb.core.index.IndexOperations;
+import org.springframework.data.mongodb.core.ReactiveMongoOperations;
 import org.springframework.data.mongodb.core.index.IndexResolver;
 import org.springframework.data.mongodb.core.index.MongoPersistentEntityIndexResolver;
+import org.springframework.data.mongodb.core.index.ReactiveIndexOperations;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentEntity;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentProperty;
 import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
@@ -33,7 +33,7 @@
   }
 
   @Autowired
-  MongoOperations mongoTemplate;
+  ReactiveMongoOperations mongoTemplate;
 
   @EventListener(ContextRefreshedEvent.class)
   public void initIndicesAfterStartup() {
@@ -41,7 +41,7 @@
     MappingContext<? extends MongoPersistentEntity<?>, MongoPersistentProperty> mappingContext = mongoTemplate.getConverter().getMappingContext();
     IndexResolver resolver = new MongoPersistentEntityIndexResolver(mappingContext);
 
-    IndexOperations indexOps = mongoTemplate.indexOps(RecommendationEntity.class);
-    resolver.resolveIndexFor(RecommendationEntity.class).forEach(e -> indexOps.createIndex(e));
+    ReactiveIndexOperations indexOps = mongoTemplate.indexOps(RecommendationEntity.class);
+    resolver.resolveIndexFor(RecommendationEntity.class).forEach(e -> indexOps.createIndex(e).block());
   }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;

@SpringBootApplication
@ComponentScan("se.magnus")
public class RecommendationServiceApplication {

  private static final Logger LOG = LoggerFactory.getLogger(RecommendationServiceApplication.class);

  public static void main(String[] args) {
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

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/persistence/RecommendationEntity.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,4 +1,6 @@
 package se.magnus.microservices.core.recommendation.persistence;
+
+import static java.lang.String.format;
 
 import org.springframework.data.annotation.Id;
 import org.springframework.data.annotation.Version;
@@ -30,6 +32,11 @@
     this.author = author;
     this.rating = rating;
     this.content = content;
+  }
+
+  @Override
+  public String toString() {
+    return format("RecommendationEntity: %s/%d", productId, recommendationId);
   }
 
   public String getId() {
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/persistence/RecommendationEntity.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.persistence;

import static java.lang.String.format;

import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Version;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import org.springframework.data.mongodb.core.mapping.Document;

@Document(collection = "recommendations")
@CompoundIndex(name = "prod-rec-id", unique = true, def = "{'productId': 1, 'recommendationId' : 1}")
public class RecommendationEntity {

  @Id
  private String id;

  @Version
  private Integer version;

  private int productId;
  private int recommendationId;
  private String author;
  private int rating;
  private String content;

  public RecommendationEntity() {
  }

  public RecommendationEntity(int productId, int recommendationId, String author, int rating, String content) {
    this.productId = productId;
    this.recommendationId = recommendationId;
    this.author = author;
    this.rating = rating;
    this.content = content;
  }

  @Override
  public String toString() {
    return format("RecommendationEntity: %s/%d", productId, recommendationId);
  }

  public String getId() {
    return id;
  }

  public Integer getVersion() {
    return version;
  }

  public int getProductId() {
    return productId;
  }

  public int getRecommendationId() {
    return recommendationId;
  }

  public String getAuthor() {
    return author;
  }

  public int getRating() {
    return rating;
  }

  public String getContent() {
    return content;
  }

  public void setId(String id) {
    this.id = id;
  }

  public void setVersion(Integer version) {
    this.version = version;
  }

  public void setProductId(int productId) {
    this.productId = productId;
  }

  public void setRecommendationId(int recommendationId) {
    this.recommendationId = recommendationId;
  }

  public void setAuthor(String author) {
    this.author = author;
  }

  public void setRating(int rating) {
    this.rating = rating;
  }

  public void setContent(String content) {
    this.content = content;
  }
}
```

</details>

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/persistence/RecommendationRepository.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/persistence/RecommendationRepository.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.persistence;

import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import reactor.core.publisher.Flux;

public interface RecommendationRepository extends ReactiveCrudRepository<RecommendationEntity, String> {
  Flux<RecommendationEntity> findByProductId(int productId);
}
```

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/MessageProcessorConfig.java` — 새 파일 (53줄)

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/MessageProcessorConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.services;

import java.util.function.Consumer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.recommendation.RecommendationService;
import se.magnus.api.event.Event;
import se.magnus.api.exceptions.EventProcessingException;

@Configuration
public class MessageProcessorConfig {

  private static final Logger LOG = LoggerFactory.getLogger(MessageProcessorConfig.class);

  private final RecommendationService recommendationService;

  public MessageProcessorConfig(RecommendationService recommendationService) {
    this.recommendationService = recommendationService;
  }

  @Bean
  public Consumer<Event<Integer, Recommendation>> messageProcessor() {
    return event -> {

      LOG.info("Process message created at {}...", event.getEventCreatedAt());

      switch (event.getEventType()) {

        case CREATE:
          Recommendation recommendation = event.getData();
          LOG.info("Create recommendation with ID: {}/{}", recommendation.getProductId(), recommendation.getRecommendationId());
          recommendationService.createRecommendation(recommendation).block();
          break;

        case DELETE:
          int productId = event.getKey();
          LOG.info("Delete recommendations with ProductID: {}", productId);
          recommendationService.deleteRecommendations(productId).block();
          break;

        default:
          String errorMessage = "Incorrect event type: " + event.getEventType() + ", expected a CREATE or DELETE event";
          LOG.warn(errorMessage);
          throw new EventProcessingException(errorMessage);
      }

      LOG.info("Message processing done!");
    };
  }
}
```

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationServiceImpl.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.services;

import static java.util.logging.Level.FINE;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.recommendation.RecommendationService;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;
import se.magnus.util.http.ServiceUtil;

@RestController
public class RecommendationServiceImpl implements RecommendationService {

  private static final Logger LOG = LoggerFactory.getLogger(RecommendationServiceImpl.class);

  private final RecommendationRepository repository;

  private final RecommendationMapper mapper;

  private final ServiceUtil serviceUtil;

  public RecommendationServiceImpl(RecommendationRepository repository, RecommendationMapper mapper, ServiceUtil serviceUtil) {
    this.repository = repository;
    this.mapper = mapper;
    this.serviceUtil = serviceUtil;
  }

  @Override
  public Mono<Recommendation> createRecommendation(Recommendation body) {

    if (body.getProductId() < 1) {
      throw new InvalidInputException("Invalid productId: " + body.getProductId());
    }

    RecommendationEntity entity = mapper.apiToEntity(body);
    Mono<Recommendation> newEntity = repository.save(entity)
      .log(LOG.getName(), FINE)
      .onErrorMap(
        DuplicateKeyException.class,
        ex -> new InvalidInputException("Duplicate key, Product Id: " + body.getProductId() + ", Recommendation Id:" + body.getRecommendationId()))
      .map(e -> mapper.entityToApi(e));

    return newEntity;
  }

  @Override
  public Flux<Recommendation> getRecommendations(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    LOG.info("Will get recommendations for product with id={}", productId);

    return repository.findByProductId(productId)
      .log(LOG.getName(), FINE)
      .map(e -> mapper.entityToApi(e))
      .map(e -> setServiceAddress(e));
  }

  @Override
  public Mono<Void> deleteRecommendations(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    LOG.debug("deleteRecommendations: tries to delete recommendations for the product with productId: {}", productId);
    return repository.deleteAll(repository.findByProductId(productId));
  }

  private Recommendation setServiceAddress(Recommendation e) {
    e.setServiceAddress(serviceUtil.getServiceAddress());
    return e;
  }
}
```

#### `microservices/recommendation-service/src/main/resources/application.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7003
spring.web.error.include-message: always

spring.mongodb:
  host: localhost
  port: 27017
  database: recommendation-db

spring.cloud.function.definition: messageProcessor

spring.cloud.stream:
  defaultBinder: rabbit
  default.contentType: application/json
  bindings.messageProcessor-in-0:
    destination: recommendations
    group: recommendationsGroup

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

spring.cloud.stream.kafka.binder:
  brokers: 127.0.0.1
  defaultBrokerPort: 9092

spring.rabbitmq:
  host: 127.0.0.1
  port: 5672
  username: guest
  password: guest

logging:
  level:
    root: INFO
    se.magnus: DEBUG
    org.springframework.data.mongodb.core.ReactiveMongoTemplate: DEBUG

management.endpoint.health.show-details: "ALWAYS"
management.endpoints.web.exposure.include: "*"
---
spring.config.activate.on-profile: docker

server.port: 8080

spring.mongodb.host: mongodb

spring.rabbitmq.host: rabbitmq

spring.cloud.stream.kafka.binder.brokers: kafka

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

management.health.rabbit.enabled: false
spring.cloud.stream.defaultBinder: kafka
spring.kafka.bootstrap-servers: kafka:9092
spring.cloud.stream.kafka.binder.replication-factor: 1
```

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/PersistenceTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -24,10 +24,10 @@
 
   @BeforeEach
   void setupDb() {
-    repository.deleteAll();
+    repository.deleteAll().block();
 
     RecommendationEntity entity = new RecommendationEntity(1, 2, "a", 3, "c");
-    savedEntity = repository.save(entity);
+    savedEntity = repository.save(entity).block();
 
     assertEqualsRecommendation(entity, savedEntity);
   }
@@ -37,33 +37,33 @@
   void create() {
 
     RecommendationEntity newEntity = new RecommendationEntity(1, 3, "a", 3, "c");
-    repository.save(newEntity);
+    repository.save(newEntity).block();
 
-    RecommendationEntity foundEntity = repository.findById(newEntity.getId()).get();
+    RecommendationEntity foundEntity = repository.findById(newEntity.getId()).block();
     assertEqualsRecommendation(newEntity, foundEntity);
 
-    assertEquals(2, repository.count());
+    assertEquals(2, (long)repository.count().block());
   }
 
   @Test
   void update() {
     savedEntity.setAuthor("a2");
-    repository.save(savedEntity);
+    repository.save(savedEntity).block();
 
-    RecommendationEntity foundEntity = repository.findById(savedEntity.getId()).get();
+    RecommendationEntity foundEntity = repository.findById(savedEntity.getId()).block();
     assertEquals(1, (long)foundEntity.getVersion());
     assertEquals("a2", foundEntity.getAuthor());
   }
 
   @Test
   void delete() {
-    repository.delete(savedEntity);
-    assertFalse(repository.existsById(savedEntity.getId()));
+    repository.delete(savedEntity).block();
+    assertFalse(repository.existsById(savedEntity.getId()).block());
   }
 
   @Test
   void getByProductId() {
-    List<RecommendationEntity> entityList = repository.findByProductId(savedEntity.getProductId());
+    List<RecommendationEntity> entityList = repository.findByProductId(savedEntity.getProductId()).collectList().block();
 
     assertThat(entityList, hasSize(1));
     assertEqualsRecommendation(savedEntity, entityList.get(0));
@@ -73,7 +73,7 @@
   void duplicateError() {
     assertThrows(DuplicateKeyException.class, () -> {
       RecommendationEntity entity = new RecommendationEntity(1, 2, "a", 3, "c");
-      repository.save(entity);
+      repository.save(entity).block();
     });
   }
 
@@ -81,22 +81,22 @@
   void optimisticLockError() {
 
     // Store the saved entity in two separate entity objects
-    RecommendationEntity entity1 = repository.findById(savedEntity.getId()).get();
-    RecommendationEntity entity2 = repository.findById(savedEntity.getId()).get();
+    RecommendationEntity entity1 = repository.findById(savedEntity.getId()).block();
+    RecommendationEntity entity2 = repository.findById(savedEntity.getId()).block();
 
     // Update the entity using the first entity object
     entity1.setAuthor("a1");
-    repository.save(entity1);
+    repository.save(entity1).block();
 
     //  Update the entity using the second entity object.
     // This should fail since the second entity now holds an old version number, i.e. an Optimistic Lock Error
     assertThrows(OptimisticLockingFailureException.class, () -> {
       entity2.setAuthor("a2");
-      repository.save(entity2);
+      repository.save(entity2).block();
     });
 
     // Get the updated entity from the database and verify its new sate
-    RecommendationEntity updatedEntity = repository.findById(savedEntity.getId()).get();
+    RecommendationEntity updatedEntity = repository.findById(savedEntity.getId()).block();
     assertEquals(1, (int)updatedEntity.getVersion());
     assertEquals("a1", updatedEntity.getAuthor());
   }
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
@@ -1,19 +1,24 @@
 package se.magnus.microservices.core.recommendation;
 
-import static org.junit.jupiter.api.Assertions.assertEquals;
+import static org.junit.jupiter.api.Assertions.*;
 import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
 import static org.springframework.http.HttpStatus.*;
 import static org.springframework.http.MediaType.APPLICATION_JSON;
-import static reactor.core.publisher.Mono.just;
+import static se.magnus.api.event.Event.Type.CREATE;
+import static se.magnus.api.event.Event.Type.DELETE;
 
+import java.util.function.Consumer;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
 import org.springframework.beans.factory.annotation.Autowired;
+import org.springframework.beans.factory.annotation.Qualifier;
 import org.springframework.boot.test.context.SpringBootTest;
 import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
 import org.springframework.http.HttpStatus;
 import org.springframework.test.web.reactive.server.WebTestClient;
 import se.magnus.api.core.recommendation.Recommendation;
+import se.magnus.api.event.Event;
+import se.magnus.api.exceptions.InvalidInputException;
 import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;
 
 @AutoConfigureWebTestClient
@@ -26,21 +31,25 @@
   @Autowired
   private RecommendationRepository repository;
 
+  @Autowired
+  @Qualifier("messageProcessor")
+  private Consumer<Event<Integer, Recommendation>> messageProcessor;
+
   @BeforeEach
   void setupDb() {
-    repository.deleteAll();
+    repository.deleteAll().block();
   }
-  
+
   @Test
   void getRecommendationsByProductId() {
 
     int productId = 1;
 
-    postAndVerifyRecommendation(productId, 1, OK);
-    postAndVerifyRecommendation(productId, 2, OK);
-    postAndVerifyRecommendation(productId, 3, OK);
+    sendCreateRecommendationEvent(productId, 1);
+    sendCreateRecommendationEvent(productId, 2);
+    sendCreateRecommendationEvent(productId, 3);
 
-    assertEquals(3, repository.findByProductId(productId).size());
+    assertEquals(3, (long)repository.findByProductId(productId).count().block());
 
     getAndVerifyRecommendationsByProductId(productId, OK)
       .jsonPath("$.length()").isEqualTo(3)
@@ -54,17 +63,17 @@
     int productId = 1;
     int recommendationId = 1;
 
-    postAndVerifyRecommendation(productId, recommendationId, OK)
-      .jsonPath("$.productId").isEqualTo(productId)
-      .jsonPath("$.recommendationId").isEqualTo(recommendationId);
+    sendCreateRecommendationEvent(productId, recommendationId);
 
-    assertEquals(1, repository.count());
+    assertEquals(1, (long)repository.count().block());
 
-    postAndVerifyRecommendation(productId, recommendationId, UNPROCESSABLE_CONTENT)
-      .jsonPath("$.path").isEqualTo("/recommendation")
-      .jsonPath("$.message").isEqualTo("Duplicate key, Product Id: 1, Recommendation Id:1");
+    InvalidInputException thrown = assertThrows(
+      InvalidInputException.class,
+      () -> sendCreateRecommendationEvent(productId, recommendationId),
+      "Expected a InvalidInputException here!");
+    assertEquals("Duplicate key, Product Id: 1, Recommendation Id:1", thrown.getMessage());
 
-    assertEquals(1, repository.count());
+    assertEquals(1, (long)repository.count().block());
   }
 
   @Test
@@ -73,13 +82,13 @@
     int productId = 1;
     int recommendationId = 1;
 
-    postAndVerifyRecommendation(productId, recommendationId, OK);
-    assertEquals(1, repository.findByProductId(productId).size());
+    sendCreateRecommendationEvent(productId, recommendationId);
+    assertEquals(1, (long)repository.findByProductId(productId).count().block());
 
-    deleteAndVerifyRecommendationsByProductId(productId, OK);
-    assertEquals(0, repository.findByProductId(productId).size());
+    sendDeleteRecommendationEvent(productId);
+    assertEquals(0, (long)repository.findByProductId(productId).count().block());
 
-    deleteAndVerifyRecommendationsByProductId(productId, OK);
+    sendDeleteRecommendationEvent(productId);
   }
 
   @Test
@@ -129,25 +138,14 @@
       .expectBody();
   }
 
-  private WebTestClient.BodyContentSpec postAndVerifyRecommendation(int productId, int recommendationId, HttpStatus expectedStatus) {
+  private void sendCreateRecommendationEvent(int productId, int recommendationId) {
     Recommendation recommendation = new Recommendation(productId, recommendationId, "Author " + recommendationId, recommendationId, "Content " + recommendationId, "SA");
-    return client.post()
-      .uri("/recommendation")
-      .body(just(recommendation), Recommendation.class)
-      .accept(APPLICATION_JSON)
-      .exchange()
-      .expectStatus().isEqualTo(expectedStatus)
-      .expectHeader().contentType(APPLICATION_JSON)
-      .expectBody();
+    Event<Integer, Recommendation> event = new Event<>(CREATE, productId, recommendation);
+    messageProcessor.accept(event);
   }
 
-  private WebTestClient.BodyContentSpec deleteAndVerifyRecommendationsByProductId(int productId, HttpStatus expectedStatus) {
-    return client.delete()
-      .uri("/recommendation?productId=" + productId)
-      .accept(APPLICATION_JSON)
-      .exchange()
-      .expectStatus().isEqualTo(expectedStatus)
-      .expectBody();
+  private void sendDeleteRecommendationEvent(int productId) {
+    Event<Integer, Recommendation> event = new Event<>(DELETE, productId, null);
+    messageProcessor.accept(event);
   }
-    
 }
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

**중간 확인**

```bash
./gradlew :microservices:recommendation-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-6"></a>

## 단계 6. `review-service`

JPA는 블로킹이라 `jdbcScheduler`(애플리케이션 클래스에 정의)에서 실행하도록 감쌉니다. 메시지 처리용 `MessageProcessorConfig`도 추가합니다.

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -15,6 +15,7 @@
 
 ext {
     mapstructVersion = '1.6.3'
+    springCloudVersion = '2025.1.4'
 }
 
 repositories {
@@ -31,6 +32,8 @@
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
     implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
+    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
+    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
     implementation 'com.mysql:mysql-connector-j'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
 
@@ -53,6 +56,12 @@
     testImplementation 'org.testcontainers:testcontainers-mysql'
 }
 
+dependencyManagement {
+    imports {
+        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
+    }
+}
+
 tasks.named('test') {
     useJUnitPlatform()
 }
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
    implementation 'com.mysql:mysql-connector-j'
    implementation "org.mapstruct:mapstruct:${mapstructVersion}"

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

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -2,16 +2,37 @@
 
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
+import org.springframework.beans.factory.annotation.Value;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
 import org.springframework.context.ConfigurableApplicationContext;
+import org.springframework.context.annotation.Bean;
 import org.springframework.context.annotation.ComponentScan;
+import reactor.core.scheduler.Scheduler;
+import reactor.core.scheduler.Schedulers;
 
 @SpringBootApplication
 @ComponentScan("se.magnus")
 public class ReviewServiceApplication {
 
   private static final Logger LOG = LoggerFactory.getLogger(ReviewServiceApplication.class);
+
+  private final Integer threadPoolSize;
+  private final Integer taskQueueSize;
+
+  public ReviewServiceApplication(
+    @Value("${app.threadPoolSize:10}") Integer threadPoolSize,
+    @Value("${app.taskQueueSize:100}") Integer taskQueueSize
+  ) {
+    this.threadPoolSize = threadPoolSize;
+    this.taskQueueSize = taskQueueSize;
+  }
+
+  @Bean
+  public Scheduler jdbcScheduler() {
+    LOG.info("Creates a jdbcScheduler with thread pool size = {}", threadPoolSize);
+    return Schedulers.newBoundedElastic(threadPoolSize, taskQueueSize, "jdbc-pool");
+  }
 
   public static void main(String[] args) {
     ConfigurableApplicationContext ctx = SpringApplication.run(ReviewServiceApplication.class, args);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;

@SpringBootApplication
@ComponentScan("se.magnus")
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
    ConfigurableApplicationContext ctx = SpringApplication.run(ReviewServiceApplication.class, args);

    String mysqlUri = ctx.getEnvironment().getProperty("spring.datasource.url");
    LOG.info("Connected to MySQL: " + mysqlUri);
  }
}
```

</details>

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/persistence/ReviewEntity.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,4 +1,6 @@
 package se.magnus.microservices.core.review.persistence;
+
+import static java.lang.String.format;
 
 import jakarta.persistence.*;
 
@@ -27,6 +29,11 @@
     this.author = author;
     this.subject = subject;
     this.content = content;
+  }
+
+  @Override
+  public String toString() {
+    return format("ReviewEntity: %s/%d", productId, reviewId);
   }
 
   public int getId() {
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/persistence/ReviewEntity.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review.persistence;

import static java.lang.String.format;

import jakarta.persistence.*;

@Entity
@Table(name = "reviews", indexes = { @Index(name = "reviews_unique_idx", unique = true, columnList = "productId,reviewId") })
public class ReviewEntity {

  @Id @GeneratedValue
  private int id;

  @Version
  private int version;

  private int productId;
  private int reviewId;
  private String author;
  private String subject;
  private String content;

  public ReviewEntity() {
  }

  public ReviewEntity(int productId, int reviewId, String author, String subject, String content) {
    this.productId = productId;
    this.reviewId = reviewId;
    this.author = author;
    this.subject = subject;
    this.content = content;
  }

  @Override
  public String toString() {
    return format("ReviewEntity: %s/%d", productId, reviewId);
  }

  public int getId() {
    return id;
  }

  public void setId(int id) {
    this.id = id;
  }

  public int getVersion() {
    return version;
  }

  public void setVersion(int version) {
    this.version = version;
  }

  public int getProductId() {
    return productId;
  }

  public void setProductId(int productId) {
    this.productId = productId;
  }

  public int getReviewId() {
    return reviewId;
  }

  public void setReviewId(int reviewId) {
    this.reviewId = reviewId;
  }

  public String getAuthor() {
    return author;
  }

  public void setAuthor(String author) {
    this.author = author;
  }

  public String getSubject() {
    return subject;
  }

  public void setSubject(String subject) {
    this.subject = subject;
  }

  public String getContent() {
    return content;
  }

  public void setContent(String content) {
    this.content = content;
  }
}
```

</details>

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/MessageProcessorConfig.java` — 새 파일 (52줄)

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/MessageProcessorConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review.services;

import java.util.function.Consumer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import se.magnus.api.core.review.Review;
import se.magnus.api.core.review.ReviewService;
import se.magnus.api.event.Event;
import se.magnus.api.exceptions.EventProcessingException;

@Configuration
public class MessageProcessorConfig {

  private static final Logger LOG = LoggerFactory.getLogger(MessageProcessorConfig.class);

  private final ReviewService reviewService;

  public MessageProcessorConfig(ReviewService reviewService) {
    this.reviewService = reviewService;
  }

  @Bean
  public Consumer<Event<Integer, Review>> messageProcessor() {
    return event -> {
      LOG.info("Process message created at {}...", event.getEventCreatedAt());

      switch (event.getEventType()) {

        case CREATE:
          Review review = event.getData();
          LOG.info("Create review with ID: {}/{}", review.getProductId(), review.getReviewId());
          reviewService.createReview(review).block();
          break;

        case DELETE:
          int productId = event.getKey();
          LOG.info("Delete reviews with ProductID: {}", productId);
          reviewService.deleteReviews(productId).block();
          break;

        default:
          String errorMessage = "Incorrect event type: " + event.getEventType() + ", expected a CREATE or DELETE event";
          LOG.warn(errorMessage);
          throw new EventProcessingException(errorMessage);
      }

      LOG.info("Message processing done!");
    };
  }
}
```

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewServiceImpl.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,10 +1,16 @@
 package se.magnus.microservices.core.review.services;
+
+import static java.util.logging.Level.FINE;
 
 import java.util.List;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
+import org.springframework.beans.factory.annotation.Qualifier;
 import org.springframework.dao.DataIntegrityViolationException;
 import org.springframework.web.bind.annotation.RestController;
+import reactor.core.publisher.Flux;
+import reactor.core.publisher.Mono;
+import reactor.core.scheduler.Scheduler;
 import se.magnus.api.core.review.Review;
 import se.magnus.api.core.review.ReviewService;
 import se.magnus.api.exceptions.InvalidInputException;
@@ -23,14 +29,26 @@
 
   private final ServiceUtil serviceUtil;
 
-  public ReviewServiceImpl(ReviewRepository repository, ReviewMapper mapper, ServiceUtil serviceUtil) {
+  private final Scheduler jdbcScheduler;
+
+  public ReviewServiceImpl(@Qualifier("jdbcScheduler") Scheduler jdbcScheduler, ReviewRepository repository, ReviewMapper mapper, ServiceUtil serviceUtil) {
+    this.jdbcScheduler = jdbcScheduler;
     this.repository = repository;
     this.mapper = mapper;
     this.serviceUtil = serviceUtil;
   }
 
   @Override
-  public Review createReview(Review body) {
+  public Mono<Review> createReview(Review body) {
+
+    if (body.getProductId() < 1) {
+      throw new InvalidInputException("Invalid productId: " + body.getProductId());
+    }
+    return Mono.fromCallable(() -> internalCreateReview(body))
+      .subscribeOn(jdbcScheduler);
+  }
+
+  private Review internalCreateReview(Review body) {
     try {
       ReviewEntity entity = mapper.apiToEntity(body);
       ReviewEntity newEntity = repository.save(entity);
@@ -44,24 +62,45 @@
   }
 
   @Override
-  public List<Review> getReviews(int productId) {
+  public Flux<Review> getReviews(int productId) {
 
     if (productId < 1) {
       throw new InvalidInputException("Invalid productId: " + productId);
     }
-    
+
+    LOG.info("Will get reviews for product with id={}", productId);
+
+    return Mono.fromCallable(() -> internalGetReviews(productId))
+      .flatMapMany(Flux::fromIterable)
+      .log(LOG.getName(), FINE)
+      .subscribeOn(jdbcScheduler);
+  }
+
+  private List<Review> internalGetReviews(int productId) {
+
     List<ReviewEntity> entityList = repository.findByProductId(productId);
     List<Review> list = mapper.entityListToApiList(entityList);
     list.forEach(e -> e.setServiceAddress(serviceUtil.getServiceAddress()));
 
-    LOG.debug("getReviews: response size: {}", list.size());
+    LOG.debug("Response size: {}", list.size());
 
     return list;
   }
 
   @Override
-  public void deleteReviews(int productId) {
+  public Mono<Void> deleteReviews(int productId) {
+
+    if (productId < 1) {
+      throw new InvalidInputException("Invalid productId: " + productId);
+    }
+
+    return Mono.fromRunnable(() -> internalDeleteReviews(productId)).subscribeOn(jdbcScheduler).then();
+  }
+
+  private void internalDeleteReviews(int productId) {
+
     LOG.debug("deleteReviews: tries to delete reviews for the product with productId: {}", productId);
+
     repository.deleteAll(repository.findByProductId(productId));
   }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewServiceImpl.java" op="write" nl="0" -->
```java
package se.magnus.microservices.core.review.services;

import static java.util.logging.Level.FINE;

import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Scheduler;
import se.magnus.api.core.review.Review;
import se.magnus.api.core.review.ReviewService;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.microservices.core.review.persistence.ReviewEntity;
import se.magnus.microservices.core.review.persistence.ReviewRepository;
import se.magnus.util.http.ServiceUtil;

@RestController
public class ReviewServiceImpl implements ReviewService {

  private static final Logger LOG = LoggerFactory.getLogger(ReviewServiceImpl.class);

  private final ReviewRepository repository;

  private final ReviewMapper mapper;

  private final ServiceUtil serviceUtil;

  private final Scheduler jdbcScheduler;

  public ReviewServiceImpl(@Qualifier("jdbcScheduler") Scheduler jdbcScheduler, ReviewRepository repository, ReviewMapper mapper, ServiceUtil serviceUtil) {
    this.jdbcScheduler = jdbcScheduler;
    this.repository = repository;
    this.mapper = mapper;
    this.serviceUtil = serviceUtil;
  }

  @Override
  public Mono<Review> createReview(Review body) {

    if (body.getProductId() < 1) {
      throw new InvalidInputException("Invalid productId: " + body.getProductId());
    }
    return Mono.fromCallable(() -> internalCreateReview(body))
      .subscribeOn(jdbcScheduler);
  }

  private Review internalCreateReview(Review body) {
    try {
      ReviewEntity entity = mapper.apiToEntity(body);
      ReviewEntity newEntity = repository.save(entity);

      LOG.debug("createReview: created a review entity: {}/{}", body.getProductId(), body.getReviewId());
      return mapper.entityToApi(newEntity);

    } catch (DataIntegrityViolationException dive) {
      throw new InvalidInputException("Duplicate key, Product Id: " + body.getProductId() + ", Review Id:" + body.getReviewId());
    }
  }

  @Override
  public Flux<Review> getReviews(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    LOG.info("Will get reviews for product with id={}", productId);

    return Mono.fromCallable(() -> internalGetReviews(productId))
      .flatMapMany(Flux::fromIterable)
      .log(LOG.getName(), FINE)
      .subscribeOn(jdbcScheduler);
  }

  private List<Review> internalGetReviews(int productId) {

    List<ReviewEntity> entityList = repository.findByProductId(productId);
    List<Review> list = mapper.entityListToApiList(entityList);
    list.forEach(e -> e.setServiceAddress(serviceUtil.getServiceAddress()));

    LOG.debug("Response size: {}", list.size());

    return list;
  }

  @Override
  public Mono<Void> deleteReviews(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    return Mono.fromRunnable(() -> internalDeleteReviews(productId)).subscribeOn(jdbcScheduler).then();
  }

  private void internalDeleteReviews(int productId) {

    LOG.debug("deleteReviews: tries to delete reviews for the product with productId: {}", productId);

    repository.deleteAll(repository.findByProductId(productId));
  }
}
```

</details>

#### `microservices/review-service/src/main/resources/application.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/review-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7004
spring.web.error.include-message: always

# Strongly recommend to set this property to "none" in a production environment!
spring.jpa.hibernate.ddl-auto: update

spring.datasource:
  url: jdbc:mysql://localhost/review-db
  username: user
  password: pwd

spring.datasource.hikari.initializationFailTimeout: 60000

spring.cloud.function.definition: messageProcessor

spring.cloud.stream:
  defaultBinder: rabbit
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

spring.cloud.stream.kafka.binder:
  brokers: 127.0.0.1
  defaultBrokerPort: 9092

spring.rabbitmq:
  host: 127.0.0.1
  port: 5672
  username: guest
  password: guest

logging:
  level:
    root: INFO
    se.magnus: DEBUG
    org.hibernate.SQL: DEBUG
    org.hibernate.type.descriptor.sql.BasicBinder: TRACE

management.endpoint.health.show-details: "ALWAYS"
management.endpoints.web.exposure.include: "*"
---
spring.config.activate.on-profile: docker

server.port: 8080

spring.datasource.url: jdbc:mysql://mysql/review-db

spring.rabbitmq.host: rabbitmq

spring.cloud.stream.kafka.binder.brokers: kafka

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

management.health.rabbit.enabled: false
spring.cloud.stream.defaultBinder: kafka
spring.kafka.bootstrap-servers: kafka:9092
spring.cloud.stream.kafka.binder.replication-factor: 1
```

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,23 +1,30 @@
 package se.magnus.microservices.core.review;
 
-import static org.junit.jupiter.api.Assertions.assertEquals;
+import static org.junit.jupiter.api.Assertions.*;
 import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
 import static org.springframework.http.HttpStatus.*;
 import static org.springframework.http.MediaType.APPLICATION_JSON;
-import static reactor.core.publisher.Mono.just;
+import static se.magnus.api.event.Event.Type.CREATE;
+import static se.magnus.api.event.Event.Type.DELETE;
 
+import java.util.function.Consumer;
 import org.junit.jupiter.api.BeforeEach;
 import org.junit.jupiter.api.Test;
 import org.springframework.beans.factory.annotation.Autowired;
+import org.springframework.beans.factory.annotation.Qualifier;
 import org.springframework.boot.test.context.SpringBootTest;
 import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
 import org.springframework.http.HttpStatus;
 import org.springframework.test.web.reactive.server.WebTestClient;
 import se.magnus.api.core.review.Review;
+import se.magnus.api.event.Event;
+import se.magnus.api.exceptions.InvalidInputException;
 import se.magnus.microservices.core.review.persistence.ReviewRepository;
 
 @AutoConfigureWebTestClient
-@SpringBootTest(webEnvironment = RANDOM_PORT)
+@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
+  "spring.cloud.stream.defaultBinder=rabbit",
+  "logging.level.se.magnus=DEBUG"})
 class ReviewServiceApplicationTests extends MySqlTestBase {
 
   @Autowired
@@ -25,6 +32,10 @@
 
   @Autowired
   private ReviewRepository repository;
+
+  @Autowired
+  @Qualifier("messageProcessor")
+  private Consumer<Event<Integer, Review>> messageProcessor;
 
   @BeforeEach
   void setupDb() {
@@ -38,9 +49,9 @@
 
     assertEquals(0, repository.findByProductId(productId).size());
 
-    postAndVerifyReview(productId, 1, OK);
-    postAndVerifyReview(productId, 2, OK);
-    postAndVerifyReview(productId, 3, OK);
+    sendCreateReviewEvent(productId, 1);
+    sendCreateReviewEvent(productId, 2);
+    sendCreateReviewEvent(productId, 3);
 
     assertEquals(3, repository.findByProductId(productId).size());
 
@@ -58,15 +69,15 @@
 
     assertEquals(0, repository.count());
 
-    postAndVerifyReview(productId, reviewId, OK)
-      .jsonPath("$.productId").isEqualTo(productId)
-      .jsonPath("$.reviewId").isEqualTo(reviewId);
+    sendCreateReviewEvent(productId, reviewId);
 
     assertEquals(1, repository.count());
 
-    postAndVerifyReview(productId, reviewId, UNPROCESSABLE_CONTENT)
-      .jsonPath("$.path").isEqualTo("/review")
-      .jsonPath("$.message").isEqualTo("Duplicate key, Product Id: 1, Review Id:1");
+    InvalidInputException thrown = assertThrows(
+      InvalidInputException.class,
+      () -> sendCreateReviewEvent(productId, reviewId),
+      "Expected a InvalidInputException here!");
+    assertEquals("Duplicate key, Product Id: 1, Review Id:1", thrown.getMessage());
 
     assertEquals(1, repository.count());
   }
@@ -77,13 +88,13 @@
     int productId = 1;
     int reviewId = 1;
 
-    postAndVerifyReview(productId, reviewId, OK);
+    sendCreateReviewEvent(productId, reviewId);
     assertEquals(1, repository.findByProductId(productId).size());
 
-    deleteAndVerifyReviewsByProductId(productId, OK);
+    sendDeleteReviewEvent(productId);
     assertEquals(0, repository.findByProductId(productId).size());
 
-    deleteAndVerifyReviewsByProductId(productId, OK);
+    sendDeleteReviewEvent(productId);
   }
 
   @Test
@@ -133,24 +144,14 @@
       .expectBody();
   }
 
-  private WebTestClient.BodyContentSpec postAndVerifyReview(int productId, int reviewId, HttpStatus expectedStatus) {
+  private void sendCreateReviewEvent(int productId, int reviewId) {
     Review review = new Review(productId, reviewId, "Author " + reviewId, "Subject " + reviewId, "Content " + reviewId, "SA");
-    return client.post()
-      .uri("/review")
-      .body(just(review), Review.class)
-      .accept(APPLICATION_JSON)
-      .exchange()
-      .expectStatus().isEqualTo(expectedStatus)
-      .expectHeader().contentType(APPLICATION_JSON)
-      .expectBody();
+    Event<Integer, Review> event = new Event<>(CREATE, productId, review);
+    messageProcessor.accept(event);
   }
 
-  private WebTestClient.BodyContentSpec deleteAndVerifyReviewsByProductId(int productId, HttpStatus expectedStatus) {
-    return client.delete()
-      .uri("/review?productId=" + productId)
-      .accept(APPLICATION_JSON)
-      .exchange()
-      .expectStatus().isEqualTo(expectedStatus)
-      .expectBody();
+  private void sendDeleteReviewEvent(int productId) {
+    Event<Integer, Review> event = new Event<>(DELETE, productId, null);
+    messageProcessor.accept(event);
   }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java" op="write" nl="0" -->
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

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
  "spring.cloud.stream.defaultBinder=rabbit",
  "logging.level.se.magnus=DEBUG"})
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

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-7"></a>

## 단계 7. `product-composite-service`

통합 클래스를 `WebClient`(조회)와 `StreamBridge`(생성·삭제 이벤트 전송)로 다시 씁니다. 핵심 서비스 상태를 모으는 `HealthCheckConfiguration`과, 보낸 메시지를 확인하는 `MessagingTests`·`IsSameEvent` 테스트가 추가됩니다.

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -13,6 +13,9 @@
     }
 }
 
+ext {
+    springCloudVersion = '2025.1.4'
+}
 repositories {
     mavenCentral()
 }
@@ -26,6 +29,9 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+    implementation 'org.springframework.boot:spring-boot-starter-webclient'
+    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
+    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
     implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:3.0.3'
 
     // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
@@ -34,8 +40,14 @@
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
+    testImplementation 'org.springframework.cloud:spring-cloud-stream-test-binder'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
+}
+dependencyManagement {
+    imports {
+        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
+    }
 }
 
 tasks.named('test') {
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
    implementation 'org.springframework.boot:spring-boot-starter-webclient'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:3.0.3'

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
    }
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/HealthCheckConfiguration.java` — 새 파일 (30줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/HealthCheckConfiguration.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.health.contributor.CompositeReactiveHealthContributor;
import org.springframework.boot.health.contributor.ReactiveHealthContributor;
import org.springframework.boot.health.contributor.ReactiveHealthIndicator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import se.magnus.microservices.composite.product.services.ProductCompositeIntegration;

@Configuration
public class HealthCheckConfiguration {

  @Autowired
  ProductCompositeIntegration integration;

  @Bean
  ReactiveHealthContributor coreServices() {

    final Map<String, ReactiveHealthIndicator> registry = new LinkedHashMap<>();

    registry.put("product", () -> integration.getProductHealth());
    registry.put("recommendation", () -> integration.getRecommendationHealth());
    registry.put("review", () -> integration.getReviewHealth());

    return CompositeReactiveHealthContributor.fromMap(registry);
  }
}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -5,16 +5,21 @@
 import io.swagger.v3.oas.models.info.Contact;
 import io.swagger.v3.oas.models.info.Info;
 import io.swagger.v3.oas.models.info.License;
+import org.slf4j.Logger;
+import org.slf4j.LoggerFactory;
 import org.springframework.beans.factory.annotation.Value;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
 import org.springframework.context.annotation.Bean;
 import org.springframework.context.annotation.ComponentScan;
-import org.springframework.web.client.RestTemplate;
+import reactor.core.scheduler.Scheduler;
+import reactor.core.scheduler.Schedulers;
 
 @SpringBootApplication
 @ComponentScan("se.magnus")
 public class ProductCompositeServiceApplication {
+
+  private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeServiceApplication.class);
 
   @Value("${api.common.version}")         String apiVersion;
   @Value("${api.common.title}")           String apiTitle;
@@ -52,9 +57,21 @@
         .url(apiExternalDocUrl));
   }
 
+  private final Integer threadPoolSize;
+  private final Integer taskQueueSize;
+
+  public ProductCompositeServiceApplication(
+    @Value("${app.threadPoolSize:10}") Integer threadPoolSize,
+    @Value("${app.taskQueueSize:100}") Integer taskQueueSize
+  ) {
+    this.threadPoolSize = threadPoolSize;
+    this.taskQueueSize = taskQueueSize;
+  }
+
   @Bean
-  RestTemplate restTemplate() {
-    return new RestTemplate();
+  public Scheduler publishEventScheduler() {
+    LOG.info("Creates a messagingScheduler with connectionPoolSize = {}", threadPoolSize);
+    return Schedulers.newBoundedElastic(threadPoolSize, taskQueueSize, "publish-pool");
   }
 
   public static void main(String[] args) {
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
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;

@SpringBootApplication
@ComponentScan("se.magnus")
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

  public static void main(String[] args) {
    SpringApplication.run(ProductCompositeServiceApplication.class, args);
  }

}
```

</details>

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java" op="write" nl="0" -->
```java
package se.magnus.microservices.composite.product.services;

import static java.util.logging.Level.FINE;
import static reactor.core.publisher.Flux.empty;
import static se.magnus.api.event.Event.Type.CREATE;
import static se.magnus.api.event.Event.Type.DELETE;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.health.contributor.Health;
import org.springframework.cloud.stream.function.StreamBridge;
import org.springframework.http.HttpStatus;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Scheduler;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.product.ProductService;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.recommendation.RecommendationService;
import se.magnus.api.core.review.Review;
import se.magnus.api.core.review.ReviewService;
import se.magnus.api.event.Event;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.api.exceptions.NotFoundException;
import se.magnus.util.http.HttpErrorInfo;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

@Component
public class ProductCompositeIntegration implements ProductService, RecommendationService, ReviewService {

  private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeIntegration.class);

  private final WebClient webClient;
  private final ObjectMapper mapper;

  private final String productServiceUrl;
  private final String recommendationServiceUrl;
  private final String reviewServiceUrl;

  private final StreamBridge streamBridge;

  private final Scheduler publishEventScheduler;

  public ProductCompositeIntegration(
    @Qualifier("publishEventScheduler") Scheduler publishEventScheduler,

    WebClient.Builder webClient,
    ObjectMapper mapper,
    StreamBridge streamBridge,

    @Value("${app.product-service.host}") String productServiceHost,
    @Value("${app.product-service.port}") int  productServicePort,

    @Value("${app.recommendation-service.host}") String recommendationServiceHost,
    @Value("${app.recommendation-service.port}") int  recommendationServicePort,

    @Value("${app.review-service.host}") String reviewServiceHost,
    @Value("${app.review-service.port}") int  reviewServicePort
  ) {

    this.publishEventScheduler = publishEventScheduler;
    this.webClient = webClient.build();
    this.mapper = mapper;
    this.streamBridge = streamBridge;

    productServiceUrl        = "http://" + productServiceHost + ":" + productServicePort;
    recommendationServiceUrl = "http://" + recommendationServiceHost + ":" + recommendationServicePort;
    reviewServiceUrl         = "http://" + reviewServiceHost + ":" + reviewServicePort;
  }

  @Override
  public Mono<Product> createProduct(Product body) {

    return Mono.fromCallable(() -> {
      sendMessage("products-out-0", new Event<>(CREATE, body.getProductId(), body));
      return body;
    }).subscribeOn(publishEventScheduler);
  }

  @Override
  public Mono<Product> getProduct(int productId) {
    String url = productServiceUrl + "/product/" + productId;
    LOG.debug("Will call the getProduct API on URL: {}", url);

    return webClient.get().uri(url).retrieve().bodyToMono(Product.class).log(LOG.getName(), FINE).onErrorMap(WebClientResponseException.class, ex -> handleException(ex));
  }

  @Override
  public Mono<Void> deleteProduct(int productId) {

    return Mono.fromRunnable(() -> sendMessage("products-out-0", new Event<>(DELETE, productId, null)))
      .subscribeOn(publishEventScheduler).then();
  }

  @Override
  public Mono<Recommendation> createRecommendation(Recommendation body) {

    return Mono.fromCallable(() -> {
      sendMessage("recommendations-out-0", new Event<>(CREATE, body.getProductId(), body));
      return body;
    }).subscribeOn(publishEventScheduler);
  }

  @Override
  public Flux<Recommendation> getRecommendations(int productId) {

    String url = recommendationServiceUrl + "/recommendation?productId=" + productId;

    LOG.debug("Will call the getRecommendations API on URL: {}", url);

    // Return an empty result if something goes wrong to make it possible for the composite service to return partial responses
    return webClient.get().uri(url).retrieve().bodyToFlux(Recommendation.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
  }

  @Override
  public Mono<Void> deleteRecommendations(int productId) {

    return Mono.fromRunnable(() -> sendMessage("recommendations-out-0", new Event<>(DELETE, productId, null)))
      .subscribeOn(publishEventScheduler).then();
  }

  @Override
  public Mono<Review> createReview(Review body) {

    return Mono.fromCallable(() -> {
      sendMessage("reviews-out-0", new Event<>(CREATE, body.getProductId(), body));
      return body;
    }).subscribeOn(publishEventScheduler);
  }

  @Override
  public Flux<Review> getReviews(int productId) {

    String url = reviewServiceUrl + "/review?productId=" + productId;

    LOG.debug("Will call the getReviews API on URL: {}", url);

    // Return an empty result if something goes wrong to make it possible for the composite service to return partial responses
    return webClient.get().uri(url).retrieve().bodyToFlux(Review.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
  }

  @Override
  public Mono<Void> deleteReviews(int productId) {

    return Mono.fromRunnable(() -> sendMessage("reviews-out-0", new Event<>(DELETE, productId, null)))
      .subscribeOn(publishEventScheduler).then();
  }

  public Mono<Health> getProductHealth() {
    return getHealth(productServiceUrl);
  }

  public Mono<Health> getRecommendationHealth() {
    return getHealth(recommendationServiceUrl);
  }

  public Mono<Health> getReviewHealth() {
    return getHealth(reviewServiceUrl);
  }

  private Mono<Health> getHealth(String url) {
    url += "/actuator/health";
    LOG.debug("Will call the Health API on URL: {}", url);
    return webClient.get().uri(url).retrieve().bodyToMono(String.class)
      .map(s -> new Health.Builder().up().build())
      .onErrorResume(ex -> Mono.just(new Health.Builder().down(ex).build()))
      .log(LOG.getName(), FINE);
  }

  private void sendMessage(String bindingName, Event event) {
    LOG.debug("Sending a {} message to {}", event.getEventType(), bindingName);
    Message message = MessageBuilder.withPayload(event)
      .setHeader("partitionKey", event.getKey())
      .build();
    streamBridge.send(bindingName, message);
  }

  private Throwable handleException(Throwable ex) {

    if (!(ex instanceof WebClientResponseException)) {
      LOG.warn("Got a unexpected error: {}, will rethrow it", ex.toString());
      return ex;
    }

    WebClientResponseException wcre = (WebClientResponseException)ex;

    switch (HttpStatus.resolve(wcre.getStatusCode().value())) {

      case NOT_FOUND:
        return new NotFoundException(getErrorMessage(wcre));

      case UNPROCESSABLE_CONTENT:
        return new InvalidInputException(getErrorMessage(wcre));

      default:
        LOG.warn("Got an unexpected HTTP error: {}, will rethrow it", wcre.getStatusCode());
        LOG.warn("Error body: {}", wcre.getResponseBodyAsString());
        return ex;
    }
  }

  private String getErrorMessage(WebClientResponseException ex) {
    try {
      return mapper.readValue(ex.getResponseBodyAsString(), HttpErrorInfo.class).getMessage();
    } catch (JacksonException ioex) {
      return ex.getMessage();
    }
  }
}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeServiceImpl.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,15 +1,18 @@
 package se.magnus.microservices.composite.product.services;
 
+import static java.util.logging.Level.FINE;
+
+import java.util.ArrayList;
 import java.util.List;
 import java.util.stream.Collectors;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
 import org.springframework.web.bind.annotation.RestController;
+import reactor.core.publisher.Mono;
 import se.magnus.api.composite.product.*;
 import se.magnus.api.core.product.Product;
 import se.magnus.api.core.recommendation.Recommendation;
 import se.magnus.api.core.review.Review;
-import se.magnus.api.exceptions.NotFoundException;
 import se.magnus.util.http.ServiceUtil;
 
 @RestController
@@ -18,86 +21,87 @@
   private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeServiceImpl.class);
 
   private final ServiceUtil serviceUtil;
-  private ProductCompositeIntegration integration;
+  private final ProductCompositeIntegration integration;
 
-  public ProductCompositeServiceImpl(
-    ServiceUtil serviceUtil, ProductCompositeIntegration integration) {
-    
+  public ProductCompositeServiceImpl(ServiceUtil serviceUtil, ProductCompositeIntegration integration) {
     this.serviceUtil = serviceUtil;
     this.integration = integration;
   }
 
   @Override
-  public void createProduct(ProductAggregate body) {
+  public Mono<Void> createProduct(ProductAggregate body) {
 
     try {
 
-      LOG.debug("createCompositeProduct: creates a new composite entity for productId: {}", body.getProductId());
+      List<Mono> monoList = new ArrayList<>();
+
+      LOG.info("Will create a new composite entity for product.id: {}", body.getProductId());
 
       Product product = new Product(body.getProductId(), body.getName(), body.getWeight(), null);
-      integration.createProduct(product);
+      monoList.add(integration.createProduct(product));
 
       if (body.getRecommendations() != null) {
         body.getRecommendations().forEach(r -> {
           Recommendation recommendation = new Recommendation(body.getProductId(), r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent(), null);
-          integration.createRecommendation(recommendation);
+          monoList.add(integration.createRecommendation(recommendation));
         });
       }
 
       if (body.getReviews() != null) {
         body.getReviews().forEach(r -> {
           Review review = new Review(body.getProductId(), r.getReviewId(), r.getAuthor(), r.getSubject(), r.getContent(), null);
-          integration.createReview(review);
+          monoList.add(integration.createReview(review));
         });
       }
 
       LOG.debug("createCompositeProduct: composite entities created for productId: {}", body.getProductId());
 
+      return Mono.zip(r -> "", monoList.toArray(new Mono[0]))
+        .doOnError(ex -> LOG.warn("createCompositeProduct failed: {}", ex.toString()))
+        .then();
+
     } catch (RuntimeException re) {
-      LOG.warn("createCompositeProduct failed", re);
+      LOG.warn("createCompositeProduct failed: {}", re.toString());
       throw re;
     }
   }
 
+  @Override
+  @SuppressWarnings("unchecked")
+  public Mono<ProductAggregate> getProduct(int productId) {
 
-  @Override
-  public ProductAggregate getProduct(int productId) {
-
-    LOG.debug("getCompositeProduct: lookup a product aggregate for productId: {}", productId);
-
-    Product product = integration.getProduct(productId);
-    if (product == null) {
-      throw new NotFoundException("No product found for productId: " + productId);
-    }
-
-    List<Recommendation> recommendations = integration.getRecommendations(productId);
-
-    List<Review> reviews = integration.getReviews(productId);
-
-    LOG.debug("getCompositeProduct: aggregate entity found for productId: {}", productId);
-
-    return createProductAggregate(product, recommendations, reviews, serviceUtil.getServiceAddress());
+    LOG.info("Will get composite product info for product.id={}", productId);
+    return Mono.zip(
+      values -> createProductAggregate((Product) values[0], (List<Recommendation>) values[1], (List<Review>) values[2], serviceUtil.getServiceAddress()),
+      integration.getProduct(productId),
+      integration.getRecommendations(productId).collectList(),
+      integration.getReviews(productId).collectList())
+      .doOnError(ex -> LOG.warn("getCompositeProduct failed: {}", ex.toString()))
+      .log(LOG.getName(), FINE);
   }
 
   @Override
-  public void deleteProduct(int productId) {
+  public Mono<Void> deleteProduct(int productId) {
 
-    LOG.debug("deleteCompositeProduct: Deletes a product aggregate for productId: {}", productId);
+    try {
 
-    integration.deleteProduct(productId);
+      LOG.info("Will delete a product aggregate for product.id: {}", productId);
 
-    integration.deleteRecommendations(productId);
+      return Mono.zip(
+        r -> "",
+        integration.deleteProduct(productId),
+        integration.deleteRecommendations(productId),
+        integration.deleteReviews(productId))
+        .doOnError(ex -> LOG.warn("delete failed: {}", ex.toString()))
+        .log(LOG.getName(), FINE).then();
 
-    integration.deleteReviews(productId);
-
-    LOG.debug("deleteCompositeProduct: aggregate entities deleted for productId: {}", productId);
+    } catch (RuntimeException re) {
+      LOG.warn("deleteCompositeProduct failed: {}", re.toString());
+      throw re;
+    }
   }
 
-  private ProductAggregate createProductAggregate(
-    Product product,
-    List<Recommendation> recommendations,
-    List<Review> reviews,
-    String serviceAddress) {
+  private ProductAggregate createProductAggregate(Product product, List<Recommendation> recommendations, List<Review> reviews, String serviceAddress) {
 
     // 1. Setup product info
     int productId = product.getProductId();
@@ -106,12 +110,12 @@
 
     // 2. Copy summary recommendation info, if available
     List<RecommendationSummary> recommendationSummaries = (recommendations == null) ? null :
-      recommendations.stream()
+       recommendations.stream()
         .map(r -> new RecommendationSummary(r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent()))
         .collect(Collectors.toList());
 
     // 3. Copy summary review info, if available
-    List<ReviewSummary> reviewSummaries = (reviews == null) ? null :
+    List<ReviewSummary> reviewSummaries = (reviews == null)  ? null :
       reviews.stream()
         .map(r -> new ReviewSummary(r.getReviewId(), r.getAuthor(), r.getSubject(), r.getContent()))
         .collect(Collectors.toList());
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services;

import static java.util.logging.Level.FINE;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;
import se.magnus.api.composite.product.*;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.review.Review;
import se.magnus.util.http.ServiceUtil;

@RestController
public class ProductCompositeServiceImpl implements ProductCompositeService {

  private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeServiceImpl.class);

  private final ServiceUtil serviceUtil;
  private final ProductCompositeIntegration integration;

  public ProductCompositeServiceImpl(ServiceUtil serviceUtil, ProductCompositeIntegration integration) {
    this.serviceUtil = serviceUtil;
    this.integration = integration;
  }

  @Override
  public Mono<Void> createProduct(ProductAggregate body) {

    try {

      List<Mono> monoList = new ArrayList<>();

      LOG.info("Will create a new composite entity for product.id: {}", body.getProductId());

      Product product = new Product(body.getProductId(), body.getName(), body.getWeight(), null);
      monoList.add(integration.createProduct(product));

      if (body.getRecommendations() != null) {
        body.getRecommendations().forEach(r -> {
          Recommendation recommendation = new Recommendation(body.getProductId(), r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent(), null);
          monoList.add(integration.createRecommendation(recommendation));
        });
      }

      if (body.getReviews() != null) {
        body.getReviews().forEach(r -> {
          Review review = new Review(body.getProductId(), r.getReviewId(), r.getAuthor(), r.getSubject(), r.getContent(), null);
          monoList.add(integration.createReview(review));
        });
      }

      LOG.debug("createCompositeProduct: composite entities created for productId: {}", body.getProductId());

      return Mono.zip(r -> "", monoList.toArray(new Mono[0]))
        .doOnError(ex -> LOG.warn("createCompositeProduct failed: {}", ex.toString()))
        .then();

    } catch (RuntimeException re) {
      LOG.warn("createCompositeProduct failed: {}", re.toString());
      throw re;
    }
  }

  @Override
  @SuppressWarnings("unchecked")
  public Mono<ProductAggregate> getProduct(int productId) {

    LOG.info("Will get composite product info for product.id={}", productId);
    return Mono.zip(
      values -> createProductAggregate((Product) values[0], (List<Recommendation>) values[1], (List<Review>) values[2], serviceUtil.getServiceAddress()),
      integration.getProduct(productId),
      integration.getRecommendations(productId).collectList(),
      integration.getReviews(productId).collectList())
      .doOnError(ex -> LOG.warn("getCompositeProduct failed: {}", ex.toString()))
      .log(LOG.getName(), FINE);
  }

  @Override
  public Mono<Void> deleteProduct(int productId) {

    try {

      LOG.info("Will delete a product aggregate for product.id: {}", productId);

      return Mono.zip(
        r -> "",
        integration.deleteProduct(productId),
        integration.deleteRecommendations(productId),
        integration.deleteReviews(productId))
        .doOnError(ex -> LOG.warn("delete failed: {}", ex.toString()))
        .log(LOG.getName(), FINE).then();

    } catch (RuntimeException re) {
      LOG.warn("deleteCompositeProduct failed: {}", re.toString());
      throw re;
    }
  }

  private ProductAggregate createProductAggregate(Product product, List<Recommendation> recommendations, List<Review> reviews, String serviceAddress) {

    // 1. Setup product info
    int productId = product.getProductId();
    String name = product.getName();
    int weight = product.getWeight();

    // 2. Copy summary recommendation info, if available
    List<RecommendationSummary> recommendationSummaries = (recommendations == null) ? null :
       recommendations.stream()
        .map(r -> new RecommendationSummary(r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent()))
        .collect(Collectors.toList());

    // 3. Copy summary review info, if available
    List<ReviewSummary> reviewSummaries = (reviews == null)  ? null :
      reviews.stream()
        .map(r -> new ReviewSummary(r.getReviewId(), r.getAuthor(), r.getSubject(), r.getContent()))
        .collect(Collectors.toList());

    // 4. Create info regarding the involved microservices addresses
    String productAddress = product.getServiceAddress();
    String reviewAddress = (reviews != null && reviews.size() > 0) ? reviews.get(0).getServiceAddress() : "";
    String recommendationAddress = (recommendations != null && recommendations.size() > 0) ? recommendations.get(0).getServiceAddress() : "";
    ServiceAddresses serviceAddresses = new ServiceAddresses(serviceAddress, productAddress, reviewAddress, recommendationAddress);

    return new ProductAggregate(productId, name, weight, recommendationSummaries, reviewSummaries, serviceAddresses);
  }
}
```

</details>

#### `microservices/product-composite-service/src/main/resources/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -76,11 +76,44 @@
     host: localhost
     port: 7004
 
+# Create the output bindings at startup. Otherwise StreamBridge creates them lazily on the first send,
+# and the three events sent in parallel can race (MessageDeliveryException: Dispatcher has no subscribers).
+spring.cloud.stream.output-bindings: products-out-0;recommendations-out-0;reviews-out-0
+
+spring.cloud.stream:
+  defaultBinder: rabbit
+  default.contentType: application/json
+  bindings:
+    products-out-0:
+      destination: products
+      producer:
+        required-groups: auditGroup
+    recommendations-out-0:
+      destination: recommendations
+      producer:
+        required-groups: auditGroup
+    reviews-out-0:
+      destination: reviews
+      producer:
+        required-groups: auditGroup
+
+spring.cloud.stream.kafka.binder:
+  brokers: 127.0.0.1
+  defaultBrokerPort: 9092
+
+spring.rabbitmq:
+  host: 127.0.0.1
+  port: 5672
+  username: guest
+  password: guest
+
 logging:
   level:
     root: INFO
     se.magnus: DEBUG
 
+management.endpoint.health.show-details: "ALWAYS"
+management.endpoints.web.exposure.include: "*"
 ---
 spring.config.activate.on-profile: docker
 
@@ -96,3 +129,30 @@
   review-service:
     host: review
     port: 8080
+
+spring.rabbitmq.host: rabbitmq
+
+spring.cloud.stream.kafka.binder.brokers: kafka
+
+---
+spring.config.activate.on-profile: streaming_partitioned
+
+spring.cloud.stream.bindings.products-out-0.producer:
+  partition-key-expression: headers['partitionKey']
+  partition-count: 2
+
+spring.cloud.stream.bindings.recommendations-out-0.producer:
+  partition-key-expression: headers['partitionKey']
+  partition-count: 2
+
+spring.cloud.stream.bindings.reviews-out-0.producer:
+  partition-key-expression: headers['partitionKey']
+  partition-count: 2
+
+---
+spring.config.activate.on-profile: kafka
+
+management.health.rabbit.enabled: false
+spring.cloud.stream.defaultBinder: kafka
+spring.kafka.bootstrap-servers: kafka:9092
+spring.cloud.stream.kafka.binder.replication-factor: 1
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/main/resources/application.yml" op="write" nl="1" -->
```yaml
springdoc:
  swagger-ui.path: /openapi/swagger-ui.html
  api-docs.path: /openapi/v3/api-docs
  packagesToScan: se.magnus.microservices.composite.product
  pathsToMatch: /**

api:

  common:
    version: 1.0.0
    title: Sample API
    description: Description of the API...
    termsOfService: MY TERMS OF SERVICE
    license: MY LICENSE
    licenseUrl: MY LICENSE URL

    externalDocDesc: MY WIKI PAGE
    externalDocUrl: MY WIKI URL
    contact:
      name: NAME OF CONTACT
      url: URL TO CONTACT
      email: contact@mail.com

  responseCodes:
    ok.description: OK
    badRequest.description: Bad Request, invalid format of the request. See response message for more information
    notFound.description: Not found, the specified id does not exist
    unprocessableEntity.description: Unprocessable entity, input parameters caused the processing to fail. See response message for more information

  product-composite:

    get-composite-product:
      description: Returns a composite view of the specified product id
      notes: |
        # Normal response
        If the requested product id is found the method will return information regarding:
        1. Product information
        1. Reviews
        1. Recommendations
        1. Service Addresses\n(technical information regarding the addresses of the microservices that created the response)

        # Expected partial and error responses
        1. If no product information is found, a **404 - Not Found** error will be returned
        1. In no recommendations or reviews are found for a product, a partial response will be returned

    create-composite-product:
      description: Creates a composite product
      notes: |
        # Normal response
        The composite product information posted to the API will be split up and stored as separate product-info, recommendation and review entities.

        # Expected error responses
        1. If a product with the same productId as specified in the posted information already exists,
           an **422 - Unprocessable Entity** error with a "duplicate key" error message will be returned

    delete-composite-product:
      description: Deletes a product composite
      notes: |
        # Normal response
        Entities for product information, recommendations and reviews related to the specified productId will be deleted.
        The implementation of the delete method is idempotent, i.e. it can be called several times with the same response.

        This means that a delete request of a non-existing product will return **200 Ok**.

server.port: 7001
spring.web.error.include-message: always

app:
  product-service:
    host: localhost
    port: 7002
  recommendation-service:
    host: localhost
    port: 7003
  review-service:
    host: localhost
    port: 7004

# Create the output bindings at startup. Otherwise StreamBridge creates them lazily on the first send,
# and the three events sent in parallel can race (MessageDeliveryException: Dispatcher has no subscribers).
spring.cloud.stream.output-bindings: products-out-0;recommendations-out-0;reviews-out-0

spring.cloud.stream:
  defaultBinder: rabbit
  default.contentType: application/json
  bindings:
    products-out-0:
      destination: products
      producer:
        required-groups: auditGroup
    recommendations-out-0:
      destination: recommendations
      producer:
        required-groups: auditGroup
    reviews-out-0:
      destination: reviews
      producer:
        required-groups: auditGroup

spring.cloud.stream.kafka.binder:
  brokers: 127.0.0.1
  defaultBrokerPort: 9092

spring.rabbitmq:
  host: 127.0.0.1
  port: 5672
  username: guest
  password: guest

logging:
  level:
    root: INFO
    se.magnus: DEBUG

management.endpoint.health.show-details: "ALWAYS"
management.endpoints.web.exposure.include: "*"
---
spring.config.activate.on-profile: docker

server.port: 8080

app:
  product-service:
    host: product
    port: 8080
  recommendation-service:
    host: recommendation
    port: 8080
  review-service:
    host: review
    port: 8080

spring.rabbitmq.host: rabbitmq

spring.cloud.stream.kafka.binder.brokers: kafka

---
spring.config.activate.on-profile: streaming_partitioned

spring.cloud.stream.bindings.products-out-0.producer:
  partition-key-expression: headers['partitionKey']
  partition-count: 2

spring.cloud.stream.bindings.recommendations-out-0.producer:
  partition-key-expression: headers['partitionKey']
  partition-count: 2

spring.cloud.stream.bindings.reviews-out-0.producer:
  partition-key-expression: headers['partitionKey']
  partition-count: 2

---
spring.config.activate.on-profile: kafka

management.health.rabbit.enabled: false
spring.cloud.stream.defaultBinder: kafka
spring.kafka.bootstrap-servers: kafka:9092
spring.cloud.stream.kafka.binder.replication-factor: 1
```

</details>

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/IsSameEvent.java` — 새 파일 (83줄)

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/IsSameEvent.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import java.util.HashMap;
import java.util.Map;
import org.hamcrest.Description;
import org.hamcrest.Matcher;
import org.hamcrest.TypeSafeMatcher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import se.magnus.api.event.Event;
import tools.jackson.core.JacksonException;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

public class IsSameEvent extends TypeSafeMatcher<String> {

  private static final Logger LOG = LoggerFactory.getLogger(IsSameEvent.class);

  private ObjectMapper mapper = new ObjectMapper();

  private Event expectedEvent;


  private IsSameEvent(Event expectedEvent) {
    this.expectedEvent = expectedEvent;
  }

  @Override
  protected boolean matchesSafely(String eventAsJson) {

    if (expectedEvent == null) {
      return false;
    }

    LOG.trace("Convert the following json string to a map: {}", eventAsJson);
    Map mapEvent = convertJsonStringToMap(eventAsJson);
    mapEvent.remove("eventCreatedAt");

    Map mapExpectedEvent = getMapWithoutCreatedAt(expectedEvent);

    LOG.trace("Got the map: {}", mapEvent);
    LOG.trace("Compare to the expected map: {}", mapExpectedEvent);
    return mapEvent.equals(mapExpectedEvent);
  }

  @Override
  public void describeTo(Description description) {
    String expectedJson = convertObjectToJsonString(expectedEvent);
    description.appendText("expected to look like " + expectedJson);
  }

  public static Matcher<String> sameEventExceptCreatedAt(Event expectedEvent) {
    return new IsSameEvent(expectedEvent);
  }

  private Map getMapWithoutCreatedAt(Event event) {
    Map mapEvent = convertObjectToMap(event);
    mapEvent.remove("eventCreatedAt");
    return mapEvent;
  }

  private Map convertObjectToMap(Object object) {
    JsonNode node = mapper.convertValue(object, JsonNode.class);
    return mapper.convertValue(node, Map.class);
  }

  private String convertObjectToJsonString(Object object) {
    try {
      return mapper.writeValueAsString(object);
    } catch (JacksonException e) {
      throw new RuntimeException(e);
    }
  }

  private Map convertJsonStringToMap(String eventAsJson) {
    try {
      return mapper.readValue(eventAsJson, new TypeReference<HashMap>(){});
    } catch (JacksonException e) {
      throw new RuntimeException(e);
    }
  }
}
```

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/IsSameEventTests.java` — 새 파일 (36줄)

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
import se.magnus.api.core.product.Product;
import se.magnus.api.event.Event;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

class IsSameEventTests {

  ObjectMapper mapper = new ObjectMapper();

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

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/MessagingTests.java` — 새 파일 (191줄)

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/MessagingTests.java" op="write" nl="0" -->
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
  properties = {"spring.main.allow-bean-definition-overriding=true"})
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

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import static java.util.Collections.singletonList;
import static org.mockito.Mockito.when;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
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

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
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

    when(compositeIntegration.getProduct(PRODUCT_ID_OK))
      .thenReturn(Mono.just(new Product(PRODUCT_ID_OK, "name", 1, "mock-address")));

    when(compositeIntegration.getRecommendations(PRODUCT_ID_OK))
      .thenReturn(Flux.fromIterable(singletonList(new Recommendation(PRODUCT_ID_OK, 1, "author", 1, "content", "mock address"))));

    when(compositeIntegration.getReviews(PRODUCT_ID_OK))
      .thenReturn(Flux.fromIterable(singletonList(new Review(PRODUCT_ID_OK, 1, "author", "subject", "content", "mock address"))));

    when(compositeIntegration.getProduct(PRODUCT_ID_NOT_FOUND)).thenThrow(new NotFoundException("NOT FOUND: " + PRODUCT_ID_NOT_FOUND));

    when(compositeIntegration.getProduct(PRODUCT_ID_INVALID)).thenThrow(new InvalidInputException("INVALID: " + PRODUCT_ID_INVALID));
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

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter07
./gradlew build
docker compose build
./test-em-all.bash start stop
```

**Kafka / 파티션 구성**

```bash
COMPOSE_FILE=docker-compose-kafka.yml ./test-em-all.bash start stop
COMPOSE_FILE=docker-compose-partitions.yml ./test-em-all.bash start stop
```

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter07
```

---

← [6장 워크북](Chapter06.md) · [워크북 목차](README.md) · [9장 워크북](Chapter09.md) →
