# 23장 교재 대응 가이드 — 네이티브 컴파일 자바 마이크로서비스

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 23 "Native-Compiled Java Microservices" (p.621–650)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

Spring AOT와 GraalVM 네이티브 이미지라는 주제와 실습 순서는 책과 같습니다. 하지만 버전이 크게 바뀌어 **Spring Boot 4는 GraalVM 25 이상**이 필요하고, 빌드 플러그인·빌더·네이티브 힌트가 달라졌습니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Introducing GraalVM / Spring AOT (p.623–626) | GraalVM 22.3 시절 설명 | 개념은 같습니다. 이 저장소는 **GraalVM 25**로 컴파일합니다 |
| Cloud Native Buildpacks (p.626) | Apple Silicon용 `dashaun/builder:tiny` 빌더 | 별도 빌더를 지정하지 않고 Spring Boot 기본 빌더를 씁니다. `bootBuildImage`에 `BP_NATIVE_IMAGE=true`, **`BP_JVM_VERSION=25`**를 넘깁니다(CI는 amd64에서 검증) |
| 빌드 파일 (p.629) | `org.graalvm.buildtools.native` 0.9.18, Boot 3.0.5, springdoc 2.1.0 | **0.11.5**, Boot 4.0.9, springdoc 3.0.3 |
| 네이티브 힌트 (p.630) | Resilience4j 애스펙트(`CircuitBreakerAspect`, `RetryAspect`, `TimeLimiterAspect`) 리플렉션 등록 | 이 저장소 구성에서는 필요 없었습니다(CI 네이티브 테스트 통과). 대신 `NativeHintsConfiguration`에 Jackson 3, springdoc, MongoDB 관련 힌트가 있습니다 |
| 트레이싱 에이전트 (p.633–634) | `jvmArgs "-agentlib:native-image-agent=..."` | `build.gradle`에 같은 줄이 주석으로 들어 있습니다. 필요할 때 주석을 풀어 쓰세요 |
| GraalVM 설치 (p.635–636) | `sdk install java 22.3.1.r17-grl` | `bootBuildImage`만 쓴다면 설치할 필요가 없습니다(빌드팩이 GraalVM 25를 사용). 로컬에서 `nativeCompile`·`nativeTest`를 하려면 `sdk list java`에서 **25.x의 `-graalce` 식별자**를 골라 설치하세요 |
| nativeTest·nativeCompile (p.637–639) | 로컬 GraalVM으로 실행 | 같은 Gradle 작업입니다. 이 두 작업은 CI에서 검증하지 않았습니다 |
| Creating Docker images (p.639–640) | `./gradlew :microservices:product-service:bootBuildImage --no-daemon` 등 | 같습니다. 이미지 이름도 `hands-on/native-*`로 같습니다 |
| JVM에서 AOT 모드 (p.643–644) | Dockerfile의 `ENTRYPOINT ["java", "-Dspring.aot.enabled=true", "org.springframework.boot.loader.JarLauncher"]` | 저장소 Dockerfile은 `-Dspring.aot.enabled=false`와 `org.springframework.boot.loader.launch.JarLauncher`입니다. 실습할 때 `false`를 `true`로 바꾸세요 |
| Testing with Docker Compose (p.640–645) | `export COMPOSE_FILE=docker-compose-native.yml`, `docker-compose ...` | 같은 파일을 `docker compose`로 씁니다. 파티션 구성은 `docker-compose-partitions-native.yml` |
| Testing with Kubernetes (p.646–649) | `docker save`/`docker load`, `dev-env-native` 환경 | 같습니다. CI의 쿠버네티스 테스트는 JVM 이미지(`dev-env`)로만 했고, `dev-env-native` 배포는 검증하지 않았습니다 |

## 더 보기

- 위키: [23장 네이티브 컴파일 자바 마이크로서비스](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/23장-네이티브-컴파일-자바-마이크로서비스)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter23)
- 학습 이슈: [#23](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/23)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
