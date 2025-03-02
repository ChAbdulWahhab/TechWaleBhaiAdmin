# Base image ke roop mein Python use karein
FROM python:3.9-slim

# Working directory set karein
WORKDIR /app

# Dependencies ko install karne ke liye requirements file copy karein
COPY requirements.txt .

# Dependencies install karein
RUN pip install --no-cache-dir -r requirements.txt

# Poore source code ko container mein copy karein
COPY . .

# Flask development server ke liye port expose karein
EXPOSE 5000

# Environment variables set karein
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development

# Command to run the Flask app using Python directly
CMD ["python", "app.py"]
