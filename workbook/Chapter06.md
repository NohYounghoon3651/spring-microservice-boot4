# 6장 워크북 — 영속성 추가

> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 6장 · 영문 3판 p.123–162 ([교재 대응 가이드](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter06/BOOK-GUIDE.md))  
> 완성 코드: [`Chapter06`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/main/Chapter06) · 위키: [6장](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/06장-영속성-추가)

## 이 장에서 만드는 것

핵심 서비스에 **데이터베이스**를 붙입니다. `product`·`recommendation`은 MongoDB, `review`는 MySQL을 씁니다.

- 엔티티와 Spring Data 리포지터리, MapStruct 매퍼
- Testcontainers로 실제 데이터베이스를 띄우는 영속성 테스트(`@ServiceConnection`)
- 생성·삭제 API 추가와 복합 서비스의 생성·삭제 구현
- 도커 컴포즈에 MongoDB·MySQL 추가

## 시작하기

5장을 끝낸 작업 폴더를 복사해서 시작합니다. 5장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.

```bash
cd ~/my-work
cp -r Chapter05 Chapter06          # 내가 만든 5장 결과에서 시작
# 또는: cp -r <저장소>/Chapter05 Chapter06        # 저장소의 5장 완성 코드에서 시작
cd Chapter06 && ./gradlew clean -q
```

## 단계 목록

1. [루트 빌드 파일·도커 컴포즈·테스트 스크립트](#단계-1) — 수정 2
2. [`api` 프로젝트 — 서비스 간 API와 DTO](#단계-2) — 수정 10
3. [`product-service`](#단계-3) — 새 파일 7 · 수정 5
4. [`recommendation-service`](#단계-4) — 새 파일 7 · 수정 5
5. [`review-service`](#단계-5) — 새 파일 7 · 수정 5
6. [`product-composite-service`](#단계-6) — 수정 4

<a id="단계-1"></a>

## 단계 1. 루트 빌드 파일·도커 컴포즈·테스트 스크립트

`docker-compose.yml`에 MongoDB(`mongo:8.0.5`)와 MySQL(`mysql:9.2.0`)을 추가합니다. `test-em-all.bash`는 테스트 데이터를 직접 만들고 지우도록 바뀝니다.

#### `docker-compose.yml` — 전체를 다음 내용으로 바꿉니다

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

  recommendation:
    build: microservices/recommendation-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
    depends_on:
      mongodb:
        condition: service_healthy

  review:
    build: microservices/review-service
    mem_limit: 512m
    environment:
      - SPRING_PROFILES_ACTIVE=docker
    depends_on:
      mysql:
        condition: service_healthy

  product-composite:
    build: microservices/product-composite-service
    mem_limit: 512m
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=docker

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
```

#### `test-em-all.bash` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -78,6 +78,50 @@
   echo "DONE, continues..."
 }
 
+function recreateComposite() {
+  local productId=$1
+  local composite=$2
+
+  assertCurl 200 "curl -X DELETE http://$HOST:$PORT/product-composite/${productId} -s"
+  curl -X POST http://$HOST:$PORT/product-composite -H "Content-Type: application/json" --data "$composite"
+}
+
+function setupTestdata() {
+
+  body="{\"productId\":$PROD_ID_NO_RECS"
+  body+=\
+',"name":"product name A","weight":100, "reviews":[
+  {"reviewId":1,"author":"author 1","subject":"subject 1","content":"content 1"},
+  {"reviewId":2,"author":"author 2","subject":"subject 2","content":"content 2"},
+  {"reviewId":3,"author":"author 3","subject":"subject 3","content":"content 3"}
+]}'
+  recreateComposite "$PROD_ID_NO_RECS" "$body"
+
+  body="{\"productId\":$PROD_ID_NO_REVS"
+  body+=\
+',"name":"product name B","weight":200, "recommendations":[
+  {"recommendationId":1,"author":"author 1","rate":1,"content":"content 1"},
+  {"recommendationId":2,"author":"author 2","rate":2,"content":"content 2"},
+  {"recommendationId":3,"author":"author 3","rate":3,"content":"content 3"}
+]}'
+  recreateComposite "$PROD_ID_NO_REVS" "$body"
+
+
+  body="{\"productId\":$PROD_ID_REVS_RECS"
+  body+=\
+',"name":"product name C","weight":300, "recommendations":[
+      {"recommendationId":1,"author":"author 1","rate":1,"content":"content 1"},
+      {"recommendationId":2,"author":"author 2","rate":2,"content":"content 2"},
+      {"recommendationId":3,"author":"author 3","rate":3,"content":"content 3"}
+  ], "reviews":[
+      {"reviewId":1,"author":"author 1","subject":"subject 1","content":"content 1"},
+      {"reviewId":2,"author":"author 2","subject":"subject 2","content":"content 2"},
+      {"reviewId":3,"author":"author 3","subject":"subject 3","content":"content 3"}
+  ]}'
+  recreateComposite "$PROD_ID_REVS_RECS" "$body"
+
+}
+
 set -e
 
 echo "Start Tests:" `date`
@@ -94,7 +138,9 @@
   docker compose up -d
 fi
 
-waitForService curl http://$HOST:$PORT/product-composite/$PROD_ID_REVS_RECS
+waitForService curl -X DELETE http://$HOST:$PORT/product-composite/$PROD_ID_NOT_FOUND
+
+setupTestdata
 
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

function recreateComposite() {
  local productId=$1
  local composite=$2

  assertCurl 200 "curl -X DELETE http://$HOST:$PORT/product-composite/${productId} -s"
  curl -X POST http://$HOST:$PORT/product-composite -H "Content-Type: application/json" --data "$composite"
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

waitForService curl -X DELETE http://$HOST:$PORT/product-composite/$PROD_ID_NOT_FOUND

setupTestdata

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

핵심 서비스 API에 `createXxx`, `deleteXxx`를 추가하고, DTO에 setter를 추가합니다(MapStruct가 객체를 채울 때 씁니다).

#### `api/src/main/java/se/magnus/api/composite/product/ProductAggregate.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -11,6 +11,15 @@
   private List<RecommendationSummary> recommendations;
   private List<ReviewSummary> reviews;
   private ServiceAddresses serviceAddresses;
+
+  public ProductAggregate() {
+    productId = 0;
+    name = null;
+    weight = 0;
+    recommendations = null;
+    reviews = null;
+    serviceAddresses = null;
+  }
 
   public ProductAggregate(
     int productId,
```

<details><summary>완성된 파일 전체 보기</summary>

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

  public ProductAggregate() {
    productId = 0;
    name = null;
    weight = 0;
    recommendations = null;
    reviews = null;
    serviceAddresses = null;
  }

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

</details>

#### `api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/ProductCompositeService.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

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
  @PostMapping(
    value    = "/product-composite",
    consumes = "application/json")
  void createProduct(@RequestBody ProductAggregate body);

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
  ProductAggregate getProduct(@PathVariable int productId);

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
  @DeleteMapping(value = "/product-composite/{productId}")
  void deleteProduct(@PathVariable int productId);
}
```

#### `api/src/main/java/se/magnus/api/composite/product/RecommendationSummary.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -7,11 +7,20 @@
   private int recommendationId;
   private String author;
   private int rate;
+  private String content;
 
-  public RecommendationSummary(int recommendationId, String author, int rate) {
+  public RecommendationSummary() {
+    this.recommendationId = 0;
+    this.author = null;
+    this.rate = 0;
+    this.content = null;
+  }
+
+  public RecommendationSummary(int recommendationId, String author, int rate, String content) {
     this.recommendationId = recommendationId;
     this.author = author;
     this.rate = rate;
+    this.content = content;
   }
 
   public int getRecommendationId() {
@@ -25,4 +34,8 @@
   public int getRate() {
     return rate;
   }
+
+  public String getContent() {
+    return content;
+  }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/RecommendationSummary.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

public class RecommendationSummary {

  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int recommendationId;
  private String author;
  private int rate;
  private String content;

  public RecommendationSummary() {
    this.recommendationId = 0;
    this.author = null;
    this.rate = 0;
    this.content = null;
  }

  public RecommendationSummary(int recommendationId, String author, int rate, String content) {
    this.recommendationId = recommendationId;
    this.author = author;
    this.rate = rate;
    this.content = content;
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
}
```

</details>

#### `api/src/main/java/se/magnus/api/composite/product/ReviewSummary.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -7,11 +7,20 @@
   private int reviewId;
   private String author;
   private String subject;
+  private String content;
 
-  public ReviewSummary(int reviewId, String author, String subject) {
+  public ReviewSummary() {
+    this.reviewId = 0;
+    this.author = null;
+    this.subject = null;
+    this.content = null;
+  }
+
+  public ReviewSummary(int reviewId, String author, String subject, String content) {
     this.reviewId = reviewId;
     this.author = author;
     this.subject = subject;
+    this.content = content;
   }
 
   public int getReviewId() {
@@ -25,4 +34,8 @@
   public String getSubject() {
     return subject;
   }
+
+  public String getContent() {
+    return content;
+  }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/composite/product/ReviewSummary.java" op="write" nl="1" -->
```java
package se.magnus.api.composite.product;

public class ReviewSummary {

  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int reviewId;
  private String author;
  private String subject;
  private String content;

  public ReviewSummary() {
    this.reviewId = 0;
    this.author = null;
    this.subject = null;
    this.content = null;
  }

  public ReviewSummary(int reviewId, String author, String subject, String content) {
    this.reviewId = reviewId;
    this.author = author;
    this.subject = subject;
    this.content = content;
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
}
```

</details>

#### `api/src/main/java/se/magnus/api/core/product/Product.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,8 +1,6 @@
 package se.magnus.api.core.product;
 
 public class Product {
-  // Fields are not final: Jackson 3 does not set final fields when deserializing
-  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
   private int productId;
   private String name;
   private int weight;
@@ -37,4 +35,20 @@
   public String getServiceAddress() {
     return serviceAddress;
   }
+
+  public void setProductId(int productId) {
+    this.productId = productId;
+  }
+
+  public void setName(String name) {
+    this.name = name;
+  }
+
+  public void setWeight(int weight) {
+    this.weight = weight;
+  }
+
+  public void setServiceAddress(String serviceAddress) {
+    this.serviceAddress = serviceAddress;
+  }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/core/product/Product.java" op="write" nl="1" -->
```java
package se.magnus.api.core.product;

public class Product {
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

  public void setProductId(int productId) {
    this.productId = productId;
  }

  public void setName(String name) {
    this.name = name;
  }

  public void setWeight(int weight) {
    this.weight = weight;
  }

  public void setServiceAddress(String serviceAddress) {
    this.serviceAddress = serviceAddress;
  }
}
```

</details>

#### `api/src/main/java/se/magnus/api/core/product/ProductService.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="api/src/main/java/se/magnus/api/core/product/ProductService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.product;

import org.springframework.web.bind.annotation.*;

public interface ProductService {

  /**
   * Sample usage, see below.
   *
   * curl -X POST $HOST:$PORT/product \
   *   -H "Content-Type: application/json" --data \
   *   '{"productId":123,"name":"product 123","weight":123}'
   *
   * @param body A JSON representation of the new product
   * @return A JSON representation of the newly created product
   */
  @PostMapping(
    value    = "/product",
    consumes = "application/json",
    produces = "application/json")
  Product createProduct(@RequestBody Product body);

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

  /**
   * Sample usage: "curl -X DELETE $HOST:$PORT/product/1".
   *
   * @param productId Id of the product
   */
  @DeleteMapping(value = "/product/{productId}")
  void deleteProduct(@PathVariable int productId);
}
```

#### `api/src/main/java/se/magnus/api/core/recommendation/Recommendation.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,8 +1,6 @@
 package se.magnus.api.core.recommendation;
 
 public class Recommendation {
-  // Fields are not final: Jackson 3 does not set final fields when deserializing
-  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
   private int productId;
   private int recommendationId;
   private String author;
@@ -58,4 +56,28 @@
   public String getServiceAddress() {
     return serviceAddress;
   }
+
+  public void setProductId(int productId) {
+    this.productId = productId;
+  }
+
+  public void setRecommendationId(int recommendationId) {
+    this.recommendationId = recommendationId;
+  }
+
+  public void setAuthor(String author) {
+    this.author = author;
+  }
+
+  public void setRate(int rate) {
+    this.rate = rate;
+  }
+
+  public void setContent(String content) {
+    this.content = content;
+  }
+
+  public void setServiceAddress(String serviceAddress) {
+    this.serviceAddress = serviceAddress;
+  }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/core/recommendation/Recommendation.java" op="write" nl="1" -->
```java
package se.magnus.api.core.recommendation;

public class Recommendation {
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

  public void setProductId(int productId) {
    this.productId = productId;
  }

  public void setRecommendationId(int recommendationId) {
    this.recommendationId = recommendationId;
  }

  public void setAuthor(String author) {
    this.author = author;
  }

  public void setRate(int rate) {
    this.rate = rate;
  }

  public void setContent(String content) {
    this.content = content;
  }

  public void setServiceAddress(String serviceAddress) {
    this.serviceAddress = serviceAddress;
  }
}
```

</details>

#### `api/src/main/java/se/magnus/api/core/recommendation/RecommendationService.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="api/src/main/java/se/magnus/api/core/recommendation/RecommendationService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.recommendation;

import java.util.List;
import org.springframework.web.bind.annotation.*;

public interface RecommendationService {

  /**
   * Sample usage, see below.
   *
   * curl -X POST $HOST:$PORT/recommendation \
   *   -H "Content-Type: application/json" --data \
   *   '{"productId":123,"recommendationId":456,"author":"me","rate":5,"content":"yada, yada, yada"}'
   *
   * @param body A JSON representation of the new recommendation
   * @return A JSON representation of the newly created recommendation
   */
  @PostMapping(
    value    = "/recommendation",
    consumes = "application/json",
    produces = "application/json")
  Recommendation createRecommendation(@RequestBody Recommendation body);

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

  /**
   * Sample usage: "curl -X DELETE $HOST:$PORT/recommendation?productId=1".
   *
   * @param productId Id of the product
   */
  @DeleteMapping(value = "/recommendation")
  void deleteRecommendations(@RequestParam(value = "productId", required = true)  int productId);
}
```

#### `api/src/main/java/se/magnus/api/core/review/Review.java` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -1,8 +1,6 @@
 package se.magnus.api.core.review;
 
 public class Review {
-  // Fields are not final: Jackson 3 does not set final fields when deserializing
-  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
   private int productId;
   private int reviewId;
   private String author;
@@ -58,4 +56,28 @@
   public String getServiceAddress() {
     return serviceAddress;
   }
+
+  public void setProductId(int productId) {
+    this.productId = productId;
+  }
+
+  public void setReviewId(int reviewId) {
+    this.reviewId = reviewId;
+  }
+
+  public void setAuthor(String author) {
+    this.author = author;
+  }
+
+  public void setSubject(String subject) {
+    this.subject = subject;
+  }
+
+  public void setContent(String content) {
+    this.content = content;
+  }
+
+  public void setServiceAddress(String serviceAddress) {
+    this.serviceAddress = serviceAddress;
+  }
 }
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="api/src/main/java/se/magnus/api/core/review/Review.java" op="write" nl="1" -->
```java
package se.magnus.api.core.review;

public class Review {
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

  public void setProductId(int productId) {
    this.productId = productId;
  }

  public void setReviewId(int reviewId) {
    this.reviewId = reviewId;
  }

  public void setAuthor(String author) {
    this.author = author;
  }

  public void setSubject(String subject) {
    this.subject = subject;
  }

  public void setContent(String content) {
    this.content = content;
  }

  public void setServiceAddress(String serviceAddress) {
    this.serviceAddress = serviceAddress;
  }
}
```

</details>

#### `api/src/main/java/se/magnus/api/core/review/ReviewService.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="api/src/main/java/se/magnus/api/core/review/ReviewService.java" op="write" nl="1" -->
```java
package se.magnus.api.core.review;

import java.util.List;
import org.springframework.web.bind.annotation.*;

public interface ReviewService {

  /**
   * Sample usage, see below.
   *
   * curl -X POST $HOST:$PORT/review \
   *   -H "Content-Type: application/json" --data \
   *   '{"productId":123,"reviewId":456,"author":"me","subject":"yada, yada, yada","content":"yada, yada, yada"}'
   *
   * @param body A JSON representation of the new review
   * @return A JSON representation of the newly created review
   */
  @PostMapping(
      value    = "/review",
      consumes = "application/json",
      produces = "application/json")
  Review createReview(@RequestBody Review body);

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

  /**
   * Sample usage: "curl -X DELETE $HOST:$PORT/review?productId=1".
   *
   * @param productId Id of the product
   */
  @DeleteMapping(value = "/review")
  void deleteReviews(@RequestParam(value = "productId", required = true)  int productId);
}
```

**중간 확인**

```bash
./gradlew :api:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-3"></a>

## 단계 3. `product-service`

MongoDB용 `ProductEntity`(`@Document`, `@Version`)와 `ProductRepository`, `ProductMapper`를 만들고 서비스 구현이 리포지터리를 쓰도록 바꿉니다. 테스트에는 `MongoDbTestBase`(Testcontainers)와 `PersistenceTests`, `MapperTests`가 추가됩니다.

#### `microservices/product-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -13,6 +13,10 @@
     }
 }
 
+ext {
+    mapstructVersion = '1.6.3'
+}
+
 repositories {
     mavenCentral()
 }
@@ -26,6 +30,12 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'
+    implementation "org.mapstruct:mapstruct:${mapstructVersion}"
+
+    compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
+    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
+    testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
 
     // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
     // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
@@ -33,8 +43,13 @@
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
+
+    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
+    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
+    testImplementation 'org.testcontainers:testcontainers-mongodb'
 }
 
 tasks.named('test') {
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
    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'
    implementation "org.mapstruct:mapstruct:${mapstructVersion}"

    compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'

    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
    testImplementation 'org.testcontainers:testcontainers-mongodb'
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
import org.springframework.data.mongodb.core.MongoOperations;
import org.springframework.data.mongodb.core.index.IndexOperations;
import org.springframework.data.mongodb.core.index.IndexResolver;
import org.springframework.data.mongodb.core.index.MongoPersistentEntityIndexResolver;
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
  MongoOperations mongoTemplate;

  @EventListener(ContextRefreshedEvent.class)
  public void initIndicesAfterStartup() {

    MappingContext<? extends MongoPersistentEntity<?>, MongoPersistentProperty> mappingContext = mongoTemplate.getConverter().getMappingContext();
    IndexResolver resolver = new MongoPersistentEntityIndexResolver(mappingContext);

    IndexOperations indexOps = mongoTemplate.indexOps(ProductEntity.class);
    resolver.resolveIndexFor(ProductEntity.class).forEach(e -> indexOps.createIndex(e));
  }
}
```

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/persistence/ProductEntity.java` — 새 파일 (68줄)

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/persistence/ProductEntity.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.persistence;

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

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/persistence/ProductRepository.java` — 새 파일 (9줄)

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/persistence/ProductRepository.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.persistence;

import java.util.Optional;
import org.springframework.data.repository.CrudRepository;
import org.springframework.data.repository.PagingAndSortingRepository;

public interface ProductRepository extends PagingAndSortingRepository<ProductEntity, String>, CrudRepository<ProductEntity, String> {
  Optional<ProductEntity> findByProductId(int productId);
}
```

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductMapper.java` — 새 파일 (21줄)

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductMapper.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.services;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Mappings;
import se.magnus.api.core.product.Product;
import se.magnus.microservices.core.product.persistence.ProductEntity;

@Mapper(componentModel = "spring")
public interface ProductMapper {

  @Mappings({
    @Mapping(target = "serviceAddress", ignore = true)
  })
  Product entityToApi(ProductEntity entity);

  @Mappings({
    @Mapping(target = "id", ignore = true), @Mapping(target = "version", ignore = true)
  })
  ProductEntity apiToEntity(Product api);
}
```

#### `microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/main/java/se/magnus/microservices/core/product/services/ProductServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product.services;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.web.bind.annotation.RestController;
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
  public Product createProduct(Product body) {
    try {
      ProductEntity entity = mapper.apiToEntity(body);
      ProductEntity newEntity = repository.save(entity);

      LOG.debug("createProduct: entity created for productId: {}", body.getProductId());
      return mapper.entityToApi(newEntity);

    } catch (DuplicateKeyException dke) {
      throw new InvalidInputException("Duplicate key, Product Id: " + body.getProductId());
    }
  }

  @Override
  public Product getProduct(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }

    ProductEntity entity = repository.findByProductId(productId)
      .orElseThrow(() -> new NotFoundException("No product found for productId: " + productId));

    Product response = mapper.entityToApi(entity);
    response.setServiceAddress(serviceUtil.getServiceAddress());

    LOG.debug("getProduct: found productId: {}", response.getProductId());

    return response;
  }

  @Override
  public void deleteProduct(int productId) {
    LOG.debug("deleteProduct: tries to delete an entity with productId: {}", productId);
    repository.findByProductId(productId).ifPresent(e -> repository.delete(e));
  }
}
```

#### `microservices/product-service/src/main/resources/application.yml` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/main/resources/application.yml" op="write" nl="0" -->
```yaml
server.port: 7002
spring.web.error.include-message: always

spring.mongodb:
  host: localhost
  port: 27017
  database: product-db

logging:
  level:
    root: INFO
    se.magnus: DEBUG
    org.springframework.data.mongodb.core.MongoTemplate: DEBUG

---
spring.config.activate.on-profile: docker

server.port: 8080

spring.mongodb.host: mongodb
```

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/MapperTests.java` — 새 파일 (37줄)

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/MapperTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;
import se.magnus.api.core.product.Product;
import se.magnus.microservices.core.product.persistence.ProductEntity;
import se.magnus.microservices.core.product.services.ProductMapper;

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

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/MongoDbTestBase.java` — 새 파일 (15줄)

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/MongoDbTestBase.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.testcontainers.mongodb.MongoDBContainer;

public abstract class MongoDbTestBase {

  @ServiceConnection
  private static MongoDBContainer database = new MongoDBContainer("mongo:8.0.5");

  static {
    database.start();
  }

}
```

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/PersistenceTests.java` — 새 파일 (139줄)

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/PersistenceTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import static java.util.stream.IntStream.rangeClosed;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.data.domain.Sort.Direction.ASC;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.mongodb.test.autoconfigure.DataMongoTest;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import se.magnus.microservices.core.product.persistence.ProductEntity;
import se.magnus.microservices.core.product.persistence.ProductRepository;

@DataMongoTest
class PersistenceTests extends MongoDbTestBase {

  @Autowired
  private ProductRepository repository;

  private ProductEntity savedEntity;

  @BeforeEach
  void setupDb() {
    repository.deleteAll();

    ProductEntity entity = new ProductEntity(1, "n", 1);
    savedEntity = repository.save(entity);

    assertEqualsProduct(entity, savedEntity);
  }


  @Test
  void create() {

    ProductEntity newEntity = new ProductEntity(2, "n", 2);
    repository.save(newEntity);

    ProductEntity foundEntity = repository.findById(newEntity.getId()).get();
    assertEqualsProduct(newEntity, foundEntity);

    assertEquals(2, repository.count());
  }

  @Test
  void update() {
    savedEntity.setName("n2");
    repository.save(savedEntity);

    ProductEntity foundEntity = repository.findById(savedEntity.getId()).get();
    assertEquals(1, (long)foundEntity.getVersion());
    assertEquals("n2", foundEntity.getName());
  }

  @Test
  void delete() {
    repository.delete(savedEntity);
    assertFalse(repository.existsById(savedEntity.getId()));
  }

  @Test
  void getByProductId() {
    Optional<ProductEntity> entity = repository.findByProductId(savedEntity.getProductId());

    assertTrue(entity.isPresent());
    assertEqualsProduct(savedEntity, entity.get());
  }

  @Test
  void duplicateError() {
    assertThrows(DuplicateKeyException.class, () -> {
      ProductEntity entity = new ProductEntity(savedEntity.getProductId(), "n", 1);
      repository.save(entity);
    });
  }

  @Test
  void optimisticLockError() {

    // Store the saved entity in two separate entity objects
    ProductEntity entity1 = repository.findById(savedEntity.getId()).get();
    ProductEntity entity2 = repository.findById(savedEntity.getId()).get();

    // Update the entity using the first entity object
    entity1.setName("n1");
    repository.save(entity1);

    // Update the entity using the second entity object.
    // This should fail since the second entity now holds an old version number, i.e. an Optimistic Lock Error
    assertThrows(OptimisticLockingFailureException.class, () -> {
      entity2.setName("n2");
      repository.save(entity2);
    }); 

    // Get the updated entity from the database and verify its new sate
    ProductEntity updatedEntity = repository.findById(savedEntity.getId()).get();
    assertEquals(1, (int)updatedEntity.getVersion());
    assertEquals("n1", updatedEntity.getName());
  }

  @Test
  void paging() {

    repository.deleteAll();

    List<ProductEntity> newProducts = rangeClosed(1001, 1010)
      .mapToObj(i -> new ProductEntity(i, "name " + i, i))
      .collect(Collectors.toList());
    repository.saveAll(newProducts);

    Pageable nextPage = PageRequest.of(0, 4, ASC, "productId");
    nextPage = testNextPage(nextPage, "[1001, 1002, 1003, 1004]", true);
    nextPage = testNextPage(nextPage, "[1005, 1006, 1007, 1008]", true);
    nextPage = testNextPage(nextPage, "[1009, 1010]", false);
  }

  private Pageable testNextPage(Pageable nextPage, String expectedProductIds, boolean expectsNextPage) {
    Page<ProductEntity> productPage = repository.findAll(nextPage);
    assertEquals(expectedProductIds, productPage.getContent().stream().map(p -> p.getProductId()).collect(Collectors.toList()).toString());
    assertEquals(expectsNextPage, productPage.hasNext());
    return productPage.nextPageable();
  }

  private void assertEqualsProduct(ProductEntity expectedEntity, ProductEntity actualEntity) {
    assertEquals(expectedEntity.getId(),               actualEntity.getId());
    assertEquals(expectedEntity.getVersion(),          actualEntity.getVersion());
    assertEquals(expectedEntity.getProductId(),        actualEntity.getProductId());
    assertEquals(expectedEntity.getName(),           actualEntity.getName());
    assertEquals(expectedEntity.getWeight(),           actualEntity.getWeight());
  }
}
```

#### `microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-service/src/test/java/se/magnus/microservices/core/product/ProductServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.product;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static reactor.core.publisher.Mono.just;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import se.magnus.api.core.product.Product;
import se.magnus.microservices.core.product.persistence.ProductRepository;

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
class ProductServiceApplicationTests extends MongoDbTestBase {

  @Autowired private WebTestClient client;

  @Autowired private ProductRepository repository;

  @BeforeEach
  void setupDb() {
    repository.deleteAll();
  }

  @Test
  void getProductById() {

    int productId = 1;

    postAndVerifyProduct(productId, OK);

    assertTrue(repository.findByProductId(productId).isPresent());

    getAndVerifyProduct(productId, OK).jsonPath("$.productId").isEqualTo(productId);
  }

  @Test
  void duplicateError() {

    int productId = 1;

    postAndVerifyProduct(productId, OK);

    assertTrue(repository.findByProductId(productId).isPresent());

    postAndVerifyProduct(productId, UNPROCESSABLE_CONTENT)
      .jsonPath("$.path").isEqualTo("/product")
      .jsonPath("$.message").isEqualTo("Duplicate key, Product Id: " + productId);
  }

  @Test
  void deleteProduct() {

    int productId = 1;

    postAndVerifyProduct(productId, OK);
    assertTrue(repository.findByProductId(productId).isPresent());

    deleteAndVerifyProduct(productId, OK);
    assertFalse(repository.findByProductId(productId).isPresent());

    deleteAndVerifyProduct(productId, OK);
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

  private WebTestClient.BodyContentSpec postAndVerifyProduct(int productId, HttpStatus expectedStatus) {
    Product product = new Product(productId, "Name " + productId, productId, "SA");
    return client.post()
      .uri("/product")
      .body(just(product), Product.class)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody();
  }

  private WebTestClient.BodyContentSpec deleteAndVerifyProduct(int productId, HttpStatus expectedStatus) {
    return client.delete()
      .uri("/product/" + productId)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectBody();
  }
}
```

#### `microservices/product-service/src/test/resources/logback-test.xml` — 새 파일 (9줄)

<!-- wb:file path="microservices/product-service/src/test/resources/logback-test.xml" op="write" nl="1" -->
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<configuration>
    <include resource="org/springframework/boot/logging/logback/defaults.xml"/>
    <include resource="org/springframework/boot/logging/logback/console-appender.xml"/>

    <root level="INFO">
        <appender-ref ref="CONSOLE" />
    </root>
</configuration>
```

**중간 확인**

```bash
./gradlew :microservices:product-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-4"></a>

## 단계 4. `recommendation-service`

`product-service`와 같은 구조로 MongoDB 영속성을 추가합니다. `RecommendationEntity`에는 `productId`+`recommendationId` 복합 인덱스가 있습니다.

#### `microservices/recommendation-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -13,6 +13,10 @@
     }
 }
 
+ext {
+    mapstructVersion = '1.6.3'
+}
+
 repositories {
     mavenCentral()
 }
@@ -26,6 +30,12 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'
+    implementation "org.mapstruct:mapstruct:${mapstructVersion}"
+
+    compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
+    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
+    testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
 
     // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
     // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
@@ -33,8 +43,13 @@
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
+
+    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
+    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
+    testImplementation 'org.testcontainers:testcontainers-mongodb'
 }
 
 tasks.named('test') {
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
    implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'
    implementation "org.mapstruct:mapstruct:${mapstructVersion}"

    compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"

    // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
    // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
    implementation group: 'io.netty', name: 'netty-resolver-dns-native-macos', classifier: 'osx-aarch_64'

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
    testImplementation 'org.springframework.boot:spring-boot-starter-data-mongodb-test'
    testImplementation 'io.projectreactor:reactor-test'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'

    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
    testImplementation 'org.testcontainers:testcontainers-mongodb'
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
import org.springframework.data.mongodb.core.MongoOperations;
import org.springframework.data.mongodb.core.index.IndexOperations;
import org.springframework.data.mongodb.core.index.IndexResolver;
import org.springframework.data.mongodb.core.index.MongoPersistentEntityIndexResolver;
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
  MongoOperations mongoTemplate;

  @EventListener(ContextRefreshedEvent.class)
  public void initIndicesAfterStartup() {

    MappingContext<? extends MongoPersistentEntity<?>, MongoPersistentProperty> mappingContext = mongoTemplate.getConverter().getMappingContext();
    IndexResolver resolver = new MongoPersistentEntityIndexResolver(mappingContext);

    IndexOperations indexOps = mongoTemplate.indexOps(RecommendationEntity.class);
    resolver.resolveIndexFor(RecommendationEntity.class).forEach(e -> indexOps.createIndex(e));
  }
}
```

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/persistence/RecommendationEntity.java` — 새 파일 (90줄)

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/persistence/RecommendationEntity.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.persistence;

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

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/persistence/RecommendationRepository.java` — 새 파일 (8줄)

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/persistence/RecommendationRepository.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.persistence;

import java.util.List;
import org.springframework.data.repository.CrudRepository;

public interface RecommendationRepository extends CrudRepository<RecommendationEntity, String> {
  List<RecommendationEntity> findByProductId(int productId);
}
```

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationMapper.java` — 새 파일 (29줄)

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationMapper.java" op="write" nl="0" -->
```java
package se.magnus.microservices.core.recommendation.services;

import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Mappings;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;

@Mapper(componentModel = "spring")
public interface RecommendationMapper {

  @Mappings({
    @Mapping(target = "rate", source = "entity.rating"),
    @Mapping(target = "serviceAddress", ignore = true)
  })
  Recommendation entityToApi(RecommendationEntity entity);

  @Mappings({
    @Mapping(target = "rating", source = "api.rate"),
    @Mapping(target = "id", ignore = true),
    @Mapping(target = "version", ignore = true)
  })
  RecommendationEntity apiToEntity(Recommendation api);

  List<Recommendation> entityListToApiList(List<RecommendationEntity> entity);

  List<RecommendationEntity> apiListToEntityList(List<Recommendation> api);
}
```

#### `microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationServiceImpl.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/main/java/se/magnus/microservices/core/recommendation/services/RecommendationServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation.services;

import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.web.bind.annotation.RestController;
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
  public Recommendation createRecommendation(Recommendation body) {
    try {
      RecommendationEntity entity = mapper.apiToEntity(body);
      RecommendationEntity newEntity = repository.save(entity);

      LOG.debug("createRecommendation: created a recommendation entity: {}/{}", body.getProductId(), body.getRecommendationId());
      return mapper.entityToApi(newEntity);

    } catch (DuplicateKeyException dke) {
      throw new InvalidInputException("Duplicate key, Product Id: " + body.getProductId() + ", Recommendation Id:" + body.getRecommendationId());
    }
  }

  @Override
  public List<Recommendation> getRecommendations(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }
    
    List<RecommendationEntity> entityList = repository.findByProductId(productId);
    List<Recommendation> list = mapper.entityListToApiList(entityList);
    list.forEach(e -> e.setServiceAddress(serviceUtil.getServiceAddress()));

    LOG.debug("getRecommendations: response size: {}", list.size());

    return list;
  }

  @Override
  public void deleteRecommendations(int productId) {
    LOG.debug("deleteRecommendations: tries to delete recommendations for the product with productId: {}", productId);
    repository.deleteAll(repository.findByProductId(productId));
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

logging:
  level:
    root: INFO
    se.magnus: DEBUG
    org.springframework.data.mongodb.core.MongoTemplate: DEBUG

---
spring.config.activate.on-profile: docker

server.port: 8080

spring.mongodb.host: mongodb
```

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MapperTests.java` — 새 파일 (73줄)

<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MapperTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.microservices.core.recommendation.persistence.RecommendationEntity;
import se.magnus.microservices.core.recommendation.services.RecommendationMapper;

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

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MongoDbTestBase.java` — 새 파일 (15줄)

<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/MongoDbTestBase.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.testcontainers.mongodb.MongoDBContainer;

public abstract class MongoDbTestBase {

  @ServiceConnection
  private static MongoDBContainer database = new MongoDBContainer("mongo:8.0.5");

  static {
    database.start();
  }

}
```

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/PersistenceTests.java` — 새 파일 (113줄)

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
    repository.deleteAll();

    RecommendationEntity entity = new RecommendationEntity(1, 2, "a", 3, "c");
    savedEntity = repository.save(entity);

    assertEqualsRecommendation(entity, savedEntity);
  }


  @Test
  void create() {

    RecommendationEntity newEntity = new RecommendationEntity(1, 3, "a", 3, "c");
    repository.save(newEntity);

    RecommendationEntity foundEntity = repository.findById(newEntity.getId()).get();
    assertEqualsRecommendation(newEntity, foundEntity);

    assertEquals(2, repository.count());
  }

  @Test
  void update() {
    savedEntity.setAuthor("a2");
    repository.save(savedEntity);

    RecommendationEntity foundEntity = repository.findById(savedEntity.getId()).get();
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
    List<RecommendationEntity> entityList = repository.findByProductId(savedEntity.getProductId());

    assertThat(entityList, hasSize(1));
    assertEqualsRecommendation(savedEntity, entityList.get(0));
  }

  @Test
  void duplicateError() {
    assertThrows(DuplicateKeyException.class, () -> {
      RecommendationEntity entity = new RecommendationEntity(1, 2, "a", 3, "c");
      repository.save(entity);
    });
  }

  @Test
  void optimisticLockError() {

    // Store the saved entity in two separate entity objects
    RecommendationEntity entity1 = repository.findById(savedEntity.getId()).get();
    RecommendationEntity entity2 = repository.findById(savedEntity.getId()).get();

    // Update the entity using the first entity object
    entity1.setAuthor("a1");
    repository.save(entity1);

    //  Update the entity using the second entity object.
    // This should fail since the second entity now holds an old version number, i.e. an Optimistic Lock Error
    assertThrows(OptimisticLockingFailureException.class, () -> {
      entity2.setAuthor("a2");
      repository.save(entity2);
    });

    // Get the updated entity from the database and verify its new sate
    RecommendationEntity updatedEntity = repository.findById(savedEntity.getId()).get();
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

#### `microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/recommendation-service/src/test/java/se/magnus/microservices/core/recommendation/RecommendationServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.recommendation;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static reactor.core.publisher.Mono.just;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.microservices.core.recommendation.persistence.RecommendationRepository;

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
class RecommendationServiceApplicationTests extends MongoDbTestBase {

  @Autowired
  private WebTestClient client;

  @Autowired
  private RecommendationRepository repository;

  @BeforeEach
  void setupDb() {
    repository.deleteAll();
  }
  
  @Test
  void getRecommendationsByProductId() {

    int productId = 1;

    postAndVerifyRecommendation(productId, 1, OK);
    postAndVerifyRecommendation(productId, 2, OK);
    postAndVerifyRecommendation(productId, 3, OK);

    assertEquals(3, repository.findByProductId(productId).size());

    getAndVerifyRecommendationsByProductId(productId, OK)
      .jsonPath("$.length()").isEqualTo(3)
      .jsonPath("$[2].productId").isEqualTo(productId)
      .jsonPath("$[2].recommendationId").isEqualTo(3);
  }

  @Test
  void duplicateError() {

    int productId = 1;
    int recommendationId = 1;

    postAndVerifyRecommendation(productId, recommendationId, OK)
      .jsonPath("$.productId").isEqualTo(productId)
      .jsonPath("$.recommendationId").isEqualTo(recommendationId);

    assertEquals(1, repository.count());

    postAndVerifyRecommendation(productId, recommendationId, UNPROCESSABLE_CONTENT)
      .jsonPath("$.path").isEqualTo("/recommendation")
      .jsonPath("$.message").isEqualTo("Duplicate key, Product Id: 1, Recommendation Id:1");

    assertEquals(1, repository.count());
  }

  @Test
  void deleteRecommendations() {

    int productId = 1;
    int recommendationId = 1;

    postAndVerifyRecommendation(productId, recommendationId, OK);
    assertEquals(1, repository.findByProductId(productId).size());

    deleteAndVerifyRecommendationsByProductId(productId, OK);
    assertEquals(0, repository.findByProductId(productId).size());

    deleteAndVerifyRecommendationsByProductId(productId, OK);
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

  private WebTestClient.BodyContentSpec postAndVerifyRecommendation(int productId, int recommendationId, HttpStatus expectedStatus) {
    Recommendation recommendation = new Recommendation(productId, recommendationId, "Author " + recommendationId, recommendationId, "Content " + recommendationId, "SA");
    return client.post()
      .uri("/recommendation")
      .body(just(recommendation), Recommendation.class)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody();
  }

  private WebTestClient.BodyContentSpec deleteAndVerifyRecommendationsByProductId(int productId, HttpStatus expectedStatus) {
    return client.delete()
      .uri("/recommendation?productId=" + productId)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectBody();
  }
    
}
```

#### `microservices/recommendation-service/src/test/resources/logback-test.xml` — 새 파일 (`microservices/product-service/src/test/resources/logback-test.xml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/recommendation-service/src/test/resources && cp microservices/product-service/src/test/resources/logback-test.xml microservices/recommendation-service/src/test/resources/logback-test.xml
```

<!-- wb:file path="microservices/recommendation-service/src/test/resources/logback-test.xml" op="cp" src="microservices/product-service/src/test/resources/logback-test.xml" -->

**중간 확인**

```bash
./gradlew :microservices:recommendation-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-5"></a>

## 단계 5. `review-service`

MySQL(JPA)을 씁니다. `ReviewEntity`(`@Entity`, `@Table`), `ReviewRepository`(`CrudRepository`)와 `MySqlTestBase`를 만듭니다. `spring.jpa.hibernate.ddl-auto`로 테이블을 만듭니다.

#### `microservices/review-service/build.gradle` — 수정

`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.

```diff
@@ -13,6 +13,10 @@
     }
 }
 
+ext {
+    mapstructVersion = '1.6.3'
+}
+
 repositories {
     mavenCentral()
 }
@@ -26,6 +30,13 @@
     implementation project(':util')
     implementation 'org.springframework.boot:spring-boot-starter-actuator'
     implementation 'org.springframework.boot:spring-boot-starter-webflux'
+    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
+    implementation 'com.mysql:mysql-connector-j'
+    implementation "org.mapstruct:mapstruct:${mapstructVersion}"
+
+    compileOnly "org.mapstruct:mapstruct-processor:${mapstructVersion}"
+    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
+    testAnnotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
 
     // To avoid the following error message on Apple silicon (for details, see https://github.com/netty/netty/issues/11693):
     // Unable to load io.netty.resolver.dns.macos.MacOSDnsServerAddressStreamProvider, fallback to system defaults. This may result in incorrect DNS resolutions on MacOS.
@@ -33,8 +44,13 @@
 
     testImplementation 'org.springframework.boot:spring-boot-starter-test'
     testImplementation 'org.springframework.boot:spring-boot-starter-webflux-test'
+    testImplementation 'org.springframework.boot:spring-boot-starter-data-jpa-test'
     testImplementation 'io.projectreactor:reactor-test'
     testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
+
+    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
+    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
+    testImplementation 'org.testcontainers:testcontainers-mysql'
 }
 
 tasks.named('test') {
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

tasks.named('test') {
    useJUnitPlatform()
}
```

</details>

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/ReviewServiceApplication.java" op="write" nl="0" -->
```java
package se.magnus.microservices.core.review;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan("se.magnus")
public class ReviewServiceApplication {

  private static final Logger LOG = LoggerFactory.getLogger(ReviewServiceApplication.class);

  public static void main(String[] args) {
    ConfigurableApplicationContext ctx = SpringApplication.run(ReviewServiceApplication.class, args);

    String mysqlUri = ctx.getEnvironment().getProperty("spring.datasource.url");
    LOG.info("Connected to MySQL: " + mysqlUri);
  }
}
```

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/persistence/ReviewEntity.java` — 새 파일 (87줄)

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/persistence/ReviewEntity.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review.persistence;

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

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/persistence/ReviewRepository.java` — 새 파일 (11줄)

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/persistence/ReviewRepository.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review.persistence;

import java.util.List;
import org.springframework.data.repository.CrudRepository;
import org.springframework.transaction.annotation.Transactional;

public interface ReviewRepository extends CrudRepository<ReviewEntity, Integer> {

  @Transactional(readOnly = true)
  List<ReviewEntity> findByProductId(int productId);
}
```

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewMapper.java` — 새 파일 (27줄)

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewMapper.java" op="write" nl="0" -->
```java
package se.magnus.microservices.core.review.services;

import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Mappings;
import se.magnus.api.core.review.Review;
import se.magnus.microservices.core.review.persistence.ReviewEntity;

@Mapper(componentModel = "spring")
public interface ReviewMapper {

  @Mappings({
    @Mapping(target = "serviceAddress", ignore = true)
  })
  Review entityToApi(ReviewEntity entity);

  @Mappings({
    @Mapping(target = "id", ignore = true),
    @Mapping(target = "version", ignore = true)
  })
  ReviewEntity apiToEntity(Review api);

  List<Review> entityListToApiList(List<ReviewEntity> entity);

  List<ReviewEntity> apiListToEntityList(List<Review> api);
}
```

#### `microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewServiceImpl.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/review-service/src/main/java/se/magnus/microservices/core/review/services/ReviewServiceImpl.java" op="write" nl="0" -->
```java
package se.magnus.microservices.core.review.services;

import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.web.bind.annotation.RestController;
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

  public ReviewServiceImpl(ReviewRepository repository, ReviewMapper mapper, ServiceUtil serviceUtil) {
    this.repository = repository;
    this.mapper = mapper;
    this.serviceUtil = serviceUtil;
  }

  @Override
  public Review createReview(Review body) {
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
  public List<Review> getReviews(int productId) {

    if (productId < 1) {
      throw new InvalidInputException("Invalid productId: " + productId);
    }
    
    List<ReviewEntity> entityList = repository.findByProductId(productId);
    List<Review> list = mapper.entityListToApiList(entityList);
    list.forEach(e -> e.setServiceAddress(serviceUtil.getServiceAddress()));

    LOG.debug("getReviews: response size: {}", list.size());

    return list;
  }

  @Override
  public void deleteReviews(int productId) {
    LOG.debug("deleteReviews: tries to delete reviews for the product with productId: {}", productId);
    repository.deleteAll(repository.findByProductId(productId));
  }
}
```

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

logging:
  level:
    root: INFO
    se.magnus: DEBUG
    org.hibernate.SQL: DEBUG
    org.hibernate.type.descriptor.sql.BasicBinder: TRACE

---
spring.config.activate.on-profile: docker

server.port: 8080

spring.datasource:
  url: jdbc:mysql://mysql/review-db
```

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/MapperTests.java` — 새 파일 (74줄)

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/MapperTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;
import se.magnus.api.core.review.Review;
import se.magnus.microservices.core.review.persistence.ReviewEntity;
import se.magnus.microservices.core.review.services.ReviewMapper;


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

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/MySqlTestBase.java` — 새 파일 (17줄)

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/MySqlTestBase.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.testcontainers.containers.JdbcDatabaseContainer;
import org.testcontainers.mysql.MySQLContainer;

public abstract class MySqlTestBase {

  // Extend startup timeout since a MySQLContainer with MySQL 8 starts very slow on Win10/WSL2
  @ServiceConnection
  static final JdbcDatabaseContainer database = new MySQLContainer("mysql:9.2.0").withStartupTimeoutSeconds(300);

  static {
    database.start();
  }

}
```

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/PersistenceTests.java` — 새 파일 (117줄)

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

@DataJpaTest
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

#### `microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/review-service/src/test/java/se/magnus/microservices/core/review/ReviewServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.core.review;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static reactor.core.publisher.Mono.just;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import se.magnus.api.core.review.Review;
import se.magnus.microservices.core.review.persistence.ReviewRepository;

@AutoConfigureWebTestClient
@SpringBootTest(webEnvironment = RANDOM_PORT)
class ReviewServiceApplicationTests extends MySqlTestBase {

  @Autowired
  private WebTestClient client;

  @Autowired
  private ReviewRepository repository;

  @BeforeEach
  void setupDb() {
    repository.deleteAll();
  }

  @Test
  void getReviewsByProductId() {

    int productId = 1;

    assertEquals(0, repository.findByProductId(productId).size());

    postAndVerifyReview(productId, 1, OK);
    postAndVerifyReview(productId, 2, OK);
    postAndVerifyReview(productId, 3, OK);

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

    postAndVerifyReview(productId, reviewId, OK)
      .jsonPath("$.productId").isEqualTo(productId)
      .jsonPath("$.reviewId").isEqualTo(reviewId);

    assertEquals(1, repository.count());

    postAndVerifyReview(productId, reviewId, UNPROCESSABLE_CONTENT)
      .jsonPath("$.path").isEqualTo("/review")
      .jsonPath("$.message").isEqualTo("Duplicate key, Product Id: 1, Review Id:1");

    assertEquals(1, repository.count());
  }

  @Test
  void deleteReviews() {

    int productId = 1;
    int reviewId = 1;

    postAndVerifyReview(productId, reviewId, OK);
    assertEquals(1, repository.findByProductId(productId).size());

    deleteAndVerifyReviewsByProductId(productId, OK);
    assertEquals(0, repository.findByProductId(productId).size());

    deleteAndVerifyReviewsByProductId(productId, OK);
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

  private WebTestClient.BodyContentSpec postAndVerifyReview(int productId, int reviewId, HttpStatus expectedStatus) {
    Review review = new Review(productId, reviewId, "Author " + reviewId, "Subject " + reviewId, "Content " + reviewId, "SA");
    return client.post()
      .uri("/review")
      .body(just(review), Review.class)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectHeader().contentType(APPLICATION_JSON)
      .expectBody();
  }

  private WebTestClient.BodyContentSpec deleteAndVerifyReviewsByProductId(int productId, HttpStatus expectedStatus) {
    return client.delete()
      .uri("/review?productId=" + productId)
      .accept(APPLICATION_JSON)
      .exchange()
      .expectStatus().isEqualTo(expectedStatus)
      .expectBody();
  }
}
```

#### `microservices/review-service/src/test/resources/logback-test.xml` — 새 파일 (`microservices/product-service/src/test/resources/logback-test.xml`와 같은 내용)

앞에서 만든 파일과 내용이 똑같으니 복사합니다.

```bash
mkdir -p microservices/review-service/src/test/resources && cp microservices/product-service/src/test/resources/logback-test.xml microservices/review-service/src/test/resources/logback-test.xml
```

<!-- wb:file path="microservices/review-service/src/test/resources/logback-test.xml" op="cp" src="microservices/product-service/src/test/resources/logback-test.xml" -->

**중간 확인**

```bash
./gradlew :microservices:review-service:build -x test   # 컴파일만 먼저 확인
```

<a id="단계-6"></a>

## 단계 6. `product-composite-service`

통합 클래스에 핵심 서비스의 생성·삭제 호출을 추가하고, 복합 서비스에 `createProduct`, `deleteProduct`를 구현합니다.

#### `microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeIntegration.java` — 전체를 다음 내용으로 바꿉니다

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

    productServiceUrl = "http://" + productServiceHost + ":" + productServicePort + "/product";
    recommendationServiceUrl = "http://" + recommendationServiceHost + ":" + recommendationServicePort + "/recommendation";
    reviewServiceUrl = "http://" + reviewServiceHost + ":" + reviewServicePort + "/review";
  }

  @Override
  public Product createProduct(Product body) {

    try {
      String url = productServiceUrl;
      LOG.debug("Will post a new product to URL: {}", url);

      Product product = restTemplate.postForObject(url, body, Product.class);
      LOG.debug("Created a product with id: {}", product.getProductId());

      return product;

    } catch (HttpClientErrorException ex) {
      throw handleHttpClientException(ex);
    }
  }

  @Override
  public Product getProduct(int productId) {

    try {
      String url = productServiceUrl + "/" + productId;
      LOG.debug("Will call the getProduct API on URL: {}", url);

      Product product = restTemplate.getForObject(url, Product.class);
      LOG.debug("Found a product with id: {}", product.getProductId());

      return product;

    } catch (HttpClientErrorException ex) {
      throw handleHttpClientException(ex);
    }
  }

  @Override
  public void deleteProduct(int productId) {
    try {
      String url = productServiceUrl + "/" + productId;
      LOG.debug("Will call the deleteProduct API on URL: {}", url);

      restTemplate.delete(url);

    } catch (HttpClientErrorException ex) {
      throw handleHttpClientException(ex);
    }
  }

  @Override
  public Recommendation createRecommendation(Recommendation body) {

    try {
      String url = recommendationServiceUrl;
      LOG.debug("Will post a new recommendation to URL: {}", url);

      Recommendation recommendation = restTemplate.postForObject(url, body, Recommendation.class);
      LOG.debug("Created a recommendation with id: {}", recommendation.getProductId());

      return recommendation;

    } catch (HttpClientErrorException ex) {
      throw handleHttpClientException(ex);
    }
  }

  @Override
  public List<Recommendation> getRecommendations(int productId) {

    try {
      String url = recommendationServiceUrl + "?productId=" + productId;

      LOG.debug("Will call the getRecommendations API on URL: {}", url);
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
  public void deleteRecommendations(int productId) {
    try {
      String url = recommendationServiceUrl + "?productId=" + productId;
      LOG.debug("Will call the deleteRecommendations API on URL: {}", url);

      restTemplate.delete(url);

    } catch (HttpClientErrorException ex) {
      throw handleHttpClientException(ex);
    }
  }

  @Override
  public Review createReview(Review body) {

    try {
      String url = reviewServiceUrl;
      LOG.debug("Will post a new review to URL: {}", url);

      Review review = restTemplate.postForObject(url, body, Review.class);
      LOG.debug("Created a review with id: {}", review.getProductId());

      return review;

    } catch (HttpClientErrorException ex) {
      throw handleHttpClientException(ex);
    }
  }

  @Override
  public List<Review> getReviews(int productId) {

    try {
      String url = reviewServiceUrl + "?productId=" + productId;

      LOG.debug("Will call the getReviews API on URL: {}", url);
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

  @Override
  public void deleteReviews(int productId) {
    try {
      String url = reviewServiceUrl + "?productId=" + productId;
      LOG.debug("Will call the deleteReviews API on URL: {}", url);

      restTemplate.delete(url);

    } catch (HttpClientErrorException ex) {
      throw handleHttpClientException(ex);
    }
  }

  private RuntimeException handleHttpClientException(HttpClientErrorException ex) {
    switch (HttpStatus.resolve(ex.getStatusCode().value())) {

      case NOT_FOUND:
        return new NotFoundException(getErrorMessage(ex));

      case UNPROCESSABLE_CONTENT:
        return new InvalidInputException(getErrorMessage(ex));

      default:
        LOG.warn("Got an unexpected HTTP error: {}, will rethrow it", ex.getStatusCode());
        LOG.warn("Error body: {}", ex.getResponseBodyAsString());
        return ex;
    }
  }

  private String getErrorMessage(HttpClientErrorException ex) {
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
@@ -2,6 +2,8 @@
 
 import java.util.List;
 import java.util.stream.Collectors;
+import org.slf4j.Logger;
+import org.slf4j.LoggerFactory;
 import org.springframework.web.bind.annotation.RestController;
 import se.magnus.api.composite.product.*;
 import se.magnus.api.core.product.Product;
@@ -12,6 +14,8 @@
 
 @RestController
 public class ProductCompositeServiceImpl implements ProductCompositeService {
+
+  private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeServiceImpl.class);
 
   private final ServiceUtil serviceUtil;
   private ProductCompositeIntegration integration;
@@ -24,7 +28,42 @@
   }
 
   @Override
+  public void createProduct(ProductAggregate body) {
+
+    try {
+
+      LOG.debug("createCompositeProduct: creates a new composite entity for productId: {}", body.getProductId());
+
+      Product product = new Product(body.getProductId(), body.getName(), body.getWeight(), null);
+      integration.createProduct(product);
+
+      if (body.getRecommendations() != null) {
+        body.getRecommendations().forEach(r -> {
+          Recommendation recommendation = new Recommendation(body.getProductId(), r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent(), null);
+          integration.createRecommendation(recommendation);
+        });
+      }
+
+      if (body.getReviews() != null) {
+        body.getReviews().forEach(r -> {
+          Review review = new Review(body.getProductId(), r.getReviewId(), r.getAuthor(), r.getSubject(), r.getContent(), null);
+          integration.createReview(review);
+        });
+      }
+
+      LOG.debug("createCompositeProduct: composite entities created for productId: {}", body.getProductId());
+
+    } catch (RuntimeException re) {
+      LOG.warn("createCompositeProduct failed", re);
+      throw re;
+    }
+  }
+
+
+  @Override
   public ProductAggregate getProduct(int productId) {
+
+    LOG.debug("getCompositeProduct: lookup a product aggregate for productId: {}", productId);
 
     Product product = integration.getProduct(productId);
     if (product == null) {
@@ -35,7 +74,23 @@
 
     List<Review> reviews = integration.getReviews(productId);
 
+    LOG.debug("getCompositeProduct: aggregate entity found for productId: {}", productId);
+
     return createProductAggregate(product, recommendations, reviews, serviceUtil.getServiceAddress());
+  }
+
+  @Override
+  public void deleteProduct(int productId) {
+
+    LOG.debug("deleteCompositeProduct: Deletes a product aggregate for productId: {}", productId);
+
+    integration.deleteProduct(productId);
+
+    integration.deleteRecommendations(productId);
+
+    integration.deleteReviews(productId);
+
+    LOG.debug("deleteCompositeProduct: aggregate entities deleted for productId: {}", productId);
   }
 
   private ProductAggregate createProductAggregate(
@@ -50,15 +105,15 @@
     int weight = product.getWeight();
 
     // 2. Copy summary recommendation info, if available
-    List<RecommendationSummary> recommendationSummaries =
-      (recommendations == null) ? null : recommendations.stream()
-        .map(r -> new RecommendationSummary(r.getRecommendationId(), r.getAuthor(), r.getRate()))
+    List<RecommendationSummary> recommendationSummaries = (recommendations == null) ? null :
+      recommendations.stream()
+        .map(r -> new RecommendationSummary(r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent()))
         .collect(Collectors.toList());
 
     // 3. Copy summary review info, if available
-    List<ReviewSummary> reviewSummaries = 
-      (reviews == null) ? null : reviews.stream()
-        .map(r -> new ReviewSummary(r.getReviewId(), r.getAuthor(), r.getSubject()))
+    List<ReviewSummary> reviewSummaries = (reviews == null) ? null :
+      reviews.stream()
+        .map(r -> new ReviewSummary(r.getReviewId(), r.getAuthor(), r.getSubject(), r.getContent()))
         .collect(Collectors.toList());
 
     // 4. Create info regarding the involved microservices addresses
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/main/java/se/magnus/microservices/composite/product/services/ProductCompositeServiceImpl.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product.services;

import java.util.List;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.RestController;
import se.magnus.api.composite.product.*;
import se.magnus.api.core.product.Product;
import se.magnus.api.core.recommendation.Recommendation;
import se.magnus.api.core.review.Review;
import se.magnus.api.exceptions.NotFoundException;
import se.magnus.util.http.ServiceUtil;

@RestController
public class ProductCompositeServiceImpl implements ProductCompositeService {

  private static final Logger LOG = LoggerFactory.getLogger(ProductCompositeServiceImpl.class);

  private final ServiceUtil serviceUtil;
  private ProductCompositeIntegration integration;

  public ProductCompositeServiceImpl(
    ServiceUtil serviceUtil, ProductCompositeIntegration integration) {
    
    this.serviceUtil = serviceUtil;
    this.integration = integration;
  }

  @Override
  public void createProduct(ProductAggregate body) {

    try {

      LOG.debug("createCompositeProduct: creates a new composite entity for productId: {}", body.getProductId());

      Product product = new Product(body.getProductId(), body.getName(), body.getWeight(), null);
      integration.createProduct(product);

      if (body.getRecommendations() != null) {
        body.getRecommendations().forEach(r -> {
          Recommendation recommendation = new Recommendation(body.getProductId(), r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent(), null);
          integration.createRecommendation(recommendation);
        });
      }

      if (body.getReviews() != null) {
        body.getReviews().forEach(r -> {
          Review review = new Review(body.getProductId(), r.getReviewId(), r.getAuthor(), r.getSubject(), r.getContent(), null);
          integration.createReview(review);
        });
      }

      LOG.debug("createCompositeProduct: composite entities created for productId: {}", body.getProductId());

    } catch (RuntimeException re) {
      LOG.warn("createCompositeProduct failed", re);
      throw re;
    }
  }


  @Override
  public ProductAggregate getProduct(int productId) {

    LOG.debug("getCompositeProduct: lookup a product aggregate for productId: {}", productId);

    Product product = integration.getProduct(productId);
    if (product == null) {
      throw new NotFoundException("No product found for productId: " + productId);
    }

    List<Recommendation> recommendations = integration.getRecommendations(productId);

    List<Review> reviews = integration.getReviews(productId);

    LOG.debug("getCompositeProduct: aggregate entity found for productId: {}", productId);

    return createProductAggregate(product, recommendations, reviews, serviceUtil.getServiceAddress());
  }

  @Override
  public void deleteProduct(int productId) {

    LOG.debug("deleteCompositeProduct: Deletes a product aggregate for productId: {}", productId);

    integration.deleteProduct(productId);

    integration.deleteRecommendations(productId);

    integration.deleteReviews(productId);

    LOG.debug("deleteCompositeProduct: aggregate entities deleted for productId: {}", productId);
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
    List<RecommendationSummary> recommendationSummaries = (recommendations == null) ? null :
      recommendations.stream()
        .map(r -> new RecommendationSummary(r.getRecommendationId(), r.getAuthor(), r.getRate(), r.getContent()))
        .collect(Collectors.toList());

    // 3. Copy summary review info, if available
    List<ReviewSummary> reviewSummaries = (reviews == null) ? null :
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
@@ -34,28 +34,33 @@
       notes: |
         # Normal response
         If the requested product id is found the method will return information regarding:
-        1. Base product information
+        1. Product information
         1. Reviews
         1. Recommendations
         1. Service Addresses\n(technical information regarding the addresses of the microservices that created the response)
 
         # Expected partial and error responses
-        In the following cases, only a partial response be created (used to simplify testing of error conditions)
+        1. If no product information is found, a **404 - Not Found** error will be returned
+        1. In no recommendations or reviews are found for a product, a partial response will be returned
 
-        ## Product id 113
-        200 - Ok, but no recommendations will be returned
+    create-composite-product:
+      description: Creates a composite product
+      notes: |
+        # Normal response
+        The composite product information posted to the API will be split up and stored as separate product-info, recommendation and review entities.
 
-        ## Product id 213
-        200 - Ok, but no reviews will be returned
+        # Expected error responses
+        1. If a product with the same productId as specified in the posted information already exists,
+           an **422 - Unprocessable Entity** error with a "duplicate key" error message will be returned
 
-        ## Non numerical product id
-        400 - A **Bad Request** error will be returned
+    delete-composite-product:
+      description: Deletes a product composite
+      notes: |
+        # Normal response
+        Entities for product information, recommendations and reviews related to the specified productId will be deleted.
+        The implementation of the delete method is idempotent, i.e. it can be called several times with the same response.
 
-        ## Product id 13
-        404 - A **Not Found** error will be returned
-
-        ## Negative product ids
-        422 - An **Unprocessable Entity** error will be returned
+        This means that a delete request of a non-existing product will return **200 Ok**.
 
 server.port: 7001
 spring.web.error.include-message: always
```

<details><summary>완성된 파일 전체 보기</summary>

<!-- wb:file path="microservices/product-composite-service/src/main/resources/application.yml" op="write" nl="0" -->
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

#### `microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java` — 전체를 다음 내용으로 바꿉니다

<!-- wb:file path="microservices/product-composite-service/src/test/java/se/magnus/microservices/composite/product/ProductCompositeServiceApplicationTests.java" op="write" nl="1" -->
```java
package se.magnus.microservices.composite.product;

import static java.util.Collections.singletonList;
import static org.mockito.Mockito.when;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;
import static org.springframework.http.HttpStatus.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static reactor.core.publisher.Mono.just;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.reactive.server.WebTestClient;
import se.magnus.api.composite.product.ProductAggregate;
import se.magnus.api.composite.product.RecommendationSummary;
import se.magnus.api.composite.product.ReviewSummary;
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
  void createCompositeProduct1() {

    ProductAggregate compositeProduct = new ProductAggregate(1, "name", 1, null, null, null);

    postAndVerifyProduct(compositeProduct, OK);
  }

  @Test
  void createCompositeProduct2() {
    ProductAggregate compositeProduct = new ProductAggregate(1, "name", 1,
      singletonList(new RecommendationSummary(1, "a", 1, "c")),
      singletonList(new ReviewSummary(1, "a", "s", "c")), null);

    postAndVerifyProduct(compositeProduct, OK);
  }

  @Test
  void deleteCompositeProduct() {
    ProductAggregate compositeProduct = new ProductAggregate(1, "name", 1,
      singletonList(new RecommendationSummary(1, "a", 1, "c")),
      singletonList(new ReviewSummary(1, "a", "s", "c")), null);

    postAndVerifyProduct(compositeProduct, OK);

    deleteAndVerifyProduct(compositeProduct.getProductId(), OK);
    deleteAndVerifyProduct(compositeProduct.getProductId(), OK);
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

**중간 확인**

```bash
./gradlew :microservices:product-composite-service:build -x test   # 컴파일만 먼저 확인
```

## 확인하기

**도커 컴포즈로 실행** (RabbitMQ)

```bash
cd ~/my-work/Chapter06
./gradlew build
docker compose build
./test-em-all.bash start stop
```

테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):

```bash
diff -r --exclude=build --exclude=.gradle . <저장소>/Chapter06
```

---

← [5장 워크북](Chapter05.md) · [워크북 목차](README.md) · [7장 워크북](Chapter07.md) →
