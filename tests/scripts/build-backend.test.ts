import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { execSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'

const ROOT = path.resolve(__dirname, '../..')
const SCRIPT = path.join(ROOT, 'scripts', 'build-backend.sh')

describe('build-backend.sh', () => {
  describe('script structure', () => {
    it('script file exists', () => {
      expect(fs.existsSync(SCRIPT)).toBe(true)
    })

    it('is executable', () => {
      const stat = fs.statSync(SCRIPT)
      // Check owner execute bit (0o100)
      expect(stat.mode & 0o111).toBeGreaterThan(0)
    })

    it('has bash shebang', () => {
      const content = fs.readFileSync(SCRIPT, 'utf-8')
      expect(content.startsWith('#!/usr/bin/env bash')).toBe(true)
    })

    it('passes bash syntax check', () => {
      // bash -n checks syntax without executing
      expect(() => execSync(`bash -n "${SCRIPT}"`)).not.toThrow()
    })

    it('uses set -euo pipefail for safety', () => {
      const content = fs.readFileSync(SCRIPT, 'utf-8')
      expect(content).toContain('set -euo pipefail')
    })
  })

  describe('script content', () => {
    let content: string

    beforeAll(() => {
      content = fs.readFileSync(SCRIPT, 'utf-8')
    })

    it('references python-build-standalone', () => {
      expect(content).toContain('python-build-standalone')
    })

    it('targets extraResources/python output', () => {
      expect(content).toContain('extraResources/python')
    })

    it('targets extraResources/backend output', () => {
      expect(content).toContain('extraResources/backend')
    })

    it('runs uv sync --no-dev', () => {
      expect(content).toContain('uv sync --no-dev')
    })

    it('handles platform detection for macOS and Linux', () => {
      expect(content).toContain('darwin')
      expect(content).toContain('aarch64')
    })

    it('cleans up downloaded archives', () => {
      // Should remove the tarball after extraction
      expect(content).toMatch(/rm\s.*\$tarball/)
    })
  })

  describe('integration', () => {
    const outDir = path.join(ROOT, 'extraResources')

    afterAll(() => {
      // Clean up extraResources created by the test
      if (fs.existsSync(outDir)) {
        fs.rmSync(outDir, { recursive: true })
      }
    })

    it('runs successfully and produces expected output structure', () => {
      // This test actually runs the script — may take a minute to download python
      execSync(`bash "${SCRIPT}"`, {
        cwd: ROOT,
        stdio: 'pipe',
        timeout: 300_000 // 5 min timeout for download
      })

      // python binary exists
      const pythonBin = path.join(outDir, 'python', 'bin', 'python3.11')
      expect(fs.existsSync(pythonBin)).toBe(true)

      // python binary is executable
      const stat = fs.statSync(pythonBin)
      expect(stat.mode & 0o111).toBeGreaterThan(0)

      // python actually works
      const version = execSync(`"${pythonBin}" --version`, { encoding: 'utf-8' })
      expect(version).toContain('Python 3.11')

      // backend app code exists
      expect(fs.existsSync(path.join(outDir, 'backend', 'app', 'main.py'))).toBe(true)
      expect(fs.existsSync(path.join(outDir, 'backend', 'pyproject.toml'))).toBe(true)

      // venv with site-packages exists
      const venvDir = path.join(outDir, 'backend', '.venv')
      expect(fs.existsSync(venvDir)).toBe(true)

      // fastapi is installed in the venv
      const sitePackages = execSync(
        `find "${venvDir}" -type d -name "fastapi" | head -1`,
        { encoding: 'utf-8' }
      ).trim()
      expect(sitePackages).toContain('fastapi')
    }, 300_000)
  })
})
