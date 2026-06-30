FROM node:22-alpine

ENV CI=true

RUN corepack enable && corepack prepare pnpm@11.5.2 --activate

WORKDIR /app

COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
RUN pnpm install --no-frozen-lockfile

COPY . .

EXPOSE 5173

CMD ["pnpm", "exec", "vite", "--host", "0.0.0.0"]
