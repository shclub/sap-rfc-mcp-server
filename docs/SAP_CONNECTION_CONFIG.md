# SAP 접속 정보 설정 (SAP Connection Parameters)

SAP RFC MCP 서버는 접속 정보를 **환경 변수** 또는 **HTTP 서버 CLI 인자**로 받습니다.

## 환경 변수 (Docker·CI 권장)

| 변수 | 필수 | 설명 | 예 |
|------|------|------|-----|
| `SAP_ASHOST` | ✓ | SAP 애플리케이션 서버 호스트 | `sap.mycompany.com` |
| `SAP_USER` | ✓ | SAP 사용자 | `RFCUSER` |
| `SAP_PASSWORD` | ✓ | SAP 비밀번호 | — |
| `SAP_SYSNR` | ✓ | 시스템 번호 | `00` |
| `SAP_CLIENT` | ✓ | 클라이언트 | `100` |
| `SAP_LANG` | | 로그온 언어 (기본: `EN`) | `EN`, `KO` |
| `SAP_TRACE` | | RFC 트레이스 레벨 (기본: `0`) | `0`–`3` |
| `SAP_CONFIG_SOURCE` | | `env` 로 두면 **환경 변수만** 사용 (Docker 권장) | `env` |

### Docker 실행 예

```bash
docker run -d \
  -e SAP_CONFIG_SOURCE=env \
  -e SAP_ASHOST=my.sap.host \
  -e SAP_USER=myuser \
  -e SAP_PASSWORD=mypass \
  -e SAP_SYSNR=00 \
  -e SAP_CLIENT=100 \
  -p 8000:8000 \
  sap-rfc-mcp-server
```

## HTTP 서버 CLI 인자

`sap-rfc-mcp-http-server` 실행 시 `--sap-*` 옵션으로 접속 정보를 넘길 수 있습니다.  
지정한 값은 환경 변수보다 우선합니다.

```bash
sap-rfc-mcp-http-server \
  --sap-ashost=my.sap.host \
  --sap-user=myuser \
  --sap-password=mypass \
  --sap-sysnr=00 \
  --sap-client=100 \
  --sap-lang=EN \
  --host=0.0.0.0 \
  --port=8000
```

- `--host`, `--port`: 서버 바인드 주소/포트 (기본: `0.0.0.0`, `8000`)
- `--reload`: 개발 시 자동 리로드

## 설정 소스 우선순위 (자동 감지 시)

`SAP_CONFIG_SOURCE` 를 두지 않으면 다음 순서로 시도합니다.

1. **Keyring** (설정된 경우)
2. **`.env` 파일** (프로젝트 루트)
3. **환경 변수** (`SAP_*`)

Docker 등에서는 **환경 변수만** 쓰려면 반드시 `SAP_CONFIG_SOURCE=env` 를 설정하세요.
