FROM node:20-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM alpine:latest
WORKDIR /shared
COPY --from=build-stage /app/dist /shared-dist
CMD sh -c "cp -rp /shared-dist/* /shared/ && echo 'Frontend build copied' && sleep infinity"
