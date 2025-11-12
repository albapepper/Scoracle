import React, { act } from 'react';
import { renderHook } from '@testing-library/react';
import { SportContextProvider, useSportContext } from '../SportContext';

test('SportContext provides default sport and can change', () => {
  const { result } = renderHook(() => useSportContext(), { wrapper: ({ children }) => <SportContextProvider>{children}</SportContextProvider> });
  expect(result.current.activeSport).toBe('football');
  act(() => result.current.changeSport('nba'));
  expect(result.current.activeSport).toBe('nba');
});