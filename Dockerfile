FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .[yaml,toml]
ENTRYPOINT ["gosek"]