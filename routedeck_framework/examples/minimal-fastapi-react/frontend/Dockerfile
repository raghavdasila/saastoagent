FROM node:20-alpine

WORKDIR /app/routedeck_framework/examples/minimal-fastapi-react/frontend

COPY routedeck_framework/react /app/routedeck_framework/react
COPY routedeck_framework/examples/minimal-fastapi-react/frontend/package*.json ./
RUN npm install

COPY routedeck_framework/examples/minimal-fastapi-react/frontend ./

ENV ROUTEDECK_BACKEND_URL=http://routedeck-backend:8096
EXPOSE 5190
CMD ["npm", "run", "dev"]
