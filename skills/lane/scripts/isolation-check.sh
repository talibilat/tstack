#!/usr/bin/env bash
# Proves lanes are isolated: every lane network holds only that lane's containers plus the base stack's
# shared services, and the names each lane uses resolve to its own containers. Exit 1 on any leak.
set -uo pipefail
fail=0
lanes=$(docker ps --format '{{.Label "com.docker.compose.project"}}' | grep -E '^lane-[0-9]+$' | sort -u)
[ -n "$lanes" ] || { echo "no running lanes"; exit 0; }
for p in $lanes; do
  for net in $(docker network ls --filter "label=com.docker.compose.project=$p" --format '{{.Name}}'); do
    for c in $(docker network inspect "$net" --format '{{range .Containers}}{{.Name}} {{end}}'); do
      proj=$(docker inspect "$c" --format '{{index .Config.Labels "com.docker.compose.project"}}')
      svc=$(docker inspect "$c" --format '{{index .Config.Labels "com.docker.compose.service"}}')
      if [ "$proj" != "$p" ] && ! [[ "$svc" =~ ^(doc-parser-lb|content-extractor-lb|presidio-analyzer|presidio-anonymizer|presidio-image-redactor)$ ]]; then
        echo "LEAK  $net holds $c from $proj"; fail=1
      fi
    done
  done
  for client in api frontend ai-backend; do
    cid=$(docker ps -q --filter "label=com.docker.compose.project=$p" --filter "label=com.docker.compose.service=$client" | head -1)
    [ -n "$cid" ] || continue
    for name in api postgres redis ai-backend qdrant neo4j shared-doc-parser-lb shared-presidio-analyzer; do
      ip=$(docker exec "$cid" getent hosts "$name" 2>/dev/null | awk '{print $1}' | head -1)
      [ -n "$ip" ] || continue
      owner=$(docker ps -q | xargs docker inspect --format '{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' | grep -w "$ip" | awk '{print $1}' | tr -d / | head -1)
      ownerproj=$(docker inspect "$owner" --format '{{index .Config.Labels "com.docker.compose.project"}}' 2>/dev/null)
      if [[ "$name" == shared-* ]]; then ok=$([ -n "$ownerproj" ] && [[ "$ownerproj" != lane-* ]] && echo y); else ok=$([ "$ownerproj" = "$p" ] && echo y); fi
      if [ "$ok" = y ]; then echo "ok    $p $client -> $name = $owner"; else echo "LEAK  $p $client -> $name = $owner ($ownerproj)"; fail=1; fi
    done
  done
done
[ $fail -eq 0 ] && echo "PASS lanes are isolated" || echo "FAIL see LEAK lines"
exit $fail
