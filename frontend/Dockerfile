# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Accept build arguments for React environment variables
ARG REACT_APP_API_URL=http://localhost:8000

# Set environment variables for the build
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Increase Node.js memory limit for build process
ENV NODE_OPTIONS="--max_old_space_size=4096"

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies needed for build)
RUN npm ci --only=production=false --silent

# Copy source code
COPY . .

# Build the app with the environment variables and memory optimization
RUN npm run build

# Production stage
FROM nginx:alpine

# Install curl for health checks
RUN apk --no-cache add curl

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built app from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]