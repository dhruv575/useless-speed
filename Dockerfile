FROM node:24-bookworm-slim AS build
WORKDIR /project
COPY package.json package-lock.json ./
COPY app/package.json ./app/package.json
RUN npm ci
COPY app ./app
RUN npm run build

FROM node:24-bookworm-slim
WORKDIR /project
ENV NODE_ENV=production HOST=0.0.0.0 PORT=8080
COPY --from=build --chown=node:node /project/app/dist ./app/dist
COPY --from=build --chown=node:node /project/app/data ./app/data
COPY --from=build --chown=node:node /project/app/server.mjs ./app/server.mjs
RUN mkdir -p /project/app/cache && chown node:node /project/app/cache
USER node
EXPOSE 8080
CMD ["node", "app/server.mjs"]
