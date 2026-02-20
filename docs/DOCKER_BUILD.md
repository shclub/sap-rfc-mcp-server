# Docker 이미지 빌드 (Linux x86_64)

Linux x86_64 전용 이미지를 빌드합니다.

### SDK 폴더

- **`nwrfcsdk_amd64/`** — Linux x86_64용 SAP NetWeaver RFC SDK (압축 해제본)

SDK는 [SAP Support Portal](https://support.sap.com)에서 Linux x86_64용을 받아 압축 해제한 뒤 프로젝트 루트에 `nwrfcsdk_amd64` 폴더로 둡니다.

### 빌드

```bash
cd /path/to/sap-rfc-mcp-server
docker build -t sap-rfc-mcp-server .
```

플랫폼을 지정하지 않으면 **linux/amd64**로 빌드됩니다.

### 실행 예

```bash
docker run -e SAP_ASHOST=my.sap.host -e SAP_USER=user -e SAP_PASSWORD=secret \
  -e SAP_SYSNR=00 -e SAP_CLIENT=100 -p 8000:8000 sap-rfc-mcp-server
```

SAP 접속 설정은 [SAP_CONNECTION_CONFIG.md](SAP_CONNECTION_CONFIG.md)를 참고하세요.
