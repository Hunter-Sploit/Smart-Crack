FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Install hashcat, john the ripper, and required extractors
RUN apt-get update && apt-get install -y --no-install-recommends \
    hashcat \
    john \
    john-data \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements and testing tools
COPY requirements.txt pyproject.toml /app/
RUN pip install --no-cache-dir -r requirements.txt pytest pytest-mock

# Copy codebase and install in editable mode
COPY . /app/
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python", "-m", "smartcrack"]
CMD ["--help"]
