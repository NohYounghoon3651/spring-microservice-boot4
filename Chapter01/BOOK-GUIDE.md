# 1장 교재 대응 가이드 — 마이크로서비스 소개

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 1 "Introduction to Microservices" (p.1–26)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

## 요약

개념 설명 장이라 예제 코드가 없고, 마이크로서비스의 정의·어려움·설계 패턴에 대한 설명은 지금도 그대로 유효합니다. 이 장에서 바꿔 읽을 것은 없습니다.

## 책 전체의 버전 대응표

이 장을 읽기 전에 책 전체에서 쓰는 버전이 이 저장소에서 어떻게 바뀌었는지 한 번 훑어 두면 이후 장을 읽기 편합니다.

| 항목 | 교재(영문 3판) | 이 저장소 |
|---|---|---|
| Java | 17 | **21** |
| Spring Boot | 3.0.4 (23장은 3.0.5) | **4.0.9** |
| Spring Framework | 6.0.6 | **7.0** (Boot 4.0.9가 관리) |
| Spring Cloud | 2022.0.1 | **2025.1.4** |
| springdoc-openapi | 2.0.2 (23장은 2.1.0) | **3.0.3** |
| Resilience4j | 2.0.2 | **2.4.0** (`resilience4j-spring-boot4`) |
| MapStruct | 1.5.3.Final | **1.6.3** |
| Testcontainers | 1.15.2 (BOM) | **2.0** (Boot가 관리) |
| Jackson | 2.x (`com.fasterxml.jackson`) | **3.x** (`tools.jackson`) |
| MySQL / MongoDB | 8.0.32 / 6.0.4 | **9.2.0 / 8.0.5** |
| RabbitMQ / Kafka(Confluent) | 3.11.8 / 7.3.1 | **4.0.7 / 7.9.0** |
| Zipkin | 2.24.0 | **3.5.0** |
| Elasticsearch / Kibana | 7.17.10 | **7.17.28** |
| Kubernetes / minikube | 1.26.1 / 1.29.0 | CI 검증: **1.37.0 / 1.39.0** |
| Istio | 1.17.0 | **1.31.4** |
| cert-manager | 1.11.0 | CI 검증: **1.21.3** |
| GraalVM (23장) | 22.3.1 for Java 17 | **25** (빌드팩이 사용) |
| Docker Compose 명령 | `docker-compose` | **`docker compose`** |

장별 세부 차이는 각 장 폴더의 `BOOK-GUIDE.md`에 있습니다.

## 더 보기

- 위키: [1장 마이크로서비스 소개](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/01장-마이크로서비스-소개)
- 학습 이슈: [#1](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/1)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
