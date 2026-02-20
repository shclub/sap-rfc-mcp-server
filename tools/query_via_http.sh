#!/usr/bin/env bash
# SAP RFC MCP HTTP 서버에 연결해 도구 목록 조회 / 데이터 조회 예시
# 사용법:
#   ./tools/query_via_http.sh                    # 도구 목록
#   ./tools/query_via_http.sh system              # 시스템 정보
#   ./tools/query_via_http.sh table T001 10       # T001 테이블 10건
#   BASE_URL=http://192.168.1.10:8000 ./tools/query_via_http.sh table MARA 5

BASE_URL="${BASE_URL:-http://localhost:8000}"

case "${1:-}" in
  "")
    echo "=== MCP tools ==="
    curl -s "${BASE_URL}/mcp/tools" | python3 -m json.tool
    ;;
  system)
    echo "=== rfc_system_info ==="
    curl -s -X POST "${BASE_URL}/mcp/call_tool" \
      -H "Content-Type: application/json" \
      -d '{"name":"rfc_system_info","arguments":{}}' | python3 -m json.tool
    ;;
  table)
    TABLE="${2:-T001}"
    ROWS="${3:-10}"
    echo "=== RFC_READ_TABLE ${TABLE} (max ${ROWS}) ==="
    curl -s -X POST "${BASE_URL}/mcp/call_tool" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"call_rfc_function\",
        \"arguments\": {
          \"function_name\": \"RFC_READ_TABLE\",
          \"parameters\": {
            \"QUERY_TABLE\": \"${TABLE}\",
            \"DELIMITER\": \"|\",
            \"ROWCOUNT\": ${ROWS}
          }
        }
      }" | python3 -m json.tool
    ;;
  *)
    echo "Usage: $0 [system|table [TABLE_NAME] [MAX_ROWS]]"
    echo "  (no args)  list MCP tools"
    echo "  system     SAP system info"
    echo "  table T001 10   read table T001, max 10 rows"
    exit 1
    ;;
esac
