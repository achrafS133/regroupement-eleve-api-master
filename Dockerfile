FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Increase pip timeout and upgrade packaging tools to reduce transient network/build errors
ENV PIP_DEFAULT_TIMEOUT=100

# Upgrade pip, setuptools, wheel first (helps with binary wheel handling)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install runtime dependencies (explicit list to avoid malformed requirements files)
RUN pip install --no-cache-dir --disable-pip-version-check \
	fastapi uvicorn sqlalchemy pydantic geopy scikit-learn

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
