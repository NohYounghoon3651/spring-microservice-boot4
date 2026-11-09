# 16장 워크북 — 쿠버네티스에 마이크로서비스 배포

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 16장 · 영문 3판 p.395–438 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter16/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter16`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter16) · 위키: [16장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/16장-쿠버네티스에-마이크로서비스-배포)

## 이 장에서 만드는 것

마이크로서비스를 **쿠버네티스에 배포**합니다. 유레카는 쿠버네티스 서비스로 대체하고, 배포는 **헬름 차트**로 만듭니다.

- 유레카 서버 삭제, 서비스 이름으로 직접 호출
- 그레이스풀 셧다운, 활성·준비 상태 프로브
- 헬름 차트: `common`(공통 템플릿) → `components`(서비스별) → `environments`(개발·운영 묶음)

## 시작하기

15장을 끝낸 작업 폴더를 복사해서 시작합니다. 15장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter15 Chapter16          # 내가 만든 15장 결과에서 시작
# 또는: cp -r <저장소>/Chapter15 Chapter16        # 저장소의 15장 완성 코드에서 시작
cd Chapter16 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 수정 5
2. [`product-service`](#단계-2) — 수정 2
3. [`recommendation-service`](#단계-3) — 수정 2
4. [`review-service`](#단계-4) — 수정 2
5. [`product-composite-service`](#단계-5) — 새 파일 1 · 수정 4
6. [`eureka-server` — 서비스 검색 서버](#단계-6) — 삭제 9
7. [`gateway` — 에지 서버](#단계-7) — 수정 3
8. [`authorization-server` — OAuth 2.0 인가 서버](#단계-8) — 수정 4
9. [`config-server` — 구성 서버](#단계-9) — 수정 1
10. [`config-repo` — 중앙 구성 파일](#단계-10) — 수정 7 · 삭제 1
11. [`kubernetes/helm` — 헬름 공통 파일](#단계-11) — 새 파일 1
12. [헬름 `common` 라이브러리 차트](#단계-12) — 새 파일 8
13. [헬름 `components` 차트 — 서비스별 차트](#단계-13) — 새 파일 70
14. [헬름 `environments` 차트 — 환경별 묶음](#단계-14) — 새 파일 8

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

`settings.gradle`에서 `eureka-server`를 빼고, 컴포즈 파일에서 `eureka`를 지웁니다. `test-em-all.bash`에 쿠버네티스에서 실행하는 경우(`USE_K8S=true`)가 추가됩니다.

#### `docker-compose-kafka.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,6 +1,7 @@
 services:
   product:
     build: microservices/product-service
+    image: hands-on/product-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
@@ -14,6 +15,7 @@
 
   product-p1:
     build: microservices/product-service
+    image: hands-on/product-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
@@ -27,6 +29,7 @@
 
   recommendation:
     build: microservices/recommendation-service
+    image: hands-on/recommendation-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
@@ -40,6 +43,7 @@
 
   recommendation-p1:
     build: microservices/recommendation-service
+    image: hands-on/recommendation-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
@@ -53,6 +57,7 @@
 
   review:
     build: microservices/review-service
+    image: hands-on/review-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
@@ -66,6 +71,7 @@
 
   review-p1:
     build: microservices/review-service
+    image: hands-on/review-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
@@ -79,6 +85,7 @@
 
   product-composite:
     build: microservices/product-composite-service
+    image: hands-on/product-composite-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,kafka
@@ -147,16 +154,9 @@
     environment:
       - ZOOKEEPER_CLIENT_PORT=2181
 
-  eureka:
-    build: spring-cloud/eureka-server
-    mem_limit: 512m
-    environment:
-    - SPRING_PROFILES_ACTIVE=docker
-    - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-    - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
-
   gateway:
     build: spring-cloud/gateway
+    image: hands-on/gateway
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
@@ -170,19 +170,21 @@
 
   auth-server:
     build: spring-cloud/authorization-server
+    image: hands-on/auth-server
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
       - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
       - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
     healthcheck:
-      test: ["CMD", "wget", "-O -", "-q", "http://localhost:9999/actuator/health"]
+      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
       interval: 5s
       timeout: 2s
       retries: 60
 
   config-server:
     build: spring-cloud/config-server
+    image: hands-on/config-server
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,native
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose-kafka.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
    image: hands-on/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      kafka:
        condition: service_healthy

  product-p1:
    build: microservices/product-service
    image: hands-on/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      kafka:
        condition: service_healthy

  recommendation:
    build: microservices/recommendation-service
    image: hands-on/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      kafka:
        condition: service_healthy

  recommendation-p1:
    build: microservices/recommendation-service
    image: hands-on/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      kafka:
        condition: service_healthy

  review:
    build: microservices/review-service
    image: hands-on/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mysql:
        condition: service_healthy
      kafka:
        condition: service_healthy

  review-p1:
    build: microservices/review-service
    image: hands-on/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mysql:
        condition: service_healthy
      kafka:
        condition: service_healthy

  product-composite:
    build: microservices/product-composite-service
    image: hands-on/product-composite-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,kafka
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      kafka:
        condition: service_healthy
      auth-server:
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

  gateway:
    build: spring-cloud/gateway
    image: hands-on/gateway
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
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
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

  config-server:
    build: spring-cloud/config-server
    image: hands-on/config-server
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,native
      - ENCRYPT_KEY=${CONFIG_SERVER_ENCRYPT_KEY}
      - SPRING_SECURITY_USER_NAME=${CONFIG_SERVER_USR}
      - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
    volumes:
      - $PWD/config-repo:/config-repo

  zipkin-server:
    image: openzipkin/zipkin:3.5.0
    restart: always
    mem_limit: 1024m
    environment:
      - STORAGE_TYPE=mem
    ports:
      - 9411:9411
```

</details>

#### `docker-compose-partitions.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,6 +1,7 @@
 services:
   product:
     build: microservices/product-service
+    image: hands-on/product-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
@@ -14,6 +15,7 @@
 
   product-p1:
     build: microservices/product-service
+    image: hands-on/product-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
@@ -27,6 +29,7 @@
 
   recommendation:
     build: microservices/recommendation-service
+    image: hands-on/recommendation-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
@@ -40,6 +43,7 @@
 
   recommendation-p1:
     build: microservices/recommendation-service
+    image: hands-on/recommendation-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
@@ -53,6 +57,7 @@
 
   review:
     build: microservices/review-service
+    image: hands-on/review-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
@@ -66,6 +71,7 @@
 
   review-p1:
     build: microservices/review-service
+    image: hands-on/review-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
@@ -79,6 +85,7 @@
 
   product-composite:
     build: microservices/product-composite-service
+    image: hands-on/product-composite-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned
@@ -130,16 +137,9 @@
       timeout: 2s
       retries: 60
 
-  eureka:
-    build: spring-cloud/eureka-server
-    mem_limit: 512m
-    environment:
-    - SPRING_PROFILES_ACTIVE=docker
-    - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-    - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
-
   gateway:
     build: spring-cloud/gateway
+    image: hands-on/gateway
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
@@ -153,19 +153,21 @@
 
   auth-server:
     build: spring-cloud/authorization-server
+    image: hands-on/auth-server
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
       - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
       - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
     healthcheck:
-      test: ["CMD", "wget", "-O -", "-q", "http://localhost:9999/actuator/health"]
+      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
       interval: 5s
       timeout: 2s
       retries: 60
 
   config-server:
     build: spring-cloud/config-server
+    image: hands-on/config-server
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,native
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose-partitions.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
    image: hands-on/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-p1:
    build: microservices/product-service
    image: hands-on/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation:
    build: microservices/recommendation-service
    image: hands-on/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation-p1:
    build: microservices/recommendation-service
    image: hands-on/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review:
    build: microservices/review-service
    image: hands-on/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review-p1:
    build: microservices/review-service
    image: hands-on/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-composite:
    build: microservices/product-composite-service
    image: hands-on/product-composite-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      rabbitmq:
        condition: service_healthy
      auth-server:
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

  gateway:
    build: spring-cloud/gateway
    image: hands-on/gateway
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
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
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

  config-server:
    build: spring-cloud/config-server
    image: hands-on/config-server
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,native
      - ENCRYPT_KEY=${CONFIG_SERVER_ENCRYPT_KEY}
      - SPRING_SECURITY_USER_NAME=${CONFIG_SERVER_USR}
      - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
    volumes:
      - $PWD/config-repo:/config-repo

  zipkin-server:
    image: openzipkin/zipkin:3.5.0
    restart: always
    mem_limit: 1024m
    environment:
      - STORAGE_TYPE=mem
    ports:
      - 9411:9411
```

</details>

#### `docker-compose.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,6 +1,7 @@
 services:
   product:
     build: microservices/product-service
+    image: hands-on/product-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
@@ -14,6 +15,7 @@
 
   recommendation:
     build: microservices/recommendation-service
+    image: hands-on/recommendation-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
@@ -27,6 +29,7 @@
 
   review:
     build: microservices/review-service
+    image: hands-on/review-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
@@ -40,6 +43,7 @@
 
   product-composite:
     build: microservices/product-composite-service
+    image: hands-on/product-composite-service
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
@@ -91,16 +95,9 @@
       timeout: 2s
       retries: 60
 
-  eureka:
-    build: spring-cloud/eureka-server
-    mem_limit: 512m
-    environment:
-    - SPRING_PROFILES_ACTIVE=docker
-    - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-    - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
-
   gateway:
     build: spring-cloud/gateway
+    image: hands-on/gateway
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
@@ -114,19 +111,21 @@
 
   auth-server:
     build: spring-cloud/authorization-server
+    image: hands-on/auth-server
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
       - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
       - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
     healthcheck:
-      test: ["CMD", "wget", "-O -", "-q", "http://localhost:9999/actuator/health"]
+      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
       interval: 5s
       timeout: 2s
       retries: 60
 
   config-server:
     build: spring-cloud/config-server
+    image: hands-on/config-server
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,native
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
    image: hands-on/product-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  recommendation:
    build: microservices/recommendation-service
    image: hands-on/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mongodb:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  review:
    build: microservices/review-service
    image: hands-on/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      mysql:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  product-composite:
    build: microservices/product-composite-service
    image: hands-on/product-composite-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    depends_on:
      rabbitmq:
        condition: service_healthy
      auth-server:
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

  gateway:
    build: spring-cloud/gateway
    image: hands-on/gateway
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
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
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

  config-server:
    build: spring-cloud/config-server
    image: hands-on/config-server
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker,native
      - ENCRYPT_KEY=${CONFIG_SERVER_ENCRYPT_KEY}
      - SPRING_SECURITY_USER_NAME=${CONFIG_SERVER_USR}
      - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
    volumes:
      - $PWD/config-repo:/config-repo

  zipkin-server:
    image: openzipkin/zipkin:3.5.0
    restart: always
    mem_limit: 1024m
    environment:
      - STORAGE_TYPE=mem
    ports:
      - 9411:9411
```

</details>

#### `settings.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -10,7 +10,6 @@
 include ':microservices:review-service'
 include ':microservices:recommendation-service'
 include ':microservices:product-composite-service'
-include ':spring-cloud:eureka-server'
 include ':spring-cloud:gateway'
 include ':spring-cloud:authorization-server'
 include ':spring-cloud:config-server'
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
include ':spring-cloud:gateway'
include ':spring-cloud:authorization-server'
include ':spring-cloud:config-server'

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
@@ -1,16 +1,28 @@
 #!/usr/bin/env bash
 #
-# Sample usage:
-#
-#   HOST=localhost PORT=7001 ./test-em-all.bash
+# With Docker Compose:
+#
+# ./test-em-all.bash
+#
+# With Kubernetes in dev environment:
+#
+#   PORT=30443 USE_K8S=true ./test-em-all.bash
+#
+# With Kubernetes in prod environment:
+#
+#   CONFIG_SERVER_USR=prod-usr CONFIG_SERVER_PWD=prod-pwd PORT=30443 USE_K8S=true ./test-em-all.bash
 #
 : ${HOST=localhost}
 : ${PORT=8443}
+: ${USE_K8S=false}
 : ${PROD_ID_REVS_RECS=1}
 : ${PROD_ID_NOT_FOUND=13}
 : ${PROD_ID_NO_RECS=113}
 : ${PROD_ID_NO_REVS=213}
 : ${SKIP_CB_TESTS=false}
+: ${NAMESPACE=hands-on}
+: ${CONFIG_SERVER_USR=dev-usr}
+: ${CONFIG_SERVER_PWD=dev-pwd}
 
 function assertCurl() {
 
@@ -183,8 +195,15 @@
 
     echo "Start Circuit Breaker tests!"
 
+    if [[ $USE_K8S == "false" ]]
+    then
+        EXEC="docker compose exec -T product-composite"
+    else
+        EXEC="kubectl -n $NAMESPACE exec deploy/product-composite -- "
+    fi
+
     # First, use the health - endpoint to verify that the circuit breaker is closed
-    assertEqual "CLOSED" "$(docker compose exec -T product-composite wget -qO - http://product-composite:8080/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Open the circuit breaker by running three slow calls in a row, i.e. that cause a timeout exception
     # Also, verify that we get 500 back and a timeout related error message
@@ -196,7 +215,7 @@
     done
 
     # Verify that the circuit breaker is open
-    assertEqual "OPEN" "$(docker compose exec -T product-composite wget -qO - http://product-composite:8080/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "OPEN" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Verify that the circuit breaker now is open by running the slow call again, verify it gets 200 back, i.e. fail fast works, and a response from the fallback method.
     assertCurl 200 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS?delay=3 $AUTH -s"
@@ -215,7 +234,7 @@
     sleep 10
 
     # Verify that the circuit breaker is in half open state
-    assertEqual "HALF_OPEN" "$(docker compose exec -T product-composite wget -qO - http://product-composite:8080/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "HALF_OPEN" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Close the circuit breaker by running three normal calls in a row
     # Also, verify that we get 200 back and a response based on information in the product database
@@ -226,12 +245,12 @@
     done
 
     # Verify that the circuit breaker is in closed state again
-    assertEqual "CLOSED" "$(docker compose exec -T product-composite wget -qO - http://product-composite:8080/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Verify that the expected state transitions happened in the circuit breaker
-    assertEqual "CLOSED_TO_OPEN"      "$(docker compose exec -T product-composite wget -qO - http://product-composite:8080/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
-    assertEqual "OPEN_TO_HALF_OPEN"   "$(docker compose exec -T product-composite wget -qO - http://product-composite:8080/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
-    assertEqual "HALF_OPEN_TO_CLOSED" "$(docker compose exec -T product-composite wget -qO - http://product-composite:8080/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
+    assertEqual "CLOSED_TO_OPEN"      "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
+    assertEqual "OPEN_TO_HALF_OPEN"   "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
+    assertEqual "HALF_OPEN_TO_CLOSED" "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
 }
 
 set -e
@@ -240,6 +259,7 @@
 
 echo "HOST=${HOST}"
 echo "PORT=${PORT}"
+echo "USE_K8S=${USE_K8S}"
 echo "SKIP_CB_TESTS=${SKIP_CB_TESTS}"
 
 if [[ $@ == *"start"* ]]
@@ -257,21 +277,11 @@
 echo ACCESS_TOKEN=$ACCESS_TOKEN
 AUTH="-H \"Authorization: Bearer $ACCESS_TOKEN\""
 
-# Verify access to Eureka and that all microservices are registered in Eureka
-# Wait until all microservices are registered in Eureka; a registration can take a few seconds
-# after the health check is OK, especially when several instances start at the same time
-for i in $(seq 1 30); do
-  [ "$(curl -H 'accept:application/json' -k https://u:p@$HOST:$PORT/eureka/api/apps -s | jq ".applications.application | length")" = "6" ] && break
-  sleep 2
-done
-assertCurl 200 "curl -H "accept:application/json" -k https://u:p@$HOST:$PORT/eureka/api/apps -s"
-assertEqual 6 $(echo $RESPONSE | jq ".applications.application | length")
-
 # Verify access to the Config server and that its encrypt/decrypt endpoints work
-assertCurl 200 "curl -H "accept:application/json" -k https://dev-usr:dev-pwd@$HOST:$PORT/config/product/docker -s"
+assertCurl 200 "curl -H "accept:application/json" -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/product/docker -s"
 TEST_VALUE="hello-world"
-ENCRYPTED_VALUE=$(curl -k https://dev-usr:dev-pwd@$HOST:$PORT/config/encrypt --data-urlencode "$TEST_VALUE" -s)
-DECRYPTED_VALUE=$(curl -k https://dev-usr:dev-pwd@$HOST:$PORT/config/decrypt -d $ENCRYPTED_VALUE -s)
+ENCRYPTED_VALUE=$(curl -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/encrypt --data-urlencode "$TEST_VALUE" -s)
+DECRYPTED_VALUE=$(curl -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/decrypt -d $ENCRYPTED_VALUE -s)
 assertEqual "$TEST_VALUE" "$DECRYPTED_VALUE"
 
 setupTestdata
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="test-em-all.bash" op="write" nl="1" -->
```bash
#!/usr/bin/env bash
#
# With Docker Compose:
#
# ./test-em-all.bash
#
# With Kubernetes in dev environment:
#
#   PORT=30443 USE_K8S=true ./test-em-all.bash
#
# With Kubernetes in prod environment:
#
#   CONFIG_SERVER_USR=prod-usr CONFIG_SERVER_PWD=prod-pwd PORT=30443 USE_K8S=true ./test-em-all.bash
#
: ${HOST=localhost}
: ${PORT=8443}
: ${USE_K8S=false}
: ${PROD_ID_REVS_RECS=1}
: ${PROD_ID_NOT_FOUND=13}
: ${PROD_ID_NO_RECS=113}
: ${PROD_ID_NO_REVS=213}
: ${SKIP_CB_TESTS=false}
: ${NAMESPACE=hands-on}
: ${CONFIG_SERVER_USR=dev-usr}
: ${CONFIG_SERVER_PWD=dev-pwd}

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
        EXEC="kubectl -n $NAMESPACE exec deploy/product-composite -- "
    fi

    # First, use the health - endpoint to verify that the circuit breaker is closed
    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Open the circuit breaker by running three slow calls in a row, i.e. that cause a timeout exception
    # Also, verify that we get 500 back and a timeout related error message
    for ((n=0; n<3; n++))
    do
        assertCurl 500 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS?delay=3 $AUTH -s"
        message=$(echo $RESPONSE | jq -r .message)
        assertEqual "Did not observe any item or terminal signal within 2000ms" "${message:0:57}"
    done

    # Verify that the circuit breaker is open
    assertEqual "OPEN" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

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
    assertEqual "HALF_OPEN" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Close the circuit breaker by running three normal calls in a row
    # Also, verify that we get 200 back and a response based on information in the product database
    for ((n=0; n<3; n++))
    do
        assertCurl 200 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS $AUTH -s"
        assertEqual "product name C" "$(echo "$RESPONSE" | jq -r .name)"
    done

    # Verify that the circuit breaker is in closed state again
    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"

    # Verify that the expected state transitions happened in the circuit breaker
    assertEqual "CLOSED_TO_OPEN"      "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
    assertEqual "OPEN_TO_HALF_OPEN"   "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
    assertEqual "HALF_OPEN_TO_CLOSED" "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
}

set -e

echo "Start Tests:" `date`

echo "HOST=${HOST}"
echo "PORT=${PORT}"
echo "USE_K8S=${USE_K8S}"
echo "SKIP_CB_TESTS=${SKIP_CB_TESTS}"

if [[ $@ == *"start"* ]]
then
  echo "Restarting the test environment..."
  echo "$ docker compose down --remove-orphans"
  docker compose down --remove-orphans
  echo "$ docker compose up -d"
  docker compose up -d
fi

waitForService curl -k https://$HOST:$PORT/actuator/health

ACCESS_TOKEN=$(curl -k https://writer:secret-writer@$HOST:$PORT/oauth2/token -d grant_type=client_credentials -d scope="product:read product:write" -s | jq .access_token -r)
echo ACCESS_TOKEN=$ACCESS_TOKEN
AUTH="-H \"Authorization: Bearer $ACCESS_TOKEN\""

# Verify access to the Config server and that its encrypt/decrypt endpoints work
assertCurl 200 "curl -H "accept:application/json" -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/product/docker -s"
TEST_VALUE="hello-world"
ENCRYPTED_VALUE=$(curl -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/encrypt --data-urlencode "$TEST_VALUE" -s)
DECRYPTED_VALUE=$(curl -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/decrypt -d $ENCRYPTED_VALUE -s)
assertEqual "$TEST_VALUE" "$DECRYPTED_VALUE"

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
assertEqual "https://$HOST:$PORT" "$(echo $RESPONSE | jq -r '.servers[0].url')"
assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/v3/api-docs.yaml"

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

유레카 클라이언트 의존성을 지웁니다.

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,11 +31,9 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
-    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation 'org.springframework.cloud:spring-cloud-starter-config'
     implementation 'org.springframework.cloud:spring-cloud-config-client'
     // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
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
    implementation 'org.springframework.cloud:spring-cloud-starter-config'
    implementation 'org.springframework.cloud:spring-cloud-config-client'
    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
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

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -22,9 +22,7 @@
 import se.magnus.microservices.core.product.persistence.ProductRepository;
 
 @AutoConfigureWebTestClient
-@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
-  "eureka.client.enabled=false",
-  "spring.cloud.config.enabled=false"})
+@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"spring.cloud.config.enabled=false"})
 class ProductServiceApplicationTests extends MongoDbTestBase {
 
   @Autowired
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java" op="write" nl="1" -->
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
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"spring.cloud.config.enabled=false"})
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

유레카 클라이언트 의존성을 지웁니다.

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,11 +31,9 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
-    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation 'org.springframework.cloud:spring-cloud-starter-config'
     implementation 'org.springframework.cloud:spring-cloud-config-client'
     // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
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
    implementation 'org.springframework.cloud:spring-cloud-starter-config'
    implementation 'org.springframework.cloud:spring-cloud-config-client'
    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
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

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -22,9 +22,7 @@
 import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;
 
 @AutoConfigureWebTestClient
-@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
-  "eureka.client.enabled=false",
-  "spring.cloud.config.enabled=false"})
+@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"spring.cloud.config.enabled=false"})
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
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"spring.cloud.config.enabled=false"})
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

유레카 클라이언트 의존성을 지웁니다.

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,11 +31,9 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
-    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation 'org.springframework.cloud:spring-cloud-starter-config'
     implementation 'org.springframework.cloud:spring-cloud-config-client'
     // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
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
    implementation 'org.springframework.cloud:spring-cloud-starter-config'
    implementation 'org.springframework.cloud:spring-cloud-config-client'
    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
    implementation 'net.ttddyy.observation:datasource-micrometer-spring-boot:2.2.1'
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

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -25,7 +25,6 @@
 @SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
   "spring.cloud.stream.defaultBinder=rabbit",
   "logging.level.se.magnus=DEBUG",
-  "eureka.client.enabled=false",
   "spring.jpa.hibernate.ddl-auto=update",
   "spring.cloud.config.enabled=false"})
 class ReviewServiceApplicationTests extends MySqlTestBase {
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
  "spring.jpa.hibernate.ddl-auto=update",
  "spring.cloud.config.enabled=false"})
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

유레카 관련 코드를 지우고, `app.resilience.enabled` 값으로 Resilience4j를 끌 수 있게 하는 `ResilienceConfig`를 추가합니다.

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -35,19 +35,16 @@
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
     implementation 'org.springframework.boot:spring-boot-starter-webclient'
-    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.boot:spring-boot-starter-security'
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation 'org.springframework.cloud:spring-cloud-starter-config'
     implementation 'org.springframework.cloud:spring-cloud-config-client'
     // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
     implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
     implementation 'org.springframework.retry:spring-retry'
-    implementation 'org.springframework.cloud:spring-cloud-starter-loadbalancer'
     implementation 'io.micrometer:micrometer-tracing-bridge-otel'
     implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
     implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
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
    implementation 'org.springframework.cloud:spring-cloud-starter-config'
    implementation 'org.springframework.cloud:spring-cloud-config-client'
    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
    implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:3.0.3'
    implementation "io.github.resilience4j:resilience4j-spring-boot4:${resilience4jVersion}"
    implementation "io.github.resilience4j:resilience4j-reactor:${resilience4jVersion}"
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'

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

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -7,11 +7,9 @@
 import io.swagger.v3.oas.models.info.License;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
-import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.beans.factory.annotation.Value;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
-import org.springframework.cloud.client.loadbalancer.reactive.ReactorLoadBalancerExchangeFilterFunction;
 import org.springframework.context.annotation.Bean;
 import org.springframework.context.annotation.ComponentScan;
 import org.springframework.web.reactive.function.client.WebClient;
@@ -78,12 +76,9 @@
     return Schedulers.newBoundedElastic(threadPoolSize, taskQueueSize, "publish-pool");
   }
 
-  @Autowired
-  private ReactorLoadBalancerExchangeFilterFunction lbFunction;
-
   @Bean
-  WebClient webClient(WebClient.Builder builder) {
-    return builder.filter(lbFunction).build();
+  public WebClient webClient(WebClient.Builder builder) {
+    return builder.build();
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
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Hooks;
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

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ResilienceConfig.java` — 새 파일 (43줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ResilienceConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.retry.RetryRegistry;
import io.github.resilience4j.timelimiter.TimeLimiterRegistry;
import java.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ResilienceConfig {

  private static final Logger LOG = LoggerFactory.getLogger(ResilienceConfig.class);

  public ResilienceConfig(
    @Value("${app.resilience.enabled:true}") String resilienceEnabledStr,
    CircuitBreakerRegistry circuitBreakerRegistry,
    TimeLimiterRegistry timeLimiterRegistry,
    RetryRegistry retryRegistry
  ) {

    // Convert resilienceEnabledStr to boolean, only set to false if set to "false" (i.e. null or a value other than "false" will be true)
    boolean resilienceEnabled = !("false".equalsIgnoreCase(resilienceEnabledStr));
    LOG.debug("Resilience4j is enabled: {} ({})", resilienceEnabled, resilienceEnabledStr);
    
    // Disable use of Resilience4j if "app.resilience.enabled = false"
    if (!resilienceEnabled) {
      LOG.warn("Resilience4j is disabled (\"app.resilience.enabled = {}\"). CircuitBreaker, TimeLimiter and Retry are not used.", resilienceEnabledStr);
      circuitBreakerRegistry.remove("product");
      // Removing the time limiter is not sufficient due to a default time limiter that kicks in
      // Instead, we replace the time limiter with a long timeout to avoid the default time limiter kicking in.
      // timeLimiterRegistry.remove("product");
      retryRegistry.remove("product");
      timeLimiterRegistry.replace("product", io.github.resilience4j.timelimiter.TimeLimiter.of(Duration.ofHours(24)));
      LOG.warn("Instead of disabling the timelimiter, a loooong time out of {} will be used", 
        timeLimiterRegistry.find("product").get().getTimeLimiterConfig().getTimeoutDuration());
    }

  }

}
```

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/MessagingTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -41,7 +41,6 @@
   properties = {
     "spring.security.oauth2.resourceserver.jwt.issuer-uri=",
     "spring.main.allow-bean-definition-overriding=true",
-    "eureka.client.enabled=false",
     "spring.cloud.stream.defaultBinder=rabbit",
     "spring.cloud.config.enabled=false"})
 @Import({TestChannelBinderConfiguration.class})
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
  webEnvironment = RANDOM_PORT,
  classes = {TestSecurityConfig.class},
  properties = {
    "spring.security.oauth2.resourceserver.jwt.issuer-uri=",
    "spring.main.allow-bean-definition-overriding=true",
    "spring.cloud.stream.defaultBinder=rabbit",
    "spring.cloud.config.enabled=false"})
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
@@ -32,7 +32,6 @@
   properties = {
     "spring.security.oauth2.resourceserver.jwt.issuer-uri=",
     "spring.main.allow-bean-definition-overriding=true",
-    "eureka.client.enabled=false",
     "spring.cloud.config.enabled=false"})
 class ProductCompositeServiceApplicationTests {
 
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import static java.util.Collections.singletonList;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
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
@SpringBootTest(
  webEnvironment = RANDOM_PORT,
  classes = {TestSecurityConfig.class},
  properties = {
    "spring.security.oauth2.resourceserver.jwt.issuer-uri=",
    "spring.main.allow-bean-definition-overriding=true",
    "spring.cloud.config.enabled=false"})
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

    when(compositeIntegration.getProduct(eq(PRODUCT_ID_OK), anyInt(), anyInt()))
      .thenReturn(Mono.just(new Product(PRODUCT_ID_OK, "name", 1, "mock-address")));

    when(compositeIntegration.getRecommendations(PRODUCT_ID_OK))
      .thenReturn(Flux.fromIterable(singletonList(new Recommendation(PRODUCT_ID_OK, 1, "author", 1, "content", "mock address"))));

    when(compositeIntegration.getReviews(PRODUCT_ID_OK))
      .thenReturn(Flux.fromIterable(singletonList(new Review(PRODUCT_ID_OK, 1, "author", "subject", "content", "mock address"))));

    when(compositeIntegration.getProduct(eq(PRODUCT_ID_NOT_FOUND), anyInt(), anyInt())).thenThrow(new NotFoundException("NOT FOUND: " + PRODUCT_ID_NOT_FOUND));

    when(compositeIntegration.getProduct(eq(PRODUCT_ID_INVALID), anyInt(), anyInt())).thenThrow(new InvalidInputException("INVALID: " + PRODUCT_ID_INVALID));
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

쿠버네티스 서비스가 서비스 검색을 대신하므로 프로젝트를 통째로 지웁니다: `rm -r spring-cloud/eureka-server`

**지울 파일**

```bash
rm spring-cloud/eureka-server/.gitignore
rm spring-cloud/eureka-server/Dockerfile
rm spring-cloud/eureka-server/build.gradle
rm spring-cloud/eureka-server/settings.gradle
rm spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/EurekaServerApplication.java
rm spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/SecurityConfig.java
rm spring-cloud/eureka-server/src/main/resources/bootstrap.yml
rm spring-cloud/eureka-server/src/test/java/se/magnus/springcloud/eurekaserver/EurekaServerApplicationTests.java
rm spring-cloud/eureka-server/src/test/resources/application.yml
```

<!-- wb:file path="spring-cloud/eureka-server/.gitignore" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/eureka-server/Dockerfile" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/eureka-server/build.gradle" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/eureka-server/settings.gradle" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/EurekaServerApplication.java" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/SecurityConfig.java" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/eureka-server/src/main/resources/bootstrap.yml" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/eureka-server/src/test/java/se/magnus/springcloud/eurekaserver/EurekaServerApplicationTests.java" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/eureka-server/src/test/resources/application.yml" op="delete" nl="0" -->

<a id="단계-7"></a>

## 단계 7. `gateway` — 에지 서버

유레카 관련 의존성과 설정을 지웁니다.

#### `spring-cloud/gateway/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,8 +31,6 @@
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
     implementation 'org.springframework.cloud:spring-cloud-starter-gateway-server-webflux'
     implementation 'org.springframework.boot:spring-boot-starter-webclient'
-    implementation 'org.springframework.boot:spring-boot-starter-restclient'
-    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
     implementation 'org.springframework.cloud:spring-cloud-starter-config'
     implementation 'org.springframework.cloud:spring-cloud-config-client'
     // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/gateway/build.gradle" op="write" nl="1" -->
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
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
    implementation 'org.springframework.cloud:spring-cloud-starter-gateway-server-webflux'
    implementation 'org.springframework.boot:spring-boot-starter-webclient'
    implementation 'org.springframework.cloud:spring-cloud-starter-config'
    implementation 'org.springframework.cloud:spring-cloud-config-client'
    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
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

#### `spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/SecurityConfig.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -19,7 +19,6 @@
         .authorizeExchange(exchange -> exchange
           .pathMatchers("/headerrouting/**").permitAll()
           .pathMatchers("/actuator/**").permitAll()
-          .pathMatchers("/eureka/**").permitAll()
           .pathMatchers("/oauth2/**").permitAll()
           .pathMatchers("/login/**").permitAll()
           .pathMatchers("/error/**").permitAll()
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/SecurityConfig.java" op="write" nl="0" -->
```java

package se.magnus.springcloud.gateway;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.web.server.SecurityWebFilterChain;

@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

  @Bean
  SecurityWebFilterChain springSecurityFilterChain(ServerHttpSecurity http) throws Exception {
    http
      .csrf(csrf -> csrf.disable()
        .authorizeExchange(exchange -> exchange
          .pathMatchers("/headerrouting/**").permitAll()
          .pathMatchers("/actuator/**").permitAll()
          .pathMatchers("/oauth2/**").permitAll()
          .pathMatchers("/login/**").permitAll()
          .pathMatchers("/error/**").permitAll()
          .pathMatchers("/openapi/**").permitAll()
          .pathMatchers("/config/**").permitAll()
          .anyExchange().authenticated()))
      .oauth2ResourceServer(server -> server
        .jwt(Customizer.withDefaults()));
    return http.build();
  }

}
```

</details>

#### `spring-cloud/gateway/src/test/java/se/magnus/springcloud/gateway/GatewayApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="spring-cloud/gateway/src/test/java/se/magnus/springcloud/gateway/GatewayApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.springcloud.gateway;

import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"spring.cloud.config.enabled=false"})
class GatewayApplicationTests {

  @Test
  void contextLoads() {
  }

}
```

**중간 확인**

```bash
./gradlew :spring-cloud:gateway:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-8"></a>

## 단계 8. `authorization-server` — OAuth 2.0 인가 서버

유레카 관련 의존성을 지우고, `Dockerfile`의 노출 포트를 80으로 바꿉니다(쿠버네티스 서비스 포트와 맞춤).

#### `spring-cloud/authorization-server/Dockerfile` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="spring-cloud/authorization-server/Dockerfile" op="write" nl="0" -->
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

EXPOSE 80

ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

#### `spring-cloud/authorization-server/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -25,8 +25,6 @@
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-authorization-server'
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-security'
-    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
-    implementation 'org.springframework.boot:spring-boot-starter-restclient'
     implementation 'org.springframework.cloud:spring-cloud-starter-config'
     implementation 'org.springframework.cloud:spring-cloud-config-client'
     // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
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

ext {
    springCloudVersion = '2025.1.4'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-authorization-server'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.cloud:spring-cloud-starter-config'
    implementation 'org.springframework.cloud:spring-cloud-config-client'
    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webmvc-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-security-test'
    testImplementation 'org.htmlunit:htmlunit'
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

#### `spring-cloud/authorization-server/src/main/java/sample/config/AuthorizationServerConfig.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -156,7 +156,7 @@
 
   @Bean
   public AuthorizationServerSettings authorizationServerSettings() {
-    return AuthorizationServerSettings.builder().issuer("http://auth-server:9999").build();
+    return AuthorizationServerSettings.builder().issuer("http://auth-server").build();
   }
 
   private Consumer<List<AuthenticationProvider>> configureAuthenticationValidator() {
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
import org.springframework.security.config.annotation.web.configurers.oauth2.server.resource.OAuth2ResourceServerConfigurer;
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

#### `spring-cloud/authorization-server/src/test/java/sample/OAuth2AuthorizationServerApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -35,7 +35,7 @@
  *
  * @author Josh Cummings
  */
-@SpringBootTest(properties = {"eureka.client.enabled=false", "spring.cloud.config.enabled=false"})
+@SpringBootTest(properties = {"spring.cloud.config.enabled=false"})
 @AutoConfigureMockMvc
 class OAuth2AuthorizationServerApplicationTests {
 
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/authorization-server/src/test/java/sample/OAuth2AuthorizationServerApplicationTests.java" op="write" nl="1" -->
```java
//CHECKSTYLE:OFF
/*
 * Copyright 2002-2018 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package sample;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.hamcrest.core.Is.is;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Base64;

/**
 * Tests for {@link OAuth2AuthorizationServerApplication}.
 *
 * @author Josh Cummings
 */
@SpringBootTest(properties = {"spring.cloud.config.enabled=false"})
@AutoConfigureMockMvc
class OAuth2AuthorizationServerApplicationTests {

  @Autowired
  MockMvc mvc;

  @Test
  void requestTokenUsingClientCredentialsGrantType() throws Exception {

    String base64Credentials = Base64.getEncoder().encodeToString("writer:secret-writer".getBytes());
    this.mvc.perform(post("/oauth2/token")
      .param("grant_type", "client_credentials")
      .header("Authorization", "Basic " + base64Credentials))
        .andExpect(status().isOk());
  }

  @Test
  void requestOpenidConfiguration() throws Exception {

    this.mvc.perform(get("/.well-known/openid-configuration"))
        .andExpect(status().isOk());
  }

  @Test
  void requestJwkSet() throws Exception {

    this.mvc.perform(get("/oauth2/jwks"))
        .andExpect(status().isOk());
  }

  @Test
  void healthy() throws Exception {
    this.mvc.perform(get("/actuator/health"))
      .andExpect(status().isOk())
      .andExpect(jsonPath("$.status", is("UP")));
  }

}
//CHECKSTYLE:ON
```

</details>

**중간 확인**

```bash
./gradlew :spring-cloud:authorization-server:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-9"></a>

## 단계 9. `config-server` — 구성 서버

쿠버네티스의 프로브 경로를 인증 없이 열어 둡니다.

#### `spring-cloud/config-server/src/main/java/se/magnus/springcloud/configserver/SecurityConfig.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="spring-cloud/config-server/src/main/java/se/magnus/springcloud/configserver/SecurityConfig.java" op="write" nl="1" -->
```java
package se.magnus.springcloud.configserver;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

  @Bean
  public SecurityFilterChain configure(HttpSecurity http) throws Exception {
    // Disable CSRF to allow POST to /encrypt and /decrypt endpoints
    http.csrf(csrf -> csrf.disable())
        .authorizeHttpRequests(requests -> requests
          .requestMatchers("/actuator/**").permitAll()
          .anyRequest().authenticated())
        .httpBasic(Customizer.withDefaults());
    return http.build();
  }
}
```

**중간 확인**

```bash
./gradlew :spring-cloud:config-server:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-10"></a>

## 단계 10. `config-repo` — 중앙 구성 파일

유레카 설정을 지우고, 그레이스풀 셧다운과 프로브(`management.endpoint.health.probes`) 설정을 추가합니다. 서비스 주소는 쿠버네티스 서비스 이름을 씁니다.

**지울 파일**

```bash
rm config-repo/eureka-server.yml
```

<!-- wb:file path="config-repo/eureka-server.yml" op="delete" nl="0" -->

#### `config-repo/application.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="config-repo/application.yml" op="write" nl="1" -->
```yaml
app:
  auth-server: localhost

spring.rabbitmq:
  host: 127.0.0.1
  port: 5672
  username: guest
  password: '{cipher}17fcf0ae5b8c5cf87de6875b699be4a1746dd493a99d926c7a26a68c422117ef'

spring.cloud.stream.kafka.binder:
  brokers: 127.0.0.1
  defaultBrokerPort: 9092

spring.cloud.stream.defaultBinder: rabbit

# WARNING: Exposing all management endpoints over http should only be used during development, must be locked down in production!
management.endpoint.health.show-details: "ALWAYS"
management.endpoints.web.exposure.include: "*"
management.endpoint.health.probes.enabled: true
management.health.rabbit.enabled: true
management.health.kafka.enabled: false

management.tracing.export.zipkin.endpoint: http://zipkin-server:9411/api/v2/spans
management.tracing.sampling.probability: 1.0

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

# Only allow management endpoints over http in production for info, health and circuitbreakerevents
management.endpoints.web.exposure.include: health,info,circuitbreakerevents
```

#### `config-repo/auth-server.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="config-repo/auth-server.yml" op="write" nl="0" -->
```yaml
server.port: 9999
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

#### `config-repo/gateway.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="config-repo/gateway.yml" op="write" nl="1" -->
```yaml
server.port: 8443

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
    password: '{cipher}d59274473b196cebe288f849c442eba34aa497d14a13e10a23f824489e1c23ec'

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

- id: config-server
  uri: ${spring.cloud.config.uri}
  predicates:
  - Path=/config/**
  filters:
  - RewritePath=/config/(?<segment>.*), /$\{segment}

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

#### `config-repo/product-composite.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -78,6 +78,10 @@
 server.port: 7001
 spring.web.error.include-message: always
 
+spring.application.name: product-composite
+
+management.endpoint.health.group.readiness.include: readinessState, rabbit
+
 # Create the output bindings at startup. Otherwise StreamBridge creates them lazily on the first send,
 # and the three events sent in parallel can race (MessageDeliveryException: Dispatcher has no subscribers).
 spring.cloud.stream.output-bindings: products-out-0;recommendations-out-0;reviews-out-0
@@ -98,7 +102,7 @@
       producer:
         required-groups: auditGroup
 
-spring.security.oauth2.resourceserver.jwt.issuer-uri: http://${app.auth-server}:9999
+spring.security.oauth2.resourceserver.jwt.issuer-uri: http://${app.auth-server}
 
 resilience4j.timelimiter:
   instances:
@@ -147,7 +151,7 @@
 ---
 spring.config.activate.on-profile: docker
 
-server.port: 8080
+server.port: 80
 
 ---
 spring.config.activate.on-profile: streaming_partitioned
@@ -163,3 +167,17 @@
 spring.cloud.stream.bindings.reviews-out-0.producer:
   partition-key-expression: headers['partitionKey']
   partition-count: 2
+
+---
+spring.config.activate.on-profile: kafka
+
+management.endpoint.health.group.readiness.include: readinessState
+
+---
+spring.config.activate.on-profile: prod
+
+logging:
+  level:
+    root: WARN
+    se.magnus: WARN
+    org.springframework.web.server.adapter.HttpWebHandlerAdapter: WARN
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/product-composite.yml" op="write" nl="1" -->
```yaml
springdoc:
  swagger-ui.path: /openapi/swagger-ui.html
  api-docs.path: /openapi/v3/api-docs
  packagesToScan: se.magnus.microservices.composite.product
  pathsToMatch: /**
  cache.disabled: true

  swagger-ui:
    oauth2-redirect-url: /swagger-ui/oauth2-redirect.html
    oauth:
      clientId: writer
      clientSecret: '{cipher}debb77857798ba70441b229de88624213b0a00b284f95fe31d1378d117cf3ffa'
      useBasicAuthenticationWithAccessCodeGrant: true
  oAuthFlow:
    authorizationUrl: https://localhost:8443/oauth2/authorize
    tokenUrl: https://localhost:8443/oauth2/token

server.forward-headers-strategy: framework

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

management.endpoint.health.group.readiness.include: readinessState, rabbit

# Create the output bindings at startup. Otherwise StreamBridge creates them lazily on the first send,
# and the three events sent in parallel can race (MessageDeliveryException: Dispatcher has no subscribers).
spring.cloud.stream.output-bindings: products-out-0;recommendations-out-0;reviews-out-0

spring.cloud.stream:
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

spring.security.oauth2.resourceserver.jwt.issuer-uri: http://${app.auth-server}

resilience4j.timelimiter:
  instances:
    product:
      timeoutDuration: 2s

resilience4j.retry:
  instances:
    product:
      maxAttempts: 3
      waitDuration: 1000
      retryExceptions:
      - org.springframework.web.reactive.function.client.WebClientResponseException$InternalServerError

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

logging:
  level:
    root: INFO
    se.magnus: INFO
    org.springframework.web.server.adapter.HttpWebHandlerAdapter: INFO

# To see tracing headers, uncomment the following two lines and restart the product-composite service
# spring.codec.log-request-details: true
# logging.level.org.springframework.web.reactive.function.client.ExchangeFunctions: TRACE

---
spring.config.activate.on-profile: docker

server.port: 80

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

management.endpoint.health.group.readiness.include: readinessState

---
spring.config.activate.on-profile: prod

logging:
  level:
    root: WARN
    se.magnus: WARN
    org.springframework.web.server.adapter.HttpWebHandlerAdapter: WARN
```

</details>

#### `config-repo/product.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,9 @@
 server.port: 7002
 spring.web.error.include-message: always
+
+spring.application.name: product
+
+management.endpoint.health.group.readiness.include: readinessState, rabbit, mongo
 
 spring.mongodb:
   host: localhost
@@ -36,7 +40,7 @@
 ---
 spring.config.activate.on-profile: docker
 
-server.port: 8080
+server.port: 80
 
 spring.mongodb.host: mongodb
 
@@ -56,3 +60,19 @@
 spring.config.activate.on-profile: streaming_instance_1
 
 spring.cloud.stream.bindings.messageProcessor-in-0.consumer.instanceIndex: 1
+
+---
+spring.config.activate.on-profile: kafka
+
+management.endpoint.health.group.readiness.include: readinessState, mongo
+
+---
+spring.config.activate.on-profile: prod
+
+spring.mongodb.host: 172.17.0.1
+
+logging:
+  level:
+    root: WARN
+    se.magnus: WARN
+    org.springframework.data.mongodb.core.MongoTemplate: WARN
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/product.yml" op="write" nl="1" -->
```yaml
server.port: 7002
spring.web.error.include-message: always

spring.application.name: product

management.endpoint.health.group.readiness.include: readinessState, rabbit, mongo

spring.mongodb:
  host: localhost
  port: 27017
  database: product-db

spring.cloud.function.definition: messageProcessor

spring.cloud.stream:
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

logging:
  level:
    root: INFO
    se.magnus: INFO
    org.springframework.data.mongodb.core.ReactiveMongoTemplate: DEBUG

---
spring.config.activate.on-profile: docker

server.port: 80

spring.mongodb.host: mongodb

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

management.endpoint.health.group.readiness.include: readinessState, mongo

---
spring.config.activate.on-profile: prod

spring.mongodb.host: 172.17.0.1

logging:
  level:
    root: WARN
    se.magnus: WARN
    org.springframework.data.mongodb.core.MongoTemplate: WARN
```

</details>

#### `config-repo/recommendation.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,9 @@
 server.port: 7003
 spring.web.error.include-message: always
+
+spring.application.name: recommendation
+
+management.endpoint.health.group.readiness.include: readinessState, rabbit, mongo
 
 spring.mongodb:
   host: localhost
@@ -36,7 +40,7 @@
 ---
 spring.config.activate.on-profile: docker
 
-server.port: 8080
+server.port: 80
 
 spring.mongodb.host: mongodb
 
@@ -56,3 +60,19 @@
 spring.config.activate.on-profile: streaming_instance_1
 
 spring.cloud.stream.bindings.messageProcessor-in-0.consumer.instanceIndex: 1
+
+---
+spring.config.activate.on-profile: kafka
+
+management.endpoint.health.group.readiness.include: readinessState, mongo
+
+---
+spring.config.activate.on-profile: prod
+
+spring.mongodb.host: 172.17.0.1
+
+logging:
+  level:
+    root: WARN
+    se.magnus: WARN
+    org.springframework.data.mongodb.core.MongoTemplate: WARN
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/recommendation.yml" op="write" nl="1" -->
```yaml
server.port: 7003
spring.web.error.include-message: always

spring.application.name: recommendation

management.endpoint.health.group.readiness.include: readinessState, rabbit, mongo

spring.mongodb:
  host: localhost
  port: 27017
  database: recommendation-db

spring.cloud.function.definition: messageProcessor

spring.cloud.stream:
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

logging:
  level:
    root: INFO
    se.magnus: INFO
    org.springframework.data.mongodb.core.ReactiveMongoTemplate: DEBUG

---
spring.config.activate.on-profile: docker

server.port: 80

spring.mongodb.host: mongodb

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

management.endpoint.health.group.readiness.include: readinessState, mongo

---
spring.config.activate.on-profile: prod

spring.mongodb.host: 172.17.0.1

logging:
  level:
    root: WARN
    se.magnus: WARN
    org.springframework.data.mongodb.core.MongoTemplate: WARN
```

</details>

#### `config-repo/review.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,9 @@
 server.port: 7004
 spring.web.error.include-message: always
+
+spring.application.name: review
+
+management.endpoint.health.group.readiness.include: readinessState, rabbit, db
 
 # Strongly recommend to set this property to "none" in a production environment!
 spring.jpa.hibernate.ddl-auto: update
@@ -42,7 +46,7 @@
 ---
 spring.config.activate.on-profile: docker
 
-server.port: 8080
+server.port: 80
 
 spring.datasource.url: jdbc:mysql://mysql/review-db
 
@@ -62,3 +66,20 @@
 spring.config.activate.on-profile: streaming_instance_1
 
 spring.cloud.stream.bindings.messageProcessor-in-0.consumer.instanceIndex: 1
+
+---
+spring.config.activate.on-profile: kafka
+
+management.endpoint.health.group.readiness.include: readinessState, db
+
+---
+spring.config.activate.on-profile: prod
+
+spring.datasource.url: jdbc:mysql://172.17.0.1:3306/review-db
+
+logging:
+  level:
+    root: WARN
+    se.magnus: WARN
+    org.hibernate.SQL: WARN
+    org.hibernate.type.descriptor.sql.BasicBinder: WARN
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
  url: jdbc:mysql://localhost/review-db
  username: user
  password: '{cipher}24b93c790fa2ed0dc5a6a2b8c39853cf4d6cd6100c248de5f279fb5dd78e7be6'

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

spring.datasource.url: jdbc:mysql://mysql/review-db

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

spring.datasource.url: jdbc:mysql://172.17.0.1:3306/review-db

logging:
  level:
    root: WARN
    se.magnus: WARN
    org.hibernate.SQL: WARN
    org.hibernate.type.descriptor.sql.BasicBinder: WARN
```

</details>

<a id="단계-11"></a>

## 단계 11. `kubernetes/helm` — 헬름 공통 파일

헬름이 만든 의존 차트 폴더를 Git에서 제외합니다.

#### `kubernetes/helm/.gitignore` — 복사/생성

Git이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요(치지 않아도 실습에는 지장이 없습니다).

<!-- wb:file path="kubernetes/helm/.gitignore" op="copy" nl="0" -->

<a id="단계-12"></a>

## 단계 12. 헬름 `common` 라이브러리 차트

모든 서비스 차트가 같이 쓰는 템플릿입니다. `_deployment.yaml`, `_service.yaml`, `_configmap_from_file.yaml`, `_secrets.yaml`과 기본값 `values.yaml`을 만듭니다.

#### `kubernetes/helm/common/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/common/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/common/Chart.yaml` — 새 파일 (6줄)

<!-- wb:file path="kubernetes/helm/common/Chart.yaml" op="write" nl="1" -->
```yaml
apiVersion: v2
name: common
type: library
description: A Helm library chart with shared definitions
version: 1.0.0
appVersion: "1.0"
```

#### `kubernetes/helm/common/templates/_configmap_from_file.yaml` — 새 파일 (12줄)

<!-- wb:file path="kubernetes/helm/common/templates/_configmap_from_file.yaml" op="write" nl="1" -->
```yaml
{{- define "common.configmap_from_file" -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ include "common.name" . }}
    helm.sh/chart: {{ include "common.chart" . }}
    app.kubernetes.io/managed-by: {{ .Release.Service }}
data:
{{ (.Files.Glob "config-repo/*").AsConfig | indent 2 }}
{{- end -}}
```

#### `kubernetes/helm/common/templates/_deployment.yaml` — 새 파일 (69줄)

<!-- wb:file path="kubernetes/helm/common/templates/_deployment.yaml" op="write" nl="0" -->
```yaml
{{- define "common.deployment" -}}
{{- $common := dict "Values" .Values.common -}} 
{{- $noCommon := omit .Values "common" -}} 
{{- $overrides := dict "Values" $noCommon -}} 
{{- $noValues := omit . "Values" -}} 
{{- with merge $noValues $overrides $common -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ include "common.name" . }}
    helm.sh/chart: {{ include "common.chart" . }}
    app.kubernetes.io/managed-by: {{ .Release.Service }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "common.name" . }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "common.name" . }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}/{{ .Values.image.name }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          {{- with .Values.image.args }}
          args:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- if .Values.env }}
          env:
          {{- range $key, $val := .Values.env }}
          - name: {{ $key }}
            value: {{ $val }}
          {{- end }}
          {{- end }}
          {{- if .Values.envFromSecretRefs }}
          envFrom:
          {{- range .Values.envFromSecretRefs }}
          - secretRef:
              name: {{ . }}
          {{- end }}
          {{- end }}
          {{- if .Values.livenessProbe_enabled }}
          livenessProbe:
{{ toYaml .Values.livenessProbe | indent 12 }}
          {{- end }}
          {{- if .Values.readinessProbe_enabled }}
          readinessProbe:
{{ toYaml .Values.readinessProbe | indent 12 }}
          {{- end }}
          ports:
{{ toYaml .Values.ports | indent 12 }}
          resources:
{{ toYaml .Values.resources | indent 12 }}
      {{- if .Values.configmap.enabled }}
          volumeMounts:
          - name: {{ include "common.fullname" . }}
            mountPath: {{ .Values.configmap.volumeMounts.mountPath }}
      volumes:
        - name: {{ include "common.fullname" . }}
          configMap:
            name: {{ include "common.fullname" . }}
      {{- end }}
{{- end -}}
{{- end -}}
```

#### `kubernetes/helm/common/templates/_helpers.tpl` — 새 파일 (31줄)

<!-- wb:file path="kubernetes/helm/common/templates/_helpers.tpl" op="write" nl="1" -->
```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "common.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "common.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "common.chart" }}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}
```

#### `kubernetes/helm/common/templates/_secrets.yaml` — 새 파일 (18줄)

<!-- wb:file path="kubernetes/helm/common/templates/_secrets.yaml" op="write" nl="1" -->
```yaml
{{- define "common.secrets" -}}
{{- range $secretName, $secretMap := .Values.secrets }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ $secretName }}
  labels:
    app.kubernetes.io/name: {{ $secretName }}
    helm.sh/chart: {{ include "common.chart" $ }}
    app.kubernetes.io/managed-by: {{ $.Release.Service }}
type: Opaque
data:
{{- range $key, $val := $secretMap }}
  {{ $key }}: {{ $val | b64enc }}
{{- end }}
---
{{- end -}}
{{- end -}}
```

#### `kubernetes/helm/common/templates/_service.yaml` — 새 파일 (22줄)

<!-- wb:file path="kubernetes/helm/common/templates/_service.yaml" op="write" nl="0" -->
```yaml
{{- define "common.service" -}}
{{- $common := dict "Values" .Values.common -}} 
{{- $noCommon := omit .Values "common" -}} 
{{- $overrides := dict "Values" $noCommon -}} 
{{- $noValues := omit . "Values" -}} 
{{- with merge $noValues $overrides $common -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ include "common.name" . }}
    helm.sh/chart: {{ include "common.chart" . }}
    app.kubernetes.io/managed-by: {{ .Release.Service }}
spec:
  type: {{ .Values.service.type }}
  ports:
{{ toYaml .Values.service.ports | indent 4 }}
  selector:
    app.kubernetes.io/name: {{ include "common.name" . }}
{{- end -}}
{{- end -}}
```

#### `kubernetes/helm/common/values.yaml` — 새 파일 (51줄)

<!-- wb:file path="kubernetes/helm/common/values.yaml" op="write" nl="1" -->
```yaml
replicaCount: 1

image:
  repository: hands-on
  tag: latest
  pullPolicy: Never
  args: []

ports:
  - name: http
    containerPort: 80
    protocol: TCP

livenessProbe_enabled: false
livenessProbe:
  httpGet:
    scheme: HTTP
    path: /actuator/health/liveness
    port: 80
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 20
  successThreshold: 1

readinessProbe_enabled: false
readinessProbe:
  httpGet:
    scheme: HTTP
    path: /actuator/health/readiness
    port: 80
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
  successThreshold: 1

configmap:
  enabled: false

resources:
  limits:
    memory: 400Mi

service:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: http
    protocol: TCP
    name: http
```

<a id="단계-13"></a>

## 단계 13. 헬름 `components` 차트 — 서비스별 차트

서비스마다 작은 차트를 만듭니다. 대부분 `common`의 템플릿을 한 줄로 불러오고, 이미지 이름과 포트 같은 값만 `values.yaml`에 적습니다. `config-server` 차트에는 `config-repo` 파일을 담습니다.

#### `kubernetes/helm/components/auth-server/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/auth-server/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/auth-server/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/auth-server/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/auth-server/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/auth-server/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Auth Server
name: auth-server
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/auth-server/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/auth-server/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/auth-server/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/auth-server/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/auth-server/values.yaml` — 새 파일 (11줄)

<!-- wb:file path="kubernetes/helm/components/auth-server/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: auth-server

image:
  name: auth-server

env:
  SPRING_PROFILES_ACTIVE: "docker"

livenessProbe_enabled: true

readinessProbe_enabled: true
```

#### `kubernetes/helm/components/config-server/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/config-server/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/config-server/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/config-server/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/config-server/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/config-server/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Config Server
name: config-server
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/config-server/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/config-server/config-repo && cp config-repo/application.yml kubernetes/helm/components/config-server/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/config-server/config-repo/auth-server.yml` — 새 파일 (`config-repo/auth-server.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/config-server/config-repo && cp config-repo/auth-server.yml kubernetes/helm/components/config-server/config-repo/auth-server.yml
```

<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/auth-server.yml" op="cp" src="config-repo/auth-server.yml" -->

#### `kubernetes/helm/components/config-server/config-repo/gateway.yml` — 새 파일 (`config-repo/gateway.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/config-server/config-repo && cp config-repo/gateway.yml kubernetes/helm/components/config-server/config-repo/gateway.yml
```

<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/gateway.yml" op="cp" src="config-repo/gateway.yml" -->

#### `kubernetes/helm/components/config-server/config-repo/product-composite.yml` — 새 파일 (`config-repo/product-composite.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/config-server/config-repo && cp config-repo/product-composite.yml kubernetes/helm/components/config-server/config-repo/product-composite.yml
```

<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/product-composite.yml" op="cp" src="config-repo/product-composite.yml" -->

#### `kubernetes/helm/components/config-server/config-repo/product.yml` — 새 파일 (`config-repo/product.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/config-server/config-repo && cp config-repo/product.yml kubernetes/helm/components/config-server/config-repo/product.yml
```

<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/product.yml" op="cp" src="config-repo/product.yml" -->

#### `kubernetes/helm/components/config-server/config-repo/recommendation.yml` — 새 파일 (`config-repo/recommendation.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/config-server/config-repo && cp config-repo/recommendation.yml kubernetes/helm/components/config-server/config-repo/recommendation.yml
```

<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/recommendation.yml" op="cp" src="config-repo/recommendation.yml" -->

#### `kubernetes/helm/components/config-server/config-repo/review.yml` — 새 파일 (`config-repo/review.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/config-server/config-repo && cp config-repo/review.yml kubernetes/helm/components/config-server/config-repo/review.yml
```

<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/review.yml" op="cp" src="config-repo/review.yml" -->

#### `kubernetes/helm/components/config-server/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/config-server/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/config-server/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/config-server/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/config-server/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/config-server/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/config-server/values.yaml` — 새 파일 (33줄)

<!-- wb:file path="kubernetes/helm/components/config-server/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: config-server

image:
  name: config-server

ports:
  - name: http
    containerPort: 8888
    protocol: TCP

env:
  SPRING_PROFILES_ACTIVE: "docker,native"

livenessProbe_enabled: true
livenessProbe:
  httpGet:
    port: 8888
readinessProbe_enabled: true
readinessProbe:
  httpGet:
    port: 8888

configmap:
  enabled: true
  volumeMounts:
    mountPath: /config-repo

service:
  ports:
  - port: 8888
    targetPort: http
    protocol: TCP
    name: http
```

#### `kubernetes/helm/components/gateway/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/gateway/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/gateway/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/gateway/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/gateway/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/gateway/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Spring Cloud Gateway
name: gateway
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/gateway/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/gateway/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/gateway/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/gateway/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/gateway/values.yaml` — 새 파일 (29줄)

<!-- wb:file path="kubernetes/helm/components/gateway/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: gateway

image:
  name: gateway

ports:
  - containerPort: 8443

env:
  SPRING_PROFILES_ACTIVE: "docker"

livenessProbe_enabled: true
livenessProbe:
  httpGet:
    scheme: HTTPS
    port: 8443
readinessProbe_enabled: true
readinessProbe:
  httpGet:
    scheme: HTTPS
    port: 8443

service:
  type: NodePort
  ports:
  - port: 443
    targetPort: 8443
    nodePort: 30443

```

#### `kubernetes/helm/components/mongodb/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/mongodb/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/mongodb/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/mongodb/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for MongoDB
name: mongodb
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/mongodb/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/mongodb/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/mongodb/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/mongodb/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/mongodb/values.yaml` — 새 파일 (14줄)

<!-- wb:file path="kubernetes/helm/components/mongodb/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: mongodb

image:
  repository: registry.hub.docker.com/library
  name: mongo
  tag: 8.0.5
  pullPolicy: IfNotPresent

ports:
  - containerPort: 27017

service:
  ports:
    - port: 27017
```

#### `kubernetes/helm/components/mysql/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/mysql/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/mysql/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/mysql/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for MySQL
name: mysql
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/mysql/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/mysql/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/mysql/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/mysql/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/mysql/values.yaml` — 새 파일 (18줄)

<!-- wb:file path="kubernetes/helm/components/mysql/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: mysql

image:
  repository: registry.hub.docker.com/library
  name: mysql
  tag: 9.2.0
  pullPolicy: IfNotPresent
ports:
  - containerPort: 3306

resources:
  limits:
    memory: 512Mi

service:
  ports:
    - port: 3306

```

#### `kubernetes/helm/components/product-composite/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/product-composite/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/product-composite/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/product-composite/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/product-composite/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/product-composite/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Product Composite microservice
name: product-composite
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/product-composite/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/product-composite/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/product-composite/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/product-composite/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/product-composite/values.yaml` — 새 파일 (12줄)

<!-- wb:file path="kubernetes/helm/components/product-composite/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: product-composite

image:
  name: product-composite-service

env:
  SPRING_PROFILES_ACTIVE: "docker"

livenessProbe_enabled: true

readinessProbe_enabled: true

```

#### `kubernetes/helm/components/product/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/product/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/product/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/product/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/product/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/product/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Product microservice
name: product
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/product/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/product/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/product/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/product/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/product/values.yaml` — 새 파일 (12줄)

<!-- wb:file path="kubernetes/helm/components/product/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: product

image:
  name: product-service

env:
  SPRING_PROFILES_ACTIVE: "docker"

livenessProbe_enabled: true

readinessProbe_enabled: true

```

#### `kubernetes/helm/components/rabbitmq/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/rabbitmq/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/rabbitmq/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/rabbitmq/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for RabbitMQ
name: rabbitmq
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/rabbitmq/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/rabbitmq/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/rabbitmq/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/rabbitmq/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/rabbitmq/values.yaml` — 새 파일 (35줄)

<!-- wb:file path="kubernetes/helm/components/rabbitmq/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: rabbitmq

image:
  repository: registry.hub.docker.com/library
  name: rabbitmq
  tag: 4.0.7-management
  pullPolicy: IfNotPresent

ports:
  - containerPort: 5671
  - containerPort: 5672
  - containerPort: 15672

readinessProbe_enabled: true
readinessProbe:
  httpGet:
    scheme: HTTP
    path: "/api/aliveness-test/%2F"
    port: 15672
    httpHeaders:
      - name: Authorization
        value: Basic Z3Vlc3Q6Z3Vlc3Q=
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 20

service:
  ports:
    - name: tcp-secure
      port: 5671
    - name: tcp-not-secure
      port: 5672
    - name: http-mgm-ui
      port: 15672
```

#### `kubernetes/helm/components/recommendation/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/recommendation/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/recommendation/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/recommendation/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/recommendation/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/recommendation/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Recommendation microservice
name: recommendation
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/recommendation/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/recommendation/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/recommendation/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/recommendation/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/recommendation/values.yaml` — 새 파일 (11줄)

<!-- wb:file path="kubernetes/helm/components/recommendation/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: recommendation

image:
  name: recommendation-service

env:
  SPRING_PROFILES_ACTIVE: "docker"

livenessProbe_enabled: true

readinessProbe_enabled: true
```

#### `kubernetes/helm/components/review/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/review/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/review/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/review/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/review/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/review/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Review microservice
name: review
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/review/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/review/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/review/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/review/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/review/values.yaml` — 새 파일 (11줄)

<!-- wb:file path="kubernetes/helm/components/review/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: review

image:
  name: review-service

env:
  SPRING_PROFILES_ACTIVE: "docker"

livenessProbe_enabled: true

readinessProbe_enabled: true
```

#### `kubernetes/helm/components/zipkin-server/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/zipkin-server/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/zipkin-server/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/zipkin-server/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for Zipkin
name: zipkin-server
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/zipkin-server/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/zipkin-server/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/zipkin-server/templates/service.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/zipkin-server/templates/service.yaml" op="write" nl="0" -->
```yaml
{{- template "common.service" . -}}
```

#### `kubernetes/helm/components/zipkin-server/values.yaml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/components/zipkin-server/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: zipkin-server

image:
  repository: registry.hub.docker.com/openzipkin
  name: zipkin
  tag: 3.5.0
  pullPolicy: IfNotPresent

env:
  STORAGE_TYPE: mem

ports:
  - containerPort: 9411

livenessProbe_enabled: true
livenessProbe:
  httpGet:
    scheme: HTTP
    path: /actuator/info
    port: 9411
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 20
  successThreshold: 1

readinessProbe_enabled: true
readinessProbe:
  httpGet:
    scheme: HTTP
    path: /actuator/health
    port: 9411
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
  successThreshold: 1

resources:
  limits:
    memory: 512Mi

service:
  ports:
    - port: 9411

```

<a id="단계-14"></a>

## 단계 14. 헬름 `environments` 차트 — 환경별 묶음

`dev-env`(개발·테스트용, 데이터베이스까지 모두)와 `prod-env`(데이터베이스는 클러스터 밖)를 만듭니다. 비밀 값은 `secrets.yaml`에서 만듭니다.

#### `kubernetes/helm/environments/dev-env/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/environments/dev-env/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/environments/dev-env/Chart.yaml` — 새 파일 (56줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env/Chart.yaml" op="write" nl="1" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for HANDS-ON MICROSERVICES WITH SPRING BOOT AND SPRING CLOUD running in a Dev and Test Environment
name: dev-env
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

  - name: config-server
    version: 1.0.0
    repository: file://../../components/config-server

  - name: gateway
    version: 1.0.0
    repository: file://../../components/gateway

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

  - name: zipkin-server
    version: 1.0.0
    repository: file://../../components/zipkin-server

```

#### `kubernetes/helm/environments/dev-env/templates/secrets.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env/templates/secrets.yaml" op="write" nl="0" -->
```yaml
{{- template "common.secrets" . -}}
```

#### `kubernetes/helm/environments/dev-env/values.yaml` — 새 파일 (47줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env/values.yaml" op="write" nl="1" -->
```yaml
secrets:

  config-server-secrets:
    ENCRYPT_KEY: my-very-secure-encrypt-key
    SPRING_SECURITY_USER_NAME: dev-usr
    SPRING_SECURITY_USER_PASSWORD: dev-pwd

  config-client-credentials:
    CONFIG_SERVER_USR: dev-usr
    CONFIG_SERVER_PWD: dev-pwd
    SPRING_CLOUD_CONFIG_URI: http://config-server:8888

mysql:
  env:
    MYSQL_ROOT_PASSWORD: rootpwd
    MYSQL_DATABASE: review-db
    MYSQL_USER: user
    MYSQL_PASSWORD: pwd

config-server:
  envFromSecretRefs:
    - config-server-secrets

gateway:
  envFromSecretRefs:
    - config-client-credentials

auth-server:
  envFromSecretRefs:
    - config-client-credentials

product:
  envFromSecretRefs:
    - config-client-credentials

recommendation:
  envFromSecretRefs:
    - config-client-credentials

review:
  envFromSecretRefs:
    - config-client-credentials

product-composite:
  envFromSecretRefs:
    - config-client-credentials

```

#### `kubernetes/helm/environments/prod-env/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/environments/prod-env/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/environments/prod-env/Chart.yaml` — 새 파일 (43줄)

<!-- wb:file path="kubernetes/helm/environments/prod-env/Chart.yaml" op="write" nl="1" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for HANDS-ON MICROSERVICES WITH SPRING BOOT AND SPRING CLOUD running in a QA or Production environment
name: prod-env
version: 1.0.0

dependencies:

  - name: common
    version: 1.0.0
    repository: file://../../common

  - name: config-server
    version: 1.0.0
    repository: file://../../components/config-server

  - name: gateway
    version: 1.0.0
    repository: file://../../components/gateway

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

  - name: zipkin-server
    version: 1.0.0
    repository: file://../../components/zipkin-server
```

#### `kubernetes/helm/environments/prod-env/templates/secrets.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/prod-env/templates/secrets.yaml" op="write" nl="0" -->
```yaml
{{- template "common.secrets" . -}}
```

#### `kubernetes/helm/environments/prod-env/values.yaml` — 새 파일 (112줄)

<!-- wb:file path="kubernetes/helm/environments/prod-env/values.yaml" op="write" nl="1" -->
```yaml
secrets:

  config-server-secrets:
    ENCRYPT_KEY: my-very-secure-encrypt-key
    SPRING_SECURITY_USER_NAME: prod-usr
    SPRING_SECURITY_USER_PASSWORD: prod-pwd

  config-client-credentials:
    CONFIG_SERVER_USR: prod-usr
    CONFIG_SERVER_PWD: prod-pwd
    SPRING_CLOUD_CONFIG_URI: http://config-server:8888

config-server:
  image:
    tag: v1
  env:
    LOGGING_LEVEL_ROOT: WARN
    MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE: "health,info"
  envFromSecretRefs:
    - config-server-secrets
  resources:
    requests:
      memory: 200Mi
    limits:
      memory: 400Mi

gateway:
  image:
    tag: v1
  env:
    SPRING_PROFILES_ACTIVE: "docker,prod"
  envFromSecretRefs:
    - config-client-credentials
  resources:
    requests:
      memory: 200Mi
    limits:
      memory: 400Mi

auth-server:
  image:
    tag: v1
  env:
    SPRING_PROFILES_ACTIVE: "docker,prod"
  envFromSecretRefs:
    - config-client-credentials
  resources:
    requests:
      memory: 200Mi
    limits:
      memory: 400Mi

product:
  image:
    tag: v1
  env:
    SPRING_PROFILES_ACTIVE: "docker,prod"
  envFromSecretRefs:
    - config-client-credentials
  resources:
    requests:
      memory: 200Mi
    limits:
      memory: 400Mi

recommendation:
  image:
    tag: v1
  env:
    SPRING_PROFILES_ACTIVE: "docker,prod"
  envFromSecretRefs:
    - config-client-credentials
  resources:
    requests:
      memory: 200Mi
    limits:
      memory: 400Mi

review:
  image:
    tag: v1
  env:
    SPRING_PROFILES_ACTIVE: "docker,prod"
  envFromSecretRefs:
    - config-client-credentials
  resources:
    requests:
      memory: 200Mi
    limits:
      memory: 400Mi

product-composite:
  image:
    tag: v1
  env:
    SPRING_PROFILES_ACTIVE: "docker,prod"
  envFromSecretRefs:
    - config-client-credentials
  resources:
    requests:
      memory: 200Mi
    limits:
      memory: 400Mi

zipkin-server:
  env:
    LOGGING_LEVEL_ROOT: WARN
  resources:
    requests:
      memory: 300Mi
    limits:
      memory: 600Mi
```

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter16
./gradlew build
docker compose build
./test-em-all.bash start stop
```

**Kafka / 파티션 구성**

```bash
COMPOSE_FILE=docker-compose-kafka.yml ./test-em-all.bash start stop
COMPOSE_FILE=docker-compose-partitions.yml ./test-em-all.bash start stop
```

**쿠버네티스(minikube)에 배포**

```bash
minikube start --driver=docker --container-runtime=docker --cpus=4 --memory=10g
eval $(minikube docker-env) && docker compose build
for f in kubernetes/helm/components/*; do helm dep up $f; done
for f in kubernetes/helm/environments/*; do helm dep up $f; done
helm install hands-on-dev-env kubernetes/helm/environments/dev-env -n hands-on --create-namespace
kubectl wait --timeout=900s --for=condition=ready pod --all -n hands-on
HOST=$(minikube ip) PORT=30443 USE_K8S=true ./test-em-all.bash
```

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter16
```

---

← [15장 워크북](Chapter15.md) · [워크북 목차](README.md) · [17장 워크북](Chapter17.md) →
