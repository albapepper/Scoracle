export type ColorScheme = 'light' | 'dark' | 'system';

export function getInitialTheme(): ColorScheme {
  if (typeof window === 'undefined') return 'system';
  
  const stored = localStorage.getItem('color-scheme') as ColorScheme | null;
  if (stored && ['light', 'dark', 'system'].includes(stored)) {
    return stored;
  }
  return 'system';
}

export function applyTheme(scheme: ColorScheme): void {
  if (typeof window === 'undefined') return;

  let effective: 'light' | 'dark';
  
  if (scheme === 'system') {
    effective = window.matchMedia('(prefers-color-scheme: dark)').matches 
      ? 'dark' 
      : 'light';
  } else {
    effective = scheme;
  }

  document.documentElement.classList.toggle('dark', effective === 'dark');
  localStorage.setItem('color-scheme', scheme);
}

export function toggleTheme(): ColorScheme {
  const current = getInitialTheme();
  const schemes: ColorScheme[] = ['light', 'dark', 'system'];
  const currentIndex = schemes.indexOf(current);
  const next = schemes[(currentIndex + 1) % schemes.length];
  applyTheme(next);
  return next;
}
