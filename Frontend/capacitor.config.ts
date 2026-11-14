import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.agroshift.app',
  appName: 'AgroShift',
  webDir: 'dist',
  backgroundColor: '#0f2a1f',
  android: {
    // Permite llamar a un backend http:// en la red local durante la demo
    allowMixedContent: true,
  },
}

export default config
