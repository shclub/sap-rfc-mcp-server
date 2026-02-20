# MCP HTTP 서버 연결 및 데이터 조회

서비스(HTTP 서버)가 떠 있는 상태에서 MCP 도구를 호출해 SAP 데이터를 조회하는 방법입니다.

## 전제

- SAP RFC MCP HTTP 서버가 **이미 실행 중** (예: Docker `-p 8000:8000` 또는 로컬 `sap-rfc-mcp-http-server`).
- 접속 URL: `http://localhost:8000` (로컬) 또는 `http://<서버IP>:8000` (원격).

---

## 1. 사용 가능한 도구 확인

```bash
curl -s http://localhost:8000/mcp/tools | python3 -m json.tool
```

또는 브라우저에서 `http://localhost:8000/docs` 로 API 문서 확인.

---

## 2. 데이터 조회 예시

### 2.1 SAP 시스템 정보 (연결 확인)

```bash
curl -s -X POST http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{"name":"rfc_system_info","arguments":{}}'
```

### 2.2 테이블 데이터 읽기 (RFC_READ_TABLE)

`call_rfc_function`으로 `RFC_READ_TABLE`을 호출합니다.

**예: T001 (회사코드) 10건**

```bash
curl -s -X POST http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "call_rfc_function",
    "arguments": {
      "function_name": "RFC_READ_TABLE",
      "parameters": {
        "QUERY_TABLE": "T001",
        "DELIMITER": "|",
        "FIELDS": [
          {"FIELDNAME": "MANDT"},
          {"FIELDNAME": "BUKRS"},
          {"FIELDNAME": "BUTXT"}
        ],
        "ROWCOUNT": 10
      }
    }
  }'
```

**예: MARA (자재 마스터) 필드 지정 + WHERE**

```bash
curl -s -X POST http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "call_rfc_function",
    "arguments": {
      "function_name": "RFC_READ_TABLE",
      "parameters": {
        "QUERY_TABLE": "MARA",
        "DELIMITER": "|",
        "FIELDS": [
          {"FIELDNAME": "MATNR"},
          {"FIELDNAME": "MTART"},
          {"FIELDNAME": "MEINS"}
        ],
        "OPTIONS": [{"TEXT": "MTART = '\''FERT'\''"}],
        "ROWCOUNT": 5
      }
    }
  }'
```

응답은 `result[].text` 에 JSON 문자열로 옵니다. 필요하면 `jq` 등으로 파싱하세요.

### 2.3 대용량 테이블 스트리밍

`stream_rfc_table_data`를 호출하면 스트림 URL을 받을 수 있습니다.

```bash
curl -s -X POST http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "stream_rfc_table_data",
    "arguments": {
      "table_name": "MARA",
      "fields": ["MATNR", "MTART", "MEINS"],
      "chunk_size": 1000
    }
  }'
```

반환된 URL로 `GET /stream/table/MARA?chunk_size=1000&fields=...` 요청하면 청크 단위로 데이터를 받을 수 있습니다.

### 2.4 RFC 함수 목록 조회

```bash
curl -s -X POST http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_rfc_functions",
    "arguments": {
      "funcs_mask": "RFC_*",
      "limit": 20
    }
  }'
```

---

## 3. Cursor에서 사용하기

Cursor는 기본적으로 **stdio** 방식 MCP를 사용합니다. 지금 서비스는 **HTTP** 서버이므로:

- **방법 A – 터미널/스크립트에서 HTTP 호출**  
  위의 `curl` 예시나 아래 `tools/query_via_http.sh` 를 사용해 데이터 조회.

- **방법 B – Cursor용 stdio MCP 사용**  
  같은 프로젝트에서 stdio 서버를 띄우고 Cursor MCP 설정에 추가:

  ```json
  {
    "servers": {
      "sap-rfc": {
        "command": "python",
        "args": ["-m", "sap_rfc_mcp_server.server"],
        "cwd": "/path/to/sap-rfc-mcp-server",
        "env": { "SAP_CONFIG_SOURCE": "env" }
      }
    }
  }
  ```

  (로컬에 SAP 설정·SDK가 있어야 합니다. Docker만 쓰는 경우에는 방법 A가 적합합니다.)

---

## 4. 헬스 체크

```bash
curl -s http://localhost:8000/health
```

정상이면 `"status": "healthy"`, SAP 연결 실패 시 `"sap_connection": "error"` 등이 나옵니다.
