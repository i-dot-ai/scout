# Use an official Node.js runtime as a parent image
FROM node:20

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY frontend/package.json frontend/package-lock.json ./

# Install the application dependencies
RUN npm ci

# Debugging step: List contents of node_modules/.bin
RUN ls -la /app/node_modules/.bin

# Copy the rest of the application code to the working directory
COPY frontend/ ./

# Expose the port the app runs on
EXPOSE 3000

# Set the PATH environment variable to include node_modules/.bin
ENV PATH /app/node_modules/.bin:$PATH

# Debugging step: Print the PATH environment variable
RUN echo $PATH

# Debugging step: Verify that the next command is available
RUN which next

# Run the development server
CMD ["npm", "run", "dev"]
