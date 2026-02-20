# Cursor에서 SAP RFC MCP 서버 연결하기

Cursor IDE에서 이 프로젝트의 MCP 서버(stdio)를 사용하는 설정 방법입니다.

## 1. 설정 위치

- **프로젝트별**: 프로젝트 루트에 `.cursor/mcp.json` (팀과 공유 시 git에 커밋)
- **전역**: `~/.cursor/mcp.json` (개인용)

## 2. 설정 방법

### 방법 A – UI로 추가

1. **Cursor 설정** 열기: `Cmd + ,` (macOS) 또는 `Ctrl + ,` (Windows)
2. **Tools & MCP** → **Add new MCP server**
3. 서버 타입에서 **Command** 선택 후 아래와 같이 입력:
   - **Name**: `sap-rfc` (원하는 이름)
   - **Command**: `python` (또는 `./venv/bin/python`)
   - **Args**: `-m`, `sap_rfc_mcp_server.server`
   - **Cwd**: 이 저장소 루트 절대 경로 (예: `/Users/you/source/sap-rfc-mcp-server`)
   - **Env** (선택): `SAP_RFC_MCP_CONFIG` = `./.env`

### 방법 B – JSON 파일로 설정

1. 프로젝트 루트에 `.cursor` 폴더가 없으면 생성합니다.
2. `.cursor/mcp.json` 파일을 만들고 아래 내용을 넣습니다. **`cwd`만 본인 환경에 맞게 수정**하세요.

```json
{
  "mcpServers": {
    "sap-rfc": {
      "command": "python",
      "args": ["-m", "sap_rfc_mcp_server.server"],
      "cwd": "/Users/jakelee/source/sap-rfc-mcp-server",
      "env": {
        "SAP_RFC_MCP_CONFIG": "./.env"
      }
    }
  }
}
```

- `cwd`: 이 저장소의 **절대 경로**로 바꿉니다.
- 가상환경을 쓰는 경우: `"command": "/Users/jakelee/source/sap-rfc-mcp-server/venv/bin/python"` 처럼 `venv`의 `python` 절대 경로를 넣고, `cwd`는 그대로 저장소 루트로 두면 됩니다.

예시 파일은 `.cursor/mcp.json.example`에 있으니 복사해서 사용할 수 있습니다.

```bash
mkdir -p .cursor
cp .cursor/mcp.json.example .cursor/mcp.json
# .cursor/mcp.json 에서 cwd 를 실제 경로로 수정
```

## 3. 사전 요구사항

- Cursor v0.40 이상
- Python 3.10+
- 이 프로젝트 의존성 설치: `pip install -e ".[docker]"` 또는 `pip install -r requirements-docker.txt`
- SAP NW RFC SDK 설치 및 `SAPNWRFC_HOME`(또는 `.env` 등) 설정
- `.env` 또는 환경변수에 SAP 연결 정보 (ASHOST, SYSNR, CLIENT, USER, PASSWD 등)

## 4. 적용 및 사용

- **MCP 설정은 Cursor를 완전히 종료한 뒤 다시 실행해야** 적용됩니다.
- Cursor를 다시 연 다음, 채팅/에이전트에서 SAP 관련 도구(예: RFC 메타 조회, 테이블 읽기 등)가 나오는지 확인하면 됩니다.

## 5. Docker로 localhost:8000에 띄워둔 경우 (HTTP)

서버를 Docker로 **http://localhost:8000** 에 띄워 두었다면, Cursor에서는 **streamableHttp** 타입으로 연결할 수 있습니다.

### JSON 설정 예시 (Docker · HTTP)

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "sap-rfc": {
      "url": "http://localhost:8000/mcp/sse"
    }
  }
}
```

또는 UI에서:

1. **Cursor 설정** → **Tools & MCP** → **Add new MCP server**
2. 타입: **Streamable HTTP** (또는 **URL**)
3. **URL**: `http://localhost:8000/mcp/sse`

### 참고

- Cursor의 **streamableHttp**는 MCP 규격의 **Streamable HTTP**(단일 URL에서 POST + SSE)를 기대합니다.
- 이 프로젝트 HTTP 서버는 **REST 스타일** (`GET /mcp/tools`, `POST /mcp/call_tool`)이라, Cursor 버전에 따라 연결이 안 될 수 있습니다. 그때는 **4번**처럼 로컬에서 stdio 서버를 띄우고 **command** 방식으로 연결하세요.
- Docker 서버만 쓸 때는 Cursor MCP 대신 [MCP_HTTP_DATA_QUERY.md](MCP_HTTP_DATA_QUERY.md)의 `curl`/스크립트로 도구를 호출할 수 있습니다.

## 6. 문제 해결

- **연결 실패**: `cwd`가 이 저장소 루트의 절대 경로인지, `python`으로 `sap_rfc_mcp_server` 모듈을 실행할 수 있는 환경인지 확인하세요.
- **SAP 연결 오류**: `.env`와 SAP NW RFC SDK 설정을 참고하세요. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)에도 정리되어 있습니다.
- **HTTP(Docker)로 Cursor 연결 안 됨**: 현재 서버가 Streamable HTTP 규격이 아니라서일 수 있습니다. 로컬 stdio(2번·3번)로 연결하거나, HTTP는 curl/스크립트로만 사용하세요.
