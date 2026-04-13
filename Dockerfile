FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port (matches the EXPOSE 8080 in Go)
EXPOSE 5001

# Run the Uvicorn server (ENTRYPOINT)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]