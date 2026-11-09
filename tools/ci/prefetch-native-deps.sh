#!/usr/bin/env bash
# Pre-download the GraalVM distribution (BellSoft Liberica NIK) that the Paketo
# buildpack needs for native images, with retries and resume, and hand it to the
# buildpack through a Paketo "dependency-mapping" binding.
#
# Why: the buildpack downloads a ~350 MB file from GitHub releases inside the
# builder container without retries, and on GitHub-hosted runners this download
# sometimes fails for hours. Downloading it here first makes the build reliable.
#
# Usage: tools/ci/prefetch-native-deps.sh <binding-dir>
#   Then build with NIK_BINDING_DIR=<binding-dir> and the init script
#   tools/ci/native-binding.init.gradle.
# If anything goes wrong, the script leaves the binding dir empty and exits 0,
# so the build falls back to the buildpack's own download.
set -uo pipefail

OUT=${1:?usage: $0 <binding-dir>}
BUILDER=${BUILDER:-paketobuildpacks/builder-noble-java-tiny:latest}
JVM=${BP_JVM_VERSION:-25}
case "$(uname -m)" in aarch64|arm64) ARCH=arm64 ;; *) ARCH=amd64 ;; esac

fail() { echo "::warning::prefetch-native-deps: $*; falling back to the buildpack download"; rm -rf "$OUT"; exit 0; }

docker pull -q "$BUILDER" >/dev/null || fail "cannot pull $BUILDER"
BP_VER=$(docker image inspect "$BUILDER" -f '{{index .Config.Labels "io.buildpacks.builder.metadata"}}' \
  | jq -r '.buildpacks[] | select(.id=="paketo-buildpacks/bellsoft-liberica") | .version' | head -1)
[ -n "$BP_VER" ] || fail "bellsoft-liberica buildpack not found in $BUILDER"

TOML=$(curl -fsSL --retry 5 --retry-all-errors \
  "https://raw.githubusercontent.com/paketo-buildpacks/bellsoft-liberica/v${BP_VER}/buildpack.toml") \
  || fail "cannot read buildpack.toml v${BP_VER}"

read -r URI SHA < <(python3 -c '
import sys, tomllib
jvm, arch = sys.argv[1], sys.argv[2]
deps = tomllib.loads(sys.stdin.read())["metadata"]["dependencies"]
for d in deps:
    if d["id"] == "native-image-svm" and d["version"].split(".")[0] == jvm and f"arch={arch}" in d.get("purl", ""):
        print(d["uri"], d["sha256"]); break
' "$JVM" "$ARCH" <<<"$TOML") || true
[ -n "${URI:-}" ] && [ -n "${SHA:-}" ] || fail "no NIK $JVM ($ARCH) in bellsoft-liberica v${BP_VER}"

mkdir -p "$OUT"
FILE=$(basename "$URI")
echo "bellsoft-liberica v${BP_VER}: downloading $FILE"
for i in 1 2 3 4 5 6; do
  curl -fL --retry 10 --retry-all-errors --retry-delay 10 -C - -o "$OUT/$FILE" "$URI" \
    && echo "$SHA  $OUT/$FILE" | sha256sum -c --quiet && break
  echo "download attempt $i failed, retrying in 30s"; rm -f "$OUT/$FILE"; sleep 30
done
echo "$SHA  $OUT/$FILE" | sha256sum -c --quiet || fail "download of $FILE failed"

echo -n "dependency-mapping" > "$OUT/type"
echo -n "file:///platform/bindings/native-deps/$FILE" > "$OUT/$SHA"
chmod -R a+rX "$OUT"
echo "binding ready: $OUT (sha256 $SHA)"
