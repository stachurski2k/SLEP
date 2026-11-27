# Build Stage
FROM node:22-alpine as build

WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Build arguments (optional overrides)
ARG VITE_API_BASE_URL
ARG VITE_MODEL_SERVICE_URL
ARG VITE_GOOGLE_CLIENT_ID

# Build the application
# If build args are passed and non-empty, use them; otherwise Vite loads .env automatically
RUN if [ -n "$VITE_GOOGLE_CLIENT_ID" ]; then export VITE_GOOGLE_CLIENT_ID="$VITE_GOOGLE_CLIENT_ID"; fi && \
    if [ -n "$VITE_API_BASE_URL" ]; then export VITE_API_BASE_URL="$VITE_API_BASE_URL"; fi && \
    if [ -n "$VITE_MODEL_SERVICE_URL" ]; then export VITE_MODEL_SERVICE_URL="$VITE_MODEL_SERVICE_URL"; fi && \
    npm run build

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
