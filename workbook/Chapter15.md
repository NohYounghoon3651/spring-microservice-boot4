# 15장 워크북 — 쿠버네티스 소개

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 15장 · 영문 3판 p.373–394 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter15/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter15`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter15) · 위키: [15장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/15장-쿠버네티스-소개)

## 이 장에서 만드는 것

쿠버네티스를 처음 써 보는 장입니다. 마이크로서비스 코드는 거의 그대로이고, nginx 예제로 디플로이먼트와 서비스를 만들어 봅니다.

## 시작하기

14장을 끝낸 작업 폴더를 복사해서 시작합니다. 14장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter14 Chapter15          # 내가 만든 14장 결과에서 시작
# 또는: cp -r <저장소>/Chapter14 Chapter15        # 저장소의 14장 완성 코드에서 시작
cd Chapter15 && ./gradlew clean -q
```

## 단계 목록

1. [`product-composite-service`](#단계-1) — 수정 3
2. [`eureka-server` — 서비스 검색 서버](#단계-2) — 수정 1
3. [`authorization-server` — OAuth 2.0 인가 서버](#단계-3) — 수정 1
4. [`kubernetes/first-attempts` — 첫 쿠버네티스 매니페스트](#단계-4) — 새 파일 2

<a id="단계-1"></a>

## 단계 1. `product-composite-service`

테스트 로그 설정과 메서드 접근 제한자를 정리합니다(동작 변화 없음).

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -77,5 +77,4 @@
 
 tasks.named('test') {
     useJUnitPlatform()
-    testLogging.showStandardStreams = true
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
}
```

</details>

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -82,7 +82,7 @@
   private ReactorLoadBalancerExchangeFilterFunction lbFunction;
 
   @Bean
-  public WebClient webClient(WebClient.Builder builder) {
+  WebClient webClient(WebClient.Builder builder) {
     return builder.filter(lbFunction).build();
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
  WebClient webClient(WebClient.Builder builder) {
    return builder.filter(lbFunction).build();
  }

  public static void main(String[] args) {
    Hooks.enableAutomaticContextPropagation();
    SpringApplication.run(ProductCompositeServiceApplication.class, args);
  }

}
```

</details>

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/TestSecurityConfig.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/TestSecurityConfig.java" op="write" nl="0" -->
```java
package se.magnus.microservices.composite.product;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.web.server.SecurityWebFilterChain;

@TestConfiguration
public class TestSecurityConfig {

  @Bean
  public SecurityWebFilterChain springSecurityFilterChain(ServerHttpSecurity http) {
    http.csrf(csrf -> csrf.disable().authorizeExchange(exchange -> exchange.anyExchange().permitAll()));
    return http.build();
  }
}
```

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-2"></a>

## 단계 2. `eureka-server` — 서비스 검색 서버

주석만 바뀝니다.

#### `spring-cloud/eureka-server/src/main/java/se/magnus/springcloud/eurekaserver/SecurityConfig.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -9,6 +9,7 @@
 import org.springframework.security.core.userdetails.UserDetails;
 import org.springframework.security.provisioning.InMemoryUserDetailsManager;
 import org.springframework.security.web.SecurityFilterChain;
+
 
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

**중간 확인**

```bash
./gradlew :spring-cloud:eureka-server:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-3"></a>

## 단계 3. `authorization-server` — OAuth 2.0 인가 서버

테스트 한 줄을 정리합니다.

#### `spring-cloud/authorization-server/src/test/java/sample/OAuth2AuthorizationServerApplicationTests.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -21,6 +21,7 @@
 import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
 import static org.hamcrest.core.Is.is;
 
+import org.junit.jupiter.api.Disabled;
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
@SpringBootTest(properties = {"eureka.client.enabled=false", "spring.cloud.config.enabled=false"})
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

<a id="단계-4"></a>

## 단계 4. `kubernetes/first-attempts` — 첫 쿠버네티스 매니페스트

nginx 디플로이먼트(파드 3개)와 NodePort 서비스입니다. `kubectl apply -f`로 적용해 봅니다.

#### `kubernetes/first-attempts/nginx-deployment.yaml` — 새 파일 (19줄)

<!-- wb:file path="kubernetes/first-attempts/nginx-deployment.yaml" op="write" nl="1" -->
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deploy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-app
  template:
    metadata:
      labels:
        app: nginx-app
    spec:
      containers:
      - name: nginx-container
        image: nginx:latest
        ports:
        - containerPort: 80
```

#### `kubernetes/first-attempts/nginx-service.yaml` — 새 파일 (12줄)

<!-- wb:file path="kubernetes/first-attempts/nginx-service.yaml" op="write" nl="1" -->
```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  type: NodePort
  selector:
    app: nginx-app
  ports:
    - targetPort: 80
      port: 80
      nodePort: 30080
```

## 확인하기

nginx 예제는 minikube에서 확인합니다.

```bash
minikube start --driver=docker
kubectl create namespace first-attempts
kubectl config set-context $(kubectl config current-context) --namespace=first-attempts
kubectl apply -f kubernetes/first-attempts/nginx-deployment.yaml
kubectl apply -f kubernetes/first-attempts/nginx-service.yaml
kubectl get all
```

```bash
cd ~/my-work/Chapter15
./gradlew build
docker compose build
./test-em-all.bash start stop      # 14장과 같은 시스템을 도커 컴포즈로 확인
```

쿠버네티스 첫 실습 매니페스트는 `kubernetes/first-attempts`에 있습니다(minikube 필요).

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter15
```

---

← [14장 워크북](Chapter14.md) · [워크북 목차](README.md) · [16장 워크북](Chapter16.md) →
