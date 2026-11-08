# 22장 교재 대응 가이드 — WSL 2와 우분투를 사용한 윈도우 설치 안내

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 22 "Installation Instructions for Microsoft Windows with WSL 2 and Ubuntu" (p.609–620)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

## 요약

윈도우에서 WSL 2와 우분투로 실습 환경을 만드는 장입니다. WSL 2·Windows Terminal·VS Code·Docker Desktop 설정 절차는 대체로 그대로 쓸 수 있고, **도구 버전은 이 저장소에 맞게 바꿔서** 설치하세요. 이 환경은 CI에서 직접 검증하지 않았습니다(CI는 우분투에서 실행되므로 WSL 안의 우분투 명령과는 가깝습니다).

## 버전 대응

| 도구 | 교재 (p.610–611) | 이 저장소 |
|---|---|---|
| Ubuntu (WSL 2) | 22.04 | 22.04 또는 24.04 |
| Java | 17.0.6 | **21** (Temurin 권장) |
| Spring Boot CLI | 3.0.4 | **4.0.x** |
| Docker Desktop for Windows | 4.14.0 | 최신. Docker Compose v2(`docker compose`) 포함 |
| Helm | 3.11.2 | 3.x 최신 |
| kubectl | 1.26.1 | 최신 |
| minikube | 1.29.1 | 최신 (CI 검증 1.39.0) |
| istioctl | 1.17.0 | **1.31.4** |
| Siege | 4.0.7 | 최신 |

## 절별 대응

| 교재 위치 | 교재 | 바꿔 쓸 것 |
|---|---|---|
| SDKMAN으로 Java 설치 (p.615) | `sdk install java 17.0.6-tem` | `sdk list java`에서 **21.x의 `-tem` 식별자**를 확인해 `sdk install java <식별자>`로 설치 |
| SDKMAN으로 Spring Boot CLI 설치 (p.615) | `sdk install springboot 3.0.4` | `sdk install springboot` (최신 4.0.x) |
| kubectl·minikube 설치 (p.616) | 버전을 박아 넣은 내려받기 URL | 각 프로젝트 문서의 최신 리눅스 설치 명령 |
| istioctl 설치 (p.616) | `ISTIO_VERSION=1.17.0` | **`ISTIO_VERSION=1.31.4`** |
| Accessing the source code (p.617–619) | 책의 원본 저장소를 클론 | `git clone https://github.com/NohYounghoon3651/spring-microservice-boot4.git` |
| 버전 확인 (p.618) | Spring Framework 6.0.6, Spring Boot 3.0.4, Spring Cloud 2022.0.1 | Spring Framework 7.0, Spring Boot 4.0.9, Spring Cloud 2025.1.4 |

## 참고

- `/etc/hosts`를 바꾸는 실습(10·17·18장)에서는 책 설명대로 윈도우의 hosts 파일도 함께 고쳐야 할 수 있습니다.

## 더 보기

- 위키: [22장 WSL 2와 우분투를 사용한 윈도우 설치 안내](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/22장-WSL-2와-우분투를-사용한-윈도우-설치-안내)
- 학습 이슈: [#22](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/22)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
