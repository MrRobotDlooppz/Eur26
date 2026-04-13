/* ============================================
   Firebase Config — Archivo de Viajes
   
   NOTA: Estas keys son PÚBLICAS por diseño de Firebase.
   La seguridad está en las Firestore Security Rules,
   no en ocultar estas credenciales.
   
   Para configurar tu proyecto:
   1. Ir a console.firebase.google.com
   2. Project Settings → General → Your apps → Web
   3. Copiar los valores aquí
   ============================================ */

const firebaseConfig = {
  apiKey: "AIzaSyDJK-eYZ9Ng5oN1W-_-yaYuq9ZY8oZuQ10",
  authDomain: "vitacoradeviajeeur26.firebaseapp.com",
  projectId: "vitacoradeviajeeur26",
  storageBucket: "vitacoradeviajeeur26.firebasestorage.app",
  messagingSenderId: "764866785718",
  appId: "1:764866785718:web:0afdfbd8b7f6bb16c69117"
};

// Inicializar Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// Mapeo UID → nombre display (se llena al autenticar)
const USER_NAMES = {
  "lucca": "Lucca",
  "marti": "Marti",
  "ale": "Ale",
  "pablo": "Pablo",
  "carlita": "Carlita"
};

/**
 * Obtiene el nombre display del usuario autenticado.
 * Usa el displayName de Firebase Auth, o extrae del email.
 */
function getDisplayName(user) {
  if (user.displayName) return user.displayName;
  const local = (user.email || "").split("@")[0].toLowerCase();
  return USER_NAMES[local] || local;
}
