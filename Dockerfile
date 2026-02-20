# SAP RFC MCP Server (Linux x86_64 only)
#
# Put in the project folder:
#   nwrfc750P_18-70002752.zip  — SAP NetWeaver RFC SDK for Linux x86_64
#   pyrfc-3.3.1.tar.gz        — pyrfc source (e.g. from PyPI)
#   docker build -t sap-rfc-mcp-server .

# Always use amd64 so SDK (nwrfcsdk_amd64) and container arch match (e.g. when building on Mac ARM)
FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app

COPY nwrfc750P_18-70002752.zip /tmp/nwrfc750P_18-70002752.zip
COPY pyrfc-3.3.1.tar.gz /tmp/pyrfc-3.3.1.tar.gz

# Extract SDK zip; find lib and include (any depth), set nwrfcsdk to a dir that has both lib/ and include/
RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip \
    && mkdir -p /usr/local/sap \
    && unzip -q /tmp/nwrfc750P_18-70002752.zip -d /usr/local/sap \
    && REAL_LIB=$(find /usr/local/sap -name 'libsapnwrfc.so*' -o -name 'libsapnwrfc.a' 2>/dev/null | head -1) \
    && FIND_HEADER=$(find /usr/local/sap -name 'sapnwrfc.h' 2>/dev/null | head -1) \
    && if [ -n "$REAL_LIB" ]; then \
         SDK_ROOT=$(dirname "$(dirname "$REAL_LIB")"); \
         PARENT=$(dirname "$SDK_ROOT"); \
         if [ ! -f "$SDK_ROOT/include/sapnwrfc.h" ]; then \
           if [ -n "$FIND_HEADER" ] && [ -f "$FIND_HEADER" ]; then \
             cp -r "$(dirname "$FIND_HEADER")" "$SDK_ROOT/include"; \
           elif [ -d "$PARENT/include" ]; then \
             cp -r "$PARENT/include" "$SDK_ROOT/"; \
           fi; \
         fi; \
         if [ "$SDK_ROOT" != "/usr/local/sap/nwrfcsdk" ]; then \
           rm -rf /usr/local/sap/nwrfcsdk; \
           mv "$SDK_ROOT" /usr/local/sap/nwrfcsdk; \
           [ "$PARENT" = "/usr/local/sap" ] || rm -rf "$PARENT"; \
         fi; \
       else \
         echo "ERROR: No Linux libs (libsapnwrfc.so/.a) in zip."; \
         echo "Contents:"; ls -laR /usr/local/sap 2>/dev/null | head -80; \
         exit 1; \
       fi \
    && for f in /usr/local/sap/nwrfcsdk/lib/libsapnwrfc.so.*; do [ -e "$f" ] && [ ! -e /usr/local/sap/nwrfcsdk/lib/libsapnwrfc.so ] && ln -sf "$(basename "$f")" /usr/local/sap/nwrfcsdk/lib/libsapnwrfc.so && break; done; true \
    && for f in /usr/local/sap/nwrfcsdk/lib/libsapucum.so.*; do [ -e "$f" ] && [ ! -e /usr/local/sap/nwrfcsdk/lib/libsapucum.so ] && ln -sf "$(basename "$f")" /usr/local/sap/nwrfcsdk/lib/libsapucum.so && break; done; true \
    && test -f /usr/local/sap/nwrfcsdk/include/sapnwrfc.h \
       || ( echo "ERROR: sapnwrfc.h not found. nwrfcsdk layout:"; ls -laR /usr/local/sap/nwrfcsdk 2>/dev/null; exit 1 ) \
    && rm -f /tmp/nwrfc750P_18-70002752.zip \
    && apt-get purge -y unzip && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

ENV SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
ENV LD_LIBRARY_PATH=${SAPNWRFC_HOME}/lib:${LD_LIBRARY_PATH:-}
ENV PATH=${SAPNWRFC_HOME}/lib:${PATH}

# 시스템 라이브러리 경로 등록
RUN echo "$SAPNWRFC_HOME/lib" > /etc/ld.so.conf.d/sapnwrfc.conf \
    && ldconfig

# 1) 휠만 받아서 --no-index로 설치
# 2) pyrfc: 로컬 pyrfc-3.3.1.tar.gz 압축 해제 → setup.py 패치 → python setup.py install
# 3) 우리 패키지는 --no-build-isolation 로 설치
COPY requirements.txt requirements-docker.txt pyproject.toml pyproject-docker.toml ./
COPY sap_rfc_mcp_server ./sap_rfc_mcp_server
RUN cp pyproject-docker.toml pyproject.toml \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential python3-dev \
    && pip download -r requirements-docker.txt -d /tmp/wheels --only-binary :all: \
    && pip install --no-cache-dir --no-index --find-links /tmp/wheels -r requirements-docker.txt \
    && pip install --no-cache-dir Cython setuptools wheel \
    && tar -xzf /tmp/pyrfc-3.3.1.tar.gz -C /tmp \
    && sed -i 's/-minline-all-stringops/-finline-stringops/g' /tmp/pyrfc-*/setup.py \
    && ( export LDFLAGS="-L$SAPNWRFC_HOME/lib ${LDFLAGS:-}" LIBRARY_PATH="$SAPNWRFC_HOME/lib${LIBRARY_PATH:+:$LIBRARY_PATH}" \
         && cd /tmp/pyrfc-* && python setup.py install ) \
    && cd /app \
    && pip install --no-cache-dir --no-deps --no-build-isolation . \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/wheels /tmp/pyrfc-3.3.1.tar.gz /tmp/pyrfc-*

# SAP connection: pass as env at runtime (docker run -e ...) or CLI (--sap-ashost=...).
#   SAP_ASHOST, SAP_USER, SAP_PASSWORD, SAP_SYSNR, SAP_CLIENT (required)
#   SAP_LANG (default: EN), SAP_TRACE (default: 0)
#   SAP_CONFIG_SOURCE=env  forces use of env only (recommended in Docker)
# Example: docker run -e SAP_ASHOST=my.sap.host -e SAP_USER=user -e SAP_PASSWORD=secret -e SAP_SYSNR=00 -e SAP_CLIENT=100 -p 8000:8000 sap-rfc-mcp-server

EXPOSE 8000

CMD ["sap-rfc-mcp-http-server"]
