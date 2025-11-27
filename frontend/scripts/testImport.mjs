(async () => {
  try {
    const mod = await import('vite');
    console.log('vite import succeeded ->', typeof mod.createServer === 'function' ? 'Node API available' : 'module loaded');
  } catch (e) {
    console.error('vite import failed', e);
    process.exit(1);
  }
})();
