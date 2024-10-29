FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip 
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# # Use the official slim version of Python 3.11
# FROM python:3.11-slim

# # Environment settings
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # Set the working directory in the container
# WORKDIR /app

# # Install necessary dependencies
# RUN apt-get update && apt-get install -y \
#     gcc \
#     libpq-dev \
#     libffi-dev \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# # Copy the requirements file
# COPY requirements.txt .

# # Install Python dependencies including Daphne
# RUN pip install --upgrade pip
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the project files into the working directory
# COPY . .

# # Expose port 8000 for Daphne
# EXPOSE 8000

# # Command to run Daphne ASGI server
# CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "myproject.asgi:application"]
