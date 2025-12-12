import { useState, useEffect } from 'react';
import { IconSun, IconMoon, IconDeviceDesktop } from '@tabler/icons-react';
import { getInitialTheme, applyTheme, type ColorScheme } from '../lib/utils/theme';

export default function ThemeToggle() {
  const [scheme, setScheme] = useState<ColorScheme>('system');

  useEffect(() => {
    const initial = getInitialTheme();
    setScheme(initial);
    applyTheme(initial);

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (scheme === 'system') {
        applyTheme('system');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [scheme]);

  const handleToggle = () => {
    const schemes: ColorScheme[] = ['light', 'dark', 'system'];
    const currentIndex = schemes.indexOf(scheme);
    const next = schemes[(currentIndex + 1) % schemes.length];
    setScheme(next);
    applyTheme(next);
  };

  const getIcon = () => {
    switch (scheme) {
      case 'light':
        return <IconSun size={20} />;
      case 'dark':
        return <IconMoon size={20} />;
      case 'system':
        return <IconDeviceDesktop size={20} />;
    }
  };

  return (
    <button
      onClick={handleToggle}
      className="btn btn-secondary"
      aria-label="Toggle theme"
      title={`Current: ${scheme}`}
    >
      {getIcon()}
    </button>
  );
}
