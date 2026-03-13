import { describe, it, expect, vi, beforeEach } from 'vitest'
import path from 'node:path'

// We test packaged-mode path resolution by mocking app.isPackaged = true
// and verifying the sidecar builds correct paths and environment.

// Mutable mock values for electron app
let mockIsPackaged = true
let mockResourcesPath = '/MockApp.app/Contents/Resources'
let mockAppPath = '/MockApp.app/Contents/Resources/app.asar'
let mockUserDataPath = '/Users/testuser/Library/Application Support/KnowHive'

vi.mock('electron', () => ({
  app: {
    get isPackaged() { return mockIsPackaged },
    getAppPath: () => mockAppPath,
    getPath: (name: string) => {
      if (name === 'userData') return mockUserDataPath
      return mockAppPath
    }
  }
}))

// Override process.resourcesPath for tests
Object.defineProperty(process, 'resourcesPath', {
  get: () => mockResourcesPath,
  configurable: true
})

vi.mock('../../electron/port', () => ({
  findSidecarPort: vi.fn(async () => 18234)
}))

// Import after mocks
import { SidecarManager } from '../../electron/sidecar'

describe('SidecarManager — packaged mode', () => {
  beforeEach(() => {
    mockIsPackaged = true
    mockResourcesPath = '/MockApp.app/Contents/Resources'
    mockAppPath = '/MockApp.app/Contents/Resources/app.asar'
    mockUserDataPath = '/Users/testuser/Library/Application Support/KnowHive'
  })

  describe('path resolution', () => {
    it('resolves python binary from extraResources on macOS/Linux', () => {
      const mgr = new SidecarManager()
      // Access private method via casting
      const pythonPath = (mgr as any).resolvePythonPath()
      expect(pythonPath).toBe(
        path.join(mockResourcesPath, 'python', 'bin', 'python3.11')
      )
    })

    it('resolves python binary for Windows when platform is win32', () => {
      const origPlatform = process.platform
      Object.defineProperty(process, 'platform', { value: 'win32', configurable: true })

      const mgr = new SidecarManager()
      const pythonPath = (mgr as any).resolvePythonPath()
      expect(pythonPath).toBe(
        path.join(mockResourcesPath, 'python', 'python.exe')
      )

      Object.defineProperty(process, 'platform', { value: origPlatform, configurable: true })
    })

    it('resolves backend dir from extraResources', () => {
      const mgr = new SidecarManager()
      const backendDir = (mgr as any).resolveBackendDir()
      expect(backendDir).toBe(path.join(mockResourcesPath, 'backend'))
    })

    it('respects custom pythonPath override in packaged mode', () => {
      const mgr = new SidecarManager({ pythonPath: '/custom/python' })
      const pythonPath = (mgr as any).resolvePythonPath()
      expect(pythonPath).toBe('/custom/python')
    })

    it('respects custom backendDir override in packaged mode', () => {
      const mgr = new SidecarManager({ backendDir: '/custom/backend' })
      const backendDir = (mgr as any).resolveBackendDir()
      expect(backendDir).toBe('/custom/backend')
    })
  })

  describe('log directory', () => {
    it('uses userData path for logs in packaged mode', () => {
      const mgr = new SidecarManager()
      const logsDir = (mgr as any).resolveLogsDir()
      expect(logsDir).toBe(
        path.join(mockUserDataPath, 'logs')
      )
    })

    it('does NOT use app.getAppPath (asar) for logs', () => {
      const mgr = new SidecarManager()
      const logsDir = (mgr as any).resolveLogsDir()
      expect(logsDir).not.toContain('app.asar')
    })
  })

  describe('spawn environment', () => {
    it('sets VIRTUAL_ENV to backend .venv in packaged mode', () => {
      const mgr = new SidecarManager()
      const env = (mgr as any).buildSpawnEnv()
      expect(env['VIRTUAL_ENV']).toBe(
        path.join(mockResourcesPath, 'backend', '.venv')
      )
    })

    it('sets PYTHONPATH to venv site-packages', () => {
      const mgr = new SidecarManager()
      const env = (mgr as any).buildSpawnEnv()
      expect(env['PYTHONPATH']).toContain('site-packages')
      expect(env['PYTHONPATH']).toContain(path.join('.venv', 'lib', 'python3.11', 'site-packages'))
    })

    it('prepends venv bin to PATH', () => {
      const mgr = new SidecarManager()
      const env = (mgr as any).buildSpawnEnv()
      const venvBin = path.join(mockResourcesPath, 'backend', '.venv', 'bin')
      expect(env['PATH']).toMatch(new RegExp(`^${venvBin.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`))
    })

    it('sets Windows-style paths when platform is win32', () => {
      const origPlatform = process.platform
      Object.defineProperty(process, 'platform', { value: 'win32', configurable: true })

      const mgr = new SidecarManager()
      const env = (mgr as any).buildSpawnEnv()
      expect(env['PYTHONPATH']).toContain(path.join('.venv', 'Lib', 'site-packages'))
      expect(env['PATH']).toContain(path.join('.venv', 'Scripts'))

      Object.defineProperty(process, 'platform', { value: origPlatform, configurable: true })
    })
  })

  describe('build args', () => {
    it('uses direct python args (not uv) in packaged mode', () => {
      const mgr = new SidecarManager()
      // Need to set _port first
      ;(mgr as any)._port = 18234
      const args = (mgr as any).buildArgs()
      expect(args).toEqual(['-m', 'app.main', '--port', '18234'])
      // Should NOT contain 'run' (uv command)
      expect(args).not.toContain('run')
    })
  })
})

describe('SidecarManager — dev mode paths', () => {
  beforeEach(() => {
    mockIsPackaged = false
  })

  it('uses uv as python command in dev mode', () => {
    const mgr = new SidecarManager()
    const pythonPath = (mgr as any).resolvePythonPath()
    expect(pythonPath).toBe('uv')
  })

  it('uses app path + backend as backend dir in dev mode', () => {
    const mgr = new SidecarManager()
    const backendDir = (mgr as any).resolveBackendDir()
    expect(backendDir).toBe(path.join(mockAppPath, 'backend'))
  })

  it('uses app path for logs dir in dev mode', () => {
    const mgr = new SidecarManager()
    const logsDir = (mgr as any).resolveLogsDir()
    expect(logsDir).toBe(path.join(mockAppPath, 'logs'))
  })

  it('does NOT set VIRTUAL_ENV in dev mode', () => {
    const mgr = new SidecarManager()
    const originalVenv = process.env['VIRTUAL_ENV']
    delete process.env['VIRTUAL_ENV']
    const env = (mgr as any).buildSpawnEnv()
    expect(env['VIRTUAL_ENV']).toBeUndefined()
    if (originalVenv) process.env['VIRTUAL_ENV'] = originalVenv
  })
})
