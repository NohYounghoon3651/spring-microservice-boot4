# 3장 워크북 — 협업 마이크로서비스 생성

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 3장 · 영문 3판 p.47–78 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter03/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter03/2-basic-rest-services`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter03/2-basic-rest-services) · 위키: [3장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/03장-협업-마이크로서비스-생성)

## 이 장에서 만드는 것

서로 협력하는 마이크로서비스 4개(`product`, `recommendation`, `review`, `product-composite`)를 처음부터 만듭니다.

- 서비스 간 API를 담는 `api` 프로젝트와 공통 코드를 담는 `util` 프로젝트
- 각 핵심 서비스의 REST API 구현(아직 데이터베이스 없이 고정 데이터를 돌려줌)
- 핵심 서비스 3개를 호출해 결과를 합치는 복합 서비스
- 예외 처리와 테스트, 전체 시스템을 확인하는 `test-em-all.bash`

이 장의 코드가 이후 모든 장의 바탕이 됩니다.

## 단계 목록

1. [Spring Initializr로 골격 만들기](#단계-1) — 새 파일 2
2. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-2) — 새 파일 1 · 수정 1
3. [`api` 프로젝트 — 서비스 간 API와 DTO](#단계-3) — 새 파일 16
4. [`util` 프로젝트 — 공통 유틸리티](#단계-4) — 새 파일 6
5. [`product-service`](#단계-5) — 새 파일 2 · 수정 3 · 삭제 1
6. [`recommendation-service`](#단계-6) — 새 파일 2 · 수정 3 · 삭제 1
7. [`review-service`](#단계-7) — 새 파일 2 · 수정 3 · 삭제 1
8. [`product-composite-service`](#단계-8) — 새 파일 3 · 수정 3 · 삭제 1

<a id="단계-1"></a>

## 단계 1. Spring Initializr로 골격 만들기

교재처럼 Spring Initializr(`spring init`)로 서비스 4개의 골격을 만듭니다. 먼저 작업 폴더를 만들고
스크립트와 루트 `settings.gradle`을 직접 칩니다.

```bash
mkdir -p ~/my-work/Chapter03 && cd ~/my-work/Chapter03
```

#### `create-projects.bash` — 새 파일

<!-- wb:file path="create-projects.bash" op="write" nl="0" -->
```bash
#!/usr/bin/env bash

mkdir microservices
cd microservices

spring init \
--boot-version=4.0.9 \
--type=gradle-project \
--java-version=21 \
--packaging=jar \
--name=product-service \
--package-name=se.magnus.microservices.core.product \
--groupId=se.magnus.microservices.core.product \
--dependencies=actuator,webflux \
--version=1.0.0-SNAPSHOT \
product-service

spring init \
--boot-version=4.0.9 \
--type=gradle-project \
--java-version=21 \
--packaging=jar \
--name=review-service \
--package-name=se.magnus.microservices.core.review \
--groupId=se.magnus.microservices.core.review \
--dependencies=actuator,webflux \
--version=1.0.0-SNAPSHOT \
review-service

spring init \
--boot-version=4.0.9 \
--type=gradle-project \
--java-version=21 \
--packaging=jar \
--name=recommendation-service \
--package-name=se.magnus.microservices.core.recommendation \
--groupId=se.magnus.microservices.core.recommendation \
--dependencies=actuator,webflux \
--version=1.0.0-SNAPSHOT \
recommendation-service

spring init \
--boot-version=4.0.9 \
--type=gradle-project \
--java-version=21 \
--packaging=jar \
--name=product-composite-service \
--package-name=se.magnus.microservices.composite.product \
--groupId=se.magnus.microservices.composite.product \
--dependencies=actuator,webflux \
--version=1.0.0-SNAPSHOT \
product-composite-service

cd ..
```

#### `settings.gradle` — 새 파일

<!-- wb:file path="settings.gradle" op="write" nl="1" -->
```groovy
pluginManagement {
    repositories {
        gradlePluginPortal()
    }
}

include ':microservices:product-service' 
include ':microservices:review-service'
include ':microservices:recommendation-service'
include ':microservices:product-composite-service'

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

```bash
chmod +x create-projects.bash && ./create-projects.bash
cp -r <저장소>/Chapter03/2-basic-rest-services/gradle .   # Gradle 래퍼
cp <저장소>/Chapter03/2-basic-rest-services/gradlew* .
./gradlew build
```

`spring init`이 서비스 4개의 골격(`build.gradle`, `settings.gradle`, 애플리케이션 클래스, 테스트 클래스, `application.properties`)을 만듭니다. 생성 결과는 저장소의 [`Chapter03/1-spring-init`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter03/1-spring-init)과 같아야 합니다. `spring` 명령이 없다면 그 폴더를 복사해서 이어가도 됩니다.

<!-- wb:file path=".gitignore" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-composite-service/.gitignore" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-composite-service/build.gradle" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-composite-service/settings.gradle" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-composite-service/src/main/resources/application.properties" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-service/.gitignore" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-service/build.gradle" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-service/settings.gradle" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/ProductServiceApplication.java" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-service/src/main/resources/application.properties" op="copy" nl="0" -->
<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java" op="copy" nl="0" -->
<!-- wb:file path="microservices/recommendation-service/.gitignore" op="copy" nl="0" -->
<!-- wb:file path="microservices/recommendation-service/build.gradle" op="copy" nl="0" -->
<!-- wb:file path="microservices/recommendation-service/settings.gradle" op="copy" nl="0" -->
<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplication.java" op="copy" nl="0" -->
<!-- wb:file path="microservices/recommendation-service/src/main/resources/application.properties" op="copy" nl="0" -->
<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java" op="copy" nl="0" -->
<!-- wb:file path="microservices/review-service/.gitignore" op="copy" nl="0" -->
<!-- wb:file path="microservices/review-service/build.gradle" op="copy" nl="0" -->
<!-- wb:file path="microservices/review-service/settings.gradle" op="copy" nl="0" -->
<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java" op="copy" nl="0" -->
<!-- wb:file path="microservices/review-service/src/main/resources/application.properties" op="copy" nl="0" -->
<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java" op="copy" nl="0" -->

<a id="단계-2"></a>

## 단계 2. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

루트 `settings.gradle`에 `api`, `util`을 추가하고, 서비스 4개를 띄운 뒤 API를 호출해 보는 `test-em-all.bash`를 만듭니다.

#### `settings.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -4,7 +4,9 @@
     }
 }
 
-include ':microservices:product-service' 
+include ':api'
+include ':util'
+include ':microservices:product-service'
 include ':microservices:review-service'
 include ':microservices:recommendation-service'
 include ':microservices:product-composite-service'
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

#### `test-em-all.bash` — 새 파일 (88줄)

<!-- wb:file path="test-em-all.bash" op="write" nl="1" -->
```bash
#!/usr/bin/env bash
#
# Sample usage:
#
#   HOST=localhost PORT=7001 ./test-em-all.bash
#
: ${HOST=localhost}
: ${PORT=7001}
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

set -e

echo "HOST=${HOST}"
echo "PORT=${PORT}"


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

echo "End, all tests OK:" `date`
```

<a id="단계-3"></a>

## 단계 3. `api` 프로젝트 — 서비스 간 API와 DTO

서비스들이 공유하는 인터페이스와 DTO입니다. `@GetMapping` 같은 매핑은 인터페이스에 두고, 구현은 각 서비스가 합니다. 예외 클래스도 여기 둡니다.

#### `api/.gitignore` — 복사/생성

Git이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요(치지 않아도 실습에는 지장이 없습니다).

<!-- wb:file path="api/.gitignore" op="copy" nl="0" -->

#### `api/build.gradle` — 새 파일 (32줄)

<!-- wb:file path="api/build.gradle" op="write" nl="1" -->
```groovy
plugins {
    id 'io.spring.dependency-management' version '1.1.7'
    id 'java'
}

group = 'se.magnus.microservices.api'
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
    springBootVersion = '4.0.9'
}

dependencies {
    implementation platform("org.springframework.boot:spring-boot-dependencies:${springBootVersion}")

    implementation 'org.springframework.boot:spring-boot-starter-webflux'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

#### `api/settings.gradle` — 새 파일 (1줄)

<!-- wb:file path="api/settings.gradle" op="write" nl="1" -->
```groovy
rootProject.name = 'api'
```

#### `api/src/main/java/se/magnus/api/composite/product/ProductAggregate.java` — 새 파일 (54줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/ProductAggregate.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

import java.util.List;

public class ProductAggregate {
  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int productId;
  private String name;
  private int weight;
  private List<RecommendationSummary> recommendations;
  private List<ReviewSummary> reviews;
  private ServiceAddresses serviceAddresses;

  public ProductAggregate(
    int productId,
    String name,
    int weight,
    List<RecommendationSummary> recommendations,
    List<ReviewSummary> reviews,
    ServiceAddresses serviceAddresses) {

    this.productId = productId;
    this.name = name;
    this.weight = weight;
    this.recommendations = recommendations;
    this.reviews = reviews;
    this.serviceAddresses = serviceAddresses;
  }

  public int getProductId() {
    return productId;
  }

  public String getName() {
    return name;
  }

  public int getWeight() {
    return weight;
  }

  public List<RecommendationSummary> getRecommendations() {
    return recommendations;
  }

  public List<ReviewSummary> getReviews() {
    return reviews;
  }

  public ServiceAddresses getServiceAddresses() {
    return serviceAddresses;
  }
}
```

#### `api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java` — 새 파일 (18줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

public interface ProductCompositeService {

  /**
   * Sample usage: "curl $HOST:$PORT/product-composite/1".
   *
   * @param productId Id of the product
   * @return the composite product info, if found, else null
   */
  @GetMapping(
    value = "/product-composite/{productId}",
    produces = "application/json")
  ProductAggregate getProduct(@PathVariable int productId);
}
```

#### `api/src/main/java/se/magnus/api/composite/product/RecommendationSummary.java` — 새 파일 (28줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/RecommendationSummary.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

public class RecommendationSummary {

  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int recommendationId;
  private String author;
  private int rate;

  public RecommendationSummary(int recommendationId, String author, int rate) {
    this.recommendationId = recommendationId;
    this.author = author;
    this.rate = rate;
  }

  public int getRecommendationId() {
    return recommendationId;
  }

  public String getAuthor() {
    return author;
  }

  public int getRate() {
    return rate;
  }
}
```

#### `api/src/main/java/se/magnus/api/composite/product/ReviewSummary.java` — 새 파일 (28줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/ReviewSummary.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

public class ReviewSummary {

  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int reviewId;
  private String author;
  private String subject;

  public ReviewSummary(int reviewId, String author, String subject) {
    this.reviewId = reviewId;
    this.author = author;
    this.subject = subject;
  }

  public int getReviewId() {
    return reviewId;
  }

  public String getAuthor() {
    return author;
  }

  public String getSubject() {
    return subject;
  }
}
```

#### `api/src/main/java/se/magnus/api/composite/product/ServiceAddresses.java` — 새 파일 (45줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/ServiceAddresses.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

public class ServiceAddresses {
  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private String cmp;
  private String pro;
  private String rev;
  private String rec;

  public ServiceAddresses() {
    cmp = null;
    pro = null;
    rev = null;
    rec = null;
  }

  public ServiceAddresses(
    String compositeAddress,
    String productAddress,
    String reviewAddress,
    String recommendationAddress) {

    this.cmp = compositeAddress;
    this.pro = productAddress;
    this.rev = reviewAddress;
    this.rec = recommendationAddress;
  }

  public String getCmp() {
    return cmp;
  }

  public String getPro() {
    return pro;
  }

  public String getRev() {
    return rev;
  }

  public String getRec() {
    return rec;
  }
}
```

#### `api/src/main/java/se/magnus/api/core/product/Product.java` — 새 파일 (40줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/core/product/Product.java" op="write" nl="1" -->
```java
package se.magnus.api.core.product;

public class Product {
  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int productId;
  private String name;
  private int weight;
  private String serviceAddress;

  public Product() {
    productId = 0;
    name = null;
    weight = 0;
    serviceAddress = null;
  }

  public Product(int productId, String name, int weight, String serviceAddress) {
    this.productId = productId;
    this.name = name;
    this.weight = weight;
    this.serviceAddress = serviceAddress;
  }

  public int getProductId() {
    return productId;
  }

  public String getName() {
    return name;
  }

  public int getWeight() {
    return weight;
  }

  public String getServiceAddress() {
    return serviceAddress;
  }
}
```

#### `api/src/main/java/se/magnus/api/core/product/ProductService.java` — 새 파일 (18줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/core/product/ProductService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.product;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

public interface ProductService {

  /**
   * Sample usage: "curl $HOST:$PORT/product/1".
   *
   * @param productId Id of the product
   * @return the product, if found, else null
   */
  @GetMapping(
    value = "/product/{productId}",
    produces = "application/json")
  Product getProduct(@PathVariable int productId);
}
```

#### `api/src/main/java/se/magnus/api/core/recommendation/Recommendation.java` — 새 파일 (61줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/core/recommendation/Recommendation.java" op="write" nl="1" -->
```java
package se.magnus.api.core.recommendation;

public class Recommendation {
  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int productId;
  private int recommendationId;
  private String author;
  private int rate;
  private String content;
  private String serviceAddress;

  public Recommendation() {
    productId = 0;
    recommendationId = 0;
    author = null;
    rate = 0;
    content = null;
    serviceAddress = null;
  }

  public Recommendation(
    int productId,
    int recommendationId,
    String author,
    int rate,
    String content,
    String serviceAddress) {

    this.productId = productId;
    this.recommendationId = recommendationId;
    this.author = author;
    this.rate = rate;
    this.content = content;
    this.serviceAddress = serviceAddress;
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

  public int getRate() {
    return rate;
  }

  public String getContent() {
    return content;
  }

  public String getServiceAddress() {
    return serviceAddress;
  }
}
```

#### `api/src/main/java/se/magnus/api/core/recommendation/RecommendationService.java` — 새 파일 (20줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/core/recommendation/RecommendationService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.recommendation;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

public interface RecommendationService {

  /**
   * Sample usage: "curl $HOST:$PORT/recommendation?productId=1".
   *
   * @param productId Id of the product
   * @return the recommendations of the product
   */
  @GetMapping(
    value = "/recommendation",
    produces = "application/json")
  List<Recommendation> getRecommendations(
    @RequestParam(value = "productId", required = true) int productId);
}
```

#### `api/src/main/java/se/magnus/api/core/review/Review.java` — 새 파일 (61줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/core/review/Review.java" op="write" nl="1" -->
```java
package se.magnus.api.core.review;

public class Review {
  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int productId;
  private int reviewId;
  private String author;
  private String subject;
  private String content;
  private String serviceAddress;

  public Review() {
    productId = 0;
    reviewId = 0;
    author = null;
    subject = null;
    content = null;
    serviceAddress = null;
  }

  public Review(
    int productId,
    int reviewId,
    String author,
    String subject,
    String content,
    String serviceAddress) {

    this.productId = productId;
    this.reviewId = reviewId;
    this.author = author;
    this.subject = subject;
    this.content = content;
    this.serviceAddress = serviceAddress;
  }

  public int getProductId() {
    return productId;
  }

  public int getReviewId() {
    return reviewId;
  }

  public String getAuthor() {
    return author;
  }

  public String getSubject() {
    return subject;
  }

  public String getContent() {
    return content;
  }

  public String getServiceAddress() {
    return serviceAddress;
  }
}
```

#### `api/src/main/java/se/magnus/api/core/review/ReviewService.java` — 새 파일 (19줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/core/review/ReviewService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.review;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

public interface ReviewService {

  /**
   * Sample usage: "curl $HOST:$PORT/review?productId=1".
   *
   * @param productId Id of the product
   * @return the reviews of the product
   */
  @GetMapping(
    value = "/review",
    produces = "application/json")
  List<Review> getReviews(@RequestParam(value = "productId", required = true) int productId);
}
```

#### `api/src/main/java/se/magnus/api/exceptions/InvalidInputException.java` — 새 파일 (17줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/exceptions/InvalidInputException.java" op="write" nl="1" -->
```java
package se.magnus.api.exceptions;

public class InvalidInputException extends RuntimeException {
  public InvalidInputException() {}

  public InvalidInputException(String message) {
    super(message);
  }

  public InvalidInputException(String message, Throwable cause) {
    super(message, cause);
  }

  public InvalidInputException(Throwable cause) {
    super(cause);
  }
}
```

#### `api/src/main/java/se/magnus/api/exceptions/NotFoundException.java` — 새 파일 (17줄)

<!-- wb:file path="api/src/main/java/se/magnus/api/exceptions/NotFoundException.java" op="write" nl="1" -->
```java
package se.magnus.api.exceptions;

public class NotFoundException extends RuntimeException {
  public NotFoundException() {}

  public NotFoundException(String message) {
    super(message);
  }

  public NotFoundException(String message, Throwable cause) {
    super(message, cause);
  }

  public NotFoundException(Throwable cause) {
    super(cause);
  }
}
```

**중간 확인**

```bash
./gradlew :api:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-4"></a>

## 단계 4. `util` 프로젝트 — 공통 유틸리티

모든 서비스가 함께 쓰는 코드입니다. `ServiceUtil`은 응답에 서비스 주소를 넣고, `GlobalControllerExceptionHandler`는 예외를 HTTP 상태 코드로 바꿉니다.

#### `util/.gitignore` — 복사/생성

Git이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요(치지 않아도 실습에는 지장이 없습니다).

<!-- wb:file path="util/.gitignore" op="copy" nl="0" -->

#### `util/build.gradle` — 새 파일 (34줄)

<!-- wb:file path="util/build.gradle" op="write" nl="0" -->
```groovy
plugins {
    id 'io.spring.dependency-management' version '1.1.7'
    id 'java'
}

group = 'se.magnus.microservices.util'
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
    springBootVersion = '4.0.9'
}

dependencies {
    implementation platform("org.springframework.boot:spring-boot-dependencies:${springBootVersion}")

    implementation project(':api')
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.junit.platform:junit-platform-launcher'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

#### `util/settings.gradle` — 새 파일 (1줄)

<!-- wb:file path="util/settings.gradle" op="write" nl="1" -->
```groovy
rootProject.name = 'util'
```

#### `util/src/main/java/se/magnus/util/http/GlobalControllerExceptionHandler.java` — 새 파일 (47줄)

<!-- wb:file path="util/src/main/java/se/magnus/util/http/GlobalControllerExceptionHandler.java" op="write" nl="1" -->
```java
package se.magnus.util.http;

import static org.springframework.http.HttpStatus.NOT_FOUND;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_CONTENT;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.api.exceptions.NotFoundException;

@RestControllerAdvice
class GlobalControllerExceptionHandler {

  private static final Logger LOG = LoggerFactory.getLogger(GlobalControllerExceptionHandler.class);

  @ResponseStatus(NOT_FOUND)
  @ExceptionHandler(NotFoundException.class)
  public @ResponseBody HttpErrorInfo handleNotFoundExceptions(
    ServerHttpRequest request, NotFoundException ex) {

    return createHttpErrorInfo(NOT_FOUND, request, ex);
  }

  @ResponseStatus(UNPROCESSABLE_CONTENT)
  @ExceptionHandler(InvalidInputException.class)
  public @ResponseBody HttpErrorInfo handleInvalidInputException(
    ServerHttpRequest request, InvalidInputException ex) {

    return createHttpErrorInfo(UNPROCESSABLE_CONTENT, request, ex);
  }

  private HttpErrorInfo createHttpErrorInfo(
    HttpStatus httpStatus, ServerHttpRequest request, Exception ex) {

    final String path = request.getPath().pathWithinApplication().value();
    final String message = ex.getMessage();

    LOG.debug("Returning HTTP status: {} for path: {}, message: {}", httpStatus, path, message);
    return new HttpErrorInfo(httpStatus, path, message);
  }
}
```

#### `util/src/main/java/se/magnus/util/http/HttpErrorInfo.java` — 새 파일 (47줄)

<!-- wb:file path="util/src/main/java/se/magnus/util/http/HttpErrorInfo.java" op="write" nl="1" -->
```java
package se.magnus.util.http;

import java.time.ZonedDateTime;
import org.springframework.http.HttpStatus;

public class HttpErrorInfo {
  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private ZonedDateTime timestamp;
  private String path;
  private HttpStatus httpStatus;
  private String message;

  public HttpErrorInfo() {
    timestamp = null;
    this.httpStatus = null;
    this.path = null;
    this.message = null;
  }

  public HttpErrorInfo(HttpStatus httpStatus, String path, String message) {
    timestamp = ZonedDateTime.now();
    this.httpStatus = httpStatus;
    this.path = path;
    this.message = message;
  }

  public ZonedDateTime getTimestamp() {
    return timestamp;
  }

  public String getPath() {
    return path;
  }

  public int getStatus() {
    return httpStatus.value();
  }

  public String getError() {
    return httpStatus.getReasonPhrase();
  }

  public String getMessage() {
    return message;
  }
}
```

#### `util/src/main/java/se/magnus/util/http/ServiceUtil.java` — 새 파일 (45줄)

<!-- wb:file path="util/src/main/java/se/magnus/util/http/ServiceUtil.java" op="write" nl="1" -->
```java
package se.magnus.util.http;

import java.net.InetAddress;
import java.net.UnknownHostException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class ServiceUtil {
  private static final Logger LOG = LoggerFactory.getLogger(ServiceUtil.class);

  private final String port;

  private String serviceAddress = null;

  public ServiceUtil(@Value("${server.port}") String port) {

    this.port = port;
  }

  public String getServiceAddress() {
    if (serviceAddress == null) {
      serviceAddress = findMyHostname() + "/" + findMyIpAddress() + ":" + port;
    }
    return serviceAddress;
  }

  private String findMyHostname() {
    try {
      return InetAddress.getLocalHost().getHostName();
    } catch (UnknownHostException e) {
      return "unknown host name";
    }
  }

  private String findMyIpAddress() {
    try {
      return InetAddress.getLocalHost().getHostAddress();
    } catch (UnknownHostException e) {
      return "unknown IP address";
    }
  }
}
```

**중간 확인**

```bash
./gradlew :util:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `product-service`

핵심 서비스입니다. `spring init`이 만든 골격에 `api`·`util` 의존성을 추가하고, 서비스 구현 클래스와 테스트를 작성합니다. 지금은 고정 데이터를 돌려줍니다.

**지울 파일**

```bash
rm microservices/product-service/src/main/resources/application.properties
```

<!-- wb:file path="microservices/product-service/src/main/resources/application.properties" op="delete" nl="0" -->

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -17,10 +17,22 @@
     mavenCentral()
 }
 
+jar {
+    enabled = false
+}
+
 dependencies {
+    implementation project(':api')
+    implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+
+    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
+    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
+    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'
+
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
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

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/ProductServiceApplication.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/ProductServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan("se.magnus")
public class ProductServiceApplication {

  public static void main(String[] args) {
    SpringApplication.run(ProductServiceApplication.class, args);
  }
}
```

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java` — 새 파일 (37줄)

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.services;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.RestController;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.product.ProductService;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.api.exceptions.NotFoundException;
import se.magnus.util.http.ServiceUtil;

@RestController
public class ProductServiceImpl implements ProductService {

  private static final Logger LOG = LoggerFactory.getLogger(ProductServiceImpl.class);

  private final ServiceUtil serviceUtil;

  public ProductServiceImpl(ServiceUtil serviceUtil) {
    this.serviceUtil = serviceUtil;
  }

  @Override
  public Product getProduct(int productId) {
    LOG.debug("/product return the found product for productId={}", productId);

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    if (productId == 13) {
      throw new NotFoundException("No product found for productId: " + productId);
    }

    return new Product(productId, "name-" + productId, 123, serviceUtil.getServiceAddress());
  }
}
```

#### `microservices/product-service/src/main/resources/application.yml` — 새 파일 (7줄)

<!-- wb:file path="microservices/product-service/src/main/resources/application.yml" op="write" nl="1" -->
```yaml
server.port: 7002
spring.web.error.include-message: always

logging:
  level:
    root: INFO
    se.magnus: DEBUG
```

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_CONTENT;
import static org.springframework.http.MediaType.APPLICATION_JSON;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.test.web.reactive.server.WebTestClient;

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
class ProductServiceApplicationTests {

  @Autowired private WebTestClient client;

  @Test
  void getProductById() {

    int productId = 1;

    client.get()
      .uri("/product/" + productId)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isOk()
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.productId").isEqualTo(productId);
  }

  @Test
  void getProductInvalidParameterString() {

    client.get()
      .uri("/product/no-integer")
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(BAD_REQUEST)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/product/no-integer")
        .jsonPath("$.message").isEqualTo("Type mismatch.");
  }

  @Test
  void getProductNotFound() {

    int productIdNotFound = 13;

    client.get()
      .uri("/product/" + productIdNotFound)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isNotFound()
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/product/" + productIdNotFound)
        .jsonPath("$.message").isEqualTo("No product found for productId: " + productIdNotFound);
  }

  @Test
  void getProductInvalidParameterNegativeValue() {

    int productIdInvalid = -1;

    client.get()
      .uri("/product/" + productIdInvalid)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(UNPROCESSABLE_CONTENT)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/product/" + productIdInvalid)
        .jsonPath("$.message").isEqualTo("Invalid productId: " + productIdInvalid);
  }
}
```

**중간 확인**

```bash
./gradlew :microservices:product-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-6"></a>

## 단계 6. `recommendation-service`

핵심 서비스입니다. `spring init`이 만든 골격에 `api`·`util` 의존성을 추가하고, 서비스 구현 클래스와 테스트를 작성합니다. 지금은 고정 데이터를 돌려줍니다.

**지울 파일**

```bash
rm microservices/recommendation-service/src/main/resources/application.properties
```

<!-- wb:file path="microservices/recommendation-service/src/main/resources/application.properties" op="delete" nl="0" -->

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -17,10 +17,22 @@
     mavenCentral()
 }
 
+jar {
+    enabled = false
+}
+
 dependencies {
+    implementation project(':api')
+    implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+
+    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
+    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
+    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'
+
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
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

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplication.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan("se.magnus")
public class RecommendationServiceApplication {

  public static void main(String[] args) {
    SpringApplication.run(RecommendationServiceApplication.class, args);
  }
}
```

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationServiceImpl.java` — 새 파일 (45줄)

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.services;

import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.RestController;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.recommendation.RecommendationService;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.util.http.ServiceUtil;

@RestController
public class RecommendationServiceImpl implements RecommendationService {

  private static final Logger LOG = LoggerFactory.getLogger(RecommendationServiceImpl.class);

  private final ServiceUtil serviceUtil;

  public RecommendationServiceImpl(ServiceUtil serviceUtil) {
    this.serviceUtil = serviceUtil;
  }

  @Override
  public List<Recommendation> getRecommendations(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    if (productId == 113) {
      LOG.debug("No recommendations found for productId: {}", productId);
      return new ArrayList<>();
    }

    List<Recommendation> list = new ArrayList<>();
    list.add(new Recommendation(productId, 1, "Author 1", 1, "Content 1", serviceUtil.getServiceAddress()));
    list.add(new Recommendation(productId, 2, "Author 2", 2, "Content 2", serviceUtil.getServiceAddress()));
    list.add(new Recommendation(productId, 3, "Author 3", 3, "Content 3", serviceUtil.getServiceAddress()));

    LOG.debug("/recommendation response size: {}", list.size());

    return list;
  }
}
```

#### `microservices/recommendation-service/src/main/resources/application.yml` — 새 파일 (7줄)

<!-- wb:file path="microservices/recommendation-service/src/main/resources/application.yml" op="write" nl="1" -->
```yaml
server.port: 7003
spring.web.error.include-message: always

logging:
  level:
    root: INFO
    se.magnus: DEBUG
```

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_CONTENT;
import static org.springframework.http.MediaType.APPLICATION_JSON;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.test.web.reactive.server.WebTestClient;

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
class RecommendationServiceApplicationTests {

  @Autowired private WebTestClient client;

  @Test
  void getRecommendationsByProductId() {

    int productId = 1;

    client.get()
      .uri("/recommendation?productId=" + productId)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isOk()
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.length()").isEqualTo(3)
        .jsonPath("$[0].productId").isEqualTo(productId);
  }

  @Test
  void getRecommendationsMissingParameter() {

    client.get()
      .uri("/recommendation")
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(BAD_REQUEST)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/recommendation")
        .jsonPath("$.message").isEqualTo("Required query parameter 'productId' is not present.");
  }

  @Test
  void getRecommendationsInvalidParameter() {

    client.get()
      .uri("/recommendation?productId=no-integer")
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(BAD_REQUEST)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/recommendation")
        .jsonPath("$.message").isEqualTo("Type mismatch.");
  }

  @Test
  void getRecommendationsNotFound() {

    int productIdNotFound = 113;

    client.get()
      .uri("/recommendation?productId=" + productIdNotFound)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isOk()
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.length()").isEqualTo(0);
  }

  @Test
  void getRecommendationsInvalidParameterNegativeValue() {

    int productIdInvalid = -1;

    client.get()
      .uri("/recommendation?productId=" + productIdInvalid)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(UNPROCESSABLE_CONTENT)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/recommendation")
        .jsonPath("$.message").isEqualTo("Invalid productId: " + productIdInvalid);
  }
}
```

**중간 확인**

```bash
./gradlew :microservices:recommendation-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-7"></a>

## 단계 7. `review-service`

핵심 서비스입니다. `spring init`이 만든 골격에 `api`·`util` 의존성을 추가하고, 서비스 구현 클래스와 테스트를 작성합니다. 지금은 고정 데이터를 돌려줍니다.

**지울 파일**

```bash
rm microservices/review-service/src/main/resources/application.properties
```

<!-- wb:file path="microservices/review-service/src/main/resources/application.properties" op="delete" nl="0" -->

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -17,10 +17,22 @@
     mavenCentral()
 }
 
+jar {
+    enabled = false
+}
+
 dependencies {
+    implementation project(':api')
+    implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+
+    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
+    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
+    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'
+
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
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

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan("se.magnus")
public class ReviewServiceApplication {

  public static void main(String[] args) {
    SpringApplication.run(ReviewServiceApplication.class, args);
  }
}
```

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewServiceImpl.java` — 새 파일 (45줄)

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review.services;

import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.RestController;
import se.magnus.api.core.review.Review;
import se.magnus.api.core.review.ReviewService;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.util.http.ServiceUtil;

@RestController
public class ReviewServiceImpl implements ReviewService {

  private static final Logger LOG = LoggerFactory.getLogger(ReviewServiceImpl.class);

  private final ServiceUtil serviceUtil;

  public ReviewServiceImpl(ServiceUtil serviceUtil) {
    this.serviceUtil = serviceUtil;
  }

  @Override
  public List<Review> getReviews(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    if (productId == 213) {
      LOG.debug("No reviews found for productId: {}", productId);
      return new ArrayList<>();
    }

    List<Review> list = new ArrayList<>();
    list.add(new Review(productId, 1, "Author 1", "Subject 1", "Content 1", serviceUtil.getServiceAddress()));
    list.add(new Review(productId, 2, "Author 2", "Subject 2", "Content 2", serviceUtil.getServiceAddress()));
    list.add(new Review(productId, 3, "Author 3", "Subject 3", "Content 3", serviceUtil.getServiceAddress()));

    LOG.debug("/reviews response size: {}", list.size());

    return list;
  }
}
```

#### `microservices/review-service/src/main/resources/application.yml` — 새 파일 (7줄)

<!-- wb:file path="microservices/review-service/src/main/resources/application.yml" op="write" nl="1" -->
```yaml
server.port: 7004
spring.web.error.include-message: always

logging:
  level:
    root: INFO
    se.magnus: DEBUG
```

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_CONTENT;
import static org.springframework.http.MediaType.APPLICATION_JSON;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.test.web.reactive.server.WebTestClient;

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
class ReviewServiceApplicationTests {

  @Autowired private WebTestClient client;

  @Test
  void getReviewsByProductId() {

    int productId = 1;

    client.get()
      .uri("/review?productId=" + productId)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isOk()
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.length()").isEqualTo(3)
        .jsonPath("$[0].productId").isEqualTo(productId);
  }

  @Test
  void getReviewsMissingParameter() {

    client.get()
      .uri("/review")
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(BAD_REQUEST)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/review")
        .jsonPath("$.message").isEqualTo("Required query parameter 'productId' is not present.");
  }

  @Test
  void getReviewsInvalidParameter() {

    client.get()
      .uri("/review?productId=no-integer")
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(BAD_REQUEST)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/review")
        .jsonPath("$.message").isEqualTo("Type mismatch.");
  }

  @Test
  void getReviewsNotFound() {

    int productIdNotFound = 213;

    client.get()
      .uri("/review?productId=" + productIdNotFound)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isOk()
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.length()").isEqualTo(0);
  }

  @Test
  void getReviewsInvalidParameterNegativeValue() {

    int productIdInvalid = -1;

    client.get()
      .uri("/review?productId=" + productIdInvalid)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(UNPROCESSABLE_CONTENT)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/review")
        .jsonPath("$.message").isEqualTo("Invalid productId: " + productIdInvalid);
  }
}
```

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-8"></a>

## 단계 8. `product-composite-service`

핵심 서비스 3개를 `RestTemplate`으로 호출하는 `ProductCompositeIntegration`과, 결과를 하나로 합치는 `ProductCompositeServiceImpl`을 만듭니다. 테스트는 통합 클래스를 `@MockitoBean`으로 바꿔 끼웁니다.

**지울 파일**

```bash
rm microservices/product-composite-service/src/main/resources/application.properties
```

<!-- wb:file path="microservices/product-composite-service/src/main/resources/application.properties" op="delete" nl="0" -->

#### `microservices/product-composite-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -17,10 +17,22 @@
     mavenCentral()
 }
 
+jar {
+    enabled = false
+}
+
 dependencies {
+    implementation project(':api')
+    implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+
+    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
+    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
+    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'
+
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
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

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplication.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication
@ComponentScan("se.magnus")
public class ProductCompositeServiceApplication {

  @Bean
  RestTemplate restTemplate() {
    return new RestTemplate();
  }

  public static void main(String[] args) {
    SpringApplication.run(ProductCompositeServiceApplication.class, args);
  }

}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java` — 새 파일 (133줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services;

import static org.springframework.http.HttpMethod.GET;

import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.product.ProductService;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.recommendation.RecommendationService;
import se.magnus.api.core.review.Review;
import se.magnus.api.core.review.ReviewService;
import se.magnus.api.exceptions.InvalidInputException;
import se.magnus.api.exceptions.NotFoundException;
import se.magnus.util.http.HttpErrorInfo;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

@Component
public class ProductCompositeIntegration implements ProductService, RecommendationService, ReviewService {

  private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeIntegration.class);

  private final RestTemplate restTemplate;
  private final ObjectMapper mapper;

  private final String productServiceUrl;
  private final String recommendationServiceUrl;
  private final String reviewServiceUrl;

  public ProductCompositeIntegration(
    RestTemplate restTemplate,
    ObjectMapper mapper,
    @Value("${app.product-service.host}") String productServiceHost,
    @Value("${app.product-service.port}") int productServicePort,
    @Value("${app.recommendation-service.host}") String recommendationServiceHost,
    @Value("${app.recommendation-service.port}") int recommendationServicePort,
    @Value("${app.review-service.host}") String reviewServiceHost,
    @Value("${app.review-service.port}") int reviewServicePort) {

    this.restTemplate = restTemplate;
    this.mapper = mapper;

    productServiceUrl = "http://" + productServiceHost + ":" + productServicePort + "/product/";
    recommendationServiceUrl = "http://" + recommendationServiceHost + ":" + recommendationServicePort + "/recommendation?productId=";
    reviewServiceUrl = "http://" + reviewServiceHost + ":" + reviewServicePort + "/review?productId=";
  }

  @Override
  public Product getProduct(int productId) {

    try {
      String url = productServiceUrl + productId;
      LOG.debug("Will call getProduct API on URL: {}", url);

      Product product = restTemplate.getForObject(url, Product.class);
      LOG.debug("Found a product with id: {}", product.getProductId());

      return product;

    } catch (HttpClientErrorException ex) {

      switch (HttpStatus.resolve(ex.getStatusCode().value())) {
        case NOT_FOUND:
          throw new NotFoundException(getErrorMessage(ex));

        case UNPROCESSABLE_CONTENT:
          throw new InvalidInputException(getErrorMessage(ex));

        default:
          LOG.warn("Got an unexpected HTTP error: {}, will rethrow it", ex.getStatusCode());
          LOG.warn("Error body: {}", ex.getResponseBodyAsString());
          throw ex;
      }
    }
  }

  private String getErrorMessage(HttpClientErrorException ex) {
    try {
      return mapper.readValue(ex.getResponseBodyAsString(), HttpErrorInfo.class).getMessage();
    } catch (JacksonException ioex) {
      return ex.getMessage();
    }
  }

  @Override
  public List<Recommendation> getRecommendations(int productId) {

    try {
      String url = recommendationServiceUrl + productId;

      LOG.debug("Will call getRecommendations API on URL: {}", url);
      List<Recommendation> recommendations = restTemplate
        .exchange(url, GET, null, new ParameterizedTypeReference<List<Recommendation>>() {})
        .getBody();

      LOG.debug("Found {} recommendations for a product with id: {}", recommendations.size(), productId);
      return recommendations;

    } catch (Exception ex) {
      LOG.warn("Got an exception while requesting recommendations, return zero recommendations: {}", ex.getMessage());
      return new ArrayList<>();
    }
  }

  @Override
  public List<Review> getReviews(int productId) {

    try {
      String url = reviewServiceUrl + productId;

      LOG.debug("Will call getReviews API on URL: {}", url);
      List<Review> reviews = restTemplate
        .exchange(url, GET, null, new ParameterizedTypeReference<List<Review>>() {})
        .getBody();

      LOG.debug("Found {} reviews for a product with id: {}", reviews.size(), productId);
      return reviews;

    } catch (Exception ex) {
      LOG.warn("Got an exception while requesting reviews, return zero reviews: {}", ex.getMessage());
      return new ArrayList<>();
    }
  }
}
```

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeServiceImpl.java` — 새 파일 (72줄)

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services;

import java.util.List;
import java.util.stream.Collectors;
import org.springframework.web.bind.annotation.RestController;
import se.magnus.api.composite.product.*;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.review.Review;
import se.magnus.api.exceptions.NotFoundException;
import se.magnus.util.http.ServiceUtil;

@RestController
public class ProductCompositeServiceImpl implements ProductCompositeService {

  private final ServiceUtil serviceUtil;
  private ProductCompositeIntegration integration;

  public ProductCompositeServiceImpl(
    ServiceUtil serviceUtil, ProductCompositeIntegration integration) {
    
    this.serviceUtil = serviceUtil;
    this.integration = integration;
  }

  @Override
  public ProductAggregate getProduct(int productId) {

    Product product = integration.getProduct(productId);
    if (product == null) {
      throw new NotFoundException("No product found for productId: " + productId);
    }

    List<Recommendation> recommendations = integration.getRecommendations(productId);

    List<Review> reviews = integration.getReviews(productId);

    return createProductAggregate(product, recommendations, reviews, serviceUtil.getServiceAddress());
  }

  private ProductAggregate createProductAggregate(
    Product product,
    List<Recommendation> recommendations,
    List<Review> reviews,
    String serviceAddress) {

    // 1. Setup product info
    int productId = product.getProductId();
    String name = product.getName();
    int weight = product.getWeight();

    // 2. Copy summary recommendation info, if available
    List<RecommendationSummary> recommendationSummaries =
      (recommendations == null) ? null : recommendations.stream()
        .map(r -> new RecommendationSummary(r.getRecommendationId(), r.getAuthor(), r.getRate()))
        .collect(Collectors.toList());

    // 3. Copy summary review info, if available
    List<ReviewSummary> reviewSummaries = 
      (reviews == null) ? null : reviews.stream()
        .map(r -> new ReviewSummary(r.getReviewId(), r.getAuthor(), r.getSubject()))
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

#### `microservices/product-composite-service/src/main/resources/application.yml` — 새 파일 (18줄)

<!-- wb:file path="microservices/product-composite-service/src/main/resources/application.yml" op="write" nl="1" -->
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
```

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import static java.util.Collections.singletonList;
import static org.mockito.Mockito.when;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_CONTENT;
import static org.springframework.http.MediaType.APPLICATION_JSON;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.reactive.server.WebTestClient;
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

  @Autowired private WebTestClient client;

  @MockitoBean private ProductCompositeIntegration compositeIntegration;

  @BeforeEach
  void setUp() {

    when(compositeIntegration.getProduct(PRODUCT_ID_OK))
      .thenReturn(new Product(PRODUCT_ID_OK, "name", 1, "mock-address"));
    when(compositeIntegration.getRecommendations(PRODUCT_ID_OK))
      .thenReturn(singletonList(new Recommendation(PRODUCT_ID_OK, 1, "author", 1, "content", "mock address")));
    when(compositeIntegration.getReviews(PRODUCT_ID_OK))
      .thenReturn(singletonList(new Review(PRODUCT_ID_OK, 1, "author", "subject", "content", "mock address")));

    when(compositeIntegration.getProduct(PRODUCT_ID_NOT_FOUND))
      .thenThrow(new NotFoundException("NOT FOUND: " + PRODUCT_ID_NOT_FOUND));

    when(compositeIntegration.getProduct(PRODUCT_ID_INVALID))
      .thenThrow(new InvalidInputException("INVALID: " + PRODUCT_ID_INVALID));
  }

  @Test
  void contextLoads() {}

  @Test
  void getProductById() {

    client.get()
      .uri("/product-composite/" + PRODUCT_ID_OK)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isOk()
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.productId").isEqualTo(PRODUCT_ID_OK)
        .jsonPath("$.recommendations.length()").isEqualTo(1)
        .jsonPath("$.reviews.length()").isEqualTo(1);
  }

  @Test
  void getProductNotFound() {

    client.get()
      .uri("/product-composite/" + PRODUCT_ID_NOT_FOUND)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isNotFound()
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/product-composite/" + PRODUCT_ID_NOT_FOUND)
        .jsonPath("$.message").isEqualTo("NOT FOUND: " + PRODUCT_ID_NOT_FOUND);
  }

  @Test
  void getProductInvalidInput() {

    client.get()
      .uri("/product-composite/" + PRODUCT_ID_INVALID)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(UNPROCESSABLE_CONTENT)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody()
        .jsonPath("$.path").isEqualTo("/product-composite/" + PRODUCT_ID_INVALID)
        .jsonPath("$.message").isEqualTo("INVALID: " + PRODUCT_ID_INVALID);
  }
}
```

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

## 확인하기

서비스 4개를 직접 띄우고 테스트합니다.

```bash
cd ~/my-work/Chapter03/2-basic-rest-services
./gradlew build
for s in product recommendation review product-composite; do
  java -jar microservices/$s-service/build/libs/*.jar &
done
./test-em-all.bash
kill $(jobs -p)   # 끝나면 서비스 종료
```

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter03/2-basic-rest-services
```

---

[워크북 목차](README.md) · [4장 워크북](Chapter04.md) →
