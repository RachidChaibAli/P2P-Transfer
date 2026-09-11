# Multi-stage Dockerfile for React + Vite Frontend
# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependency specifications first for optimal layer caching
COPY package*.json ./
RUN npm ci

# Copy source code and build production bundle
COPY . .
RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:alpine AS runner

# Copy custom nginx configuration (SPA routing & reverse proxy)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
