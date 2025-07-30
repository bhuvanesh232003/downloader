FROM python:3.11-slim

# Create working directory
WORKDIR /app

# Copy files to container
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]
