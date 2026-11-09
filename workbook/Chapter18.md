# 18장 워크북 — 서비스 메시를 사용한 관찰 가능성 및 관리 편의성 향상

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 18장 · 영문 3판 p.465–522 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter18/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter18`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter18) · 위키: [18장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/18장-서비스-메시를-사용한-관찰-가능성-및-관리-편의성-향상)

## 이 장에서 만드는 것

**이스티오 서비스 메시**를 도입합니다. 코드 변경은 적고, 대부분 쿠버네티스·헬름 설정입니다.

- 추적을 Jaeger로 보내고 B3 헤더로 전파(`TracingConfig`)
- 이스티오 리소스: Gateway, VirtualService, DestinationRule, mTLS, JWT 인증
- 장애·지연 주입과 블루/그린 배포 실습 파일

## 시작하기

17장을 끝낸 작업 폴더를 복사해서 시작합니다. 17장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter17 Chapter18          # 내가 만든 17장 결과에서 시작
# 또는: cp -r <저장소>/Chapter17 Chapter18        # 저장소의 17장 완성 코드에서 시작
cd Chapter18 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 수정 4
2. [`api` 프로젝트 — 서비스 간 API와 DTO](#단계-2) — 수정 4
3. [`product-service`](#단계-3) — 새 파일 1 · 수정 2
4. [`recommendation-service`](#단계-4) — 새 파일 1 · 수정 2
5. [`review-service`](#단계-5) — 새 파일 1 · 수정 2
6. [`product-composite-service`](#단계-6) — 새 파일 1 · 수정 4
7. [`gateway` — 에지 서버](#단계-7) — 수정 3
8. [`authorization-server` — OAuth 2.0 인가 서버](#단계-8) — 수정 3
9. [`config-repo` — 중앙 구성 파일](#단계-9) — 수정 2
10. [`kubernetes` — 클러스터 설정 파일](#단계-10) — 새 파일 3
11. [`kubernetes/resilience-tests` — 장애·지연 주입](#단계-11) — 새 파일 2
12. [`kubernetes/routing-tests` — 트래픽 분할](#단계-12) — 새 파일 1
13. [헬름 `common` 라이브러리 차트](#단계-13) — 새 파일 3 · 수정 3 · 삭제 2
14. [헬름 `components` 차트 — 서비스별 차트](#단계-14) — 새 파일 24 · 수정 9 · 삭제 5
15. [헬름 `environments` 차트 — 환경별 묶음](#단계-15) — 새 파일 13 · 수정 6 · 삭제 4

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

컴포즈 파일은 관리 포트 분리(4004)에 맞춰 헬스 체크를 바꾸고 Zipkin을 뺍니다(추적은 이스티오의 Jaeger가 받음). `test-em-all.bash`는 기본값이 쿠버네티스(`minikube.me`) 실행으로 바뀝니다.

#### `docker-compose-kafka.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -122,6 +122,7 @@
 
   mongodb:
     image: mongo:8.0.5
+    restart: always
     mem_limit: 512m
     ports:
       - "27017:27017"
@@ -137,6 +138,7 @@
 
   mysql:
     image: mysql:9.2.0
+    restart: always
     mem_limit: 512m
     ports:
       - "3306:3306"
@@ -206,12 +208,12 @@
     volumes:
       - $PWD/config-repo:/config-repo
     healthcheck:
-      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
+      test: ["CMD", "wget", "-O -", "-q", "http://localhost:4004/actuator/health"]
       interval: 5s
       timeout: 2s
       retries: 60
 
-  zipkin-server:
+  jaeger-collector.istio-system:
     image: openzipkin/zipkin:3.5.0
     restart: always
     mem_limit: 1024m
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

</details>

#### `docker-compose-partitions.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -136,6 +136,7 @@
 
   mongodb:
     image: mongo:8.0.5
+    restart: always
     mem_limit: 512m
     ports:
       - "27017:27017"
@@ -151,6 +152,7 @@
 
   mysql:
     image: mysql:9.2.0
+    restart: always
     mem_limit: 512m
     ports:
       - "3306:3306"
@@ -167,6 +169,7 @@
 
   rabbitmq:
     image: rabbitmq:4.0.7-management
+    restart: always
     mem_limit: 512m
     ports:
       - 5672:5672
@@ -210,12 +213,12 @@
     volumes:
       - $PWD/config-repo:/config-repo
     healthcheck:
-      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
-      interval: 5s
-      timeout: 2s
-      retries: 60
-
-  zipkin-server:
+      test: ["CMD", "wget", "-O -", "-q", "http://localhost:4004/actuator/health"]
+      interval: 5s
+      timeout: 2s
+      retries: 60
+
+  jaeger-collector.istio-system:
     image: openzipkin/zipkin:3.5.0
     restart: always
     mem_limit: 1024m
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

</details>

#### `docker-compose.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -77,6 +77,7 @@
 
   mongodb:
     image: mongo:8.0.5
+    restart: always
     mem_limit: 512m
     ports:
       - "27017:27017"
@@ -92,6 +93,7 @@
 
   mysql:
     image: mysql:9.2.0
+    restart: always
     mem_limit: 512m
     ports:
       - "3306:3306"
@@ -108,6 +110,7 @@
 
   rabbitmq:
     image: rabbitmq:4.0.7-management
+    restart: always
     mem_limit: 512m
     ports:
       - 5672:5672
@@ -151,12 +154,12 @@
     volumes:
       - $PWD/config-repo:/config-repo
     healthcheck:
-      test: ["CMD", "wget", "-O -", "-q", "http://localhost/actuator/health"]
+      test: ["CMD", "wget", "-O -", "-q", "http://localhost:4004/actuator/health"]
       interval: 5s
       timeout: 2s
       retries: 60
 
-  zipkin-server:
+  jaeger-collector.istio-system:
     image: openzipkin/zipkin:3.5.0
     restart: always
     mem_limit: 1024m
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

</details>

#### `test-em-all.bash` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -2,15 +2,17 @@
 #
 # With Docker Compose:
 #
+#   HOST=localhost PORT=8443 HEALTH_URL=https://localhost:8443 USE_K8S=false ./test-em-all.bash
+#
+# With Kubernetes:
+#
 #   ./test-em-all.bash
 #
-# With Kubernetes:
-#
-#   HOST=minikube.me USE_K8S=true ./test-em-all.bash
-#
-: ${HOST=localhost}
-: ${PORT=8443}
-: ${USE_K8S=false}
+: ${HOST=minikube.me}
+: ${PORT=443}
+: ${USE_K8S=true}
+: ${HEALTH_URL=https://health.minikube.me}
+: ${MGM_PORT=4004}
 : ${PROD_ID_REVS_RECS=1}
 : ${PROD_ID_NOT_FOUND=13}
 : ${PROD_ID_NO_RECS=113}
@@ -193,11 +195,11 @@
     then
         EXEC="docker compose exec -T product-composite"
     else
-        EXEC="kubectl -n $NAMESPACE exec deploy/product-composite -- "
+        EXEC="kubectl -n $NAMESPACE exec deploy/product-composite -c product-composite -- "
     fi
 
     # First, use the health - endpoint to verify that the circuit breaker is closed
-    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Open the circuit breaker by running three slow calls in a row, i.e. that cause a timeout exception
     # Also, verify that we get 500 back and a timeout related error message
@@ -209,7 +211,7 @@
     done
 
     # Verify that the circuit breaker is open
-    assertEqual "OPEN" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "OPEN" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Verify that the circuit breaker now is open by running the slow call again, verify it gets 200 back, i.e. fail fast works, and a response from the fallback method.
     assertCurl 200 "curl -k https://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS?delay=3 $AUTH -s"
@@ -228,7 +230,7 @@
     sleep 10
 
     # Verify that the circuit breaker is in half open state
-    assertEqual "HALF_OPEN" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "HALF_OPEN" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Close the circuit breaker by running three normal calls in a row
     # Also, verify that we get 200 back and a response based on information in the product database
@@ -239,12 +241,12 @@
     done
 
     # Verify that the circuit breaker is in closed state again
-    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
+    assertEqual "CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/health | jq -r .components.circuitBreakers.details.product.details.state)"
 
     # Verify that the expected state transitions happened in the circuit breaker
-    assertEqual "CLOSED_TO_OPEN"      "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
-    assertEqual "OPEN_TO_HALF_OPEN"   "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
-    assertEqual "HALF_OPEN_TO_CLOSED" "$($EXEC wget -qO - http://localhost/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
+    assertEqual "CLOSED_TO_OPEN"      "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-3].stateTransition)"
+    assertEqual "OPEN_TO_HALF_OPEN"   "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-2].stateTransition)"
+    assertEqual "HALF_OPEN_TO_CLOSED" "$($EXEC wget -qO - http://localhost:${MGM_PORT}/actuator/circuitbreakerevents/product/STATE_TRANSITION | jq -r .circuitBreakerEvents[-1].stateTransition)"
 }
 
 set -e
@@ -254,6 +256,8 @@
 echo "HOST=${HOST}"
 echo "PORT=${PORT}"
 echo "USE_K8S=${USE_K8S}"
+echo "HEALTH_URL=${HEALTH_URL}"
+echo "MGM_PORT=${MGM_PORT}"
 echo "SKIP_CB_TESTS=${SKIP_CB_TESTS}"
 
 if [[ $@ == *"start"* ]]
@@ -265,7 +269,7 @@
   docker compose up -d
 fi
 
-waitForService curl -k https://$HOST:$PORT/actuator/health
+waitForService curl -k $HEALTH_URL/actuator/health
 
 ACCESS_TOKEN=$(curl -k https://writer:secret-writer@$HOST:$PORT/oauth2/token -d grant_type=client_credentials -d scope="product:read product:write" -s | jq .access_token -r)
 echo ACCESS_TOKEN=$ACCESS_TOKEN
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

## 단계 2. `api` 프로젝트 — 서비스 간 API와 DTO

핵심 서비스 API가 요청 헤더(`HttpHeaders`)를 받도록 바꿉니다. 복합 서비스가 받은 헤더를 핵심 서비스로 넘겨, 블루/그린 배포의 `X-group` 헤더 라우팅이 끝까지 이어지게 합니다.

#### `api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -5,6 +5,7 @@
 import io.swagger.v3.oas.annotations.responses.ApiResponses;
 import io.swagger.v3.oas.annotations.security.SecurityRequirement;
 import io.swagger.v3.oas.annotations.tags.Tag;
+import org.springframework.http.HttpHeaders;
 import org.springframework.http.HttpStatus;
 import org.springframework.web.bind.annotation.*;
 import reactor.core.publisher.Mono;
@@ -54,6 +55,7 @@
     value = "/product-composite/{productId}",
     produces = "application/json")
   Mono<ProductAggregate> getProduct(
+    @RequestHeader HttpHeaders headers,
     @PathVariable int productId,
     @RequestParam(value = "delay", required = false, defaultValue = "0") int delay,
     @RequestParam(value = "faultPercent", required = false, defaultValue = "0") int faultPercent
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@SecurityRequirement(name = "security_auth")
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
  Mono<ProductAggregate> getProduct(
    @RequestHeader HttpHeaders headers,
    @PathVariable int productId,
    @RequestParam(value = "delay", required = false, defaultValue = "0") int delay,
    @RequestParam(value = "faultPercent", required = false, defaultValue = "0") int faultPercent
  );

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

#### `api/src/main/java/se/magnus/api/core/product/ProductService.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,7 +1,9 @@
 package se.magnus.api.core.product;
 
+import org.springframework.http.HttpHeaders;
 import org.springframework.web.bind.annotation.GetMapping;
 import org.springframework.web.bind.annotation.PathVariable;
+import org.springframework.web.bind.annotation.RequestHeader;
 import org.springframework.web.bind.annotation.RequestParam;
 import reactor.core.publisher.Mono;
 
@@ -19,6 +21,7 @@
     value = "/product/{productId}",
     produces = "application/json")
   Mono<Product> getProduct(
+    @RequestHeader HttpHeaders headers,
     @PathVariable int productId,
     @RequestParam(value = "delay", required = false, defaultValue = "0") int delay,
     @RequestParam(value = "faultPercent", required = false, defaultValue = "0") int faultPercent
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/core/product/ProductService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.product;

import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;
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
  Mono<Product> getProduct(
    @RequestHeader HttpHeaders headers,
    @PathVariable int productId,
    @RequestParam(value = "delay", required = false, defaultValue = "0") int delay,
    @RequestParam(value = "faultPercent", required = false, defaultValue = "0") int faultPercent
  );

  Mono<Void> deleteProduct(int productId);
}
```

</details>

#### `api/src/main/java/se/magnus/api/core/recommendation/RecommendationService.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,6 @@
 package se.magnus.api.core.recommendation;
 
+import org.springframework.http.HttpHeaders;
 import org.springframework.web.bind.annotation.*;
 import reactor.core.publisher.Flux;
 import reactor.core.publisher.Mono;
@@ -18,6 +19,7 @@
     value = "/recommendation",
     produces = "application/json")
   Flux<Recommendation> getRecommendations(
+    @RequestHeader HttpHeaders headers,
     @RequestParam(value = "productId", required = true) int productId);
 
   Mono<Void> deleteRecommendations(int productId);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/core/recommendation/RecommendationService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.recommendation;

import org.springframework.http.HttpHeaders;
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
    @RequestHeader HttpHeaders headers,
    @RequestParam(value = "productId", required = true) int productId);

  Mono<Void> deleteRecommendations(int productId);
}
```

</details>

#### `api/src/main/java/se/magnus/api/core/review/ReviewService.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,6 @@
 package se.magnus.api.core.review;
 
+import org.springframework.http.HttpHeaders;
 import org.springframework.web.bind.annotation.*;
 import reactor.core.publisher.Flux;
 import reactor.core.publisher.Mono;
@@ -17,7 +18,9 @@
   @GetMapping(
     value = "/review",
     produces = "application/json")
-  Flux<Review> getReviews(@RequestParam(value = "productId", required = true) int productId);
+  Flux<Review> getReviews(
+    @RequestHeader HttpHeaders headers,
+    @RequestParam(value = "productId", required = true) int productId);
 
   Mono<Void> deleteReviews(int productId);
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/core/review/ReviewService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.review;

import org.springframework.http.HttpHeaders;
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
  Flux<Review> getReviews(
    @RequestHeader HttpHeaders headers,
    @RequestParam(value = "productId", required = true) int productId);

  Mono<Void> deleteReviews(int productId);
}
```

</details>

**중간 확인**

```bash
./gradlew :api:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-3"></a>

## 단계 3. `product-service`

`TracingConfig`로 B3 헤더 전파를 설정하고, 추적 의존성을 Brave + `spring-boot-starter-zipkin`으로 바꿉니다.

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -34,10 +34,8 @@
     implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
-    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
-    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
-    implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
+    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
     implementation 'org.springframework.retry:spring-retry'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
 
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

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/TracingConfig.java` — 새 파일 (23줄)

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/TracingConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import brave.baggage.BaggagePropagation;
import brave.baggage.BaggagePropagationCustomizer;
import brave.propagation.B3Propagation;
import brave.propagation.Propagation;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
public class TracingConfig {

  @Bean
  BaggagePropagation.FactoryBuilder myPropagationFactoryBuilder(
    ObjectProvider<BaggagePropagationCustomizer> baggagePropagationCustomizers) {
    Propagation.Factory delegate = B3Propagation.newFactoryBuilder().injectFormat(B3Propagation.Format.MULTI).build();
    BaggagePropagation.FactoryBuilder builder = BaggagePropagation.newFactoryBuilder(delegate);
    baggagePropagationCustomizers.orderedStream().forEach((customizer) -> customizer.customize(builder));
    return builder;
  }
    
}
```

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -7,6 +7,7 @@
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
 import org.springframework.dao.DuplicateKeyException;
+import org.springframework.http.HttpHeaders;
 import org.springframework.web.bind.annotation.RestController;
 import reactor.core.publisher.Mono;
 import se.magnus.api.core.product.Product;
@@ -53,7 +54,7 @@
   }
 
   @Override
-  public Mono<Product> getProduct(int productId, int delay, int faultPercent) {
+  public Mono<Product> getProduct(HttpHeaders headers, int productId, int delay, int faultPercent) {
 
     if (productId < 1) {
       throw new InvalidInputException("Invalid productId: " + productId);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.services;

import static java.util.logging.Level.FINE;

import java.time.Duration;
import java.util.Random;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpHeaders;
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
  public Mono<Product> getProduct(HttpHeaders headers, int productId, int delay, int faultPercent) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    LOG.info("Will get product info for id={}", productId);

    return repository.findByProductId(productId)
      .map(e -> throwErrorIfBadLuck(e, faultPercent))
      .delayElement(Duration.ofSeconds(delay))
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

  private ProductEntity throwErrorIfBadLuck(ProductEntity entity, int faultPercent) {

    if (faultPercent == 0) {
      return entity;
    }

    int randomThreshold = getRandomNumber(1, 100);

    if (faultPercent < randomThreshold) {
      LOG.debug("We got lucky, no error occurred, {} < {}", faultPercent, randomThreshold);
    } else {
      LOG.info("Bad luck, an error occurred, {} >= {}", faultPercent, randomThreshold);
      throw new RuntimeException("Something went wrong...");
    }

    return entity;
  }

  private final Random randomNumberGenerator = new Random();

  private int getRandomNumber(int min, int max) {

    if (max < min) {
      throw new IllegalArgumentException("Max must be greater than min");
    }

    return randomNumberGenerator.nextInt((max - min) + 1) + min;
  }
}
```

</details>

**중간 확인**

```bash
./gradlew :microservices:product-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-4"></a>

## 단계 4. `recommendation-service`

`TracingConfig`로 B3 헤더 전파를 설정하고, 추적 의존성을 Brave + `spring-boot-starter-zipkin`으로 바꿉니다.

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -34,10 +34,8 @@
     implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
-    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
-    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
-    implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
+    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
     implementation 'org.springframework.retry:spring-retry'
     implementation "org.mapstruct:mapstruct:${mapstructVersion}"
 
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

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/TracingConfig.java` — 새 파일 (23줄)

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/TracingConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import brave.baggage.BaggagePropagation;
import brave.baggage.BaggagePropagationCustomizer;
import brave.propagation.B3Propagation;
import brave.propagation.Propagation;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
public class TracingConfig {

  @Bean
  BaggagePropagation.FactoryBuilder myPropagationFactoryBuilder(
    ObjectProvider<BaggagePropagationCustomizer> baggagePropagationCustomizers) {
    Propagation.Factory delegate = B3Propagation.newFactoryBuilder().injectFormat(B3Propagation.Format.MULTI).build();
    BaggagePropagation.FactoryBuilder builder = BaggagePropagation.newFactoryBuilder(delegate);
    baggagePropagationCustomizers.orderedStream().forEach((customizer) -> customizer.customize(builder));
    return builder;
  }
    
}
```

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationServiceImpl.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -5,6 +5,7 @@
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
 import org.springframework.dao.DuplicateKeyException;
+import org.springframework.http.HttpHeaders;
 import org.springframework.web.bind.annotation.RestController;
 import reactor.core.publisher.Flux;
 import reactor.core.publisher.Mono;
@@ -51,7 +52,7 @@
   }
 
   @Override
-  public Flux<Recommendation> getRecommendations(int productId) {
+  public Flux<Recommendation> getRecommendations(HttpHeaders headers, int productId) {
 
     if (productId < 1) {
       throw new InvalidInputException("Invalid productId: " + productId);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.services;

import static java.util.logging.Level.FINE;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpHeaders;
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
  public Flux<Recommendation> getRecommendations(HttpHeaders headers, int productId) {

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

</details>

**중간 확인**

```bash
./gradlew :microservices:recommendation-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `review-service`

`TracingConfig`로 B3 헤더 전파를 설정하고, 추적 의존성을 Brave + `spring-boot-starter-zipkin`으로 바꿉니다.

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -34,10 +34,8 @@
     implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
-    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
-    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
-    implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
+    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
     implementation 'net.ttddyy.observation:datasource-micrometer-spring-boot:2.2.1'
     implementation 'org.springframework.retry:spring-retry'
     implementation 'com.mysql:mysql-connector-j'
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

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/TracingConfig.java` — 새 파일 (23줄)

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/TracingConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import brave.baggage.BaggagePropagation;
import brave.baggage.BaggagePropagationCustomizer;
import brave.propagation.B3Propagation;
import brave.propagation.Propagation;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
public class TracingConfig {

  @Bean
  BaggagePropagation.FactoryBuilder myPropagationFactoryBuilder(
    ObjectProvider<BaggagePropagationCustomizer> baggagePropagationCustomizers) {
    Propagation.Factory delegate = B3Propagation.newFactoryBuilder().injectFormat(B3Propagation.Format.MULTI).build();
    BaggagePropagation.FactoryBuilder builder = BaggagePropagation.newFactoryBuilder(delegate);
    baggagePropagationCustomizers.orderedStream().forEach((customizer) -> customizer.customize(builder));
    return builder;
  }
    
}
```

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewServiceImpl.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -7,6 +7,7 @@
 import org.slf4j.LoggerFactory;
 import org.springframework.beans.factory.annotation.Qualifier;
 import org.springframework.dao.DataIntegrityViolationException;
+import org.springframework.http.HttpHeaders;
 import org.springframework.web.bind.annotation.RestController;
 import reactor.core.publisher.Flux;
 import reactor.core.publisher.Mono;
@@ -62,7 +63,7 @@
   }
 
   @Override
-  public Flux<Review> getReviews(int productId) {
+  public Flux<Review> getReviews(HttpHeaders headers, int productId) {
 
     if (productId < 1) {
       throw new InvalidInputException("Invalid productId: " + productId);
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
import org.springframework.http.HttpHeaders;
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
  public Flux<Review> getReviews(HttpHeaders headers, int productId) {

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

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-6"></a>

## 단계 6. `product-composite-service`

다른 서비스와 같이 `TracingConfig`와 추적 의존성 변경입니다.

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -39,10 +39,8 @@
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
     implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
-    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
-    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
-    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
-    implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
+    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
     implementation 'org.springframework.retry:spring-retry'
     implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:3.0.3'
     implementation "io.github.resilience4j:resilience4j-spring-boot4:${resilience4jVersion}"
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

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/TracingConfig.java` — 새 파일 (23줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/TracingConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import brave.baggage.BaggagePropagation;
import brave.baggage.BaggagePropagationCustomizer;
import brave.propagation.B3Propagation;
import brave.propagation.Propagation;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
public class TracingConfig {

  @Bean
  BaggagePropagation.FactoryBuilder myPropagationFactoryBuilder(
    ObjectProvider<BaggagePropagationCustomizer> baggagePropagationCustomizers) {
    Propagation.Factory delegate = B3Propagation.newFactoryBuilder().injectFormat(B3Propagation.Format.MULTI).build();
    BaggagePropagation.FactoryBuilder builder = BaggagePropagation.newFactoryBuilder(delegate);
    baggagePropagationCustomizers.orderedStream().forEach((customizer) -> customizer.customize(builder));
    return builder;
  }
    
}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -14,6 +14,7 @@
 import org.slf4j.LoggerFactory;
 import org.springframework.beans.factory.annotation.Qualifier;
 import org.springframework.cloud.stream.function.StreamBridge;
+import org.springframework.http.HttpHeaders;
 import org.springframework.http.HttpStatus;
 import org.springframework.messaging.Message;
 import org.springframework.messaging.support.MessageBuilder;
@@ -82,21 +83,26 @@
   @Retry(name = "product")
   @TimeLimiter(name = "product")
   @CircuitBreaker(name = "product", fallbackMethod = "getProductFallbackValue")
-  public Mono<Product> getProduct(int productId, int delay, int faultPercent) {
+  public Mono<Product> getProduct(HttpHeaders headers, int productId, int delay, int faultPercent) {
 
     URI url = UriComponentsBuilder.fromUriString(PRODUCT_SERVICE_URL
       + "/product/{productId}?delay={delay}&faultPercent={faultPercent}").build(productId, delay, faultPercent);
     LOG.debug("Will call the getProduct API on URL: {}", url);
 
     return webClient.get().uri(url)
+      .headers(h -> h.addAll(headers))
       .retrieve().bodyToMono(Product.class).log(LOG.getName(), FINE)
       .onErrorMap(WebClientResponseException.class, ex -> handleException(ex));
   }
 
-  private Mono<Product> getProductFallbackValue(int productId, int delay, int faultPercent, CallNotPermittedException ex) {
+  private Mono<Product> getProductFallbackValue(HttpHeaders headers, int productId, int delay, int faultPercent, CallNotPermittedException ex) {
 
     LOG.warn("Creating a fail-fast fallback product for productId = {}, delay = {}, faultPercent = {} and exception = {} ",
       productId, delay, faultPercent, ex.toString());
+
+    if (productId < 1) {
+      throw new InvalidInputException("Invalid productId: " + productId);
+    }
 
     if (productId == 13) {
       String errMsg = "Product Id: " + productId + " not found in fallback cache!";
@@ -124,14 +130,14 @@
   }
 
   @Override
-  public Flux<Recommendation> getRecommendations(int productId) {
+  public Flux<Recommendation> getRecommendations(HttpHeaders headers, int productId) {
 
     URI url = UriComponentsBuilder.fromUriString(RECOMMENDATION_SERVICE_URL + "/recommendation?productId={productId}").build(productId);
 
     LOG.debug("Will call the getRecommendations API on URL: {}", url);
 
     // Return an empty result if something goes wrong to make it possible for the composite service to return partial responses
-    return webClient.get().uri(url).retrieve().bodyToFlux(Recommendation.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
+    return webClient.get().uri(url).headers(h -> h.addAll(headers)).retrieve().bodyToFlux(Recommendation.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
   }
 
   @Override
@@ -151,14 +157,14 @@
   }
 
   @Override
-  public Flux<Review> getReviews(int productId) {
+  public Flux<Review> getReviews(HttpHeaders headers, int productId) {
 
     URI url = UriComponentsBuilder.fromUriString(REVIEW_SERVICE_URL + "/review?productId={productId}").build(productId);
 
     LOG.debug("Will call the getReviews API on URL: {}", url);
 
     // Return an empty result if something goes wrong to make it possible for the composite service to return partial responses
-    return webClient.get().uri(url).retrieve().bodyToFlux(Review.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
+    return webClient.get().uri(url).headers(h -> h.addAll(headers)).retrieve().bodyToFlux(Review.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
   }
 
   @Override
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services;

import static java.util.logging.Level.FINE;
import static reactor.core.publisher.Flux.empty;
import static se.magnus.api.event.Event.Type.CREATE;
import static se.magnus.api.event.Event.Type.DELETE;

import io.github.resilience4j.circuitbreaker.CallNotPermittedException;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import java.net.URI;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cloud.stream.function.StreamBridge;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.web.util.UriComponentsBuilder;
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
import se.magnus.util.http.ServiceUtil;
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

  private final ServiceUtil serviceUtil;

  public ProductCompositeIntegration(
    @Qualifier("publishEventScheduler") Scheduler publishEventScheduler,
    WebClient webClient,
    ObjectMapper mapper,
    StreamBridge streamBridge,
    ServiceUtil serviceUtil
  ) {
    this.webClient = webClient;

    this.publishEventScheduler = publishEventScheduler;
    this.mapper = mapper;
    this.streamBridge = streamBridge;
    this.serviceUtil = serviceUtil;
  }

  @Override
  public Mono<Product> createProduct(Product body) {

    return Mono.fromCallable(() -> {
      sendMessage("products-out-0", new Event<>(CREATE, body.getProductId(), body));
      return body;
    }).subscribeOn(publishEventScheduler);
  }

  @Override
  @Retry(name = "product")
  @TimeLimiter(name = "product")
  @CircuitBreaker(name = "product", fallbackMethod = "getProductFallbackValue")
  public Mono<Product> getProduct(HttpHeaders headers, int productId, int delay, int faultPercent) {

    URI url = UriComponentsBuilder.fromUriString(PRODUCT_SERVICE_URL
      + "/product/{productId}?delay={delay}&faultPercent={faultPercent}").build(productId, delay, faultPercent);
    LOG.debug("Will call the getProduct API on URL: {}", url);

    return webClient.get().uri(url)
      .headers(h -> h.addAll(headers))
      .retrieve().bodyToMono(Product.class).log(LOG.getName(), FINE)
      .onErrorMap(WebClientResponseException.class, ex -> handleException(ex));
  }

  private Mono<Product> getProductFallbackValue(HttpHeaders headers, int productId, int delay, int faultPercent, CallNotPermittedException ex) {

    LOG.warn("Creating a fail-fast fallback product for productId = {}, delay = {}, faultPercent = {} and exception = {} ",
      productId, delay, faultPercent, ex.toString());

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    if (productId == 13) {
      String errMsg = "Product Id: " + productId + " not found in fallback cache!";
      LOG.warn(errMsg);
      throw new NotFoundException(errMsg);
    }

    return Mono.just(new Product(productId, "Fallback product" + productId, productId, serviceUtil.getServiceAddress()));
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
  public Flux<Recommendation> getRecommendations(HttpHeaders headers, int productId) {

    URI url = UriComponentsBuilder.fromUriString(RECOMMENDATION_SERVICE_URL + "/recommendation?productId={productId}").build(productId);

    LOG.debug("Will call the getRecommendations API on URL: {}", url);

    // Return an empty result if something goes wrong to make it possible for the composite service to return partial responses
    return webClient.get().uri(url).headers(h -> h.addAll(headers)).retrieve().bodyToFlux(Recommendation.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
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
  public Flux<Review> getReviews(HttpHeaders headers, int productId) {

    URI url = UriComponentsBuilder.fromUriString(REVIEW_SERVICE_URL + "/review?productId={productId}").build(productId);

    LOG.debug("Will call the getReviews API on URL: {}", url);

    // Return an empty result if something goes wrong to make it possible for the composite service to return partial responses
    return webClient.get().uri(url).headers(h -> h.addAll(headers)).retrieve().bodyToFlux(Review.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
  }

  @Override
  public Mono<Void> deleteReviews(int productId) {

    return Mono.fromRunnable(() -> sendMessage("reviews-out-0", new Event<>(DELETE, productId, null)))
      .subscribeOn(publishEventScheduler).then();
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

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeServiceImpl.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -9,6 +9,7 @@
 import java.util.stream.Collectors;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
+import org.springframework.http.HttpHeaders;
 import org.springframework.security.core.context.ReactiveSecurityContextHolder;
 import org.springframework.security.core.context.SecurityContext;
 import org.springframework.security.core.context.SecurityContextImpl;
@@ -84,22 +85,38 @@
   }
 
   @Override
-  public Mono<ProductAggregate> getProduct(int productId, int delay, int faultPercent) {
-    return observationWithProductInfo(productId, () -> getProductInternal(productId, delay, faultPercent));
+  public Mono<ProductAggregate> getProduct(HttpHeaders requestHeaders, int productId, int delay, int faultPercent) {
+    return observationWithProductInfo(productId, () -> getProductInternal(requestHeaders, productId, delay, faultPercent));
   }
 
   @SuppressWarnings("unchecked")
-  private Mono<ProductAggregate> getProductInternal(int productId, int delay, int faultPercent) {
+  private Mono<ProductAggregate> getProductInternal(HttpHeaders requestHeaders, int productId, int delay, int faultPercent) {
     LOG.info("Will get composite product info for product.id={}", productId);
+
+    HttpHeaders headers = getHeaders(requestHeaders, "X-group");
+
     return Mono.zip(
         values -> createProductAggregate(
           (SecurityContext) values[0], (Product) values[1], (List<Recommendation>) values[2], (List<Review>) values[3], serviceUtil.getServiceAddress()),
         getSecurityContextMono(),
-        integration.getProduct(productId, delay, faultPercent),
-        integration.getRecommendations(productId).collectList(),
-        integration.getReviews(productId).collectList())
+        integration.getProduct(headers, productId, delay, faultPercent),
+        integration.getRecommendations(headers, productId).collectList(),
+        integration.getReviews(headers, productId).collectList())
       .doOnError(ex -> LOG.warn("getCompositeProduct failed: {}", ex.toString()))
       .log(LOG.getName(), FINE);
+  }
+
+  private HttpHeaders getHeaders(HttpHeaders requesthHeaders, String... headers) {
+    LOG.trace("Will look for {} headers: {}", headers.length, headers);
+    HttpHeaders h = new HttpHeaders();
+    for (String header : headers) {
+      List<String> value = requesthHeaders.get(header);
+      if (value != null) {
+        h.addAll(header, value);
+      }
+    }
+    LOG.trace("Will transfer {}, headers: {}", h.size(), h);
+    return h;
   }
 
   @Override
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services;

import static java.util.logging.Level.FINE;

import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.security.core.context.ReactiveSecurityContextHolder;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextImpl;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;
import se.magnus.api.composite.product.*;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.review.Review;
import se.magnus.microservices.composite.product.services.tracing.ObservationUtil;
import se.magnus.util.http.ServiceUtil;

@RestController
public class ProductCompositeServiceImpl implements ProductCompositeService {

  private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeServiceImpl.class);

  private final SecurityContext nullSecCtx = new SecurityContextImpl();

  private final ServiceUtil serviceUtil;
  private final ObservationUtil observationUtil;
  private final ProductCompositeIntegration integration;

  public ProductCompositeServiceImpl(ServiceUtil serviceUtil, ObservationUtil observationUtil, ProductCompositeIntegration integration) {
    this.serviceUtil = serviceUtil;
    this.observationUtil = observationUtil;
    this.integration = integration;
  }

  @Override
  public Mono<Void> createProduct(ProductAggregate body) {
    return observationWithProductInfo(body.getProductId(), () -> createProductInternal(body));
  }

  private Mono<Void> createProductInternal(ProductAggregate body) {
    try {

      List<Mono> monoList = new ArrayList<>();

      monoList.add(getLogAuthorizationInfoMono());

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
  public Mono<ProductAggregate> getProduct(HttpHeaders requestHeaders, int productId, int delay, int faultPercent) {
    return observationWithProductInfo(productId, () -> getProductInternal(requestHeaders, productId, delay, faultPercent));
  }

  @SuppressWarnings("unchecked")
  private Mono<ProductAggregate> getProductInternal(HttpHeaders requestHeaders, int productId, int delay, int faultPercent) {
    LOG.info("Will get composite product info for product.id={}", productId);

    HttpHeaders headers = getHeaders(requestHeaders, "X-group");

    return Mono.zip(
        values -> createProductAggregate(
          (SecurityContext) values[0], (Product) values[1], (List<Recommendation>) values[2], (List<Review>) values[3], serviceUtil.getServiceAddress()),
        getSecurityContextMono(),
        integration.getProduct(headers, productId, delay, faultPercent),
        integration.getRecommendations(headers, productId).collectList(),
        integration.getReviews(headers, productId).collectList())
      .doOnError(ex -> LOG.warn("getCompositeProduct failed: {}", ex.toString()))
      .log(LOG.getName(), FINE);
  }

  private HttpHeaders getHeaders(HttpHeaders requesthHeaders, String... headers) {
    LOG.trace("Will look for {} headers: {}", headers.length, headers);
    HttpHeaders h = new HttpHeaders();
    for (String header : headers) {
      List<String> value = requesthHeaders.get(header);
      if (value != null) {
        h.addAll(header, value);
      }
    }
    LOG.trace("Will transfer {}, headers: {}", h.size(), h);
    return h;
  }

  @Override
  public Mono<Void> deleteProduct(int productId) {
    return observationWithProductInfo(productId, () -> deleteProductInternal(productId));
  }

  private Mono<Void> deleteProductInternal(int productId) {
    try {

      LOG.info("Will delete a product aggregate for product.id: {}", productId);

      return Mono.zip(r -> "",
          getLogAuthorizationInfoMono(),
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

  private <T> T observationWithProductInfo(int productInfo, Supplier<T> supplier) {
    return observationUtil.observe(
      "composite observation",
      "product info",
      "productId",
      String.valueOf(productInfo),
      supplier);
  }

  private ProductAggregate createProductAggregate(
    SecurityContext sc, Product product, List<Recommendation> recommendations, List<Review> reviews, String serviceAddress) {

    logAuthorizationInfo(sc);

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

  private Mono<SecurityContext> getLogAuthorizationInfoMono() {
    return getSecurityContextMono().doOnNext(sc -> logAuthorizationInfo(sc));
  }

  private Mono<SecurityContext> getSecurityContextMono() {
    return ReactiveSecurityContextHolder.getContext().defaultIfEmpty(nullSecCtx);
  }

  private void logAuthorizationInfo(SecurityContext sc) {
    if (sc != null && sc.getAuthentication() != null && sc.getAuthentication() instanceof JwtAuthenticationToken) {
      Jwt jwtToken = ((JwtAuthenticationToken)sc.getAuthentication()).getToken();
      logAuthorizationInfo(jwtToken);
    } else {
      LOG.warn("No JWT based Authentication supplied, running tests are we?");
    }
  }

  private void logAuthorizationInfo(Jwt jwt) {
    if (jwt == null) {
      LOG.warn("No JWT supplied, running tests are we?");
    } else {
      if (LOG.isDebugEnabled()) {
        URL issuer = jwt.getIssuer();
        List<String> audience = jwt.getAudience();
        Object subject = jwt.getClaims().get("sub");
        Object scopes = jwt.getClaims().get("scope");
        Object expires = jwt.getClaims().get("exp");

        LOG.debug("Authorization info: Subject: {}, scopes: {}, expires {}: issuer: {}, audience: {}", subject, scopes, expires, issuer, audience);
      }
    }
  }
}
```

</details>

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,8 +1,7 @@
 package se.magnus.microservices.composite.product;
 
 import static java.util.Collections.singletonList;
-import static org.mockito.ArgumentMatchers.anyInt;
-import static org.mockito.ArgumentMatchers.eq;
+import static org.mockito.ArgumentMatchers.*;
 import static org.mockito.Mockito.when;
 import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
 import static org.springframework.http.HttpStatus.*;
@@ -47,18 +46,18 @@
   @BeforeEach
   void setUp() {
 
-    when(compositeIntegration.getProduct(eq(PRODUCT_ID_OK), anyInt(), anyInt()))
+    when(compositeIntegration.getProduct(any(), eq(PRODUCT_ID_OK), anyInt(), anyInt()))
       .thenReturn(Mono.just(new Product(PRODUCT_ID_OK, "name", 1, "mock-address")));
 
-    when(compositeIntegration.getRecommendations(PRODUCT_ID_OK))
+    when(compositeIntegration.getRecommendations(any(), eq(PRODUCT_ID_OK)))
       .thenReturn(Flux.fromIterable(singletonList(new Recommendation(PRODUCT_ID_OK, 1, "author", 1, "content", "mock address"))));
 
-    when(compositeIntegration.getReviews(PRODUCT_ID_OK))
+    when(compositeIntegration.getReviews(any(), eq(PRODUCT_ID_OK)))
       .thenReturn(Flux.fromIterable(singletonList(new Review(PRODUCT_ID_OK, 1, "author", "subject", "content", "mock address"))));
 
-    when(compositeIntegration.getProduct(eq(PRODUCT_ID_NOT_FOUND), anyInt(), anyInt())).thenThrow(new NotFoundException("NOT FOUND: " + PRODUCT_ID_NOT_FOUND));
+    when(compositeIntegration.getProduct(any(), eq(PRODUCT_ID_NOT_FOUND), anyInt(), anyInt())).thenThrow(new NotFoundException("NOT FOUND: " + PRODUCT_ID_NOT_FOUND));
 
-    when(compositeIntegration.getProduct(eq(PRODUCT_ID_INVALID), anyInt(), anyInt())).thenThrow(new InvalidInputException("INVALID: " + PRODUCT_ID_INVALID));
+    when(compositeIntegration.getProduct(any(), eq(PRODUCT_ID_INVALID), anyInt(), anyInt())).thenThrow(new InvalidInputException("INVALID: " + PRODUCT_ID_INVALID));
   }
 
   @Test
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

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-7"></a>

## 단계 7. `gateway` — 에지 서버

다른 서비스와 같이 추적 의존성을 Brave로 바꾸고, B3 헤더 전파를 애플리케이션 클래스에서 설정합니다.

#### `spring-cloud/gateway/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -31,10 +31,8 @@
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
     implementation 'org.springframework.cloud:spring-cloud-starter-gateway-server-webflux'
     implementation 'org.springframework.boot:spring-boot-starter-webclient'
-    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
-    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
-    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
-    implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
+    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
     implementation 'org.springframework.retry:spring-retry'
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
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
    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
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

#### `spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/GatewayApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,5 +1,10 @@
 package se.magnus.springcloud.gateway;
 
+import brave.baggage.BaggagePropagation;
+import brave.baggage.BaggagePropagationCustomizer;
+import brave.propagation.B3Propagation;
+import brave.propagation.Propagation;
+import org.springframework.beans.factory.ObjectProvider;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
 import org.springframework.cloud.client.loadbalancer.LoadBalanced;
@@ -16,6 +21,15 @@
     return WebClient.builder();
   }
 
+  @Bean
+  BaggagePropagation.FactoryBuilder myPropagationFactoryBuilder(
+    ObjectProvider<BaggagePropagationCustomizer> baggagePropagationCustomizers) {
+    Propagation.Factory delegate = B3Propagation.newFactoryBuilder().injectFormat(B3Propagation.Format.MULTI).build();
+    BaggagePropagation.FactoryBuilder builder = BaggagePropagation.newFactoryBuilder(delegate);
+    baggagePropagationCustomizers.orderedStream().forEach((customizer) -> customizer.customize(builder));
+    return builder;
+  }
+
   public static void main(String[] args) {
     Hooks.enableAutomaticContextPropagation();
     SpringApplication.run(GatewayApplication.class, args);
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/GatewayApplication.java" op="write" nl="1" -->
```java
package se.magnus.springcloud.gateway;

import brave.baggage.BaggagePropagation;
import brave.baggage.BaggagePropagationCustomizer;
import brave.propagation.B3Propagation;
import brave.propagation.Propagation;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Hooks;

@SpringBootApplication
public class GatewayApplication {

  @Bean
  @LoadBalanced
  public WebClient.Builder loadBalancedWebClientBuilder() {
    return WebClient.builder();
  }

  @Bean
  BaggagePropagation.FactoryBuilder myPropagationFactoryBuilder(
    ObjectProvider<BaggagePropagationCustomizer> baggagePropagationCustomizers) {
    Propagation.Factory delegate = B3Propagation.newFactoryBuilder().injectFormat(B3Propagation.Format.MULTI).build();
    BaggagePropagation.FactoryBuilder builder = BaggagePropagation.newFactoryBuilder(delegate);
    baggagePropagationCustomizers.orderedStream().forEach((customizer) -> customizer.customize(builder));
    return builder;
  }

  public static void main(String[] args) {
    Hooks.enableAutomaticContextPropagation();
    SpringApplication.run(GatewayApplication.class, args);
  }

}
```

</details>

#### `spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/HealthCheckConfiguration.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -28,11 +28,11 @@
 
     final Map<String, ReactiveHealthIndicator> registry = new LinkedHashMap<>();
 
-    registry.put("product",           () -> getHealth("http://product"));
-    registry.put("recommendation",    () -> getHealth("http://recommendation"));
-    registry.put("review",            () -> getHealth("http://review"));
-    registry.put("product-composite", () -> getHealth("http://product-composite"));
-    registry.put("auth-server",       () -> getHealth("http://auth-server"));
+    registry.put("product",           () -> getHealth("http://product:4004"));
+    registry.put("recommendation",    () -> getHealth("http://recommendation:4004"));
+    registry.put("review",            () -> getHealth("http://review:4004"));
+    registry.put("product-composite", () -> getHealth("http://product-composite:4004"));
+    registry.put("auth-server",       () -> getHealth("http://auth-server:4004"));
 
     return CompositeReactiveHealthContributor.fromMap(registry);
   }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/HealthCheckConfiguration.java" op="write" nl="1" -->
```java
package se.magnus.springcloud.gateway;

import static java.util.logging.Level.FINE;

import java.util.LinkedHashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.health.contributor.*;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Configuration
public class HealthCheckConfiguration {

  private static final Logger LOG = LoggerFactory.getLogger(HealthCheckConfiguration.class);

  private WebClient webClient;

  public HealthCheckConfiguration(WebClient.Builder webClientBuilder) {
    this.webClient = webClientBuilder.build();
  }

  @Bean
  ReactiveHealthContributor healthcheckMicroservices() {

    final Map<String, ReactiveHealthIndicator> registry = new LinkedHashMap<>();

    registry.put("product",           () -> getHealth("http://product:4004"));
    registry.put("recommendation",    () -> getHealth("http://recommendation:4004"));
    registry.put("review",            () -> getHealth("http://review:4004"));
    registry.put("product-composite", () -> getHealth("http://product-composite:4004"));
    registry.put("auth-server",       () -> getHealth("http://auth-server:4004"));

    return CompositeReactiveHealthContributor.fromMap(registry);
  }

  private Mono<Health> getHealth(String baseUrl) {
    String url = baseUrl + "/actuator/health";
    LOG.debug("Setting up a call to the Health API on URL: {}", url);
    return webClient.get().uri(url).retrieve().bodyToMono(String.class)
      .map(s -> new Health.Builder().up().build())
      .onErrorResume(ex -> Mono.just(new Health.Builder().down(ex).build()))
      .log(LOG.getName(), FINE);
  }

}
```

</details>

**중간 확인**

```bash
./gradlew :spring-cloud:gateway:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-8"></a>

## 단계 8. `authorization-server` — OAuth 2.0 인가 서버

추적 의존성을 Brave로 바꿉니다.

#### `spring-cloud/authorization-server/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -21,11 +21,8 @@
     implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-authorization-server'
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-security'
-    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
-    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
-    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
-    implementation 'org.springframework.boot:spring-boot-zipkin'
-    implementation 'org.springframework.retry:spring-retry:2.0.13'
+    implementation 'io.micrometer:micrometer-tracing-bridge-brave'
+    implementation 'org.springframework.boot:spring-boot-starter-zipkin'
 
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

#### `spring-cloud/authorization-server/src/main/java/sample/OAuth2AuthorizationServerApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -16,8 +16,14 @@
  */
 package sample;
 
+import brave.baggage.BaggagePropagation;
+import brave.baggage.BaggagePropagationCustomizer;
+import brave.propagation.B3Propagation;
+import brave.propagation.Propagation;
+import org.springframework.beans.factory.ObjectProvider;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
+import org.springframework.context.annotation.Bean;
 
 /**
  * @author Joe Grandja
@@ -26,6 +32,15 @@
 @SpringBootApplication
 public class OAuth2AuthorizationServerApplication {
 
+  @Bean
+  BaggagePropagation.FactoryBuilder myPropagationFactoryBuilder(
+    ObjectProvider<BaggagePropagationCustomizer> baggagePropagationCustomizers) {
+    Propagation.Factory delegate = B3Propagation.newFactoryBuilder().injectFormat(B3Propagation.Format.MULTI).build();
+    BaggagePropagation.FactoryBuilder builder = BaggagePropagation.newFactoryBuilder(delegate);
+    baggagePropagationCustomizers.orderedStream().forEach((customizer) -> customizer.customize(builder));
+    return builder;
+  }
+
   public static void main(String[] args) {
     SpringApplication.run(OAuth2AuthorizationServerApplication.class, args);
   }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/authorization-server/src/main/java/sample/OAuth2AuthorizationServerApplication.java" op="write" nl="1" -->
```java
//CHECKSTYLE:OFF
/*
 * Copyright 2020 the original author or authors.
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
package sample;

import brave.baggage.BaggagePropagation;
import brave.baggage.BaggagePropagationCustomizer;
import brave.propagation.B3Propagation;
import brave.propagation.Propagation;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

/**
 * @author Joe Grandja
 * @since 0.0.1
 */
@SpringBootApplication
public class OAuth2AuthorizationServerApplication {

  @Bean
  BaggagePropagation.FactoryBuilder myPropagationFactoryBuilder(
    ObjectProvider<BaggagePropagationCustomizer> baggagePropagationCustomizers) {
    Propagation.Factory delegate = B3Propagation.newFactoryBuilder().injectFormat(B3Propagation.Format.MULTI).build();
    BaggagePropagation.FactoryBuilder builder = BaggagePropagation.newFactoryBuilder(delegate);
    baggagePropagationCustomizers.orderedStream().forEach((customizer) -> customizer.customize(builder));
    return builder;
  }

  public static void main(String[] args) {
    SpringApplication.run(OAuth2AuthorizationServerApplication.class, args);
  }

}
//CHECKSTYLE:ON
```

</details>

#### `spring-cloud/authorization-server/src/test/java/sample/OAuth2AuthorizationServerApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -21,7 +21,6 @@
 import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
 import static org.hamcrest.core.Is.is;
 
-import org.junit.jupiter.api.Disabled;
 import org.junit.jupiter.api.Test;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
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

<a id="단계-9"></a>

## 단계 9. `config-repo` — 중앙 구성 파일

추적 주소를 Jaeger(`jaeger-collector.istio-system:9411`)로 바꾸고, 관리 엔드포인트를 별도 포트(4004, 게이트웨이는 8443)로 분리합니다.

#### `config-repo/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -12,13 +12,14 @@
 spring.cloud.stream.defaultBinder: rabbit
 
 # WARNING: Exposing all management endpoints over http should only be used during development, must be locked down in production!
+management.server.port: 4004
 management.endpoint.health.show-details: "ALWAYS"
 management.endpoints.web.exposure.include: "*"
 management.endpoint.health.probes.enabled: true
 management.health.rabbit.enabled: true
 management.health.kafka.enabled: false
 
-management.tracing.export.zipkin.endpoint: http://zipkin-server:9411/api/v2/spans
+management.tracing.export.zipkin.endpoint: http://jaeger-collector.istio-system:9411/api/v2/spans
 management.tracing.sampling.probability: 1.0
 logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
 logging.include-application-name: false
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

# Only allow management endpoints over http in production for info, health and circuitbreakerevents
management.endpoints.web.exposure.include: health,info,circuitbreakerevents
```

</details>

#### `config-repo/gateway.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,4 +1,5 @@
 server.port: 8443
+management.server.port: 8443
 spring.application.name: gateway
 
 # During development, allow forwarding the X-Forwarded-* and Forwarded headers from any proxies.
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

<a id="단계-10"></a>

## 단계 10. `kubernetes` — 클러스터 설정 파일

네임스페이스(사이드카 자동 주입 라벨), 이스티오 추적 설정(`istio-tracing.yml`), Telemetry API(`istio-telemetry.yml`)입니다.

#### `kubernetes/hands-on-namespace.yml` — 새 파일 (6줄)

<!-- wb:file path="kubernetes/hands-on-namespace.yml" op="write" nl="1" -->
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hands-on
  labels:
    istio-injection: enabled
```

#### `kubernetes/istio-telemetry.yml` — 새 파일 (9줄)

<!-- wb:file path="kubernetes/istio-telemetry.yml" op="write" nl="0" -->
```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: mesh-default
spec:
  tracing:
  - providers:
    - name: "zipkin"
    randomSamplingPercentage: 100.00
```

#### `kubernetes/istio-tracing.yml` — 새 파일 (12줄)

<!-- wb:file path="kubernetes/istio-tracing.yml" op="write" nl="1" -->
```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    enableTracing: true
    defaultConfig:
      tracing: {} # disable legacy MeshConfig tracing options
    extensionProviders:
    - name: "zipkin"
      zipkin:
        service: zipkin.istio-system.svc.cluster.local
        port: 9411
```

<a id="단계-11"></a>

## 단계 11. `kubernetes/resilience-tests` — 장애·지연 주입

상품 서비스에 장애와 지연을 넣는 VirtualService입니다.

#### `kubernetes/resilience-tests/product-virtual-service-with-delay.yml` — 새 파일 (15줄)

<!-- wb:file path="kubernetes/resilience-tests/product-virtual-service-with-delay.yml" op="write" nl="1" -->
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: product
spec:
  hosts:
    - product
  http:
  - route:
    - destination:
        host: product
    fault:
      delay:
        fixedDelay: 3s
        percent: 100
```

#### `kubernetes/resilience-tests/product-virtual-service-with-faults.yml` — 새 파일 (16줄)

<!-- wb:file path="kubernetes/resilience-tests/product-virtual-service-with-faults.yml" op="write" nl="0" -->
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: product
spec:
  hosts:
    - product
  http:
  - route:
    - destination:
        host: product
    fault:
      abort:
        httpStatus: 500
        percentage:
          value: 20
```

<a id="단계-12"></a>

## 단계 12. `kubernetes/routing-tests` — 트래픽 분할

구버전과 새 버전 사이에 트래픽을 나누는 스크립트입니다.

#### `kubernetes/routing-tests/split-traffic-between-old-and-new-services.bash` — 새 파일 (21줄)

<!-- wb:file path="kubernetes/routing-tests/split-traffic-between-old-and-new-services.bash" op="write" nl="1" -->
```bash
#!/usr/bin/env bash

set -e

old_percentage=$1
new_percentage=$2

kubectl patch virtualservice product --type=json -p="[
  {\"op\": \"add\", \"path\": \"/spec/http/1/route/0/weight\", \"value\": ${old_percentage}},
  {\"op\": \"add\", \"path\": \"/spec/http/1/route/1/weight\", \"value\": ${new_percentage}}
]"

kubectl patch virtualservice recommendation --type=json -p="[
  {\"op\": \"add\", \"path\": \"/spec/http/1/route/0/weight\", \"value\": ${old_percentage}},
  {\"op\": \"add\", \"path\": \"/spec/http/1/route/1/weight\", \"value\": ${new_percentage}}
]"

kubectl patch virtualservice review --type=json -p="[
  {\"op\": \"add\", \"path\": \"/spec/http/1/route/0/weight\", \"value\": ${old_percentage}},
  {\"op\": \"add\", \"path\": \"/spec/http/1/route/1/weight\", \"value\": ${new_percentage}}
]"
```

<a id="단계-13"></a>

## 단계 13. 헬름 `common` 라이브러리 차트

Ingress·Issuer 템플릿을 지우고 이스티오 템플릿(`_istio_base.yaml`, `_istio_dr_mutual_tls.yaml`, `_istio_vs_green_blue_deploy.yaml`)을 추가합니다.

**지울 파일**

```bash
rm kubernetes/helm/common/templates/_ingress.yaml
rm kubernetes/helm/common/templates/_issuer.yaml
```

<!-- wb:file path="kubernetes/helm/common/templates/_ingress.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/common/templates/_issuer.yaml" op="delete" nl="0" -->

#### `kubernetes/helm/common/templates/_deployment.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -19,8 +19,16 @@
       app.kubernetes.io/name: {{ include "common.name" . }}
   template:
     metadata:
+{{- if .Values.annotations }}
+{{- with .Values.annotations }}
+      annotations:
+{{ toYaml . | indent 8 }}
+{{- end }}
+{{- end }}
       labels:
         app.kubernetes.io/name: {{ include "common.name" . }}
+        app: {{ include "common.name" . }}
+        version: {{ .Values.image.tag }}
     spec:
       containers:
         - name: {{ .Chart.Name }}
```

<details><summary>완성된 파일 전체 보기</summary>

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
{{- if .Values.annotations }}
{{- with .Values.annotations }}
      annotations:
{{ toYaml . | indent 8 }}
{{- end }}
{{- end }}
      labels:
        app.kubernetes.io/name: {{ include "common.name" . }}
        app: {{ include "common.name" . }}
        version: {{ .Values.image.tag }}
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

</details>

#### `kubernetes/helm/common/templates/_istio_base.yaml` — 새 파일 (131줄)

<!-- wb:file path="kubernetes/helm/common/templates/_istio_base.yaml" op="write" nl="1" -->
```yaml
{{- define "common.istio_base" -}}
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: product-composite-require-jwt
spec:
  action: ALLOW
  rules:
  - {}
  selector:
    matchLabels:
      app.kubernetes.io/name: product-composite
---
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: PERMISSIVE
---
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: product-composite-request-authentication
spec:
  jwtRules:
  - forwardOriginalToken: true
    issuer: http://auth-server
    jwksUri: http://auth-server.hands-on.svc.cluster.local/oauth2/jwks
  selector:
    matchLabels:
      app.kubernetes.io/name: product-composite
---
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: hands-on-gw
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - minikube.me
    port:
      name: https
      number: 443
      protocol: HTTPS
    tls:
      credentialName: hands-on-certificate
      mode: SIMPLE
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: hands-on-vs
spec:
  gateways:
  - hands-on-gw
  hosts:
  - minikube.me
  http:
  - match:
    - uri:
        prefix: /oauth2
    route:
    - destination:
        host: auth-server
  - match:
    - uri:
        prefix: /login
    route:
    - destination:
        host: auth-server
  - match:
    - uri:
        prefix: /error
    route:
    - destination:
        host: auth-server
  - match:
    - uri:
        prefix: /product-composite
    route:
    - destination:
        host: product-composite
        port:
          number: 80
  - match:
    - uri:
        prefix: /openapi
    route:
    - destination:
        host: product-composite
        port:
          number: 80
---
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: health-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - "health.minikube.me"
    port:
      number: 443
      name: https-health
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: hands-on-certificate
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: health-vs
spec:
  hosts:
  - "health.minikube.me"
  gateways:
  - health-gateway
  http:
  - route:
    - destination:
        host: product-composite
        port:
          number: 4004
{{- end -}}
```

#### `kubernetes/helm/common/templates/_istio_dr_mutual_tls.yaml` — 새 파일 (20줄)

<!-- wb:file path="kubernetes/helm/common/templates/_istio_dr_mutual_tls.yaml" op="write" nl="1" -->
```yaml
{{- define "common.istio_dr_mutual_tls" -}}
{{- range $idx, $dr := .Values.destinationRules }}
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: {{ $dr.name }}
spec:
  host: {{ $dr.name }}
{{- if $dr.subsets }}
{{- with $dr.subsets }}
  subsets:
{{ toYaml . | indent 2 }}
{{- end }}
{{- end }}
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
---
{{- end -}}
{{- end -}}
```

#### `kubernetes/helm/common/templates/_istio_vs_green_blue_deploy.yaml` — 새 파일 (30줄)

<!-- wb:file path="kubernetes/helm/common/templates/_istio_vs_green_blue_deploy.yaml" op="write" nl="1" -->
```yaml
{{- define "common.istio_vs_green_blue_deploy" -}}
{{- range $name := .Values.virtualServices }}
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: {{ $name }}
spec:
  hosts:
  - {{ $name }}
  http:
  - match:
    - headers:
        X-group:
          exact: test
    route:
    - destination:
        host: {{ $name }}
        subset: new
  - route:
    - destination:
        host: {{ $name }}
        subset: old
      weight: 100
    - destination:
        host: {{ $name }}
        subset: new
      weight: 0
---
{{- end -}}
{{- end -}}
```

#### `kubernetes/helm/common/templates/_service.yaml` — 전체를 다음 내용으로 바꿉니다

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
  name: {{ include "common.name" . }}
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

#### `kubernetes/helm/common/values.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -22,7 +22,7 @@
   httpGet:
     scheme: HTTP
     path: /actuator/health/liveness
-    port: 80
+    port: 4004
   initialDelaySeconds: 10
   periodSeconds: 10
   timeoutSeconds: 2
@@ -34,7 +34,7 @@
   httpGet:
     scheme: HTTP
     path: /actuator/health/readiness
-    port: 80
+    port: 4004
   initialDelaySeconds: 10
   periodSeconds: 10
   timeoutSeconds: 2
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
    port: 4004
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
    port: 4004
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

<a id="단계-14"></a>

## 단계 14. 헬름 `components` 차트 — 서비스별 차트

서비스 차트 값을 이스티오에 맞추고, 블루/그린 배포용 차트를 추가합니다.

**지울 파일**

```bash
rm kubernetes/helm/components/zipkin-server/Chart.lock
rm kubernetes/helm/components/zipkin-server/Chart.yaml
rm kubernetes/helm/components/zipkin-server/templates/deployment.yaml
rm kubernetes/helm/components/zipkin-server/templates/service.yaml
rm kubernetes/helm/components/zipkin-server/values.yaml
```

<!-- wb:file path="kubernetes/helm/components/zipkin-server/Chart.lock" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/zipkin-server/Chart.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/zipkin-server/templates/deployment.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/zipkin-server/templates/service.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/components/zipkin-server/values.yaml" op="delete" nl="0" -->

#### `kubernetes/helm/components/auth-server/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/auth-server/config-repo && cp config-repo/application.yml kubernetes/helm/components/auth-server/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/auth-server/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/mongodb/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/mongodb/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: mongodb

annotations:
  sidecar.istio.io/inject: "false"

image:
  repository: registry.hub.docker.com/library
  name: mongo
  tag: 8.0.5
  pullPolicy: IfNotPresent

ports:
  - containerPort: 27017

service:
  ports:
    - name: mongo
      port: 27017
```

#### `kubernetes/helm/components/mysql/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/components/mysql/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: mysql

annotations:
  sidecar.istio.io/inject: "false"

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
    - name: mysql
      port: 3306
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
@@ -2,6 +2,14 @@
 
 image:
   name: product-composite-service
+
+ports:
+  - name: http
+    containerPort: 80
+    protocol: TCP
+  - name: http-mgm
+    containerPort: 4004
+    protocol: TCP
 
 env:
   SPRING_PROFILES_ACTIVE: "docker"
@@ -15,3 +23,12 @@
   enabled: true
   volumeMounts:
     mountPath: /config-repo
+
+service:
+  ports:
+    - port: 80
+      name: http
+      targetPort: 80
+    - port: 4004
+      name: http-mgm
+      targetPort: 4004
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="kubernetes/helm/components/product-composite/values.yaml" op="write" nl="0" -->
```yaml
fullnameOverride: product-composite

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

#### `kubernetes/helm/components/product-green/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/product-green/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/product-green/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/product-green/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/product-green/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/product-green/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Product microservice
name: product-green
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/product-green/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product-green/config-repo && cp config-repo/application.yml kubernetes/helm/components/product-green/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/product-green/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/product-green/config-repo/product.yml` — 새 파일 (`config-repo/product.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product-green/config-repo && cp config-repo/product.yml kubernetes/helm/components/product-green/config-repo/product.yml
```

<!-- wb:file path="kubernetes/helm/components/product-green/config-repo/product.yml" op="cp" src="config-repo/product.yml" -->

#### `kubernetes/helm/components/product-green/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/product-green/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/product-green/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/product-green/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/product-green/values.yaml` — 새 파일 (18줄)

<!-- wb:file path="kubernetes/helm/components/product-green/values.yaml" op="write" nl="1" -->
```yaml
nameOverride: product
fullnameOverride: product-green

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

#### `kubernetes/helm/components/product/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/product/config-repo && cp config-repo/application.yml kubernetes/helm/components/product/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/product/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/rabbitmq/values.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,4 +1,7 @@
 fullnameOverride: rabbitmq
+
+annotations:
+  sidecar.istio.io/inject: "false"
 
 image:
   repository: registry.hub.docker.com/library
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="kubernetes/helm/components/rabbitmq/values.yaml" op="write" nl="1" -->
```yaml
fullnameOverride: rabbitmq

annotations:
  sidecar.istio.io/inject: "false"

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

#### `kubernetes/helm/components/recommendation-green/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/recommendation-green/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/recommendation-green/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/recommendation-green/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/recommendation-green/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/recommendation-green/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Recommendation microservice
name: recommendation-green
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/recommendation-green/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/recommendation-green/config-repo && cp config-repo/application.yml kubernetes/helm/components/recommendation-green/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/recommendation-green/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/recommendation-green/config-repo/recommendation.yml` — 새 파일 (`config-repo/recommendation.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/recommendation-green/config-repo && cp config-repo/recommendation.yml kubernetes/helm/components/recommendation-green/config-repo/recommendation.yml
```

<!-- wb:file path="kubernetes/helm/components/recommendation-green/config-repo/recommendation.yml" op="cp" src="config-repo/recommendation.yml" -->

#### `kubernetes/helm/components/recommendation-green/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/recommendation-green/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/recommendation-green/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/recommendation-green/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/recommendation-green/values.yaml` — 새 파일 (18줄)

<!-- wb:file path="kubernetes/helm/components/recommendation-green/values.yaml" op="write" nl="1" -->
```yaml
nameOverride: recommendation
fullnameOverride: recommendation-green

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

#### `kubernetes/helm/components/recommendation/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/recommendation/config-repo && cp config-repo/application.yml kubernetes/helm/components/recommendation/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/recommendation/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/review-green/.helmignore` — 복사/생성

헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요.

<!-- wb:file path="kubernetes/helm/components/review-green/.helmignore" op="copy" nl="0" -->

#### `kubernetes/helm/components/review-green/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/components/review-green/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/components/review-green/Chart.yaml` — 새 파일 (10줄)

<!-- wb:file path="kubernetes/helm/components/review-green/Chart.yaml" op="write" nl="0" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for the Review microservice
name: review-green
version: 1.0.0

dependencies:
  - name: common
    version: 1.0.0
    repository: file://../../common
```

#### `kubernetes/helm/components/review-green/config-repo/application.yml` — 새 파일 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review-green/config-repo && cp config-repo/application.yml kubernetes/helm/components/review-green/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/review-green/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

#### `kubernetes/helm/components/review-green/config-repo/review.yml` — 새 파일 (`config-repo/review.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review-green/config-repo && cp config-repo/review.yml kubernetes/helm/components/review-green/config-repo/review.yml
```

<!-- wb:file path="kubernetes/helm/components/review-green/config-repo/review.yml" op="cp" src="config-repo/review.yml" -->

#### `kubernetes/helm/components/review-green/templates/configmap_from_file.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/review-green/templates/configmap_from_file.yaml" op="write" nl="0" -->
```yaml
{{- template "common.configmap_from_file" . -}}
```

#### `kubernetes/helm/components/review-green/templates/deployment.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/components/review-green/templates/deployment.yaml" op="write" nl="0" -->
```yaml
{{- template "common.deployment" . -}}
```

#### `kubernetes/helm/components/review-green/values.yaml` — 새 파일 (18줄)

<!-- wb:file path="kubernetes/helm/components/review-green/values.yaml" op="write" nl="1" -->
```yaml
nameOverride: review
fullnameOverride: review-green

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

#### `kubernetes/helm/components/review/config-repo/application.yml` — 전체를 바꿉니다 (`config-repo/application.yml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p kubernetes/helm/components/review/config-repo && cp config-repo/application.yml kubernetes/helm/components/review/config-repo/application.yml
```

<!-- wb:file path="kubernetes/helm/components/review/config-repo/application.yml" op="cp" src="config-repo/application.yml" -->

<a id="단계-15"></a>

## 단계 15. 헬름 `environments` 차트 — 환경별 묶음

`istio-system` 환경 차트(Kiali·Jaeger·Grafana·Prometheus 노출, 인증서)를 추가하고 개발·운영 환경에 이스티오 리소스를 넣습니다.

**지울 파일**

```bash
rm kubernetes/helm/environments/dev-env/templates/ingress.yaml
rm kubernetes/helm/environments/dev-env/templates/issuer.yaml
rm kubernetes/helm/environments/prod-env/templates/ingress.yaml
rm kubernetes/helm/environments/prod-env/templates/issuer.yaml
```

<!-- wb:file path="kubernetes/helm/environments/dev-env/templates/ingress.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/environments/dev-env/templates/issuer.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/environments/prod-env/templates/ingress.yaml" op="delete" nl="0" -->
<!-- wb:file path="kubernetes/helm/environments/prod-env/templates/issuer.yaml" op="delete" nl="0" -->

#### `kubernetes/helm/environments/dev-env/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/environments/dev-env/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/environments/dev-env/Chart.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -41,7 +41,3 @@
   - name: product-composite
     version: 1.0.0
     repository: file://../../components/product-composite
-
-  - name: zipkin-server
-    version: 1.0.0
-    repository: file://../../components/zipkin-server
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
```

</details>

#### `kubernetes/helm/environments/dev-env/templates/istio_base.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env/templates/istio_base.yaml" op="write" nl="0" -->
```yaml
{{- template "common.istio_base" . -}}
```

#### `kubernetes/helm/environments/dev-env/templates/istio_dr_mutual_tls.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/dev-env/templates/istio_dr_mutual_tls.yaml" op="write" nl="0" -->
```yaml
{{- template "common.istio_dr_mutual_tls" . -}}
```

#### `kubernetes/helm/environments/dev-env/values.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,19 +1,3 @@
-ingress:
-  host: minikube.me
-  paths:
-    - path: /oauth2
-      service: auth-server
-    - path: /login
-      service: auth-server
-    - path: /error
-      service: auth-server
-    - path: /product-composite
-      service: product-composite
-    - path: /actuator/health
-      service: product-composite
-    - path: /openapi
-      service: product-composite
-
 secrets:
 
   rabbitmq-server-credentials:
@@ -77,3 +61,10 @@
 product-composite:
   envFromSecretRefs:
     - rabbitmq-credentials
+
+destinationRules:
+  - name: product-composite
+  - name: auth-server
+  - name: product
+  - name: recommendation
+  - name: review
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="kubernetes/helm/environments/dev-env/values.yaml" op="write" nl="1" -->
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

destinationRules:
  - name: product-composite
  - name: auth-server
  - name: product
  - name: recommendation
  - name: review
```

</details>

#### `kubernetes/helm/environments/istio-system/Chart.yaml` — 새 파일 (6줄)

<!-- wb:file path="kubernetes/helm/environments/istio-system/Chart.yaml" op="write" nl="1" -->
```yaml
apiVersion: v2
appVersion: "1.0"
description: A Helm chart for added definitions in the istio-system namespace
name: istio-system
version: 1.0.0

```

#### `kubernetes/helm/environments/istio-system/templates/expose-grafana.yml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/environments/istio-system/templates/expose-grafana.yml" op="write" nl="1" -->
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: grafana-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - "grafana.minikube.me"
    port:
      number: 443
      name: https-grafana
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: hands-on-certificate
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: grafana-vs
  namespace: istio-system
spec:
  hosts:
  - "grafana.minikube.me"
  gateways:
  - grafana-gateway
  http:
  - route:
    - destination:
        host: grafana
        port:
          number: 3000
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: grafana
  namespace: istio-system
spec:
  host: grafana
  trafficPolicy:
    tls:
      mode: DISABLE
```

#### `kubernetes/helm/environments/istio-system/templates/expose-kiali.yml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/environments/istio-system/templates/expose-kiali.yml" op="write" nl="1" -->
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: kiali-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - "kiali.minikube.me"
    port:
      number: 443
      name: https-kiali
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: hands-on-certificate
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: kiali-vs
  namespace: istio-system
spec:
  hosts:
  - "kiali.minikube.me"
  gateways:
  - kiali-gateway
  http:
  - route:
    - destination:
        host: kiali
        port:
          number: 20001
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: kiali
  namespace: istio-system
spec:
  host: kiali
  trafficPolicy:
    tls:
      mode: DISABLE
```

#### `kubernetes/helm/environments/istio-system/templates/expose-prometheus.yml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/environments/istio-system/templates/expose-prometheus.yml" op="write" nl="1" -->
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: prometheus-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - "prometheus.minikube.me"
    port:
      number: 443
      name: https-prom
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: hands-on-certificate
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: prometheus-vs
  namespace: istio-system
spec:
  hosts:
  - "prometheus.minikube.me"
  gateways:
  - prometheus-gateway
  http:
  - route:
    - destination:
        host: prometheus
        port:
          number: 9090
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: prometheus
  namespace: istio-system
spec:
  host: prometheus
  trafficPolicy:
    tls:
      mode: DISABLE
```

#### `kubernetes/helm/environments/istio-system/templates/expose-tracing.yml` — 새 파일 (46줄)

<!-- wb:file path="kubernetes/helm/environments/istio-system/templates/expose-tracing.yml" op="write" nl="1" -->
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: tracing-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - hosts:
    - "tracing.minikube.me"
    port:
      number: 443
      name: https-tracing
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: hands-on-certificate
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: tracing-vs
  namespace: istio-system
spec:
  hosts:
  - "tracing.minikube.me"
  gateways:
  - tracing-gateway
  http:
  - route:
    - destination:
        host: tracing
        port:
          number: 80
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: tracing
  namespace: istio-system
spec:
  host: tracing
  trafficPolicy:
    tls:
      mode: DISABLE
```

#### `kubernetes/helm/environments/istio-system/templates/hands-on-certificate.yaml` — 새 파일 (37줄)

<!-- wb:file path="kubernetes/helm/environments/istio-system/templates/hands-on-certificate.yaml" op="write" nl="1" -->
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: hands-on-certificate
spec:
  commonName: minikube.me
  subject:
    countries:
    - my-country
    localities:
    - my-locality
    organizationalUnits:
    - my-ou
    organizations:
    - my-org
    postalCodes:
    - my-pc
    provinces:
    - my-province
    serialNumber: my-sn
    streetAddresses:
    - my-address
  dnsNames:
  - minikube.me
  - health.minikube.me
  - dashboard.minikube.me
  - kiali.minikube.me
  - tracing.minikube.me
  - prometheus.minikube.me
  - grafana.minikube.me
  - kibana.minikube.me
  - elasticsearch.minikube.me
  - mail.minikube.me
  issuerRef:
    name: ca-issuer
  secretName: hands-on-certificate

```

#### `kubernetes/helm/environments/istio-system/templates/selfsigned-issuer.yaml` — 새 파일 (25줄)

<!-- wb:file path="kubernetes/helm/environments/istio-system/templates/selfsigned-issuer.yaml" op="write" nl="0" -->
```yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ca-cert
spec:
  isCA: true
  commonName: hands-on-ca
  secretName: ca-secret
  issuerRef:
    name: selfsigned-issuer
---
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: ca-issuer
spec:
  ca:
    secretName: ca-secret
```

#### `kubernetes/helm/environments/istio-system/values.yaml` — 빈 파일

내용이 없는 파일입니다.

```bash
mkdir -p kubernetes/helm/environments/istio-system && touch kubernetes/helm/environments/istio-system/values.yaml
```

<!-- wb:file path="kubernetes/helm/environments/istio-system/values.yaml" op="empty" -->

#### `kubernetes/helm/environments/prod-env/Chart.lock` — 복사/생성

`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요.

<!-- wb:file path="kubernetes/helm/environments/prod-env/Chart.lock" op="copy" nl="0" -->

#### `kubernetes/helm/environments/prod-env/Chart.yaml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -30,6 +30,14 @@
     version: 1.0.0
     repository: file://../../components/product-composite
 
-  - name: zipkin-server
+  - name: product-green
     version: 1.0.0
-    repository: file://../../components/zipkin-server
+    repository: file://../../components/product-green
+
+  - name: recommendation-green
+    version: 1.0.0
+    repository: file://../../components/recommendation-green
+
+  - name: review-green
+    version: 1.0.0
+    repository: file://../../components/review-green
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

  - name: product-green
    version: 1.0.0
    repository: file://../../components/product-green

  - name: recommendation-green
    version: 1.0.0
    repository: file://../../components/recommendation-green

  - name: review-green
    version: 1.0.0
    repository: file://../../components/review-green
```

</details>

#### `kubernetes/helm/environments/prod-env/templates/istio_base.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/prod-env/templates/istio_base.yaml" op="write" nl="0" -->
```yaml
{{- template "common.istio_base" . -}}
```

#### `kubernetes/helm/environments/prod-env/templates/istio_dr_mutual_tls.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/prod-env/templates/istio_dr_mutual_tls.yaml" op="write" nl="0" -->
```yaml
{{- template "common.istio_dr_mutual_tls" . -}}
```

#### `kubernetes/helm/environments/prod-env/templates/istio_vs_green_blue_deploy.yaml` — 새 파일 (1줄)

<!-- wb:file path="kubernetes/helm/environments/prod-env/templates/istio_vs_green_blue_deploy.yaml" op="write" nl="0" -->
```yaml
{{- template "common.istio_vs_green_blue_deploy" . -}}
```

#### `kubernetes/helm/environments/prod-env/values.yaml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="kubernetes/helm/environments/prod-env/values.yaml" op="write" nl="0" -->
```yaml
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
  fullnameOverride: product-v1
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
  fullnameOverride: recommendation-v1
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
  fullnameOverride: review-v1
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

product-green:
  fullnameOverride: product-v2
  image:
    tag: v2
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

recommendation-green:
  fullnameOverride: recommendation-v2
  image:
    tag: v2
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

review-green:
  fullnameOverride: review-v2
  image:
    tag: v2
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

virtualServices:
  - product
  - recommendation
  - review

destinationRules:
  - name: product-composite
  - name: auth-server
  - name: product
    subsets:
    - labels:
        version: v1
      name: old
    - labels:
        version: v2
      name: new
  - name: recommendation
    subsets:
    - labels:
        version: v1
      name: old
    - labels:
        version: v2
      name: new
  - name: review
    subsets:
    - labels:
        version: v1
      name: old
    - labels:
        version: v2
      name: new
```

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter18
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
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter18
```

---

← [17장 워크북](Chapter17.md) · [워크북 목차](README.md) · [19장 워크북](Chapter19.md) →
