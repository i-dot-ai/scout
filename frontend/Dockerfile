# Use an official Node.js runtime as a parent image
FROM node:20

# Set the working directory in the container
WORKDIR /app

# Copy the application code to the working directory
COPY frontend/ ./

# Install the application dependencies
RUN npm ci

# Expose the port the app runs on
EXPOSE 3000

# Run the development server
CMD ["npm", "run", "dev"]
