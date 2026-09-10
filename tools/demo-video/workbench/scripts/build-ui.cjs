// Standalone workbench only: not an ARO/Next/Eve build. Reuses installed tooling.
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const modules = process.env.OPS_BUILD_MODULES || path.join(process.env.HOME, 'projects/win-agent-os/node_modules');
require(path.join(modules, 'esbuild')).buildSync({entryPoints:[path.join(root,'web/app.jsx')],bundle:true,minify:true,format:'iife',platform:'browser',outfile:path.join(root,'web/app.js'),nodePaths:[modules],define:{'process.env.NODE_ENV':'"production"'},legalComments:'eof'});
console.log('独立运维界面打包完成；运行不依赖原项目 node_modules。');
