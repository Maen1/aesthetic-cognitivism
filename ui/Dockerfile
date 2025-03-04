# Build
FROM node:23 as build
WORKDIR /app
COPY package*.json .
RUN npm install 
COPY . .
RUN npm run build 

# Serve the app using Nginx
FROM nginx:stable-alpine3.20-perl
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]