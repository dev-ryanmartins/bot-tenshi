module.exports = {
  apps: [
    {
      name: "tenshi-bot",
      script: "main.py",
      interpreter: "python3",
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_restarts: 20,
      restart_delay: 5000,
      env: {
        PYTHONUNBUFFERED: "1",
        ENABLE_SITE: "1",
        SITE_HOST: "0.0.0.0",
        SITE_PORT: "8081",
      },
    },
  ],
};
