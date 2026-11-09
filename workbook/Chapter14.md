# 14장 워크북 — 분산 추적

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 14장 · 영문 3판 p.349–372 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter14/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter14`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter14) · 위키: [14장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/14장-분산-추적)

## 이 장에서 만드는 것

**Micrometer Tracing과 Zipkin**으로 분산 추적을 추가합니다.

- 모든 서비스에 추적 의존성과 Zipkin 주소 설정
- 로그에 추적 ID 넣기
- 복합 서비스에서 사용자 정의 스팬과 태그 만들기

## 시작하기

13장을 끝낸 작업 폴더를 복사해서 시작합니다. 13장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter13 Chapter14          # 내가 만든 13장 결과에서 시작
# 또는: cp -r <저장소>/Chapter13 Chapter14        # 저장소의 13장 완성 코드에서 시작
cd Chapter14 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 수정 3
2. [`product-service`](#단계-2) — 수정 4
3. [`recommendation-service`](#단계-3) — 수정 3
4. [`review-service`](#단계-4) — 수정 3
5. [`product-composite-service`](#단계-5) — 새 파일 3 · 수정 5
6. [`eureka-server` — 서비스 검색 서버](#단계-6) — 수정 3
7. [`gateway` — 에지 서버](#단계-7) — 수정 3
8. [`authorization-server` — OAuth 2.0 인가 서버](#단계-8) — 수정 3
9. [`config-repo` — 중앙 구성 파일](#단계-9) — 수정 5

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

세 컴포즈 파일에 Zipkin 서버(`openzipkin/zipkin:3.5.0`)를 추가합니다.

#### `docker-compose-kafka.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -191,3 +191,12 @@
       - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
     volumes:
       - $PWD/config-repo:/config-repo
+
+  zipkin-server:
+    image: openzipkin/zipkin:3.5.0
+    restart: always
+    mem_limit: 1024m
+    environment:
+      - STORAGE_TYPE=mem
+    ports:
+      - 9411:9411
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose-kafka.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
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

  eureka:
    build: spring-cloud/eureka-server
    mem_limit: 512m
    environment:
    - SPRING_PROFILES_ACTIVE=docker
    - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
    - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}

  gateway:
    build: spring-cloud/gateway
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
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost:9999/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

  config-server:
    build: spring-cloud/config-server
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
@@ -174,3 +174,12 @@
       - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
     volumes:
       - $PWD/config-repo:/config-repo
+
+  zipkin-server:
+    image: openzipkin/zipkin:3.5.0
+    restart: always
+    mem_limit: 1024m
+    environment:
+      - STORAGE_TYPE=mem
+    ports:
+      - 9411:9411
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose-partitions.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
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

  eureka:
    build: spring-cloud/eureka-server
    mem_limit: 512m
    environment:
    - SPRING_PROFILES_ACTIVE=docker
    - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
    - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}

  gateway:
    build: spring-cloud/gateway
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
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost:9999/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

  config-server:
    build: spring-cloud/config-server
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
@@ -135,3 +135,12 @@
       - SPRING_SECURITY_USER_PASSWORD=${CONFIG_SERVER_PWD}
     volumes:
       - $PWD/config-repo:/config-repo
+
+  zipkin-server:
+    image: openzipkin/zipkin:3.5.0
+    restart: always
+    mem_limit: 1024m
+    environment:
+      - STORAGE_TYPE=mem
+    ports:
+      - 9411:9411
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="docker-compose.yml" op="write" nl="1" -->
```yaml
services:
  product:
    build: microservices/product-service
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

  eureka:
    build: spring-cloud/eureka-server
    mem_limit: 512m
    environment:
    - SPRING_PROFILES_ACTIVE=docker
    - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
    - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}

  gateway:
    build: spring-cloud/gateway
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
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - CONFIG_SERVER_USR=${CONFIG_SERVER_USR}
      - CONFIG_SERVER_PWD=${CONFIG_SERVER_PWD}
    healthcheck:
      test: ["CMD", "wget", "-O -", "-q", "http://localhost:9999/actuator/health"]
      interval: 5s
      timeout: 2s
      retries: 60

  config-server:
    build: spring-cloud/config-server
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

<a id="단계-2"></a>

## 단계 2. `product-service`

추적 의존성을 추가하고, 리액티브 코드에서 추적 정보가 이어지도록 애플리케이션 클래스에서 `Hooks.enableAutomaticContextPropagation()`을 호출합니다.

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -42,6 +42,10 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
     implementation 'org.springframework.retry:spring-retry'
+    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
+    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
+    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
+    implementation 'org.springframework.boot:spring-boot-zipkin'
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

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/ProductServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -16,6 +16,7 @@
 import org.springframework.data.mongodb.core.index.ReactiveIndexOperations;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentEntity;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentProperty;
+import reactor.core.publisher.Hooks;
 import se.magnus.microservices.core.product.persistence.ProductEntity;
 
 @SpringBootApplication
@@ -25,6 +26,7 @@
   private static final Logger LOG = LoggerFactory.getLogger(ProductServiceApplication.class);
 
   public static void main(String[] args) {
+    Hooks.enableAutomaticContextPropagation();
     ConfigurableApplicationContext ctx = SpringApplication.run(ProductServiceApplication.class, args);
 
     String mongodDbHost = ctx.getEnvironment().getProperty("spring.mongodb.host");
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
import reactor.core.publisher.Hooks;
import se.magnus.microservices.core.product.persistence.ProductEntity;

@SpringBootApplication
@ComponentScan("se.magnus")
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

#### `microservices/product-service/src/main/resources/bootstrap.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/main/resources/bootstrap.yml" op="write" nl="1" -->
```yaml
spring.application.name: product

logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
logging.include-application-name: false

spring.cloud.config:
  failFast: true
  retry:
    initialInterval: 3000
    multiplier: 1.3
    maxInterval: 10000
    maxAttempts: 20
  uri: http://localhost:8888
  username: ${CONFIG_SERVER_USR}
  password: ${CONFIG_SERVER_PWD}    

---
spring.config.activate.on-profile: docker

spring.cloud.config.uri: http://config-server:8888
```

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff

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
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
  "eureka.client.enabled=false",
  "spring.cloud.config.enabled=false"})
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

추적 의존성을 추가하고, 리액티브 코드에서 추적 정보가 이어지도록 애플리케이션 클래스에서 `Hooks.enableAutomaticContextPropagation()`을 호출합니다.

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -42,6 +42,10 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
     implementation 'org.springframework.retry:spring-retry'
+    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
+    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
+    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
+    implementation 'org.springframework.boot:spring-boot-zipkin'
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

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -16,6 +16,7 @@
 import org.springframework.data.mongodb.core.index.ReactiveIndexOperations;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentEntity;
 import org.springframework.data.mongodb.core.mapping.MongoPersistentProperty;
+import reactor.core.publisher.Hooks;
 import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
 
 @SpringBootApplication
@@ -25,6 +26,7 @@
   private static final Logger LOG = LoggerFactory.getLogger(RecommendationServiceApplication.class);
 
   public static void main(String[] args) {
+    Hooks.enableAutomaticContextPropagation();
     ConfigurableApplicationContext ctx = SpringApplication.run(RecommendationServiceApplication.class, args);
 
     String mongodDbHost = ctx.getEnvironment().getProperty("spring.mongodb.host");
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
import reactor.core.publisher.Hooks;
import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;

@SpringBootApplication
@ComponentScan("se.magnus")
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

#### `microservices/recommendation-service/src/main/resources/bootstrap.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/main/resources/bootstrap.yml" op="write" nl="1" -->
```yaml
spring.application.name: recommendation

logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
logging.include-application-name: false

spring.cloud.config:
  failFast: true
  retry:
    initialInterval: 3000
    multiplier: 1.3
    maxInterval: 10000
    maxAttempts: 20
  uri: http://localhost:8888
  username: ${CONFIG_SERVER_USR}
  password: ${CONFIG_SERVER_PWD}    

---
spring.config.activate.on-profile: docker

spring.cloud.config.uri: http://config-server:8888
```

**중간 확인**

```bash
./gradlew :microservices:recommendation-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-4"></a>

## 단계 4. `review-service`

추적 의존성을 추가하고, 리액티브 코드에서 추적 정보가 이어지도록 애플리케이션 클래스에서 `Hooks.enableAutomaticContextPropagation()`을 호출합니다.

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -42,6 +42,11 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
     implementation 'org.springframework.retry:spring-retry'
+    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
+    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
+    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
+    implementation 'org.springframework.boot:spring-boot-zipkin'
+    implementation 'net.ttddyy.observation:datasource-micrometer-spring-boot:2.2.1'
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

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -8,6 +8,7 @@
 import org.springframework.context.ConfigurableApplicationContext;
 import org.springframework.context.annotation.Bean;
 import org.springframework.context.annotation.ComponentScan;
+import reactor.core.publisher.Hooks;
 import reactor.core.scheduler.Scheduler;
 import reactor.core.scheduler.Schedulers;
 
@@ -35,6 +36,7 @@
   }
 
   public static void main(String[] args) {
+    Hooks.enableAutomaticContextPropagation();
     ConfigurableApplicationContext ctx = SpringApplication.run(ReviewServiceApplication.class, args);
 
     String mysqlUri = ctx.getEnvironment().getProperty("spring.datasource.url");
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
import reactor.core.publisher.Hooks;
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
    Hooks.enableAutomaticContextPropagation();
    ConfigurableApplicationContext ctx = SpringApplication.run(ReviewServiceApplication.class, args);

    String mysqlUri = ctx.getEnvironment().getProperty("spring.datasource.url");
    LOG.info("Connected to MySQL: " + mysqlUri);
  }
}
```

</details>

#### `microservices/review-service/src/main/resources/bootstrap.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/review-service/src/main/resources/bootstrap.yml" op="write" nl="1" -->
```yaml
spring.application.name: review

logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
logging.include-application-name: false

spring.cloud.config:
  failFast: true
  retry:
    initialInterval: 3000
    multiplier: 1.3
    maxInterval: 10000
    maxAttempts: 20
  uri: http://localhost:8888
  username: ${CONFIG_SERVER_USR}
  password: ${CONFIG_SERVER_PWD}    

---
spring.config.activate.on-profile: docker

spring.cloud.config.uri: http://config-server:8888
```

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `product-composite-service`

추적 의존성과 함께 `ObservationUtil`(사용자 정의 스팬), `BuildInfoObservationFilter`(빌드 정보 태그), `ObservationRegistryConfig`를 추가합니다.

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -25,6 +25,10 @@
     enabled = false
 }
 
+springBoot {
+    buildInfo()
+}
+
 dependencies {
     implementation project(':api')
     implementation project(':util')
@@ -43,6 +47,11 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
     implementation 'org.springframework.retry:spring-retry'
+    implementation 'org.springframework.cloud:spring-cloud-starter-loadbalancer'
+    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
+    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
+    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
+    implementation 'org.springframework.boot:spring-boot-zipkin'
     implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:3.0.3'
     implementation "io.github.resilience4j:resilience4j-spring-boot4:${resilience4jVersion}"
     implementation "io.github.resilience4j:resilience4j-reactor:${resilience4jVersion}"
@@ -68,4 +77,5 @@
 
 tasks.named('test') {
     useJUnitPlatform()
+    testLogging.showStandardStreams = true
 }
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
    implementation 'org.springframework.boot:spring-boot-starter-restclient'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-resource-server'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-rabbit'
    implementation 'org.springframework.cloud:spring-cloud-starter-stream-kafka'
    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
    implementation 'org.springframework.cloud:spring-cloud-starter-config'
    implementation 'org.springframework.cloud:spring-cloud-config-client'
    // The starter-bootstrap, starter-aspectj, and retry dependencies are required by the config-client
    implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
    implementation 'org.springframework.boot:spring-boot-starter-aspectj'
    implementation 'org.springframework.retry:spring-retry'
    implementation 'org.springframework.cloud:spring-cloud-starter-loadbalancer'
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
    testLogging.showStandardStreams = true
}
```

</details>

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -7,13 +7,15 @@
 import io.swagger.v3.oas.models.info.License;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
+import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.beans.factory.annotation.Value;
 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
-import org.springframework.cloud.client.loadbalancer.LoadBalanced;
+import org.springframework.cloud.client.loadbalancer.reactive.ReactorLoadBalancerExchangeFilterFunction;
 import org.springframework.context.annotation.Bean;
 import org.springframework.context.annotation.ComponentScan;
 import org.springframework.web.reactive.function.client.WebClient;
+import reactor.core.publisher.Hooks;
 import reactor.core.scheduler.Scheduler;
 import reactor.core.scheduler.Schedulers;
 
@@ -76,13 +78,16 @@
     return Schedulers.newBoundedElastic(threadPoolSize, taskQueueSize, "publish-pool");
   }
 
+  @Autowired
+  private ReactorLoadBalancerExchangeFilterFunction lbFunction;
+
   @Bean
-  @LoadBalanced
-  public WebClient.Builder loadBalancedWebClientBuilder() {
-    return WebClient.builder();
+  public WebClient webClient(WebClient.Builder builder) {
+    return builder.filter(lbFunction).build();
   }
 
   public static void main(String[] args) {
+    Hooks.enableAutomaticContextPropagation();
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
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.loadbalancer.reactive.ReactorLoadBalancerExchangeFilterFunction;
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

  @Autowired
  private ReactorLoadBalancerExchangeFilterFunction lbFunction;

  @Bean
  public WebClient webClient(WebClient.Builder builder) {
    return builder.filter(lbFunction).build();
  }

  public static void main(String[] args) {
    Hooks.enableAutomaticContextPropagation();
    SpringApplication.run(ProductCompositeServiceApplication.class, args);
  }

}
```

</details>

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -56,12 +56,12 @@
 
   public ProductCompositeIntegration(
     @Qualifier("publishEventScheduler") Scheduler publishEventScheduler,
-    WebClient.Builder webClientBuilder,
+    WebClient webClient,
     ObjectMapper mapper,
     StreamBridge streamBridge,
     ServiceUtil serviceUtil
   ) {
-    this.webClient = webClientBuilder.build();
+    this.webClient = webClient;
 
     this.publishEventScheduler = publishEventScheduler;
     this.mapper = mapper;
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
  public Mono<Product> getProduct(int productId, int delay, int faultPercent) {

    URI url = UriComponentsBuilder.fromUriString(PRODUCT_SERVICE_URL
      + "/product/{productId}?delay={delay}&faultPercent={faultPercent}").build(productId, delay, faultPercent);
    LOG.debug("Will call the getProduct API on URL: {}", url);

    return webClient.get().uri(url)
      .retrieve().bodyToMono(Product.class).log(LOG.getName(), FINE)
      .onErrorMap(WebClientResponseException.class, ex -> handleException(ex));
  }

  private Mono<Product> getProductFallbackValue(int productId, int delay, int faultPercent, CallNotPermittedException ex) {

    LOG.warn("Creating a fail-fast fallback product for productId = {}, delay = {}, faultPercent = {} and exception = {} ",
      productId, delay, faultPercent, ex.toString());

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
  public Flux<Recommendation> getRecommendations(int productId) {

    URI url = UriComponentsBuilder.fromUriString(RECOMMENDATION_SERVICE_URL + "/recommendation?productId={productId}").build(productId);

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

    URI url = UriComponentsBuilder.fromUriString(REVIEW_SERVICE_URL + "/review?productId={productId}").build(productId);

    LOG.debug("Will call the getReviews API on URL: {}", url);

    // Return an empty result if something goes wrong to make it possible for the composite service to return partial responses
    return webClient.get().uri(url).retrieve().bodyToFlux(Review.class).log(LOG.getName(), FINE).onErrorResume(error -> empty());
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
@@ -5,6 +5,7 @@
 import java.net.URL;
 import java.util.ArrayList;
 import java.util.List;
+import java.util.function.Supplier;
 import java.util.stream.Collectors;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
@@ -19,6 +20,7 @@
 import se.magnus.api.core.product.Product;
 import se.magnus.api.core.recommendation.Recommendation;
 import se.magnus.api.core.review.Review;
+import se.magnus.microservices.composite.product.services.tracing.ObservationUtil;
 import se.magnus.util.http.ServiceUtil;
 
 @RestController
@@ -29,16 +31,21 @@
   private final SecurityContext nullSecCtx = new SecurityContextImpl();
 
   private final ServiceUtil serviceUtil;
+  private final ObservationUtil observationUtil;
   private final ProductCompositeIntegration integration;
 
-  public ProductCompositeServiceImpl(ServiceUtil serviceUtil, ProductCompositeIntegration integration) {
+  public ProductCompositeServiceImpl(ServiceUtil serviceUtil, ObservationUtil observationUtil, ProductCompositeIntegration integration) {
     this.serviceUtil = serviceUtil;
+    this.observationUtil = observationUtil;
     this.integration = integration;
   }
 
   @Override
   public Mono<Void> createProduct(ProductAggregate body) {
-
+    return observationWithProductInfo(body.getProductId(), () -> createProductInternal(body));
+  }
+
+  private Mono<Void> createProductInternal(ProductAggregate body) {
     try {
 
       List<Mono> monoList = new ArrayList<>();
@@ -77,32 +84,39 @@
   }
 
   @Override
+  public Mono<ProductAggregate> getProduct(int productId, int delay, int faultPercent) {
+    return observationWithProductInfo(productId, () -> getProductInternal(productId, delay, faultPercent));
+  }
+
   @SuppressWarnings("unchecked")
-  public Mono<ProductAggregate> getProduct(int productId, int delay, int faultPercent) {
-
+  private Mono<ProductAggregate> getProductInternal(int productId, int delay, int faultPercent) {
     LOG.info("Will get composite product info for product.id={}", productId);
     return Mono.zip(
-      values -> createProductAggregate(
-        (SecurityContext) values[0], (Product) values[1], (List<Recommendation>) values[2], (List<Review>) values[3], serviceUtil.getServiceAddress()),
-      getSecurityContextMono(),
-      integration.getProduct(productId, delay, faultPercent),
-      integration.getRecommendations(productId).collectList(),
-      integration.getReviews(productId).collectList())
+        values -> createProductAggregate(
+          (SecurityContext) values[0], (Product) values[1], (List<Recommendation>) values[2], (List<Review>) values[3], serviceUtil.getServiceAddress()),
+        getSecurityContextMono(),
+        integration.getProduct(productId, delay, faultPercent),
+        integration.getRecommendations(productId).collectList(),
+        integration.getReviews(productId).collectList())
       .doOnError(ex -> LOG.warn("getCompositeProduct failed: {}", ex.toString()))
       .log(LOG.getName(), FINE);
   }
 
   @Override
   public Mono<Void> deleteProduct(int productId) {
+    return observationWithProductInfo(productId, () -> deleteProductInternal(productId));
+  }
+
+  private Mono<Void> deleteProductInternal(int productId) {
     try {
 
       LOG.info("Will delete a product aggregate for product.id: {}", productId);
 
       return Mono.zip(r -> "",
-        getLogAuthorizationInfoMono(),
-        integration.deleteProduct(productId),
-        integration.deleteRecommendations(productId),
-        integration.deleteReviews(productId))
+          getLogAuthorizationInfoMono(),
+          integration.deleteProduct(productId),
+          integration.deleteRecommendations(productId),
+          integration.deleteReviews(productId))
         .doOnError(ex -> LOG.warn("delete failed: {}", ex.toString()))
         .log(LOG.getName(), FINE).then();
 
@@ -110,6 +124,15 @@
       LOG.warn("deleteCompositeProduct failed: {}", re.toString());
       throw re;
     }
+  }
+
+  private <T> T observationWithProductInfo(int productInfo, Supplier<T> supplier) {
+    return observationUtil.observe(
+      "composite observation",
+      "product info",
+      "productId",
+      String.valueOf(productInfo),
+      supplier);
   }
 
   private ProductAggregate createProductAggregate(
@@ -124,7 +147,7 @@
 
     // 2. Copy summary recommendation info, if available
     List<RecommendationSummary> recommendationSummaries = (recommendations == null) ? null :
-       recommendations.stream()
+      recommendations.stream()
         .map(r -> new RecommendationSummary(r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent()))
         .collect(Collectors.toList());
 
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
  public Mono<ProductAggregate> getProduct(int productId, int delay, int faultPercent) {
    return observationWithProductInfo(productId, () -> getProductInternal(productId, delay, faultPercent));
  }

  @SuppressWarnings("unchecked")
  private Mono<ProductAggregate> getProductInternal(int productId, int delay, int faultPercent) {
    LOG.info("Will get composite product info for product.id={}", productId);
    return Mono.zip(
        values -> createProductAggregate(
          (SecurityContext) values[0], (Product) values[1], (List<Recommendation>) values[2], (List<Review>) values[3], serviceUtil.getServiceAddress()),
        getSecurityContextMono(),
        integration.getProduct(productId, delay, faultPercent),
        integration.getRecommendations(productId).collectList(),
        integration.getReviews(productId).collectList())
      .doOnError(ex -> LOG.warn("getCompositeProduct failed: {}", ex.toString()))
      .log(LOG.getName(), FINE);
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

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/tracing/BuildInfoObservationFilter.java` — 새 파일 (21줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/tracing/BuildInfoObservationFilter.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services.tracing;

import io.micrometer.common.KeyValue;
import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationFilter;
import org.springframework.boot.info.BuildProperties;

public class BuildInfoObservationFilter implements ObservationFilter {

  private final BuildProperties buildProperties;

  public BuildInfoObservationFilter(BuildProperties buildProperties) {
    this.buildProperties = buildProperties;
  }

  @Override
  public Observation.Context map(final Observation.Context context) {
    KeyValue buildVersion = KeyValue.of("build.version", buildProperties.getVersion());
    return context.addLowCardinalityKeyValue(buildVersion);
  }
}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/tracing/ObservationRegistryConfig.java` — 새 파일 (21줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/tracing/ObservationRegistryConfig.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services.tracing;

import io.micrometer.observation.ObservationRegistry;
import org.springframework.boot.info.BuildProperties;
import org.springframework.boot.micrometer.observation.autoconfigure.ObservationRegistryCustomizer;
import org.springframework.context.annotation.Configuration;

@Configuration(proxyBeanMethods = false)
public class ObservationRegistryConfig implements ObservationRegistryCustomizer<ObservationRegistry> {

  private final BuildProperties buildProperties;

  public ObservationRegistryConfig(BuildProperties buildProperties) {
    this.buildProperties = buildProperties;
  }

  @Override
  public void customize(final ObservationRegistry registry) {
    registry.observationConfig().observationFilter(new BuildInfoObservationFilter(buildProperties));
  }
}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/tracing/ObservationUtil.java` — 새 파일 (24줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/tracing/ObservationUtil.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services.tracing;

import io.micrometer.observation.Observation;
import io.micrometer.observation.ObservationRegistry;
import java.util.function.Supplier;
import org.springframework.stereotype.Component;

@Component
public class ObservationUtil {

  private final ObservationRegistry registry;

  public ObservationUtil(ObservationRegistry registry) {
    this.registry = registry;
  }

  public <T> T observe(String observationName, String contextualName, String highCardinalityKey, String highCardinalityValue, Supplier<T> supplier) {
    return Observation.createNotStarted(observationName, registry)
      .contextualName(contextualName)
      .highCardinalityKeyValue(highCardinalityKey, highCardinalityValue)
      .observe(supplier);
  }

}
```

#### `microservices/product-composite-service/src/main/resources/bootstrap.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-composite-service/src/main/resources/bootstrap.yml" op="write" nl="1" -->
```yaml
spring.application.name: product-composite

logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
logging.include-application-name: false

spring.cloud.config:
  failFast: true
  retry:
    initialInterval: 3000
    multiplier: 1.3
    maxInterval: 10000
    maxAttempts: 20
  uri: http://localhost:8888
  username: ${CONFIG_SERVER_USR}
  password: ${CONFIG_SERVER_PWD}    

---
spring.config.activate.on-profile: docker

spring.cloud.config.uri: http://config-server:8888
```

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-6"></a>

## 단계 6. `eureka-server` — 서비스 검색 서버

추적 의존성을 추가합니다.

#### `spring-cloud/eureka-server/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -34,6 +34,10 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
     implementation 'org.springframework.retry:spring-retry'
+    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
+    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
+    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
+    implementation 'org.springframework.boot:spring-boot-zipkin'
     implementation 'org.glassfish.jaxb:jaxb-runtime'
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-resttestclient'
```

<details><summary>완성된 파일 전체 보기</summary>

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

</details>

#### `spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/SecurityConfig.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -9,7 +9,6 @@
 import org.springframework.security.core.userdetails.UserDetails;
 import org.springframework.security.provisioning.InMemoryUserDetailsManager;
 import org.springframework.security.web.SecurityFilterChain;
-
 
 @Configuration
 public class SecurityConfig {
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/SecurityConfig.java" op="write" nl="0" -->
```java
package se.magnus.springcloud.eurekaserver;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

  private final String username;
  private final String password;

  public SecurityConfig(
    @Value("${app.eureka-username}") String username,
    @Value("${app.eureka-password}") String password
  ) {
    this.username = username;
    this.password = password;
  }

  @Bean
  public InMemoryUserDetailsManager userDetailsService() {
    @SuppressWarnings("deprecation") // Ok for test purposes, not for production use
    UserDetails user = User.withDefaultPasswordEncoder()
      .username(username)
      .password(password)
      .roles("USER")
      .build();
    return new InMemoryUserDetailsManager(user);
  }

  @Bean
  public SecurityFilterChain configure(HttpSecurity http) throws Exception {
    // Disable CSRF to allow services to register themselves with Eureka
    http
      .csrf(csrf -> csrf.disable())
      .authorizeHttpRequests(requests -> requests.anyRequest().authenticated())
      .httpBasic(Customizer.withDefaults());
    return http.build();
  }
}
```

</details>

#### `spring-cloud/eureka-server/src/main/resources/bootstrap.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="spring-cloud/eureka-server/src/main/resources/bootstrap.yml" op="write" nl="1" -->
```yaml
spring.application.name: eureka-server

logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
logging.include-application-name: false

spring.cloud.config:
  failFast: true
  retry:
    initialInterval: 3000
    multiplier: 1.3
    maxInterval: 10000
    maxAttempts: 20
  uri: http://localhost:8888
  username: ${CONFIG_SERVER_USR}
  password: ${CONFIG_SERVER_PWD}    

---
spring.config.activate.on-profile: docker

spring.cloud.config.uri: http://config-server:8888
```

**중간 확인**

```bash
./gradlew :spring-cloud:eureka-server:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-7"></a>

## 단계 7. `gateway` — 에지 서버

추적 의존성을 추가하고 컨텍스트 전파를 켭니다.

#### `spring-cloud/gateway/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -39,6 +39,10 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
     implementation 'org.springframework.retry:spring-retry'
+    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
+    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
+    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
+    implementation 'org.springframework.boot:spring-boot-zipkin'
 
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
    implementation 'org.springframework.boot:spring-boot-starter-restclient'
    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
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

#### `spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/GatewayApplication.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="spring-cloud/gateway/src/main/java/se/magnus/springcloud/gateway/GatewayApplication.java" op="write" nl="1" -->
```java
package se.magnus.springcloud.gateway;

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

  public static void main(String[] args) {
    Hooks.enableAutomaticContextPropagation();
    SpringApplication.run(GatewayApplication.class, args);
  }

}
```

#### `spring-cloud/gateway/src/main/resources/bootstrap.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="spring-cloud/gateway/src/main/resources/bootstrap.yml" op="write" nl="1" -->
```yaml
spring.application.name: gateway

logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
logging.include-application-name: false

spring.cloud.config:
  failFast: true
  retry:
    initialInterval: 3000
    multiplier: 1.3
    maxInterval: 10000
    maxAttempts: 20
  uri: http://localhost:8888
  username: ${CONFIG_SERVER_USR}
  password: ${CONFIG_SERVER_PWD}    

---
spring.config.activate.on-profile: docker

spring.cloud.config.uri: http://config-server:8888
```

**중간 확인**

```bash
./gradlew :spring-cloud:gateway:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-8"></a>

## 단계 8. `authorization-server` — OAuth 2.0 인가 서버

추적 의존성을 추가합니다.

#### `spring-cloud/authorization-server/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -33,6 +33,10 @@
     implementation 'org.springframework.cloud:spring-cloud-starter-bootstrap'
     implementation 'org.springframework.boot:spring-boot-starter-aspectj'
     implementation 'org.springframework.retry:spring-retry'
+    implementation 'io.micrometer:micrometer-tracing-bridge-otel'
+    implementation 'io.opentelemetry:opentelemetry-exporter-zipkin'
+    implementation 'org.springframework.boot:spring-boot-micrometer-tracing-opentelemetry'
+    implementation 'org.springframework.boot:spring-boot-zipkin'
 
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

ext {
    springCloudVersion = '2025.1.4'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-security-oauth2-authorization-server'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
    implementation 'org.springframework.boot:spring-boot-starter-restclient'
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

#### `spring-cloud/authorization-server/src/main/java/sample/OAuth2AuthorizationServerApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff

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

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * @author Joe Grandja
 * @since 0.0.1
 */
@SpringBootApplication
public class OAuth2AuthorizationServerApplication {

  public static void main(String[] args) {
    SpringApplication.run(OAuth2AuthorizationServerApplication.class, args);
  }

}
//CHECKSTYLE:ON
```

</details>

#### `spring-cloud/authorization-server/src/main/resources/bootstrap.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="spring-cloud/authorization-server/src/main/resources/bootstrap.yml" op="write" nl="1" -->
```yaml
spring.application.name: auth-server

logging.pattern.correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
logging.include-application-name: false

spring.cloud.config:
  failFast: true
  retry:
    initialInterval: 3000
    multiplier: 1.3
    maxInterval: 10000
    maxAttempts: 20
  uri: http://localhost:8888
  username: ${CONFIG_SERVER_USR}
  password: ${CONFIG_SERVER_PWD}    

---
spring.config.activate.on-profile: docker

spring.cloud.config.uri: http://config-server:8888
```

**중간 확인**

```bash
./gradlew :spring-cloud:authorization-server:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-9"></a>

## 단계 9. `config-repo` — 중앙 구성 파일

`management.tracing.export.zipkin.endpoint`와 샘플링 비율, 로그 패턴(`logging.pattern.correlation`)을 설정합니다.

#### `config-repo/application.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -30,6 +30,9 @@
 management.endpoint.health.show-details: "ALWAYS"
 management.endpoints.web.exposure.include: "*"
 
+management.tracing.export.zipkin.endpoint: http://zipkin-server:9411/api/v2/spans
+management.tracing.sampling.probability: 1.0
+
 ---
 spring.config.activate.on-profile: docker
 
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/application.yml" op="write" nl="0" -->
```yaml
app:
  eureka-username: u
  eureka-password: '{cipher}bf298f6d5f878b342f9e44bec08cb9ac00b4ce57e98316f030194a225fac89fb'
  eureka-server: localhost
  auth-server: localhost

eureka:
  client:
    serviceUrl:
      defaultZone: "http://${app.eureka-username}:${app.eureka-password}@${app.eureka-server}:8761/eureka/"
    initialInstanceInfoReplicationIntervalSeconds: 5
    registryFetchIntervalSeconds: 5
  instance:
    leaseRenewalIntervalInSeconds: 5
    leaseExpirationDurationInSeconds: 5

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

management.tracing.export.zipkin.endpoint: http://zipkin-server:9411/api/v2/spans
management.tracing.sampling.probability: 1.0

---
spring.config.activate.on-profile: docker

spring.rabbitmq.host: rabbitmq

spring.cloud.stream.kafka.binder.brokers: kafka

app:
  eureka-server: eureka
  auth-server: auth-server

---
spring.config.activate.on-profile: kafka

management.health.rabbit.enabled: false
spring.cloud.stream.defaultBinder: kafka
spring.kafka.bootstrap-servers: kafka:9092
spring.cloud.stream.kafka.binder.replication-factor: 1
```

</details>

#### `config-repo/product-composite.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -137,8 +137,12 @@
 logging:
   level:
     root: INFO
-    se.magnus: DEBUG
-    org.springframework.web.server.adapter.HttpWebHandlerAdapter: TRACE
+    se.magnus: INFO
+    org.springframework.web.server.adapter.HttpWebHandlerAdapter: INFO
+
+# To see tracing headers, uncomment the following two lines and restart the product-composite service
+# spring.codec.log-request-details: true
+# logging.level.org.springframework.web.reactive.function.client.ExchangeFunctions: TRACE
 
 ---
 spring.config.activate.on-profile: docker
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

spring.security.oauth2.resourceserver.jwt.issuer-uri: http://${app.auth-server}:9999

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

server.port: 8080

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
```

</details>

#### `config-repo/product.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -30,7 +30,7 @@
 logging:
   level:
     root: INFO
-    se.magnus: DEBUG
+    se.magnus: INFO
     org.springframework.data.mongodb.core.ReactiveMongoTemplate: DEBUG
 
 ---
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/product.yml" op="write" nl="1" -->
```yaml
server.port: 7002
spring.web.error.include-message: always

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

server.port: 8080

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
```

</details>

#### `config-repo/recommendation.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -30,7 +30,7 @@
 logging:
   level:
     root: INFO
-    se.magnus: DEBUG
+    se.magnus: INFO
     org.springframework.data.mongodb.core.ReactiveMongoTemplate: DEBUG
 
 ---
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/recommendation.yml" op="write" nl="1" -->
```yaml
server.port: 7003
spring.web.error.include-message: always

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

server.port: 8080

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
```

</details>

#### `config-repo/review.yml` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -35,7 +35,7 @@
 logging:
   level:
     root: INFO
-    se.magnus: DEBUG
+    se.magnus: INFO
     org.hibernate.SQL: DEBUG
     org.hibernate.type.descriptor.sql.BasicBinder: TRACE
 
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="config-repo/review.yml" op="write" nl="1" -->
```yaml
server.port: 7004
spring.web.error.include-message: always

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

server.port: 8080

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
```

</details>

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter14
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
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter14
```

---

← [13장 워크북](Chapter13.md) · [워크북 목차](README.md) · [15장 워크북](Chapter15.md) →
