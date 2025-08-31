# Multi-stage build for Manufacturing AI Assistant Frontend
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Install dependencies for development
FROM base as development

# Copy package files first for better caching
COPY package*.json ./

# Install all dependencies including dev dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3002

# Command for development
CMD ["npm", "start"]

# Build stage
FROM base as build

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Copy built app from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
