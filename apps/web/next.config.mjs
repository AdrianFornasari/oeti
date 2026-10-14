/** @type {import('next').NextConfig} */
const config = {
  agentRules: false,
  ...(process.env.OETI_LOW_MEMORY === "1" ? { experimental: {
    cpus: 1,
    webpackMemoryOptimizations: true,
    webpackBuildWorker: false,
  } } : {}),
};

export default config;
