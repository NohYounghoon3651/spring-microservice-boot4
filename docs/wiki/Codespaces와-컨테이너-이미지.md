# Codespaces와 컨테이너 이미지

## GitHub Codespaces로 바로 실습하기

설치 없이 브라우저에서 실습할 수 있습니다.

1. 저장소에서 **Code → Codespaces → Create codespace on main**을 누릅니다.
2. 4코어·16GB 이상 머신을 고릅니다(도커 컴포즈로 전체 시스템을 띄우려면 필요).
3. 터미널에서 장별 실습을 실행합니다.

```bash
cd Chapter13
./gradlew build
docker compose build
./test-em-all.bash start stop
```

개발 컨테이너(`.devcontainer/devcontainer.json`)에는 JDK 21, Docker(Docker-in-Docker), kubectl, Helm, minikube, jq가 들어 있습니다. 같은 환경이 CI(`devcontainer.yml`)에서도 빌드되어 4장 빌드까지 확인됩니다. 이스티오 장(18장 이후)은 메모리가 많이 필요하므로 로컬 환경을 권장합니다.

## 미리 빌드된 이미지 사용하기

릴리스가 나올 때마다 장별 서비스 이미지가 GitHub Container Registry에 올라갑니다. 태그는 릴리스 버전(예: `1.0.2`)과 가장 최근 릴리스를 가리키는 `latest`입니다. 버전 목록은 [릴리스](https://github.com/NohYounghoon3651/spring-microservice-boot4/releases)에서 볼 수 있습니다.

```text
ghcr.io/nohyounghoon3651/spring-microservice-boot4/ch13-product-service:latest
ghcr.io/nohyounghoon3651/spring-microservice-boot4/ch13-product-composite-service:latest
…
```

빌드를 건너뛰고 싶다면 이미지를 받아 교재의 이미지 이름(`hands-on/…`)으로 태그를 붙인 뒤 실행합니다.

```bash
cd Chapter13
CH=ch13
VER=latest   # 특정 버전은 VER=1.0.2처럼
REPO=ghcr.io/nohyounghoon3651/spring-microservice-boot4
for img in $(docker compose config --images | grep '^hands-on/'); do
  name=${img#hands-on/}
  docker pull $REPO/$CH-$name:$VER && docker tag $REPO/$CH-$name:$VER $img
done
./test-em-all.bash start stop
```
