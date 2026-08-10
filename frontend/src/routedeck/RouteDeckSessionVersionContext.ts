import { createContext, useContext } from "react";


export const RouteDeckSessionVersionContext = createContext(0);

export function useRouteDeckSessionVersion(): number {
  return useContext(RouteDeckSessionVersionContext);
}
