export interface SportInfo { id: string; display: string; }
export interface SportContextValue { activeSport: string; sports: SportInfo[]; changeSport: (id: string) => void; }
export function useSportContext(): SportContextValue;