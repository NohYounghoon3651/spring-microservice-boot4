# 9장 워크북 — 넷플릭스 유레카를 사용한 서비스 검색

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 9장 · 영문 3판 p.225–244 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter09/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter09`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter09) · 위키: [9장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/09장-넷플릭스-유레카를-사용한-서비스-검색)

## 이 장에서 만드는 것

**넷플릭스 유레카**로 서비스 검색을 추가합니다. 서비스 주소를 고정하지 않고, 유레카에 등록된 인스턴스 중에서 골라 호출합니다.

- `eureka-server` 프로젝트
- 각 서비스를 유레카 클라이언트로 등록
- 복합 서비스는 `@LoadBalanced` WebClient로 `http://product` 같은 서비스 이름을 호출

## 시작하기

7장을 끝낸 작업 폴더를 복사해서 시작합니다. 7장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter07 Chapter09          # 내가 만든 7장 결과에서 시작
# 또는: cp -r <저장소>/Chapter07 Chapter09        # 저장소의 7장 완성 코드에서 시작
cd Chapter09 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 수정 5
2. [`product-service`](#단계-2) — 수정 3
3. [`recommendation-service`](#단계-3) — 수정 3
4. [`review-service`](#단계-4) — 수정 3
5. [`product-composite-service`](#단계-5) — 수정 6
6. [`eureka-server` — 서비스 검색 서버](#단계-6) — 새 파일 7

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

`settings.gradle`에 `eureka-server`를 추가하고, 세 컴포즈 파일에 `eureka` 컨테이너를 추가합니다. `test-em-all.bash`는 서비스가 유레카에 등록될 때까지 기다립니다.

#### `docker-compose-kafka.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -132,3 +132,9 @@
       - "2181:2181"
     environment:
       - ZOOKEEPER_CLIENT_PORT=2181
+
+  eureka:
+    build: spring-cloud/eureka-server
+    mem_limit: 512m
+    ports:
+      - "8761:8761"
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose-kafka.yml" op="write" nl="0" -->
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

  eureka:
    build: spring-cloud/eureka-server
    mem_limit: 512m
    ports:
      - "8761:8761"
```

</details>

#### `docker-compose-partitions.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -115,3 +115,9 @@
       interval: 5s
       timeout: 2s
       retries: 60
+
+  eureka:
+    build: spring-cloud/eureka-server
+    mem_limit: 512m
+    ports:
+      - "8761:8761"
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose-partitions.yml" op="write" nl="0" -->
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

  eureka:
    build: spring-cloud/eureka-server
    mem_limit: 512m
    ports:
      - "8761:8761"
```

</details>

#### `docker-compose.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -82,3 +82,9 @@
       interval: 5s
       timeout: 2s
       retries: 60
+
+  eureka:
+    build: spring-cloud/eureka-server
+    mem_limit: 512m
+    ports:
+      - "8761:8761"
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

  eureka:
    build: spring-cloud/eureka-server
    mem_limit: 512m
    ports:
      - "8761:8761"
```

</details>

#### `settings.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -10,6 +10,7 @@
 include ':microservices:review-service'
 include ':microservices:recommendation-service'
 include ':microservices:product-composite-service'
+include ':spring-cloud:eureka-server'
 
 // ---------------------------------------------------------------------------
 // Security patches (Dependabot alerts). Spring Boot stays at 4.0.9; only the
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="settings.gradle" op="write" nl="1" -->
```groovy
pluginManagement {
    repositories {
        gradlePluginPortal()
    }
}

include ':api'
include ':util'
include ':microservices:product-service'
include ':microservices:review-service'
include ':microservices:recommendation-service'
include ':microservices:product-composite-service'
include ':spring-cloud:eureka-server'

// ---------------------------------------------------------------------------
// Security patches (Dependabot alerts). Spring Boot stays at 4.0.9; only the
// vulnerable transitive libraries are raised to their patched versions.
// See MIGRATION-BOOT4.md, "2-5. 의존성 보안 패치".
// ---------------------------------------------------------------------------
def securityPatches = [
    'com.rabbitmq:amqp-client'                                    : '5.37.1',    // spring-rabbit (Boot 4.0.9: 5.27.1)
    'at.yawk.lz4:lz4-java'                                        : '1.11.4',    // kafka-clients
    'org.xerial.snappy:snappy-java'                               : '1.1.10.9',  // kafka-clients
    'com.google.guava:guava'                                      : '33.7.2-jre',// Netflix Eureka (archaius, servo)
    'org.apache.httpcomponents:httpclient'                        : '4.5.14',    // Netflix Eureka
    'org.apache.httpcomponents.client5:httpclient5'               : '5.6.3',
    'org.apache.httpcomponents.core5:httpcore5'                   : '5.4.3',
    'org.apache.httpcomponents.core5:httpcore5-h2'                : '5.4.3',
    'org.apache.commons:commons-lang3'                            : '3.20.0',    // Spring Boot Gradle plugin (buildpacks)
    'io.opentelemetry:opentelemetry-api'                          : '1.67.0',
    'io.opentelemetry:opentelemetry-common'                       : '1.67.0',
    'io.opentelemetry:opentelemetry-context'                      : '1.67.0',
    'io.opentelemetry:opentelemetry-sdk'                          : '1.67.0',
    'io.opentelemetry:opentelemetry-sdk-common'                   : '1.67.0',
    'io.opentelemetry:opentelemetry-sdk-trace'                    : '1.67.0',
    'io.opentelemetry:opentelemetry-sdk-metrics'                  : '1.67.0',
    'io.opentelemetry:opentelemetry-sdk-logs'                     : '1.67.0',
    'io.opentelemetry:opentelemetry-sdk-extension-autoconfigure-spi': '1.67.0',
    'io.opentelemetry:opentelemetry-exporter-common'              : '1.67.0',
    'io.opentelemetry:opentelemetry-extension-trace-propagators'  : '1.67.0',
    'io.opentelemetry:opentelemetry-exporter-zipkin'              : '1.64.0',    // last release of the Zipkin exporter
]
gradle.beforeProject { project ->
    // Application classpaths: explicit versions win over the Spring Boot and Spring Cloud BOMs
    project.pluginManager.withPlugin('io.spring.dependency-management') {
        project.dependencyManagement {
            dependencies {
                securityPatches.each { ga, v -> dependency "${ga}:${v}" }
            }
        }
    }
    // Build script classpath (Spring Boot Gradle plugin and its buildpack support)
    project.buildscript.configurations.configureEach {
        resolutionStrategy.eachDependency { details ->
            def v = securityPatches["${details.requested.group}:${details.requested.name}".toString()]
            if (v) details.useVersion(v)
        }
    }
}
```

</details>

#### `test-em-all.bash` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -195,6 +195,17 @@
 fi
 
 waitForService curl http://$HOST:$PORT/actuator/health
+
+# Verify access to Eureka and that all four microservices are registered in Eureka
+# Wait until all microservices are registered in Eureka; a registration can take a few seconds
+# after the health check is OK, especially when several instances start at the same time
+for i in $(seq 1 30); do
+  [ "$(curl -H 'accept:application/json' $HOST:8761/eureka/apps -s | jq ".applications.application | length")" = "4" ] && break
+  sleep 2
+done
+assertCurl 200 "curl -H "accept:application/json" $HOST:8761/eureka/apps -s"
+assertEqual 4 $(echo $RESPONSE | jq ".applications.application | length")
+
 setupTestdata
 
 waitForMessageProcessing
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

# Verify access to Eureka and that all four microservices are registered in Eureka
# Wait until all microservices are registered in Eureka; a registration can take a few seconds
# after the health check is OK, especially when several instances start at the same time
for i in $(seq 1 30); do
  [ "$(curl -H 'accept:application/json' $HOST:8761/eureka/apps -s | jq ".applications.application | length")" = "4" ] && break
  sleep 2
done
assertCurl 200 "curl -H "accept:application/json" $HOST:8761/eureka/apps -s"
assertEqual 4 $(echo $RESPONSE | jq ".applications.application | length")

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

## 단계 2. `product-service`

`spring-cloud-starter-netflix-eureka-client` 의존성과 유레카 서버 주소 설정을 추가합니다.

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,10 +31,11 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-
+    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
 
     compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
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
    implementation 'org.springframework.boot:spring-boot-starter-restclient'
    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
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

#### `microservices/product-service/src/main/resources/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,19 @@
 server.port: 7002
 spring.web.error.include-message: always
+
+spring.application.name: product
+
+app.eureka-server: localhost
+
+eureka:
+  client:
+    serviceUrl:
+      defaultZone: http://${app.eureka-server}:8761/eureka/
+    initialInstanceInfoReplicationIntervalSeconds: 5
+    registryFetchIntervalSeconds: 5
+  instance:
+    leaseRenewalIntervalInSeconds: 5
+    leaseExpirationDurationInSeconds: 5
 
 spring.mongodb:
   host: localhost
@@ -51,6 +65,8 @@
 
 server.port: 8080
 
+app.eureka-server: eureka
+
 spring.mongodb.host: mongodb
 
 spring.rabbitmq.host: rabbitmq
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7002
spring.web.error.include-message: always

spring.application.name: product

app.eureka-server: localhost

eureka:
  client:
    serviceUrl:
      defaultZone: http://${app.eureka-server}:8761/eureka/
    initialInstanceInfoReplicationIntervalSeconds: 5
    registryFetchIntervalSeconds: 5
  instance:
    leaseRenewalIntervalInSeconds: 5
    leaseExpirationDurationInSeconds: 5

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

app.eureka-server: eureka

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

</details>

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -22,7 +22,7 @@
 import se.magnus.microservices.core.product.persistence.ProductRepository;
 
 @AutoConfigureWebTestClient
-@SpringBootTest(webEnvironment = RANDOM_PORT)
+@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"eureka.client.enabled=false"})
 class ProductServiceApplicationTests extends MongoDbTestBase {
 
   @Autowired
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
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"eureka.client.enabled=false"})
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

<a id="단계-3"></a>

## 단계 3. `recommendation-service`

`spring-cloud-starter-netflix-eureka-client` 의존성과 유레카 서버 주소 설정을 추가합니다.

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,9 +31,11 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
+    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
 
     compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
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
    implementation 'org.springframework.boot:spring-boot-starter-restclient'
    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
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

#### `microservices/recommendation-service/src/main/resources/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,19 @@
 server.port: 7003
 spring.web.error.include-message: always
+
+spring.application.name: recommendation
+
+app.eureka-server: localhost
+
+eureka:
+  client:
+    serviceUrl:
+      defaultZone: http://${app.eureka-server}:8761/eureka/
+    initialInstanceInfoReplicationIntervalSeconds: 5
+    registryFetchIntervalSeconds: 5
+  instance:
+    leaseRenewalIntervalInSeconds: 5
+    leaseExpirationDurationInSeconds: 5
 
 spring.mongodb:
   host: localhost
@@ -51,6 +65,8 @@
 
 server.port: 8080
 
+app.eureka-server: eureka
+
 spring.mongodb.host: mongodb
 
 spring.rabbitmq.host: rabbitmq
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7003
spring.web.error.include-message: always

spring.application.name: recommendation

app.eureka-server: localhost

eureka:
  client:
    serviceUrl:
      defaultZone: http://${app.eureka-server}:8761/eureka/
    initialInstanceInfoReplicationIntervalSeconds: 5
    registryFetchIntervalSeconds: 5
  instance:
    leaseRenewalIntervalInSeconds: 5
    leaseExpirationDurationInSeconds: 5

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

app.eureka-server: eureka

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

</details>

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -22,7 +22,7 @@
 import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;
 
 @AutoConfigureWebTestClient
-@SpringBootTest(webEnvironment = RANDOM_PORT)
+@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"eureka.client.enabled=false"})
 class RecommendationServiceApplicationTests extends MongoDbTestBase {
 
   @Autowired
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
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"eureka.client.enabled=false"})
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

<a id="단계-4"></a>

## 단계 4. `review-service`

`spring-cloud-starter-netflix-eureka-client` 의존성과 유레카 서버 주소 설정을 추가합니다.

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,9 +31,11 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
+    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation 'com.mysql:mysql-connector-j'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
 
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
    implementation 'org.springframework.boot:spring-boot-starter-restclient'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
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

#### `microservices/review-service/src/main/resources/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,19 @@
 server.port: 7004
 spring.web.error.include-message: always
+
+spring.application.name: review
+
+app.eureka-server: localhost
+
+eureka:
+  client:
+    serviceUrl:
+      defaultZone: http://${app.eureka-server}:8761/eureka/
+    initialInstanceInfoReplicationIntervalSeconds: 5
+    registryFetchIntervalSeconds: 5
+  instance:
+    leaseRenewalIntervalInSeconds: 5
+    leaseExpirationDurationInSeconds: 5
 
 # Strongly recommend to set this property to "none" in a production environment!
 spring.jpa.hibernate.ddl-auto: update
@@ -57,6 +71,8 @@
 
 server.port: 8080
 
+app.eureka-server: eureka
+
 spring.datasource.url: jdbc:mysql://mysql/review-db
 
 spring.rabbitmq.host: rabbitmq
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7004
spring.web.error.include-message: always

spring.application.name: review

app.eureka-server: localhost

eureka:
  client:
    serviceUrl:
      defaultZone: http://${app.eureka-server}:8761/eureka/
    initialInstanceInfoReplicationIntervalSeconds: 5
    registryFetchIntervalSeconds: 5
  instance:
    leaseRenewalIntervalInSeconds: 5
    leaseExpirationDurationInSeconds: 5

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

app.eureka-server: eureka

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

</details>

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -24,7 +24,8 @@
 @AutoConfigureWebTestClient
 @SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
   "spring.cloud.stream.defaultBinder=rabbit",
-  "logging.level.se.magnus=DEBUG"})
+  "logging.level.se.magnus=DEBUG",
+  "eureka.client.enabled=false"})
 class ReviewServiceApplicationTests extends MySqlTestBase {
 
   @Autowired
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
  "logging.level.se.magnus=DEBUG",
  "eureka.client.enabled=false"})
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

<a id="단계-5"></a>

## 단계 5. `product-composite-service`

`@LoadBalanced WebClient.Builder` 빈을 정의하고, 통합 클래스에서 서비스 주소 대신 `http://product` 같은 서비스 이름을 씁니다.

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -30,8 +30,10 @@
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
     implementation 'org.springframework.boot:spring-boot-starter-webclient'
+    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
+    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:3.0.3'
 
     // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
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
    implementation 'org.springframework.boot:spring-boot-starter-restclient'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
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

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -10,8 +10,10 @@
 import org.springframework.beans.factory.annotation.Value;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
+import org.springframework.cloud.client.loadbalancer.LoadBalanced;
 import org.springframework.context.annotation.Bean;
 import org.springframework.context.annotation.ComponentScan;
+import org.springframework.web.reactive.function.client.WebClient;
 import reactor.core.scheduler.Scheduler;
 import reactor.core.scheduler.Schedulers;
 
@@ -74,6 +76,13 @@
     return Schedulers.newBoundedElastic(threadPoolSize, taskQueueSize, "publish-pool");
   }
 
+
+  @Bean
+  @LoadBalanced
+  public WebClient.Builder loadBalancedWebClientBuilder() {
+    return WebClient.builder();
+  }
+
   public static void main(String[] args) {
     SpringApplication.run(ProductCompositeServiceApplication.class, args);
   }
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
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.web.reactive.function.client.WebClient;
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


  @Bean
  @LoadBalanced
  public WebClient.Builder loadBalancedWebClientBuilder() {
    return WebClient.builder();
  }

  public static void main(String[] args) {
    SpringApplication.run(ProductCompositeServiceApplication.class, args);
  }

}
```

</details>

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -8,7 +8,6 @@
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
 import org.springframework.beans.factory.annotation.Qualifier;
-import org.springframework.beans.factory.annotation.Value;
 import org.springframework.boot.health.contributor.Health;
 import org.springframework.cloud.stream.function.StreamBridge;
 import org.springframework.http.HttpStatus;
@@ -38,42 +37,26 @@
 
   private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeIntegration.class);
 
+  private static final String PRODUCT_SERVICE_URL = "http://product";
+  private static final String RECOMMENDATION_SERVICE_URL = "http://recommendation";
+  private static final String REVIEW_SERVICE_URL = "http://review";
+
+  private final Scheduler publishEventScheduler;
   private final WebClient webClient;
   private final ObjectMapper mapper;
-
-  private final String productServiceUrl;
-  private final String recommendationServiceUrl;
-  private final String reviewServiceUrl;
-
   private final StreamBridge streamBridge;
-
-  private final Scheduler publishEventScheduler;
 
   public ProductCompositeIntegration(
     @Qualifier("publishEventScheduler") Scheduler publishEventScheduler,
-
-    WebClient.Builder webClient,
+    WebClient.Builder webClientBuilder,
     ObjectMapper mapper,
-    StreamBridge streamBridge,
-
-    @Value("${app.product-service.host}") String productServiceHost,
-    @Value("${app.product-service.port}") int  productServicePort,
-
-    @Value("${app.recommendation-service.host}") String recommendationServiceHost,
-    @Value("${app.recommendation-service.port}") int  recommendationServicePort,
-
-    @Value("${app.review-service.host}") String reviewServiceHost,
-    @Value("${app.review-service.port}") int  reviewServicePort
+    StreamBridge streamBridge
   ) {
+    this.webClient = webClientBuilder.build();
 
     this.publishEventScheduler = publishEventScheduler;
-    this.webClient = webClient.build();
     this.mapper = mapper;
     this.streamBridge = streamBridge;
-
-    productServiceUrl        = "http://" + productServiceHost + ":" + productServicePort;
-    recommendationServiceUrl = "http://" + recommendationServiceHost + ":" + recommendationServicePort;
-    reviewServiceUrl         = "http://" + reviewServiceHost + ":" + reviewServicePort;
   }
 
   @Override
@@ -87,7 +70,7 @@
 
   @Override
   public Mono<Product> getProduct(int productId) {
-    String url = productServiceUrl + "/product/" + productId;
+    String url = PRODUCT_SERVICE_URL + "/product/" + productId;
     LOG.debug("Will call the getProduct API on URL: {}", url);
 
     return webClient.get().uri(url).retrieve().bodyToMono(Product.class).log(LOG.getName(), FINE).onErrorMap(WebClientResponseException.class, ex -> handleException(ex));
@@ -112,7 +95,7 @@
   @Override
   public Flux<Recommendation> getRecommendations(int productId) {
 
-    String url = recommendationServiceUrl + "/recommendation?productId=" + productId;
+    String url = RECOMMENDATION_SERVICE_URL + "/recommendation?productId=" + productId;
 
     LOG.debug("Will call the getRecommendations API on URL: {}", url);
 
@@ -139,7 +122,7 @@
   @Override
   public Flux<Review> getReviews(int productId) {
 
-    String url = reviewServiceUrl + "/review?productId=" + productId;
+    String url = REVIEW_SERVICE_URL + "/review?productId=" + productId;
 
     LOG.debug("Will call the getReviews API on URL: {}", url);
 
@@ -155,15 +138,15 @@
   }
 
   public Mono<Health> getProductHealth() {
-    return getHealth(productServiceUrl);
+    return getHealth(PRODUCT_SERVICE_URL);
   }
 
   public Mono<Health> getRecommendationHealth() {
-    return getHealth(recommendationServiceUrl);
+    return getHealth(RECOMMENDATION_SERVICE_URL);
   }
 
   public Mono<Health> getReviewHealth() {
-    return getHealth(reviewServiceUrl);
+    return getHealth(REVIEW_SERVICE_URL);
   }
 
   private Mono<Health> getHealth(String url) {
```

<details><summary>완성된 파일 전체 보기</summary>

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

  private static final String PRODUCT_SERVICE_URL = "http://product";
  private static final String RECOMMENDATION_SERVICE_URL = "http://recommendation";
  private static final String REVIEW_SERVICE_URL = "http://review";

  private final Scheduler publishEventScheduler;
  private final WebClient webClient;
  private final ObjectMapper mapper;
  private final StreamBridge streamBridge;

  public ProductCompositeIntegration(
    @Qualifier("publishEventScheduler") Scheduler publishEventScheduler,
    WebClient.Builder webClientBuilder,
    ObjectMapper mapper,
    StreamBridge streamBridge
  ) {
    this.webClient = webClientBuilder.build();

    this.publishEventScheduler = publishEventScheduler;
    this.mapper = mapper;
    this.streamBridge = streamBridge;
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
    String url = PRODUCT_SERVICE_URL + "/product/" + productId;
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

    String url = RECOMMENDATION_SERVICE_URL + "/recommendation?productId=" + productId;

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

    String url = REVIEW_SERVICE_URL + "/review?productId=" + productId;

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
    return getHealth(PRODUCT_SERVICE_URL);
  }

  public Mono<Health> getRecommendationHealth() {
    return getHealth(RECOMMENDATION_SERVICE_URL);
  }

  public Mono<Health> getReviewHealth() {
    return getHealth(REVIEW_SERVICE_URL);
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

</details>

#### `microservices/product-composite-service/src/main/resources/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -65,16 +65,19 @@
 server.port: 7001
 spring.web.error.include-message: always
 
-app:
-  product-service:
-    host: localhost
-    port: 7002
-  recommendation-service:
-    host: localhost
-    port: 7003
-  review-service:
-    host: localhost
-    port: 7004
+spring.application.name: product-composite
+
+app.eureka-server: localhost
+
+eureka:
+  client:
+    serviceUrl:
+      defaultZone: http://${app.eureka-server}:8761/eureka/
+    initialInstanceInfoReplicationIntervalSeconds: 5
+    registryFetchIntervalSeconds: 5
+  instance:
+    leaseRenewalIntervalInSeconds: 5
+    leaseExpirationDurationInSeconds: 5
 
 # Create the output bindings at startup. Otherwise StreamBridge creates them lazily on the first send,
 # and the three events sent in parallel can race (MessageDeliveryException: Dispatcher has no subscribers).
@@ -119,16 +122,7 @@
 
 server.port: 8080
 
-app:
-  product-service:
-    host: product
-    port: 8080
-  recommendation-service:
-    host: recommendation
-    port: 8080
-  review-service:
-    host: review
-    port: 8080
+app.eureka-server: eureka
 
 spring.rabbitmq.host: rabbitmq
 
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

spring.application.name: product-composite

app.eureka-server: localhost

eureka:
  client:
    serviceUrl:
      defaultZone: http://${app.eureka-server}:8761/eureka/
    initialInstanceInfoReplicationIntervalSeconds: 5
    registryFetchIntervalSeconds: 5
  instance:
    leaseRenewalIntervalInSeconds: 5
    leaseExpirationDurationInSeconds: 5

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

app.eureka-server: eureka

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

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/MessagingTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -36,8 +36,10 @@
 
 @AutoConfigureWebTestClient
 @SpringBootTest(
-  webEnvironment = RANDOM_PORT,
-  properties = {"spring.main.allow-bean-definition-overriding=true"})
+  webEnvironment = RANDOM_PORT, properties = {
+    "spring.main.allow-bean-definition-overriding=true",
+    "eureka.client.enabled=false"})
+
 @Import({TestChannelBinderConfiguration.class})
 class MessagingTests {
 
```

<details><summary>완성된 파일 전체 보기</summary>

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
  webEnvironment = RANDOM_PORT, properties = {
    "spring.main.allow-bean-definition-overriding=true",
    "eureka.client.enabled=false"})

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

</details>

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -24,7 +24,7 @@
 import se.magnus.microservices.composite.product.services.ProductCompositeIntegration;
 
 @AutoConfigureWebTestClient
-@SpringBootTest(webEnvironment = RANDOM_PORT)
+@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"eureka.client.enabled=false"})
 class ProductCompositeServiceApplicationTests {
 
   private static final int PRODUCT_ID_OK = 1;
```

<details><summary>완성된 파일 전체 보기</summary>

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
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"eureka.client.enabled=false"})
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

</details>

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-6"></a>

## 단계 6. `eureka-server` — 서비스 검색 서버

새 프로젝트입니다. `@EnableEurekaServer` 하나로 유레카 서버가 됩니다.

#### `spring-cloud/eureka-server/.gitignore` — 복사/생성

Git이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요(치지 않아도 실습에는 지장이 없습니다).

<!-- wb:file path="spring-cloud/eureka-server/.gitignore" op="copy" nl="0" -->

#### `spring-cloud/eureka-server/Dockerfile` — 새 파일 (15줄)

<!-- wb:file path="spring-cloud/eureka-server/Dockerfile" op="write" nl="1" -->
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

EXPOSE 8761

ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

#### `spring-cloud/eureka-server/build.gradle` — 새 파일 (44줄)

<!-- wb:file path="spring-cloud/eureka-server/build.gradle" op="write" nl="0" -->
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

ext {
    springCloudVersion = '2025.1.4'
}

jar {
    enabled = false
}

dependencies {
    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-server'
    implementation 'org.glassfish.jaxb:jaxb-runtime'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-resttestclient'
    testImplementation 'org.springframework.boot:spring-boot-restclient'
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

#### `spring-cloud/eureka-server/settings.gradle` — 새 파일 (1줄)

<!-- wb:file path="spring-cloud/eureka-server/settings.gradle" op="write" nl="1" -->
```groovy
rootProject.name = 'eureka-server'
```

#### `spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/EurekaServerApplication.java` — 새 파일 (16줄)

<!-- wb:file path="spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/EurekaServerApplication.java" op="write" nl="1" -->
```java
package se.magnus.springcloud.eurekaserver;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

@EnableEurekaServer
@SpringBootApplication
public class EurekaServerApplication {

  public static void main(String[] args) {
    SpringApplication.run(EurekaServerApplication.class, args);
  }

}

```

#### `spring-cloud/eureka-server/src/main/resources/application.yml` — 새 파일 (17줄)

<!-- wb:file path="spring-cloud/eureka-server/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server:
  port: 8761

eureka:
  instance:
    hostname: localhost
  client:
    registerWithEureka: false
    fetchRegistry: false
    serviceUrl:
      defaultZone: http://${eureka.instance.hostname}:${server.port}/eureka/
  # from: https://github.com/spring-cloud-samples/eureka/blob/master/src/main/resources/application.yml
  server:
    waitTimeInMsWhenSyncEmpty: 0
    response-cache-update-interval-ms: 5000

management.endpoints.web.exposure.include: "*"
```

#### `spring-cloud/eureka-server/src/test/java/se/magnus/springcloud/eurekaserver/EurekaServerApplicationTests.java` — 새 파일 (45줄)

<!-- wb:file path="spring-cloud/eureka-server/src/test/java/se/magnus/springcloud/eurekaserver/EurekaServerApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.springcloud.eurekaserver;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.resttestclient.TestRestTemplate;
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureTestRestTemplate;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

@AutoConfigureTestRestTemplate
@SpringBootTest(webEnvironment = RANDOM_PORT)
class EurekaServerApplicationTests {

  @Test
  void contextLoads() {
  }

  @Autowired
  private TestRestTemplate testRestTemplate;

  @Test
  void catalogLoads() {

    String expectedReponseBody = "{\"applications\":{\"versions__delta\":\"1\",\"apps__hashcode\":\"\",\"application\":[]}}";
    ResponseEntity<String> entity = testRestTemplate.getForEntity("/eureka/apps", String.class);
    assertEquals(HttpStatus.OK, entity.getStatusCode());
    assertEquals(expectedReponseBody, entity.getBody());
  }

  @Test
  void healthy() {
    // Spring Boot 4 enables the liveness/readiness probes by default, so the response
    // also contains a "groups" field. Only verify the status.
    String expectedStatus = "\"status\":\"UP\"";
    ResponseEntity<String> entity = testRestTemplate.getForEntity("/actuator/health", String.class);
    assertEquals(HttpStatus.OK, entity.getStatusCode());
    assertTrue(entity.getBody().contains(expectedStatus));
  }
}

```

**중간 확인**

```bash
./gradlew :spring-cloud:eureka-server:build -x test   # 컴파일만 먼저 확인
```

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter09
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
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter09
```

---

← [7장 워크북](Chapter07.md) · [워크북 목차](README.md) · [10장 워크북](Chapter10.md) →
