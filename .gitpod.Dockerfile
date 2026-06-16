# GitPod Base Image with Python
# ==============================
FROM gitpod/workspace-python-3.11

# تثبيت أي أدوات نظام إضافية عند الحاجة
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

USER gitpod
