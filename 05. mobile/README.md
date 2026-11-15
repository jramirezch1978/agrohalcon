# App móvil de AllpaShift (Android e iOS)

La app móvil es el **mismo frontend** (`03. frontend`) empaquetado con **Capacitor 6** (compila con Java 17).
Los archivos web van dentro de la app y esta llama a la API Java del servidor (regla 1 del doc 29).

| Qué | Dónde |
|---|---|
| APK de Android (debug, listo para instalar) | `release/android/allpashift-1.0.0.apk` |
| Proyecto de iOS para Xcode (en una Mac: abrir `App/App.xcworkspace` → Product → Archive) | `release/ios/allpashift-ios-xcode.zip` |
| Proyecto nativo Android / iOS | `03. frontend/android`, `03. frontend/ios` |

## Diseño móvil
- Barra de estado verde `#0f2a1f` con texto claro; pantalla de inicio (splash) con el logo.
- Botón "atrás" de Android: vuelve a la pantalla anterior; en la portada cierra la app.
- Ubicación con GPS (permiso explicado en iOS), navegación inferior y áreas seguras (notch).
- API: `VITE_API_URL=http://2.29.101.199` (`03. frontend/.env.mobile`). Cuando haya HTTPS (Cloudflare) se cambia aquí y se quita `usesCleartextTraffic` / `NSAllowsArbitraryLoads`.

## Volver a generar
```bash
cd "03. frontend"
npm install
npm run android:sync
cd android
gradlew.bat assembleDebug
```
Requisitos: Java 17 (`JAVA_HOME`) y Android SDK 34 o superior.
