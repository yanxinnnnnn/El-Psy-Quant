FROM node:24-alpine AS dependencies

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS builder

ARG EL_PSY_QUANT_API_ORIGIN=http://backend:8000
ARG EL_PSY_QUANT_ALLOW_COMPOSE_API_ORIGIN=1
ENV EL_PSY_QUANT_API_ORIGIN=${EL_PSY_QUANT_API_ORIGIN}
ENV EL_PSY_QUANT_ALLOW_COMPOSE_API_ORIGIN=${EL_PSY_QUANT_ALLOW_COMPOSE_API_ORIGIN}

COPY . .
RUN npm run build

FROM node:24-alpine AS runner

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000

WORKDIR /app

COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/scripts/verify-mvp.mjs ./verify-mvp.mjs

USER node

EXPOSE 3000

CMD ["node", "server.js"]
