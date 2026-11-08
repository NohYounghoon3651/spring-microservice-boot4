# 21장 교재 대응 가이드 — macOS 설치 안내

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 21 "Installation Instructions for macOS" (p.599–608)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

## 요약

macOS에 실습 도구를 설치하는 장입니다. 설치 방법(Homebrew, 공식 설치 스크립트)은 대체로 그대로 쓸 수 있지만, **도구 버전은 이 저장소에 맞게 바꿔서** 설치하세요. macOS 환경은 CI에서 직접 검증하지 않았습니다.

## 버전 대응

| 도구 | 교재 (p.600) | 이 저장소 |
|---|---|---|
| Java | 17.0.6 | **21** (Temurin 권장) |
| Spring Boot CLI | 3.0.4 | **4.0.x** (`spring init`으로 3장 골격을 만들 때만 필요) |
| Docker Desktop | 4.12.0 | 최신. Docker Compose v2(`docker compose`) 포함 |
| Git, curl, jq | 책의 버전 | 최신 |
| Helm | 3.11.1 | 3.x 최신 |
| kubectl | 1.26.1 | minikube가 만드는 클러스터 버전과 맞춰 최신 |
| minikube | 1.29.0 | 최신 (CI 검증 1.39.0) |
| istioctl | 1.17.0 | **1.31.4** |
| Siege | 4.1.6 | 최신 |

## 절별 대응

| 교재 위치 | 교재 | 바꿔 쓸 것 |
|---|---|---|
| Installing tools (p.599–606) | 버전을 박아 넣은 kubectl·minikube 내려받기 URL (`v1.26.1`, `v1.29.0`) | 각 프로젝트 문서의 최신 설치 명령을 쓰세요. Homebrew를 쓴다면 `brew install kubectl minikube helm`처럼 버전 없이 설치해도 됩니다 |
| istioctl 설치 (p.602) | `ISTIO_VERSION=1.17.0` | **`ISTIO_VERSION=1.31.4`**. Apple Silicon은 책처럼 `TARGET_ARCH=arm64`를 붙입니다 |
| Java 설치 | Java 17 | Java **21** |
| Accessing the source code (p.606–608) | 책의 원본 저장소를 `git clone` | 이 저장소를 클론합니다: `git clone https://github.com/NohYounghoon3651/spring-microservice-boot4.git` |
| 버전 확인 (p.607) | Spring Framework 6.0.6, Spring Boot 3.0.4, Spring Cloud 2022.0.1 | Spring Framework 7.0, Spring Boot 4.0.9, Spring Cloud 2025.1.4 |

## 참고

- 설치 없이 실습하려면 GitHub Codespaces를 쓸 수 있습니다(위키 "Codespaces와 컨테이너 이미지").

## 더 보기

- 위키: [21장 macOS 설치 안내](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/21장-macOS-설치-안내)
- 학습 이슈: [#21](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/21)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
