FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/deghosal-2026/ai-code-guardian"
LABEL org.opencontainers.image.description="AI Code Governance CI Bot"

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir . && rm -rf ~/.cache/pip

RUN adduser --disabled-password --gecos "" guardian
USER guardian

ENTRYPOINT ["python", "-m", "guardian"]
