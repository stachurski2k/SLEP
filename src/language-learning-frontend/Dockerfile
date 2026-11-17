# Build Stage
FROM node:22-alpine as build

WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Build arguments
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_MODEL_SERVICE_URL=http://localhost:5001

# Set environment variables from build args so Vite can pick them up
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_MODEL_SERVICE_URL=$VITE_MODEL_SERVICE_URL

# Build the application
RUN npm run build

# Production Stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
