import { existsSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const frontendDir = resolve(rootDir, 'frontend')
const viteCli = resolve(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js')
const pythonCandidates = process.platform === 'win32'
  ? [resolve(rootDir, '.venv', 'Scripts', 'python.exe'), resolve(rootDir, 'venv', 'Scripts', 'python.exe')]
  : [resolve(rootDir, '.venv', 'bin', 'python'), resolve(rootDir, 'venv', 'bin', 'python')]

let apiProcess
let frontendProcess
let ownsApiProcess = false

function isRunning(process) {
  return process && process.exitCode === null && process.signalCode === null
}

async function apiIsHealthy() {
  try {
    const response = await fetch('http://127.0.0.1:8000/health')
    return response.ok
  } catch {
    return false
  }
}

async function waitForApi(child) {
  const deadline = Date.now() + 15000
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`API exited with code ${child.exitCode}`)
    }
    if (await apiIsHealthy()) return
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 250))
  }
  throw new Error('API did not become healthy within 15 seconds')
}

async function main() {
  if (!existsSync(viteCli)) {
    throw new Error('Frontend dependencies are missing. Run npm install in frontend/.')
  }

  if (await apiIsHealthy()) {
    console.log('Using the API already running at http://127.0.0.1:8000')
  } else {
    const python = pythonCandidates.find((candidate) => existsSync(candidate))
    if (!python) {
      throw new Error('Python environment not found. Create .venv and install backend/requirements.txt first.')
    }

    console.log('Starting the API at http://127.0.0.1:8000')
    apiProcess = spawn(python, [
      '-m', 'uvicorn', 'app.main:app', '--app-dir', 'backend', '--reload',
      '--reload-dir', 'backend',
      '--host', '127.0.0.1', '--port', '8000',
    ], { cwd: rootDir, stdio: 'inherit' })
    ownsApiProcess = true
    await waitForApi(apiProcess)
  }

  console.log('Starting the frontend; open the Vite URL printed below.')
  frontendProcess = spawn(process.execPath, [viteCli], {
    cwd: frontendDir,
    stdio: 'inherit',
  })

  process.on('SIGINT', () => {
    frontendProcess.kill('SIGINT')
    if (ownsApiProcess && isRunning(apiProcess)) apiProcess.kill('SIGINT')
  })
  process.on('SIGTERM', () => {
    frontendProcess.kill('SIGTERM')
    if (ownsApiProcess && isRunning(apiProcess)) apiProcess.kill('SIGTERM')
  })

  const exitCode = await new Promise((resolveExit, rejectExit) => {
    frontendProcess.once('error', rejectExit)
    frontendProcess.once('exit', resolveExit)
  })
  if (ownsApiProcess && isRunning(apiProcess)) apiProcess.kill()
  process.exitCode = exitCode ?? 0
}

main().catch((error) => {
  console.error(error.message)
  if (ownsApiProcess && isRunning(apiProcess)) apiProcess.kill()
  process.exitCode = 1
})