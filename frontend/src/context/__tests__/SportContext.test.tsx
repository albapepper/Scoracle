import React, { act } from 'react';
import { renderHook } from '@testing-library/react';
// eslint-disable-next-line @typescript-eslint/no-var-requires
const Ctx = require('../SportContext');
const Provider = Ctx.SportContextProvider as React.ComponentType<{children: React.ReactNode}>;
const useSportContext = Ctx.useSportContext as () => { activeSport: string; changeSport: (id: string) => void };

test('SportContext provides default sport and can change', () => {
  const { result } = renderHook(() => useSportContext(), { wrapper: ({ children }) => <Provider>{children}</Provider> });
  expect(result.current.activeSport).toBe('soccer');
  act(() => result.current.changeSport('basketball'));
  expect(result.current.activeSport).toBe('basketball');
});