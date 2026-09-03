FROM node:20-alpine AS base

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

RUN npm run build

EXPOSE 3000

ENV HOSTNAME="0.0.0.0"

CMD ["sh", "-c", "npx next start -p ${PORT:-3000} -H 0.0.0.0"]

