
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const isWindows = process.platform === 'win32';

function run(command, cwd = process.cwd()) {
  console.log(`\n> Running: ${command} in ${cwd}`);
  try {
    execSync(command, { stdio: 'inherit', cwd });
  } catch (error) {
    console.error(`Command failed: ${command}`);
    process.exit(1);
  }
}

console.log('=== Paper Classifier One-Step Setup ===');

// 1. Install root dependencies
console.log('\n--- 1/4 Installing root dependencies ---');
run('npm install');

// 2. Install frontend dependencies
console.log('\n--- 2/4 Installing frontend dependencies ---');
run('npm install', path.join(__dirname, 'frontend'));

// 3. Setup Python Backend
console.log('\n--- 3/4 Setting up Python virtual environment ---');
const backendDir = path.join(__dirname, 'backend');
const venvPath = path.join(backendDir, 'venv');

if (!fs.existsSync(venvPath)) {
  run('python3 -m venv venv', backendDir);
} else {
  console.log('Virtual environment already exists.');
}

// 4. Install Python requirements
console.log('\n--- 4/4 Installing Python dependencies ---');
const pipPath = isWindows 
  ? path.join('venv', 'Scripts', 'pip')
  : path.join('venv', 'bin', 'pip');

run(`${pipPath} install -r requirements.txt`, backendDir);

console.log('\n========================================');
console.log('Setup Complete!');
console.log('You can now run "npm start" to launch the app.');
console.log('========================================');
