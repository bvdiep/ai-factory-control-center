module.exports = {
  apps: [
    {
      name: "ai-factory-control-center",
      script: "python3",
      args: "main.py",
      interpreter: "python3",
      env: {
        PORT: 5001,
        NODE_ENV: "production"
      },
      watch: false,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: "logs/err.log",
      out_file: "logs/out.log",
      merge_logs: true,
      autorestart: true
    }
  ]
};
