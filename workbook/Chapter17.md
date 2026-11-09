# 17장 워크북 — 쿠버네티스 기능으로 시스템 환경 단순화

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 17장 · 영문 3판 p.439–464 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter17/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter17`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter17) · 위키: [17장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/17장-쿠버네티스-기능으로-시스템-환경-단순화)

## 이 장에서 만드는 것

쿠버네티스 기능으로 시스템을 단순하게 만듭니다.

- Config Server 대신 **ConfigMap·Secret**: 서비스별 차트에 설정 파일을 담고 `SPRING_CONFIG_LOCATION`으로 읽음
- 게이트웨이 대신 **Ingress**, 인증서는 **cert-manager**가 발급
- 구성 서버 프로젝트와 `bootstrap.yml` 삭제

## 시작하기

16장을 끝낸 작업 폴더를 복사해서 시작합니다. 16장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter16 Chapter17          # 내가 만든 16장 결과에서 시작
# 또는: cp -r <저장소>/Chapter16 Chapter17        # 저장소의 16장 완성 코드에서 시작
cd Chapter17 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 수정 6
2. [`product-service`](#단계-2) — 수정 3 · 삭제 1
3. [`recommendation-service`](#단계-3) — 수정 3 · 삭제 1
4. [`review-service`](#단계-4) — 수정 3 · 삭제 1
5. [`product-composite-service`](#단계-5) — 수정 3 · 삭제 1
6. [`gateway` — 에지 서버](#단계-6) — 수정 3 · 삭제 1
7. [`authorization-server` — OAuth 2.0 인가 서버](#단계-7) — 수정 2 · 삭제 1
8. [`config-server` — 구성 서버](#단계-8) — 삭제 8
9. [`config-repo` — 중앙 구성 파일](#단계-9) — 수정 5
10. [헬름 `common` 라이브러리 차트](#단계-10) — 새 파일 2 · 수정 1
11. [헬름 `components` 차트 — 서비스별 차트](#단계-11) — 새 파일 15 · 수정 7 · 삭제 20
12. [헬름 `environments` 차트 — 환경별 묶음](#단계-12) — 새 파일 4 · 수정 6

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

`settings.gradle`에서 `config-server`를 빼고, 컴포즈 파일에서 구성 서버 대신 `config-repo`를 마운트해 읽도록 바꿉니다. `.env`에 데이터베이스 계정이 추가됩니다.

#### `.env` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path=".env" op="write" nl="0" -->
```bash
RABBITMQ_USR=rabbit-user-prod
RABBITMQ_PWD=rabbit-pwd-prod

MONGODB_USR=mongodb-user-prod
MONGODB_PWD=mongodb-pwd-prod

MYSQL_ROOT_PWD=rootpwd
MYSQL_USR=mysql-user-prod
MYSQL_PWD=mysql-pwd-prod

GATEWAY_TLS_PWD=password
```

#### `docker-compose-kafka.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -5,8 +5,12 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -19,8 +23,12 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -33,8 +41,12 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -47,8 +59,12 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -61,8 +77,11 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0,kafka
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
+      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
+      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mysql:
         condition: service_healthy
@@ -75,8 +94,11 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1,kafka
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
+      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
+      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mysql:
         condition: service_healthy
@@ -89,8 +111,9 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,kafka
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product-composite.yml
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       kafka:
         condition: service_healthy
@@ -103,6 +126,9 @@
     ports:
       - "27017:27017"
     command: mongod
+    environment:
+      - MONGO_INITDB_ROOT_USERNAME=${MONGODB_USR}
+      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PWD}
     healthcheck:
       test: echo 'db.runCommand("ping").ok' | mongosh --quiet
       interval: 5s
@@ -115,12 +141,12 @@
     ports:
       - "3306:3306"
     environment:
-      - MYSQL_ROOT_PASSWORD=rootpwd
+      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PWD}
       - MYSQL_DATABASE=review-db
-      - MYSQL_USER=user
-      - MYSQL_PASSWORD=pwd
-    healthcheck:
-      test: "/usr/bin/mysql --user=user --password=pwd --execute \"SHOW DATABASES;\""
+      - MYSQL_USER=${MYSQL_USR}
+      - MYSQL_PASSWORD=${MYSQL_PWD}
+    healthcheck:
+      test: "/usr/bin/mysql --user=${MYSQL_USR} --password=${MYSQL_PWD} --execute \"SHOW DATABASES;\""
       interval: 5s
       timeout: 2s
       retries: 60
@@ -160,8 +186,10 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/gateway.yml
+      - SPRING_SSL_BUNDLE_JKS_GATEWAY_KEYSTORE_PASSWORD=${GATEWAY_TLS_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     ports:
       - "8443:8443"
     depends_on:
@@ -174,25 +202,14 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/auth-server.yml
+    volumes:
+      - $PWD/config-repo:/config-repo
     healthcheck:
       test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
       interval: 5s
       timeout: 2s
       retries: 60
-
-  config-server:
-    build: spring-cloud/config-server
-    image: hands-on/config-server
-    mem_limit: 512m
-    environment:
-      - SPRING_PROFILES_ACTIVE=docker,native
-      - ENCRYPT_KEY=${CONFIG_SERVER_ENCRYPT_KEY}
-      - SPRING_SECURITY_USER_NAME=${CONFIG_SERVER_USR}
-      - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
-    volumes:
-      - $PWD/config-repo:/config-repo
 
   zipkin-server:
     image: openzipkin/zipkin:3.5.0
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
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
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
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
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
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
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
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
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
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
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
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
    volumes:
      - $PWD/config-repo:/config-repo
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
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product-composite.yml
    volumes:
      - $PWD/config-repo:/config-repo
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
    mem_limit: 512m
    ports:
      - "3306:3306"
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
      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/gateway.yml
      - SPRING_SSL_BUNDLE_JKS_GATEWAY_KEYSTORE_PASSWORD=${GATEWAY_TLS_PWD}
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
    volumes:
      - $PWD/config-repo:/config-repo
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

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
@@ -5,8 +5,14 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -19,8 +25,14 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -33,8 +45,14 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -47,8 +65,14 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -61,8 +85,13 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_0
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
+      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mysql:
         condition: service_healthy
@@ -75,8 +104,13 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned,streaming_instance_1
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
+      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mysql:
         condition: service_healthy
@@ -89,8 +123,11 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker,streaming_partitioned
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product-composite.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       rabbitmq:
         condition: service_healthy
@@ -103,6 +140,9 @@
     ports:
       - "27017:27017"
     command: mongod
+    environment:
+      - MONGO_INITDB_ROOT_USERNAME=${MONGODB_USR}
+      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PWD}
     healthcheck:
       test: echo 'db.runCommand("ping").ok' | mongosh --quiet
       interval: 5s
@@ -115,12 +155,12 @@
     ports:
       - "3306:3306"
     environment:
-      - MYSQL_ROOT_PASSWORD=rootpwd
+      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PWD}
       - MYSQL_DATABASE=review-db
-      - MYSQL_USER=user
-      - MYSQL_PASSWORD=pwd
-    healthcheck:
-      test: "/usr/bin/mysql --user=user --password=pwd --execute \"SHOW DATABASES;\""
+      - MYSQL_USER=${MYSQL_USR}
+      - MYSQL_PASSWORD=${MYSQL_PWD}
+    healthcheck:
+      test: "/usr/bin/mysql --user=${MYSQL_USR} --password=${MYSQL_PWD} --execute \"SHOW DATABASES;\""
       interval: 5s
       timeout: 2s
       retries: 60
@@ -131,6 +171,9 @@
     ports:
       - 5672:5672
       - 15672:15672
+    environment:
+      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USR}
+      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PWD}
     healthcheck:
       test: ["CMD", "rabbitmqctl", "status"]
       interval: 5s
@@ -143,8 +186,12 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/gateway.yml
+      - SPRING_SSL_BUNDLE_JKS_GATEWAY_KEYSTORE_PASSWORD=${GATEWAY_TLS_PWD}
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     ports:
       - "8443:8443"
     depends_on:
@@ -157,25 +204,16 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/auth-server.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     healthcheck:
       test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
       interval: 5s
       timeout: 2s
       retries: 60
-
-  config-server:
-    build: spring-cloud/config-server
-    image: hands-on/config-server
-    mem_limit: 512m
-    environment:
-      - SPRING_PROFILES_ACTIVE=docker,native
-      - ENCRYPT_KEY=${CONFIG_SERVER_ENCRYPT_KEY}
-      - SPRING_SECURITY_USER_NAME=${CONFIG_SERVER_USR}
-      - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
-    volumes:
-      - $PWD/config-repo:/config-repo
 
   zipkin-server:
     image: openzipkin/zipkin:3.5.0
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
    build: microservices/product-service
    image: hands-on/product-service
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
    build: microservices/recommendation-service
    image: hands-on/recommendation-service
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
    build: microservices/recommendation-service
    image: hands-on/recommendation-service
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
    build: microservices/review-service
    image: hands-on/review-service
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
    build: microservices/review-service
    image: hands-on/review-service
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
    build: microservices/product-composite-service
    image: hands-on/product-composite-service
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
    mem_limit: 512m
    ports:
      - "3306:3306"
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
      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

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
@@ -5,8 +5,14 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -19,8 +25,14 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/recommendation.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_MONGODB_AUTHENTICATION_DATABASE=admin
+      - SPRING_MONGODB_USERNAME=${MONGODB_USR}
+      - SPRING_MONGODB_PASSWORD=${MONGODB_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mongodb:
         condition: service_healthy
@@ -33,8 +45,13 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/review.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+      - SPRING_DATASOURCE_USERNAME=${MYSQL_USR}
+      - SPRING_DATASOURCE_PASSWORD=${MYSQL_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       mysql:
         condition: service_healthy
@@ -47,8 +64,11 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/product-composite.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     depends_on:
       rabbitmq:
         condition: service_healthy
@@ -61,6 +81,9 @@
     ports:
       - "27017:27017"
     command: mongod
+    environment:
+      - MONGO_INITDB_ROOT_USERNAME=${MONGODB_USR}
+      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PWD}
     healthcheck:
       test: echo 'db.runCommand("ping").ok' | mongosh --quiet
       interval: 5s
@@ -73,12 +96,12 @@
     ports:
       - "3306:3306"
     environment:
-      - MYSQL_ROOT_PASSWORD=rootpwd
+      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PWD}
       - MYSQL_DATABASE=review-db
-      - MYSQL_USER=user
-      - MYSQL_PASSWORD=pwd
+      - MYSQL_USER=${MYSQL_USR}
+      - MYSQL_PASSWORD=${MYSQL_PWD}
     healthcheck:
-      test: "/usr/bin/mysql --user=user --password=pwd --execute \"SHOW DATABASES;\""
+      test: "/usr/bin/mysql --user=${MYSQL_USR} --password=${MYSQL_PWD} --execute \"SHOW DATABASES;\""
       interval: 5s
       timeout: 2s
       retries: 60
@@ -89,6 +112,9 @@
     ports:
       - 5672:5672
       - 15672:15672
+    environment:
+      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USR}
+      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PWD}
     healthcheck:
       test: ["CMD", "rabbitmqctl", "status"]
       interval: 5s
@@ -101,8 +127,12 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/gateway.yml
+      - SPRING_SSL_BUNDLE_JKS_GATEWAY_KEYSTORE_PASSWORD=${GATEWAY_TLS_PWD}
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     ports:
       - "8443:8443"
     depends_on:
@@ -115,25 +145,16 @@
     mem_limit: 512m
     environment:
       - SPRING_PROFILES_ACTIVE=docker
-      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
-      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
+      - SPRING_CONFIG_LOCATION=file:/config-repo/application.yml,file:/config-repo/auth-server.yml
+      - SPRING_RABBITMQ_USERNAME=${RABBITMQ_USR}
+      - SPRING_RABBITMQ_PASSWORD=${RABBITMQ_PWD}
+    volumes:
+      - $PWD/config-repo:/config-repo
     healthcheck:
       test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
       interval: 5s
       timeout: 2s
       retries: 60
-
-  config-server:
-    build: spring-cloud/config-server
-    image: hands-on/config-server
-    mem_limit: 512m
-    environment:
-      - SPRING_PROFILES_ACTIVE=docker,native
-      - ENCRYPT_KEY=${CONFIG_SERVER_ENCRYPT_KEY}
-      - SPRING_SECURITY_USER_NAME=${CONFIG_SERVER_USR}
-      - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
-    volumes:
-      - $PWD/config-repo:/config-repo
 
   zipkin-server:
     image: openzipkin/zipkin:3.5.0
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
    build: microservices/recommendation-service
    image: hands-on/recommendation-service
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
    build: microservices/review-service
    image: hands-on/review-service
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
    build: microservices/product-composite-service
    image: hands-on/product-composite-service
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
    mem_limit: 512m
    ports:
      - "3306:3306"
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
      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

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
@@ -12,7 +12,6 @@
 include ':microservices:product-composite-service'
 include ':spring-cloud:gateway'
 include ':spring-cloud:authorization-server'
-include ':spring-cloud:config-server'
 
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
include ':spring-cloud:gateway'
include ':spring-cloud:authorization-server'

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
@@ -2,15 +2,11 @@
 #
 # With Docker Compose:
 #
-# ./test-em-all.bash
-#
-# With Kubernetes in dev environment:
-#
-#   PORT=30443 USE_K8S=true ./test-em-all.bash
-#
-# With Kubernetes in prod environment:
-#
-#   CONFIG_SERVER_USR=prod-usr CONFIG_SERVER_PWD=prod-pwd PORT=30443 USE_K8S=true ./test-em-all.bash
+#   ./test-em-all.bash
+#
+# With Kubernetes:
+#
+#   HOST=minikube.me USE_K8S=true ./test-em-all.bash
 #
 : ${HOST=localhost}
 : ${PORT=8443}
@@ -21,8 +17,6 @@
 : ${PROD_ID_NO_REVS=213}
 : ${SKIP_CB_TESTS=false}
 : ${NAMESPACE=hands-on}
-: ${CONFIG_SERVER_USR=dev-usr}
-: ${CONFIG_SERVER_PWD=dev-pwd}
 
 function assertCurl() {
 
@@ -277,13 +271,6 @@
 echo ACCESS_TOKEN=$ACCESS_TOKEN
 AUTH="-H \"Authorization: Bearer $ACCESS_TOKEN\""
 
-# Verify access to the Config server and that its encrypt/decrypt endpoints work
-assertCurl 200 "curl -H "accept:application/json" -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/product/docker -s"
-TEST_VALUE="hello-world"
-ENCRYPTED_VALUE=$(curl -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/encrypt --data-urlencode "$TEST_VALUE" -s)
-DECRYPTED_VALUE=$(curl -k https://$CONFIG_SERVER_USR:$CONFIG_SERVER_PWD@$HOST:$PORT/config/decrypt -d $ENCRYPTED_VALUE -s)
-assertEqual "$TEST_VALUE" "$DECRYPTED_VALUE"
-
 setupTestdata
 
 waitForMessageProcessing
@@ -338,7 +325,11 @@
 assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/swagger-ui/oauth2-redirect.html"
 assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/v3/api-docs"
 assertEqual "3.1.0" "$(echo $RESPONSE | jq -r .openapi)"
-assertEqual "https://$HOST:$PORT" "$(echo $RESPONSE | jq -r '.servers[0].url')"
+# Skip this test since the server url is missing the port when deployed on Kubernetes
+if [[ $USE_K8S == "false" ]]
+then
+  assertEqual "https://$HOST:$PORT" "$(echo $RESPONSE | jq -r '.servers[0].url')"
+fi
 assertCurl 200 "curl -ks  https://$HOST:$PORT/openapi/v3/api-docs.yaml"
 
 if [[ $SKIP_CB_TESTS == "false" ]]
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="test-em-all.bash" op="write" nl="1" -->
```bash
#!/usr/bin/env bash
#
# With Docker Compose:
#
#   ./test-em-all.bash
#
# With Kubernetes:
#
#   HOST=minikube.me USE_K8S=true ./test-em-all.bash
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

`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다.

**지울 파일**

```bash
rm microservices/product-service/src/main/resources/bootstrap.yml
```

<!-- wb:file path="microservices/product-service/src/main/resources/bootstrap.yml" op="delete" nl="0" -->

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -34,16 +34,11 @@
     implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'org.springframework.cloud:spring-cloud-starter-config'
-    implementation 'org.springframework.cloud:spring-cloud-config-client'
-    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
-    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
-    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
-    implementation 'org.springframework.retry:spring-retry'
     implementation 'io.micrometer:micrometer-tracing-bridge-otel'
     implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
     implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
     implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'org.springframework.retry:spring-retry'
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
    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
    implementation 'org.springframework.retry:spring-retry'
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

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/PersistenceTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -11,7 +11,7 @@
 import se.magnus.microservices.core.product.persistence.ProductEntity;
 import se.magnus.microservices.core.product.persistence.ProductRepository;
 
-@DataMongoTest(properties = {"spring.cloud.config.enabled=false"})
+@DataMongoTest
 class PersistenceTests extends MongoDbTestBase {
 
   @Autowired
```

<details><summary>완성된 파일 전체 보기</summary>

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

</details>

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -22,7 +22,7 @@
 import se.magnus.microservices.core.product.persistence.ProductRepository;
 
 @AutoConfigureWebTestClient
-@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"spring.cloud.config.enabled=false"})
+@SpringBootTest(webEnvironment = RANDOM_PORT)
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

<a id="단계-3"></a>

## 단계 3. `recommendation-service`

`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다.

**지울 파일**

```bash
rm microservices/recommendation-service/src/main/resources/bootstrap.yml
```

<!-- wb:file path="microservices/recommendation-service/src/main/resources/bootstrap.yml" op="delete" nl="0" -->

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -34,16 +34,11 @@
     implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'org.springframework.cloud:spring-cloud-starter-config'
-    implementation 'org.springframework.cloud:spring-cloud-config-client'
-    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
-    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
-    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
-    implementation 'org.springframework.retry:spring-retry'
     implementation 'io.micrometer:micrometer-tracing-bridge-otel'
     implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
     implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
     implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'org.springframework.retry:spring-retry'
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
    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
    implementation 'org.springframework.retry:spring-retry'
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

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/PersistenceTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -14,7 +14,7 @@
 import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
 import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;
 
-@DataMongoTest(properties = {"spring.cloud.config.enabled=false"})
+@DataMongoTest
 class PersistenceTests extends MongoDbTestBase {
 
   @Autowired
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
@@ -22,7 +22,7 @@
 import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;
 
 @AutoConfigureWebTestClient
-@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {"spring.cloud.config.enabled=false"})
+@SpringBootTest(webEnvironment = RANDOM_PORT)
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

<a id="단계-4"></a>

## 단계 4. `review-service`

`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다.

**지울 파일**

```bash
rm microservices/review-service/src/main/resources/bootstrap.yml
```

<!-- wb:file path="microservices/review-service/src/main/resources/bootstrap.yml" op="delete" nl="0" -->

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -34,17 +34,12 @@
     implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'org.springframework.cloud:spring-cloud-starter-config'
-    implementation 'org.springframework.cloud:spring-cloud-config-client'
-    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
-    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
-    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
-    implementation 'org.springframework.retry:spring-retry'
     implementation 'io.micrometer:micrometer-tracing-bridge-otel'
     implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
     implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
     implementation 'org.springframework.boot:spring-boot-zipkin'
     implementation 'net.ttddyy.observation:datasource-micrometer-spring-boot:2.2.1'
+    implementation 'org.springframework.retry:spring-retry'
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
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
    implementation 'net.ttddyy.observation:datasource-micrometer-spring-boot:2.2.1'
    implementation 'org.springframework.retry:spring-retry'
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

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/PersistenceTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -16,7 +16,7 @@
 import se.magnus.microservices.core.review.persistence.ReviewEntity;
 import se.magnus.microservices.core.review.persistence.ReviewRepository;
 
-@DataJpaTest(properties = {"spring.jpa.hibernate.ddl-auto=update", "spring.cloud.config.enabled=false"})
+@DataJpaTest(properties = {"spring.jpa.hibernate.ddl-auto=update"})
 @Transactional(propagation = NOT_SUPPORTED)
 class PersistenceTests extends MySqlTestBase {
 
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/PersistenceTests.java" op="write" nl="0" -->
```java
package se.magnus.microservices.core.review;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.transaction.annotation.Propagation.NOT_SUPPORTED;

import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.transaction.annotation.Transactional;
import se.magnus.microservices.core.review.persistence.ReviewEntity;
import se.magnus.microservices.core.review.persistence.ReviewRepository;

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
@@ -25,8 +25,7 @@
 @SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
   "spring.cloud.stream.defaultBinder=rabbit",
   "logging.level.se.magnus=DEBUG",
-  "spring.jpa.hibernate.ddl-auto=update",
-  "spring.cloud.config.enabled=false"})
+  "spring.jpa.hibernate.ddl-auto=update"})
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

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `product-composite-service`

`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다.

**지울 파일**

```bash
rm microservices/product-composite-service/src/main/resources/bootstrap.yml
```

<!-- wb:file path="microservices/product-composite-service/src/main/resources/bootstrap.yml" op="delete" nl="0" -->

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -39,16 +39,11 @@
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'org.springframework.cloud:spring-cloud-starter-config'
-    implementation 'org.springframework.cloud:spring-cloud-config-client'
-    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
-    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
-    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
-    implementation 'org.springframework.retry:spring-retry'
     implementation 'io.micrometer:micrometer-tracing-bridge-otel'
     implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
     implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
     implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'org.springframework.retry:spring-retry'
     implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:3.0.3'
     implementation "io.github.resilience4j:resilience4j-spring-boot4:${resilience4jVersion}"
     implementation "io.github.resilience4j:resilience4j-reactor:${resilience4jVersion}"
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
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
    implementation 'org.springframework.retry:spring-retry'
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

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/MessagingTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -41,8 +41,7 @@
   properties = {
     "spring.security.oauth2.resourceserver.jwt.issuer-uri=",
     "spring.main.allow-bean-definition-overriding=true",
-    "spring.cloud.stream.defaultBinder=rabbit",
-    "spring.cloud.config.enabled=false"})
+    "spring.cloud.stream.defaultBinder=rabbit"})
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
@@ -31,8 +31,7 @@
   classes = {TestSecurityConfig.class},
   properties = {
     "spring.security.oauth2.resourceserver.jwt.issuer-uri=",
-    "spring.main.allow-bean-definition-overriding=true",
-    "spring.cloud.config.enabled=false"})
+    "spring.main.allow-bean-definition-overriding=true"})
 class ProductCompositeServiceApplicationTests {
 
   private static final int PRODUCT_ID_OK = 1;
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

## 단계 6. `gateway` — 에지 서버

`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다. 쿠버네티스에서는 Ingress가 외부 요청을 받지만, 도커 컴포즈 실행을 위해 게이트웨이 프로젝트는 남겨 둡니다.

**지울 파일**

```bash
rm spring-cloud/gateway/src/main/resources/bootstrap.yml
```

<!-- wb:file path="spring-cloud/gateway/src/main/resources/bootstrap.yml" op="delete" nl="0" -->

#### `spring-cloud/gateway/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,16 +31,11 @@
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
     implementation 'org.springframework.cloud:spring-cloud-starter-gateway-server-webflux'
     implementation 'org.springframework.boot:spring-boot-starter-webclient'
-    implementation 'org.springframework.cloud:spring-cloud-starter-config'
-    implementation 'org.springframework.cloud:spring-cloud-config-client'
-    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
-    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
-    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
-    implementation 'org.springframework.retry:spring-retry'
     implementation 'io.micrometer:micrometer-tracing-bridge-otel'
     implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
     implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
     implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'org.springframework.retry:spring-retry'
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
 }
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
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
    implementation 'org.springframework.retry:spring-retry'

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
@@ -23,7 +23,6 @@
           .pathMatchers("/login/**").permitAll()
           .pathMatchers("/error/**").permitAll()
           .pathMatchers("/openapi/**").permitAll()
-          .pathMatchers("/config/**").permitAll()
           .anyExchange().authenticated()))
       .oauth2ResourceServer(server -> server
         .jwt(Customizer.withDefaults()));
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

@SpringBootTest(webEnvironment = RANDOM_PORT)
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

<a id="단계-7"></a>

## 단계 7. `authorization-server` — OAuth 2.0 인가 서버

`bootstrap.yml`과 구성 클라이언트 의존성을 지웁니다.

**지울 파일**

```bash
rm spring-cloud/authorization-server/src/main/resources/bootstrap.yml
```

<!-- wb:file path="spring-cloud/authorization-server/src/main/resources/bootstrap.yml" op="delete" nl="0" -->

#### `spring-cloud/authorization-server/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -17,24 +17,15 @@
     mavenCentral()
 }
 
-ext {
-    springCloudVersion = '2025.1.4'
-}
-
 dependencies {
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-authorization-server'
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-security'
-    implementation 'org.springframework.cloud:spring-cloud-starter-config'
-    implementation 'org.springframework.cloud:spring-cloud-config-client'
-    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
-    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
-    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
-    implementation 'org.springframework.retry:spring-retry'
     implementation 'io.micrometer:micrometer-tracing-bridge-otel'
     implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
     implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
     implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'org.springframework.retry:spring-retry:2.0.13'
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-starter-webmvc-test'
@@ -42,12 +33,6 @@
     testImplementation 'org.htmlunit:htmlunit'
 }
 
-dependencyManagement {
-    imports {
-        mavenBom "org.springframework.cloud:spring-cloud-dependencies:${springCloudVersion}"
-    }
-}
-
 tasks.named('test') {
     useJUnitPlatform()
 }
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
    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
    implementation 'org.springframework.boot:spring-boot-zipkin'
    implementation 'org.springframework.retry:spring-retry:2.0.13'

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

#### `spring-cloud/authorization-server/src/test/java/sample/OAuth2AuthorizationServerApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -35,7 +35,7 @@
  *
  * @author Josh Cummings
  */
-@SpringBootTest(properties = {"spring.cloud.config.enabled=false"})
+@SpringBootTest
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
@SpringBootTest
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

<a id="단계-8"></a>

## 단계 8. `config-server` — 구성 서버

ConfigMap이 대신하므로 프로젝트를 통째로 지웁니다: `rm -r spring-cloud/config-server`

**지울 파일**

```bash
rm spring-cloud/config-server/.gitignore
rm spring-cloud/config-server/Dockerfile
rm spring-cloud/config-server/build.gradle
rm spring-cloud/config-server/settings.gradle
rm spring-cloud/config-server/src/main/java/se/magnus/springcloud/configserver/ConfigServerApplication.java
rm spring-cloud/config-server/src/main/java/se/magnus/springcloud/configserver/SecurityConfig.java
rm spring-cloud/config-server/src/main/resources/application.yml
rm spring-cloud/config-server/src/test/java/se/magnus/springcloud/configserver/ConfigServerApplicationTests.java
```

<!-- wb:file path="spring-cloud/config-server/.gitignore" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/config-server/Dockerfile" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/config-server/build.gradle" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/config-server/settings.gradle" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/config-server/src/main/java/se/magnus/springcloud/configserver/ConfigServerApplication.java" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/config-server/src/main/java/se/magnus/springcloud/configserver/SecurityConfig.java" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/config-server/src/main/resources/application.yml" op="delete" nl="0" -->
<!-- wb:file path="spring-cloud/config-server/src/test/java/se/magnus/springcloud/configserver/ConfigServerApplicationTests.java" op="delete" nl="0" -->

<a id="단계-9"></a>

## 단계 9. `config-repo` — 중앙 구성 파일

RabbitMQ 계정처럼 암호화해 두던 비밀 값을 빼고(이제 쿠버네티스 Secret이나 `.env`로 전달), 로그 패턴을 정리합니다.

#### `config-repo/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -4,8 +4,6 @@
 spring.rabbitmq:
   host: 127.0.0.1
   port: 5672
-  username: guest
-  password: '{cipher}17fcf0ae5b8c5cf87de6875b699be4a1746dd493a99d926c7a26a68c422117ef'
 
 spring.cloud.stream.kafka.binder:
   brokers: 127.0.0.1
@@ -22,6 +20,8 @@
 
 management.tracing.export.zipkin.endpoint: http://zipkin-server:9411/api/v2/spans
 management.tracing.sampling.probability: 1.0
+logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
+logging.include-application-name: false
 
 server.shutdown: graceful
 spring.lifecycle.timeout-per-shutdown-phase: 10s
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
management.endpoint.health.show-details: "ALWAYS"
management.endpoints.web.exposure.include: "*"
management.endpoint.health.probes.enabled: true
management.health.rabbit.enabled: true
management.health.kafka.enabled: false

management.tracing.export.zipkin.endpoint: http://zipkin-server:9411/api/v2/spans
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

# Only allow management endpoints over http in production for info, health and circuitbreakerevents
management.endpoints.web.exposure.include: health,info,circuitbreakerevents
```

</details>

#### `config-repo/auth-server.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="config-repo/auth-server.yml" op="write" nl="1" -->
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
@@ -1,4 +1,5 @@
 server.port: 8443
+spring.application.name: gateway
 
 # During development, allow forwarding the X-Forwarded-* and Forwarded headers from any proxies.
 # When usd in QA and production, this should be set to a specific IP address or CIDR range, e.g. 10\.0\.0\..* (Java Regular Expression).
@@ -11,7 +12,6 @@
   keystore:
     type: PKCS12
     location: classpath:keystore/edge.p12
-    password: '{cipher}d59274473b196cebe288f849c442eba34aa497d14a13e10a23f824489e1c23ec'
 
 server.ssl.bundle: gateway
 
@@ -42,13 +42,6 @@
   predicates:
   - Path=/openapi/**
 
-- id: config-server
-  uri: ${spring.cloud.config.uri}
-  predicates:
-  - Path=/config/**
-  filters:
-  - RewritePath=/config/(?<segment>.*), /$\{segment}
-
 spring.security.oauth2.resourceserver.jwt.issuer-uri: http://${app.auth-server}
 
 management.endpoint.gateway.access: unrestricted
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/gateway.yml" op="write" nl="1" -->
```yaml
server.port: 8443
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

#### `config-repo/product-composite.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -9,7 +9,8 @@
     oauth2-redirect-url: /swagger-ui/oauth2-redirect.html
     oauth:
       clientId: writer
-      clientSecret: '{cipher}debb77857798ba70441b229de88624213b0a00b284f95fe31d1378d117cf3ffa'
+      # TODO: EXTERNALIZE!
+      clientSecret: secret-writer
       useBasicAuthenticationWithAccessCodeGrant: true
   oAuthFlow:
     authorizationUrl: https://localhost:8443/oauth2/authorize
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
      # TODO: EXTERNALIZE!
      clientSecret: secret-writer
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

#### `config-repo/review.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -10,8 +10,6 @@
 
 spring.datasource:
   url: jdbc:mysql://localhost/review-db
-  username: user
-  password: '{cipher}24b93c790fa2ed0dc5a6a2b8c39853cf4d6cd6100c248de5f279fb5dd78e7be6'
 
 spring.datasource.hikari.initializationFailTimeout: 60000
 
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

<a id="단계-10"></a>

## 단계 10. 헬름 `common` 라이브러리 차트

Ingress와 cert-manager `Issuer` 템플릿(`_ingress.yaml`, `_issuer.yaml`)을 추가합니다.

#### `kubernetes/helm/common/templates/_ingress.yaml` — 새 파일 (39줄)

<!-- wb:file path="kubernetes/helm/common/templates/_ingress.yaml" op="write" nl="0" -->
```yaml
{{- define "common.ingress" -}}
{{- $common := dict "Values" .Values.common -}}
{{- $noCommon := omit .Values "common" -}} 
{{- $overrides := dict "Values" $noCommon -}} 
{{- $noValues := omit . "Values" -}} 
{{- with merge $noValues $overrides $common -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "common.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ include "common.name" . }}
    helm.sh/chart: {{ include "common.chart" . }}
    app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.ingress.annotations }}
  annotations:
{{ toYaml . | indent 4 }}
{{- end }}
spec:
  tls:
    - hosts:
        - {{ .Values.ingress.host | quote }}
      secretName: {{ .Values.ingress.tls.secretName }}
  rules:
    - host: {{ .Values.ingress.host | quote }}
      http:
        paths:
        {{- range .Values.ingress.paths }}
          - path: {{ .path }}
            pathType: Prefix
            backend:
              service:
                name: {{ .service }}
                port:
                  name: http

        {{- end }}
{{- end }}
{{- end -}}
```

#### `kubernetes/helm/common/templates/_issuer.yaml` — 새 파일 (8줄)

<!-- wb:file path="kubernetes/helm/common/templates/_issuer.yaml" op="write" nl="0" -->
```yaml
{{- define "common.issuer" -}}
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: selfsigned
spec:
  selfSigned: {}
{{- end -}}
```

#### `kubernetes/helm/common/values.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,4 +1,10 @@
 replicaCount: 1
+
+ingress:
+  annotations:
+    cert-manager.io/issuer: selfsigned
+  tls:
+    secretName: tls-certificate
 
 image:
   repository: hands-on
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="kubernetes/helm/common/values.yaml" op="write" nl="1" -->
```yaml
replicaCount: 1

ingress:
  annotations:
    cert-manager.io/issuer: selfsigned
  tls:
    secretName: tls-certificate

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

</details>

<a id="단계-11"></a>

## 단계 11. 헬름 `components` 차트 — 서비스별 차트

`config-server` 차트를 지우고, 서비스별 차트에 `config-repo` 파일과 ConfigMap 템플릿을 넣습니다. `config-repo` 파일은 루트의 `config-repo`와 내용이 같아 복사하면 됩니다.

**지울 파일**

```bash
rm kubernetes/helm/components/config-server/.helmignore
rm kubernetes/helm/components/config-server/Chart.lock
rm kubernetes/helm/components/config-server/Chart.yaml
rm kubernetes/helm/components/config-server/config-repo/application.yml
rm kubernetes/helm/components/config-server/config-repo/auth-server.yml
rm kubernetes/helm/components/config-server/config-repo/gateway.yml
rm kubernetes/helm/components/config-server/config-repo/product-composite.yml
rm kubernetes/helm/components/config-server/config-repo/product.yml
rm kubernetes/helm/components/config-server/config-repo/recommendation.yml
rm kubernetes/helm/components/config-server/config-repo/review.yml
rm kubernetes/helm/components/config-server/templates/configmap_from_file.yaml
rm kubernetes/helm/components/config-server/templates/deployment.yaml
rm kubernetes/helm/components/config-server/templates/service.yaml
rm kubernetes/helm/components/config-server/values.yaml
rm kubernetes/helm/components/gateway/.helmignore
rm kubernetes/helm/components/gateway/Chart.lock
rm kubernetes/helm/components/gateway/Chart.yaml
rm kubernetes/helm/components/gateway/templates/deployment.yaml
rm kubernetes/helm/components/gateway/templates/service.yaml
rm kubernetes/helm/components/gateway/values.yaml
```

<!-- wb:file path="kubernetes/helm/components/config-server/.helmignore" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/Chart.lock" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/Chart.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/application.yml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/auth-server.yml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/gateway.yml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/product-composite.yml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/product.yml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/recommendation.yml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/config-repo/review.yml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/templates/configmap_from_file.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/templates/deployment.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/templates/service.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/config-server/values.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/gateway/.helmignore" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/gateway/Chart.lock" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/gateway/Chart.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/gateway/templates/deployment.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/gateway/templates/service.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/gateway/values.yaml" op="delete" nl="0" -->

#### `kubernetes/helm/components/auth-server/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/auth-server/config-repo && cp config-repo/application.yml kubernetes/helm/components/auth-server/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/auth-server/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/auth-server/config-repo/auth-server.yml` — 새 파일 (`config-repo/auth-server.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/auth-server/config-repo && cp config-repo/auth-server.yml kubernetes/helm/components/auth-server/config-repo/auth-server.yml
```

<!-- wb:file path="kubernetes/helm/components/auth-server/config-repo/auth-server.yml" op="cp" src="config-repo/auth-server.yml" -->

#### `kubernetes/helm/components/auth-server/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/auth-server/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/auth-server/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/auth-server/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: auth-server

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

#### `kubernetes/helm/components/mysql/values.yaml` — 전체를 다음 내용으로 바꿉니다

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

#### `kubernetes/helm/components/product-composite/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product-composite/config-repo && cp config-repo/application.yml kubernetes/helm/components/product-composite/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/product-composite/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/product-composite/config-repo/product-composite.yml` — 새 파일 (`config-repo/product-composite.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product-composite/config-repo && cp config-repo/product-composite.yml kubernetes/helm/components/product-composite/config-repo/product-composite.yml
```

<!-- wb:file path="kubernetes/helm/components/product-composite/config-repo/product-composite.yml" op="cp" src="config-repo/product-composite.yml" -->

#### `kubernetes/helm/components/product-composite/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/product-composite/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/product-composite/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/product-composite/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: product-composite

image:
  name: product-composite-service

env:
  SPRING_PROFILES_ACTIVE: "docker"
  SPRING_CONFIG_LOCATION: file:/config-repo/application.yml,file:/config-repo/product-composite.yml

livenessProbe_enabled: true

readinessProbe_enabled: true

configmap:
  enabled: true
  volumeMounts:
    mountPath: /config-repo
```

#### `kubernetes/helm/components/product/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product/config-repo && cp config-repo/application.yml kubernetes/helm/components/product/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/product/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/product/config-repo/product.yml` — 새 파일 (`config-repo/product.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product/config-repo && cp config-repo/product.yml kubernetes/helm/components/product/config-repo/product.yml
```

<!-- wb:file path="kubernetes/helm/components/product/config-repo/product.yml" op="cp" src="config-repo/product.yml" -->

#### `kubernetes/helm/components/product/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/product/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/product/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/product/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: product

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

#### `kubernetes/helm/components/rabbitmq/values.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -19,7 +19,7 @@
     port: 15672
     httpHeaders:
       - name: Authorization
-        value: Basic Z3Vlc3Q6Z3Vlc3Q=
+        value: Basic cmFiYml0LXVzZXItZGV2OnJhYmJpdC1wd2QtZGV2
   initialDelaySeconds: 10
   periodSeconds: 5
   timeoutSeconds: 3
```

<details><summary>완성된 파일 전체 보기</summary>

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
        value: Basic cmFiYml0LXVzZXItZGV2OnJhYmJpdC1wd2QtZGV2
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

</details>

#### `kubernetes/helm/components/recommendation/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/recommendation/config-repo && cp config-repo/application.yml kubernetes/helm/components/recommendation/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/recommendation/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/recommendation/config-repo/recommendation.yml` — 새 파일 (`config-repo/recommendation.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/recommendation/config-repo && cp config-repo/recommendation.yml kubernetes/helm/components/recommendation/config-repo/recommendation.yml
```

<!-- wb:file path="kubernetes/helm/components/recommendation/config-repo/recommendation.yml" op="cp" src="config-repo/recommendation.yml" -->

#### `kubernetes/helm/components/recommendation/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/recommendation/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/recommendation/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/recommendation/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: recommendation

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

#### `kubernetes/helm/components/review/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review/config-repo && cp config-repo/application.yml kubernetes/helm/components/review/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/review/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/review/config-repo/review.yml` — 새 파일 (`config-repo/review.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review/config-repo && cp config-repo/review.yml kubernetes/helm/components/review/config-repo/review.yml
```

<!-- wb:file path="kubernetes/helm/components/review/config-repo/review.yml" op="cp" src="config-repo/review.yml" -->

#### `kubernetes/helm/components/review/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/review/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/review/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/review/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: review

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

<a id="단계-12"></a>

## 단계 12. 헬름 `environments` 차트 — 환경별 묶음

환경 차트에서 `config-server`를 빼고 Ingress·Issuer를 추가합니다. `Chart.lock`은 `helm dep up`으로 다시 만듭니다.

#### `kubernetes/helm/environments/dev-env/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/environments/dev-env/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/environments/dev-env/Chart.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -22,14 +22,6 @@
     version: 1.0.0
     repository: file://../../components/mysql
 
-  - name: config-server
-    version: 1.0.0
-    repository: file://../../components/config-server
-
-  - name: gateway
-    version: 1.0.0
-    repository: file://../../components/gateway
-
   - name: auth-server
     version: 1.0.0
     repository: file://../../components/auth-server
@@ -53,4 +45,3 @@
   - name: zipkin-server
     version: 1.0.0
     repository: file://../../components/zipkin-server
-
```

<details><summary>완성된 파일 전체 보기</summary>

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

</details>

#### `kubernetes/helm/environments/dev-env/templates/ingress.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env/templates/ingress.yaml" op="write" nl="0" -->
```yaml
{{- template "common.ingress" . -}}
```

#### `kubernetes/helm/environments/dev-env/templates/issuer.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env/templates/issuer.yaml" op="write" nl="0" -->
```yaml
{{- template "common.issuer" . -}}
```

#### `kubernetes/helm/environments/dev-env/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/environments/dev-env/values.yaml" op="write" nl="1" -->
```yaml
ingress:
  host: minikube.me
  paths:
    - path: /oauth2
      service: auth-server
    - path: /login
      service: auth-server
    - path: /error
      service: auth-server
    - path: /product-composite
      service: product-composite
    - path: /actuator/health
      service: product-composite
    - path: /openapi
      service: product-composite

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
  envFromSecretRefs:
    - rabbitmq-credentials
    - mongodb-credentials

recommendation:
  envFromSecretRefs:
    - rabbitmq-credentials
    - mongodb-credentials

review:
  envFromSecretRefs:
    - rabbitmq-credentials
    - mysql-credentials

product-composite:
  envFromSecretRefs:
    - rabbitmq-credentials
```

#### `kubernetes/helm/environments/prod-env/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/environments/prod-env/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/environments/prod-env/Chart.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -9,14 +9,6 @@
   - name: common
     version: 1.0.0
     repository: file://../../common
-
-  - name: config-server
-    version: 1.0.0
-    repository: file://../../components/config-server
-
-  - name: gateway
-    version: 1.0.0
-    repository: file://../../components/gateway
 
   - name: auth-server
     version: 1.0.0
```

<details><summary>완성된 파일 전체 보기</summary>

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

</details>

#### `kubernetes/helm/environments/prod-env/templates/ingress.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/prod-env/templates/ingress.yaml" op="write" nl="0" -->
```yaml
{{- template "common.ingress" . -}}
```

#### `kubernetes/helm/environments/prod-env/templates/issuer.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/prod-env/templates/issuer.yaml" op="write" nl="0" -->
```yaml
{{- template "common.issuer" . -}}
```

#### `kubernetes/helm/environments/prod-env/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/environments/prod-env/values.yaml" op="write" nl="1" -->
```yaml
ingress:
  host: minikube.me
  paths:
    - path: /oauth2
      service: auth-server
    - path: /login
      service: auth-server
    - path: /error
      service: auth-server
    - path: /product-composite
      service: product-composite
    - path: /actuator/health
      service: product-composite
    - path: /openapi
      service: product-composite

secrets:

  rabbitmq-credentials:
    SPRING_RABBITMQ_USERNAME: rabbit-user-prod
    SPRING_RABBITMQ_PASSWORD: rabbit-pwd-prod

  mongodb-credentials:
    SPRING_MONGODB_AUTHENTICATION_DATABASE: admin
    SPRING_MONGODB_USERNAME: mongodb-user-prod
    SPRING_MONGODB_PASSWORD: mongodb-pwd-prod

  mysql-credentials:
    SPRING_DATASOURCE_USERNAME: mysql-user-prod
    SPRING_DATASOURCE_PASSWORD: mysql-pwd-prod

auth-server:
  image:
    tag: v1
  env:
    SPRING_PROFILES_ACTIVE: "docker,prod"
  envFromSecretRefs:
    - rabbitmq-credentials
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
    - rabbitmq-credentials
    - mongodb-credentials
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
    - rabbitmq-credentials
    - mongodb-credentials
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
    - rabbitmq-credentials
    - mysql-credentials
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
    - rabbitmq-credentials
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
cd ~/my-work/Chapter17
./gradlew build
docker compose build
./test-em-all.bash start stop
```

**Kafka / 파티션 구성**

```bash
COMPOSE_FILE=docker-compose-kafka.yml ./test-em-all.bash start stop
COMPOSE_FILE=docker-compose-partitions.yml ./test-em-all.bash start stop
```

**쿠버네티스(minikube)에 배포** — Ingress와 cert-manager 사용

```bash
minikube start --driver=docker --container-runtime=docker --cpus=4 --memory=10g
minikube addons enable ingress
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager --create-namespace -n cert-manager --set crds.enabled=true --wait
eval $(minikube docker-env) && docker compose build
for f in kubernetes/helm/components/*; do helm dep up $f; done
for f in kubernetes/helm/environments/*; do helm dep up $f; done
helm install hands-on-dev-env kubernetes/helm/environments/dev-env -n hands-on --create-namespace
kubectl wait --timeout=900s --for=condition=ready pod --all -n hands-on
echo "$(minikube ip) minikube.me" | sudo tee -a /etc/hosts
HOST=minikube.me PORT=443 USE_K8S=true ./test-em-all.bash
```

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter17
```

---

← [16장 워크북](Chapter16.md) · [워크북 목차](README.md) · [18장 워크북](Chapter18.md) →
