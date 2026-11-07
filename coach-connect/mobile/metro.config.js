// Learn more: https://docs.expo.dev/guides/customizing-metro
const http = require('node:http');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
const backend = new URL(process.env.COACH_BACKEND_URL || 'http://127.0.0.1:8000');

// The Expo dev server forwards /api to the backend: the phone needs a single address (this server),
// which also works through `expo start --tunnel` when the network blocks direct connections.
config.server = {
  ...config.server,
  enhanceMiddleware: (metroMiddleware) => (req, res, next) => {
    if (!req.url.startsWith('/api/')) {
      return metroMiddleware(req, res, next);
    }
    const upstream = http.request(
      { host: backend.hostname, port: backend.port, path: req.url, method: req.method, headers: { ...req.headers, host: backend.host } },
      (response) => {
        res.writeHead(response.statusCode ?? 502, response.headers);
        response.pipe(res);
      },
    );
    upstream.on('error', () => {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ code: 'network', detail: `Backend non raggiungibile su ${backend.origin}` }));
    });
    req.pipe(upstream);
  },
};

module.exports = config;
