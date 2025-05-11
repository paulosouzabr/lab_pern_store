FROM node:16
WORKDIR /usr/src/app
COPY . .
RUN npm ci --no-audit --legacy-peer-deps || npm ci --no-audit --legacy-peer-deps --maxsockets 1
RUN npm run build
RUN npm install
RUN chown -R node:node /usr/src/app
EXPOSE 3000
USER node
CMD ["npm", "run", "start"]

