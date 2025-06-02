FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    psycopg2-binary \
    sqlalchemy

# Set working directory
WORKDIR /app

# Copy the MCP server code
COPY src/postgres/mcp_server.py .

# Set the entrypoint
ENTRYPOINT ["python", "mcp_server.py"] 