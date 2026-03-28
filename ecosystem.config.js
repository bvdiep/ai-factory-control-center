module.exports = {
  apps: [
    {
      name: "ai-factory-control-center",
      script: "app/main.py",
      interpreter: "./.venv/bin/python",
      env: {
        PORT: 5001,
        NODE_ENV: "production"
      },
      watch: false,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: "/home/dd/work/diep/ai-factory-control-center-data/logs/err.log",
      out_file: "/home/dd/work/diep/ai-factory-control-center-data/logs/out.log",
      merge_logs: true,
      autorestart: true
    }
  ]
};
