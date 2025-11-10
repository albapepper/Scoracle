import React, { act } from 'react';
import { renderHook } from '@testing-library/react';
import { ThemeProvider, useThemeMode } from '../index';

test('ThemeProvider toggles color scheme', () => {
  const { result } = renderHook(() => useThemeMode(), { wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider> });
  const initial = result.current.colorScheme;
  act(() => result.current.toggleColorScheme());
  expect(result.current.colorScheme).not.toBe(initial);
});