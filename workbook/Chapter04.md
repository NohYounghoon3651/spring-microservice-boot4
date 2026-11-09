# 4장 워크북 — 도커를 사용한 배포

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 4장 · 영문 3판 p.79–102 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter04/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter04`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter04) · 위키: [4장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/04장-도커를-사용한-배포)

## 이 장에서 만드는 것

3장에서 만든 서비스들을 **도커 컨테이너**로 만들고 **도커 컴포즈**로 한 번에 띄웁니다.

- 서비스마다 `Dockerfile` (레이어로 나눈 JAR, Java 21 JRE)
- `docker` 프로필: 컨테이너 안에서 쓸 포트와 다른 서비스 주소
- `docker-compose.yml`과, 시스템을 띄우고 내리는 기능을 더한 `test-em-all.bash`

## 시작하기

3장을 끝낸 작업 폴더를 복사해서 시작합니다. 3장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter03 Chapter04          # 내가 만든 3장 결과에서 시작
# 또는: cp -r <저장소>/Chapter03/2-basic-rest-services Chapter04        # 저장소의 3장 완성 코드에서 시작
cd Chapter04 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 새 파일 1 · 수정 1
2. [`product-service`](#단계-2) — 새 파일 1 · 수정 1
3. [`recommendation-service`](#단계-3) — 새 파일 1 · 수정 1
4. [`review-service`](#단계-4) — 새 파일 1 · 수정 1
5. [`product-composite-service`](#단계-5) — 새 파일 1 · 수정 1

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

`docker-compose.yml`로 서비스 4개를 한 번에 띄웁니다. `test-em-all.bash`에는 `start`/`stop` 인자로 컴포즈를 올리고 내리는 기능과, 서비스가 준비될 때까지 기다리는 함수가 추가됩니다.

#### `docker-compose.yml` — 새 파일 (26줄)

<!-- wb:file path="docker-compose.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker

  recommendation:
    build: microservices/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker

  review:
    build: microservices/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker

  product-composite:
    build: microservices/product-composite-service
    mem_limit: 512m
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=docker
```

#### `test-em-all.bash` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -5,7 +5,7 @@
 #   HOST=localhost PORT=7001 ./test-em-all.bash
 #
 : ${HOST=localhost}
-: ${PORT=7001}
+: ${PORT=8080}
 : ${PROD_ID_REVS_RECS=1}
 : ${PROD_ID_NOT_FOUND=13}
 : ${PROD_ID_NO_RECS=113}
@@ -49,11 +49,52 @@
   fi
 }
 
+function testUrl() {
+  url=$@
+  if $url -ks -f -o /dev/null
+  then
+    return 0
+  else
+    return 1
+  fi;
+}
+
+function waitForService() {
+  url=$@
+  echo -n "Wait for: $url... "
+  n=0
+  until testUrl $url
+  do
+    n=$((n + 1))
+    if [[ $n == 100 ]]
+    then
+      echo " Give up"
+      exit 1
+    else
+      sleep 3
+      echo -n ", retry #$n "
+    fi
+  done
+  echo "DONE, continues..."
+}
+
 set -e
+
+echo "Start Tests:" `date`
 
 echo "HOST=${HOST}"
 echo "PORT=${PORT}"
 
+if [[ $@ == *"start"* ]]
+then
+  echo "Restarting the test environment..."
+  echo "$ docker compose down --remove-orphans"
+  docker compose down --remove-orphans
+  echo "$ docker compose up -d"
+  docker compose up -d
+fi
+
+waitForService curl http://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS
 
 # Verify that a normal request works, expect three recommendations and three reviews
 assertCurl 200 "curl http://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS -s"
@@ -85,4 +126,11 @@
 assertCurl 400 "curl http://$HOST:$PORT/product-composite/invalidProductId -s"
 assertEqual "\"Type mismatch.\"" "$(echo $RESPONSE | jq .message)"
 
+if [[ $@ == *"stop"* ]]
+then
+    echo "We are done, stopping the test environment..."
+    echo "$ docker compose down"
+    docker compose down
+fi
+
 echo "End, all tests OK:" `date`
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

waitForService curl http://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS

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

`Dockerfile`을 추가하고, `application.yml`에 `docker` 프로필(포트 8080)을 추가합니다. 네 서비스의 `Dockerfile`은 내용이 같습니다.

#### `microservices/product-service/Dockerfile` — 새 파일 (15줄)

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

ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

#### `microservices/product-service/src/main/resources/application.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7002
spring.web.error.include-message: always

logging:
  level:
    root: INFO
    se.magnus: DEBUG

---
spring.config.activate.on-profile: docker

server.port: 8080
```

**중간 확인**

```bash
./gradlew :microservices:product-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-3"></a>

## 단계 3. `recommendation-service`

`Dockerfile`을 추가하고, `application.yml`에 `docker` 프로필(포트 8080)을 추가합니다. 네 서비스의 `Dockerfile`은 내용이 같습니다.

#### `microservices/recommendation-service/Dockerfile` — 새 파일 (`microservices/product-service/Dockerfile`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/recommendation-service && cp microservices/product-service/Dockerfile microservices/recommendation-service/Dockerfile
```

<!-- wb:file path="microservices/recommendation-service/Dockerfile" op="cp" src="microservices/product-service/Dockerfile" -->

#### `microservices/recommendation-service/src/main/resources/application.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7003
spring.web.error.include-message: always

logging:
  level:
    root: INFO
    se.magnus: DEBUG

---
spring.config.activate.on-profile: docker

server.port: 8080
```

**중간 확인**

```bash
./gradlew :microservices:recommendation-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-4"></a>

## 단계 4. `review-service`

`Dockerfile`을 추가하고, `application.yml`에 `docker` 프로필(포트 8080)을 추가합니다. 네 서비스의 `Dockerfile`은 내용이 같습니다.

#### `microservices/review-service/Dockerfile` — 새 파일 (`microservices/product-service/Dockerfile`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/review-service && cp microservices/product-service/Dockerfile microservices/review-service/Dockerfile
```

<!-- wb:file path="microservices/review-service/Dockerfile" op="cp" src="microservices/product-service/Dockerfile" -->

#### `microservices/review-service/src/main/resources/application.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/review-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7004
spring.web.error.include-message: always

logging:
  level:
    root: INFO
    se.magnus: DEBUG

---
spring.config.activate.on-profile: docker

server.port: 8080
```

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `product-composite-service`

`Dockerfile`을 추가하고, `docker` 프로필에서 핵심 서비스 주소를 컨테이너 이름(`product`, `recommendation`, `review`)으로 바꿉니다.

#### `microservices/product-composite-service/Dockerfile` — 새 파일 (`microservices/product-service/Dockerfile`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/product-composite-service && cp microservices/product-service/Dockerfile microservices/product-composite-service/Dockerfile
```

<!-- wb:file path="microservices/product-composite-service/Dockerfile" op="cp" src="microservices/product-service/Dockerfile" -->

#### `microservices/product-composite-service/src/main/resources/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -16,3 +16,19 @@
   level:
     root: INFO
     se.magnus: DEBUG
+
+---
+spring.config.activate.on-profile: docker
+
+server.port: 8080
+
+app:
+  product-service:
+    host: product
+    port: 8080
+  recommendation-service:
+    host: recommendation
+    port: 8080
+  review-service:
+    host: review
+    port: 8080
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
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

logging:
  level:
    root: INFO
    se.magnus: DEBUG

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
```

</details>

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter04
./gradlew build
docker compose build
./test-em-all.bash start stop
```

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter04
```

---

← [3장 워크북](Chapter03.md) · [워크북 목차](README.md) · [5장 워크북](Chapter05.md) →
