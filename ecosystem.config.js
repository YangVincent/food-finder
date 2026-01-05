module.exports = {
  apps: [
    {
      name: 'food-finder-api',
      cwd: '/home/vincent/food-finder',
      script: '/home/vincent/food-finder/venv/bin/python',
      args: '-m uvicorn ui.api.main:app --host 0.0.0.0 --port 8000',
      env: {
        PYTHONPATH: '/home/vincent/food-finder',
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 1000,
    },
    {
      name: 'food-finder-web',
      cwd: '/home/vincent/food-finder/ui/web',
      script: 'npm',
      args: 'run preview',
      env: {
        NODE_ENV: 'production',
        PORT: '3003',
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 1000,
    },
    {
      name: 'food-finder-enrich',
      cwd: '/home/vincent/food-finder',
      script: '/home/vincent/food-finder/venv/bin/python',
      args: 'main.py enrich --batch 50',
      env: {
        PYTHONPATH: '/home/vincent/food-finder',
        PYTHONUNBUFFERED: '1',
      },
      autorestart: false,
      watch: false,
    },
  ],
};
