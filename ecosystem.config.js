module.exports = {
  apps: [
    {
      name: 'food-finder-api',
      cwd: '/home/vincent/food-finder',
      script: '/usr/bin/python3',
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
        PORT: '3001',
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 1000,
    },
  ],
};
