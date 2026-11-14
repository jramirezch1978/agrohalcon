/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_USE_MOCK: string
  /** Opcional: servicio de cálculos en Python (modo híbrido) */
  readonly VITE_CALCULOS_URL?: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}
