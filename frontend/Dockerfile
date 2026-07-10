FROM node:24-alpine

WORKDIR /app/frontend

COPY vendor/routedeck-v0-compat /app/vendor/routedeck-v0-compat
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .

EXPOSE 3000

CMD ["npm", "run", "dev"]
