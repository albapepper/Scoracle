FROM node:16-alpine as build

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install

# Copy application source
COPY . .

# Build the production bundle
RUN npm run build

# Production image
FROM nginx:stable-alpine

# Copy build artifacts into nginx html directory
COPY --from=build /app/build /usr/share/nginx/html

# Provide custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]