import { useLayoutEffect, useRef } from "react";

export function useInitialFieldFocus() {
  const ref = useRef<HTMLInputElement>(null);
  useLayoutEffect(() => {
    ref.current?.focus();
  }, []);
  return ref;
}
