const fs = require('fs');
const path = require('path');

const repoRoot = process.cwd();
const srcDir = path.join(repoRoot, 'src');

if (!fs.existsSync(srcDir)) {
  console.error('Error: src/ directory not found. Run from repo root.');
  process.exit(1);
}

const htmlFiles = fs.readdirSync(srcDir).filter(file => file.endsWith('.html'));
const pageNames = ['index', 'about', 'services', 'projects', 'contact', 'blogs'];

htmlFiles.forEach(file => {
  const filePath = path.join(srcDir, file);
  let content = fs.readFileSync(filePath, 'utf8');

  // normalize internal page links to ./page.html and home -> index
  content = content.replace(/(href|src)=(["'])(?:\.\/)?home\.html\2/g, '$1=$2./index.html$2');
  content = content.replace(/(href|src)=(["'])(?:\.\/)?index\.html\2/g, '$1=$2./index.html$2');

  pageNames.forEach(page => {
    if (page === 'index') return;
    const regex = new RegExp(`(href|src)=(['"])(?:\./)?${page}\.html\\2`, 'g');
    content = content.replace(regex, `$1=$2./${page}.html$2`);
  });

  // normalize asset paths for local assets
  const assetPrefixes = ['assets', 'css', 'js', 'images', 'img', 'fonts', 'static'];
  assetPrefixes.forEach(prefix => {
    const re = new RegExp(`(href|src)=(["'])(?:\\/)?${prefix}\\/`, 'g');
    content = content.replace(re, `$1=$2./${prefix}/`);
  });

  // avoid duplicate .//
  content = content.replace(/\.\/\./g, './');

  fs.writeFileSync(filePath, content, 'utf8');
  console.log(`Updated ${file}`);
});

console.log('HTML link update complete.');
