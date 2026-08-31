const { spawn } = require('child_process');
const path = require('path');

const rootDir = __dirname;
const backendDir = path.join(rootDir, 'backend');
const frontendDir = path.join(rootDir, 'frontend');

console.log('\x1b[36m%s\x1b[0m', '🐾 Starting Haven Pet Full Stack (Backend + Frontend)...');

// Start backend
const isWindows = process.platform === 'win32';
const pythonCmd = isWindows ? 'python' : 'python3';
const npxCmd = isWindows ? 'npx.cmd' : 'npx';

const backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000'], {
  cwd: backendDir,
  shell: true,
  stdio: ['inherit', 'pipe', 'pipe'],
  env: { ...process.env, PYTHONUNBUFFERED: '1' },
});

backendProcess.stdout.on('data', (data) => {
  process.stdout.write(`\x1b[34m[Backend]\x1b[0m ${data}`);
});

backendProcess.stderr.on('data', (data) => {
  process.stderr.write(`\x1b[34m[Backend]\x1b[0m ${data}`);
});

// Start frontend
const frontendProcess = spawn(npxCmd, ['vite', '--host'], {
  cwd: frontendDir,
  shell: true,
  stdio: ['inherit', 'pipe', 'pipe'],
});

frontendProcess.stdout.on('data', (data) => {
  process.stdout.write(`\x1b[32m[Frontend]\x1b[0m ${data}`);
});

frontendProcess.stderr.on('data', (data) => {
  process.stderr.write(`\x1b[32m[Frontend]\x1b[0m ${data}`);
});

const cleanup = () => {
  console.log('\n\x1b[33m%s\x1b[0m', '🛑 Shutting down Haven Pet servers...');
  try {
    if (backendProcess.pid) {
      if (isWindows) {
        spawn('taskkill', ['/pid', backendProcess.pid.toString(), '/f', '/t']);
      } else {
        backendProcess.kill('SIGTERM');
      }
    }
  } catch (e) {}

  try {
    if (frontendProcess.pid) {
      if (isWindows) {
        spawn('taskkill', ['/pid', frontendProcess.pid.toString(), '/f', '/t']);
      } else {
        frontendProcess.kill('SIGTERM');
      }
    }
  } catch (e) {}

  process.exit(0);
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', cleanup);
