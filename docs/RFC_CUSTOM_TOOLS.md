# RFC 커스텀 도구 (Config-driven Tools)

**RFC 함수명을 입력** → **도구를 만들기 위한 meta 정보가 나오고**, 그 meta를 **다시 API로 넘기면 도구가 생성**됩니다. 도구 삭제도 가능합니다.

## 흐름 (2단계)

1. **RFC 함수명으로 meta 조회** (도구는 아직 생성 안 함)  
   - `GET /api/rfc-tools/meta/{function_name}`  
   - 예: `GET /api/rfc-tools/meta/RFC_READ_TABLE`  
   - 응답: `{ "function_name": "...", "tool_definition": { ... } }` → 이 `tool_definition`이 도구 만들 때 쓸 meta.

2. **meta를 넘겨서 도구 생성**  
   - `POST /api/rfc-tools`  
   - body에 1번에서 받은 `tool_definition` 전체를 넣으면 됨. (필요하면 `name` 등 수정 가능.)

3. **도구 삭제**  
   - `DELETE /api/rfc-tools/{tool_name}`

## 설정 파일

- **경로**: 프로젝트 루트의 `rfc_tools.json` (기본값)
- **환경 변수**: `RFC_TOOLS_CONFIG` 로 다른 경로 지정 가능

예시는 `rfc_tools.json.example` 을 복사해 수정하면 됩니다.

```bash
cp rfc_tools.json.example rfc_tools.json
# rfc_tools.json 편집
```

## 설정 형식

```json
{
  "tools": [
    {
      "name": "도구_ID",
      "description": "도구 설명 (MCP에 노출)",
      "function_name": "SAP_RFC_함수명",
      "import_parameters": {
        "RFC_파라미터명": {
          "description": "설명",
          "default": "기본값",
          "type": "string|integer"
        }
      },
      "export_parameters": ["반환할_EXPORT_이름"] 또는 null(전체),
      "table_parameters": ["반환할_TABLE_이름"] 또는 null(전체)
    }
  ]
}
```

- **name**: MCP 도구 이름 (고유)
- **description**: 도구 설명
- **function_name**: 호출할 SAP RFC 함수
- **import_parameters**: RFC의 IMPORT/입력 파라미터 → 도구 입력으로 매핑. `default` 가 있으면 도구 호출 시 생략 가능.
- **export_parameters**: RFC 결과에서 반환할 EXPORT 파라미터 이름 목록. `null` 이면 전체 반환.
- **table_parameters**: RFC 결과에서 반환할 TABLE 파라미터 이름 목록. `null` 이면 전체 반환.

도구 호출 시 인자로 넘긴 값은 `import_parameters` 기본값을 덮어쓰고, `_extra_parameters` 로 추가 RFC 파라미터를 넘길 수 있습니다.

## 예: T001 조회 도구

```json
{
  "name": "read_t001",
  "description": "Read company code table T001",
  "function_name": "RFC_READ_TABLE",
  "import_parameters": {
    "QUERY_TABLE": { "description": "SAP table name", "default": "T001" },
    "DELIMITER": { "default": "|" },
    "ROWCOUNT": { "default": 100, "type": "integer" }
  },
  "table_parameters": ["DATA"]
}
```

서버 실행 후 MCP/HTTP에서 `read_t001` 도구가 보이고, 호출 시 위 파라미터로 `RFC_READ_TABLE` 이 호출되며 `DATA` 테이블만 반환됩니다.

## REST API (HTTP 서버)

### 1) RFC 함수명 → meta 조회 (도구 생성용)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| **GET** | **`/api/rfc-tools/meta/{function_name}`** | **RFC 함수명을 넣으면 도구 만들기 위한 meta(정의)만 반환. 도구는 생성하지 않음.** |

- 쿼리: `language` (선택, 기본 `EN`)
- 응답: `{ "function_name": "RFC_READ_TABLE", "tool_definition": { "name", "description", "function_name", "import_parameters", "export_parameters", "table_parameters" } }`

**예**

```bash
curl "http://localhost:8000/api/rfc-tools/meta/RFC_READ_TABLE"
curl "http://localhost:8000/api/rfc-tools/meta/RFC_READ_TABLE?language=EN"
```

### 2) meta로 도구 생성

| 메서드 | 경로 | 설명 |
|--------|------|------|
| **POST** | **`/api/rfc-tools`** | **1번에서 받은 `tool_definition`을 body에 넣어 호출하면 도구 생성** |

**예** (1번 응답의 `tool_definition`을 그대로 body에 넣음. `name`만 바꿀 수 있음)

```bash
# 1) meta 조회
META=$(curl -s "http://localhost:8000/api/rfc-tools/meta/RFC_READ_TABLE")
# 2) tool_definition만 추출해 name 수정 후 생성 (예: jq 사용)
# echo "$META" | jq '.tool_definition | .name = "read_table"' | curl -X POST http://localhost:8000/api/rfc-tools -H "Content-Type: application/json" -d @-
```

또는 1번 응답에서 `tool_definition` 객체를 복사해 `name`을 원하는 도구 이름으로 바꾼 뒤 POST body로 보내면 됩니다.

### 3) 도구 조회·수정·삭제 (도구 이름 기준)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/rfc-tools` | 커스텀 도구 정의 목록 |
| GET | `/api/rfc-tools/{name}` | 도구 이름으로 단일 정의 조회 |
| PUT | `/api/rfc-tools/{name}` | 도구 정의 수정 |
| DELETE | `/api/rfc-tools/{name}` | **도구 삭제** |

**예: 도구 삭제**

```bash
curl -X DELETE http://localhost:8000/api/rfc-tools/read_table
```

### 한 번에 하기 (선택)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/rfc-tools/from-rfc` | body에 `function_name`, 선택 `tool_name`, `create: true` → meta 조회 후 바로 도구 생성 |

설정은 서버가 사용하는 `rfc_tools.json` 경로에 저장됩니다. (`RFC_TOOLS_CONFIG` 또는 프로젝트 루트)

## 적용 대상

- **stdio MCP 서버** (`python -m sap_rfc_mcp_server.server`)
- **HTTP MCP 서버** (`sap-rfc-mcp-http-server` / `python -m sap_rfc_mcp_server.http_server`)

설정 파일을 읽을 수 있는 경로에서 서버를 실행하면 됩니다. (`RFC_TOOLS_CONFIG` 또는 프로젝트 루트의 `rfc_tools.json`)
