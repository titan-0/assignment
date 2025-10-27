FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend .

EXPOSE 5173

ENV VITE_API_BASE=http://backend:8000
ENV VITE_WS_URL=ws://backend:8000/ws/live

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
