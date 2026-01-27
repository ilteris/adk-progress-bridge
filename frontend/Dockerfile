# Stage 1: Build the Vue.js application
FROM node:20-slim AS build-stage

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build argument for the API URL
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:stable-alpine AS production-stage

# Copy the build output from the build-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy a custom Nginx configuration if needed (e.g., for SPA routing)
# RUN echo 'server { listen 80; location / { root /usr/share/nginx/html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
