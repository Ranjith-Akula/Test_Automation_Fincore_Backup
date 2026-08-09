const fs = require('fs');
const path = require('path');

describe('UI configuration', () => {
  it('defaults the Vite dev server to port 3000 and uses a same-origin API base URL', () => {
    const viteConfigPath = path.join(__dirname, '..', 'client', 'vite.config.js');
    const viteConfig = fs.readFileSync(viteConfigPath, 'utf8');

    expect(viteConfig).toContain('3000');
    expect(viteConfig).not.toContain('30000');

    const apiServicePath = path.join(__dirname, '..', 'client', 'src', 'services', 'api.js');
    const apiService = fs.readFileSync(apiServicePath, 'utf8');

    expect(apiService).toContain("'/api/v1'");
  });
});
